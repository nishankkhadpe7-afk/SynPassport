"""Assurance agent execution loop.

Manages plan-generate-evaluate-diagnose-repair cycles under strict candidate
and repair budgets enforced in code. Enforces process and holdout isolation.
The agent never assigns verdicts and never selects the winning candidate.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from synpassport.agent.cache import ReplayCache, compute_replay_key
from synpassport.agent.explanation import generate_explanation
from synpassport.agent.llm import BaseLLMClient, MockLLM, query_llm_structured
from synpassport.agent.prompts import (
    SYSTEM_PROMPT,
    format_agent_context,
    sanitize_schema_summary,
)
from synpassport.agent.repairs import validate_repair_action
from synpassport.agent.tools import AgentToolRegistry
from synpassport.checks.run import run_checks_pipeline
from synpassport.checks.splitter import split_train_holdout
from synpassport.generators.base import BaseGenerator
from synpassport.generators.sdv_wrapper import CTGANGenerator, GaussianCopulaGenerator
from synpassport.passport.builder import build_passport, get_code_version
from synpassport.policy.engine import evaluate_policy
from synpassport.policy.loader import load_policy

__all__ = ["AssuranceAgentLoop"]


class AssuranceAgentLoop:
    """Executes bounded assurance loop and dispatches structured actions."""

    def __init__(
        self,
        llm_client: BaseLLMClient | None = None,
        max_candidates: int = 3,
        max_repairs: int = 2,
        cache_dir: str | Path = "./replay",
        replay_mode: bool = False,
        event_listener: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.llm_client: BaseLLMClient = llm_client or MockLLM()
        self.max_candidates = max_candidates
        self.max_repairs = max_repairs
        self.candidates_evaluated = 0
        self.repairs_attempted = 0
        self.agent_rejections: list[dict[str, str]] = []
        self.repairs_log: list[dict[str, Any]] = []
        self.tool_registry = AgentToolRegistry()
        self.replay_cache = ReplayCache(cache_dir=cache_dir)
        self.replay_mode = replay_mode
        self.event_listener = event_listener

    def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit run event to registered listener."""
        if self.event_listener is not None:
            try:
                self.event_listener(event_type, data)
            except Exception:
                pass

    def run(
        self,
        real_data_path: str | Path,
        mission: dict[str, Any],
        policy_id_or_path: str | Path,
        output_dir: str | Path = "./data/agent_runs",
        holdout_path: str | Path | None = None,
        signing_key: Any = None,
        seed: int = 1234,
        target_col: str | None = None,
    ) -> dict[str, Any]:
        """Execute assurance cycle and return final evaluation bundle with passport."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        policy = load_policy(policy_id_or_path)
        policy_id = str(policy.get("id", "custom-policy"))

        # Budget from policy or class defaults
        policy_budget = policy.get("budget", {})
        self.max_candidates = int(policy_budget.get("max_candidates", self.max_candidates))
        self.max_repairs = int(policy_budget.get("max_repairs", self.max_repairs))

        self._emit("step", {"phase": "plan", "message": "Planning assurance run..."})

        # Check replay cache
        cache_key = compute_replay_key(mission=mission, policy_id=policy_id, seed=seed)
        if self.replay_mode and self.replay_cache.has(cache_key):
            cached = self.replay_cache.get(cache_key)
            if cached is not None:
                self._emit("step", {"phase": "replay", "message": "Loaded run from replay cache"})
                if "candidates" in cached:
                    for c in cached["candidates"]:
                        self._emit("candidate", {
                            "candidate_id": c.get("candidate_id"),
                            "verdicts": c.get("verdicts", {}),
                        })
                else:
                    self._emit("candidate", {
                        "candidate_id": cached.get("best_candidate_id", "candidate_001"),
                        "verdicts": cached.get("verdicts", {}),
                    })
                if "repairs" in cached:
                    for r in cached["repairs"]:
                        self._emit("repair", r)
                if "agent_rejections" in cached:
                    for rej in cached["agent_rejections"]:
                        self._emit("rejection", rej)
                self._emit("finalized", {
                    "best_candidate_id": cached.get("best_candidate_id"),
                    "verdicts": cached.get("verdicts", {}),
                })
                # Materialize candidate CSV in output_dir so callers can inspect/verify it
                cand_name = str(
                    cached.get("passport", {})
                    .get("dataset", {})
                    .get("name", "candidate_001.csv")
                )
                cand_dest = out_dir / cand_name
                if not cand_dest.is_file():
                    real_df = pd.read_csv(real_data_path)
                    split = split_train_holdout(real_df, train_ratio=0.5, seed=seed)
                    gen_copula = GaussianCopulaGenerator(seed=seed)
                    gen_copula.fit(split.train_df)
                    synth_df = gen_copula.sample(num_rows=len(split.train_df), seed=seed)
                    synth_df.to_csv(cand_dest, index=False)
                return cached

        # Load and partition dataset
        real_df = pd.read_csv(real_data_path)
        if holdout_path and Path(holdout_path).is_file():
            train_df = real_df
            holdout_df = pd.read_csv(holdout_path)
        else:
            split = split_train_holdout(real_df, train_ratio=0.5, seed=seed)
            train_df = split.train_df
            holdout_df = split.holdout_df

        train_csv = out_dir / "train_partition.csv"
        holdout_csv = out_dir / "holdout_partition.csv"
        train_df.to_csv(train_csv, index=False)
        holdout_df.to_csv(holdout_csv, index=False)

        # Sanitized schema summary for prompt context (NO raw rows, NO holdout)
        dtypes_map = {col: str(train_df[col].dtype) for col in train_df.columns}
        schema_summary = sanitize_schema_summary(
            columns=list(train_df.columns),
            dtypes=dtypes_map,
            row_count=len(train_df),
        )

        current_generator = "GaussianCopula"
        current_params: dict[str, Any] = {}
        candidate_history: list[dict[str, Any]] = []

        # -------------------------------------------------------------
        # Main Loop: plan -> generate -> evaluate -> diagnose -> repair
        # -------------------------------------------------------------
        while True:
            # 1. Budget enforcement in code: Candidate Cap (max 3)
            if self.candidates_evaluated >= self.max_candidates:
                break

            cand_idx = self.candidates_evaluated + 1
            candidate_id = f"candidate_{cand_idx:03d}"
            cand_csv = out_dir / f"{candidate_id}.csv"

            # 2. Generator instantiation and sampling
            cand_seed = seed + self.candidates_evaluated * 10
            gen: BaseGenerator
            if current_generator == "CTGAN":
                epochs = int(current_params.get("epochs", 50))
                gen = CTGANGenerator(epochs=epochs, seed=cand_seed)
            else:
                gen = GaussianCopulaGenerator(seed=cand_seed)

            gen.fit(train_df)
            synth_df = gen.sample(num_rows=len(train_df), seed=cand_seed)
            synth_df.to_csv(cand_csv, index=False)
            self.candidates_evaluated += 1
            self._emit(
                "candidate",
                {"candidate_id": candidate_id, "generator": current_generator},
            )

            # 3. Evaluation engine (runs 8 checks against holdout isolated partition)
            evidence_records = run_checks_pipeline(
                data_path=train_csv,
                synth_path=cand_csv,
                policy_id_or_path=policy_id_or_path,
                holdout_path=holdout_csv,
                db_path=out_dir / "evidence.db",
                candidate_id=candidate_id,
                seed=cand_seed,
                target_col=target_col,
            )

            # 4. Deterministic policy engine verdicts
            verdicts = evaluate_policy(policy, evidence_records)
            self._emit(
                "evaluation",
                {"candidate_id": candidate_id, "verdicts": verdicts},
            )

            fail_count = sum(1 for v in verdicts.values() if v == "FAIL")
            inconclusive_count = sum(1 for v in verdicts.values() if v == "INSUFFICIENT_EVIDENCE")
            numeric_vals = [r.value for r in evidence_records if r.value is not None]
            mean_score = float(np.mean(numeric_vals)) if numeric_vals else 0.0

            cand_record = {
                "candidate_id": candidate_id,
                "generator": current_generator,
                "params": copy.deepcopy(current_params),
                "csv_path": str(cand_csv),
                "evidence": evidence_records,
                "verdicts": verdicts,
                "fail_count": fail_count,
                "inconclusive_count": inconclusive_count,
                "mean_score": mean_score,
            }
            candidate_history.append(cand_record)

            # Check if all required uses pass
            if all(v == "PASS" for v in verdicts.values()):
                break

            # 5. Budget enforcement in code: Repair Cap (max 2)
            if self.repairs_attempted >= self.max_repairs:
                break

            # 6. Agent Turn: Diagnose and propose repair
            budget_state = {
                "candidates_evaluated": self.candidates_evaluated,
                "max_candidates": self.max_candidates,
                "repairs_attempted": self.repairs_attempted,
                "max_repairs": self.max_repairs,
            }
            context_prompt = format_agent_context(
                mission=mission,
                policy=policy,
                schema_summary=schema_summary,
                candidate_history=candidate_history,
                budget_state=budget_state,
                agent_rejections=self.agent_rejections,
            )

            decision, err_logs = query_llm_structured(
                client=self.llm_client,
                prompt=context_prompt,
                system_prompt=SYSTEM_PROMPT,
                tool_registry=self.tool_registry,
                max_retries=3,
            )

            # Record any rejected attempts or schema errors from the turn
            for err in err_logs:
                proposal_name = "LLM turn error"
                if " rejected: " in err:
                    raw_prop = err.split(" rejected: ")[0]
                    if raw_prop.startswith("Action '") and raw_prop.endswith("'"):
                        proposal_name = raw_prop[8:-1]
                    else:
                        proposal_name = raw_prop
                self.agent_rejections.append({
                    "proposal": proposal_name,
                    "reason": err,
                })
                self._emit("rejection", {"proposal": proposal_name, "reason": err})

            if decision is None:
                break

            action = str(decision.get("action"))
            args = decision.get("args") or {}

            if action == "finalize":
                break

            if action == "propose_repair":
                repair_action = str(args.get("action"))
                repair_params = args.get("params") or {}

                # Validate proposal against strict whitelist
                is_valid, reason = validate_repair_action(repair_action, repair_params)
                if not is_valid:
                    self.agent_rejections.append({
                        "proposal": f"{repair_action}: {repair_params}",
                        "reason": reason,
                    })
                    self._emit("rejection", {"proposal": repair_action, "reason": reason})
                    break

                # Apply whitelisted repair
                self.repairs_log.append({
                    "action": repair_action,
                    "params": repair_params,
                    "candidate_id": candidate_id,
                })
                self.repairs_attempted += 1
                self._emit("repair", {
                    "action": repair_action,
                    "params": repair_params,
                    "candidate_id": candidate_id,
                })

                if repair_action == "tune_hyperparameters":
                    current_params.update(repair_params)
                elif repair_action == "switch_generator":
                    current_generator = repair_params.get(
                        "target_generator",
                        "CTGAN" if current_generator == "GaussianCopula" else "GaussianCopula",
                    )
                elif repair_action == "enable_dp_training":
                    current_params["dp_enabled"] = True
            else:
                # Any other proposal not part of repair flow is rejected
                self.agent_rejections.append({
                    "proposal": action,
                    "reason": f"Action '{action}' is not permitted during repair step",
                })
                self._emit("rejection", {
                    "proposal": action,
                    "reason": f"Action '{action}' is not permitted during repair step",
                })
                break

        # -------------------------------------------------------------
        # Candidate Selection by Deterministic Policy Engine Ordering
        # (fewest FAIL -> fewest INSUFFICIENT -> highest aggregate)
        # -------------------------------------------------------------
        candidate_history.sort(
            key=lambda c: (c["fail_count"], c["inconclusive_count"], -c["mean_score"])
        )
        best_candidate = candidate_history[0]

        # -------------------------------------------------------------
        # Post-run Explanation with Evidence Citations
        # -------------------------------------------------------------
        explanation_bundle = generate_explanation(best_candidate["evidence"])

        # -------------------------------------------------------------
        # Passport Assembly
        # -------------------------------------------------------------
        run_info = {
            "code_version": get_code_version(),
            "seeds": [seed],
            "candidates_evaluated": self.candidates_evaluated,
            "repairs_attempted": self.repairs_attempted,
        }

        passport = build_passport(
            dataset_path=best_candidate["csv_path"],
            mission=mission,
            policy=policy,
            evidence=best_candidate["evidence"],
            verdicts=best_candidate["verdicts"],
            run_info=run_info,
            repairs=self.repairs_log,
            agent_rejections=self.agent_rejections,
            signing_key=signing_key,
        )

        self._emit("finalized", {
            "best_candidate_id": best_candidate["candidate_id"],
            "verdicts": best_candidate["verdicts"],
        })

        candidates_summary = [
            {
                "candidate_id": c["candidate_id"],
                "generator": c["generator"],
                "verdicts": c["verdicts"],
                "fail_count": c["fail_count"],
                "inconclusive_count": c["inconclusive_count"],
                "mean_score": c["mean_score"],
                "csv_path": c["csv_path"],
            }
            for c in candidate_history
        ]

        final_bundle: dict[str, Any] = {
            "best_candidate_id": best_candidate["candidate_id"],
            "candidates_evaluated": self.candidates_evaluated,
            "repairs_attempted": self.repairs_attempted,
            "verdicts": best_candidate["verdicts"],
            "candidates": candidates_summary,
            "repairs": copy.deepcopy(self.repairs_log),
            "agent_rejections": copy.deepcopy(self.agent_rejections),
            "explanation": explanation_bundle,
            "passport": passport.to_dict(),
        }

        # Save to replay cache
        self.replay_cache.save(cache_key, final_bundle)

        return final_bundle
