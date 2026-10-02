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
from synpassport.agent.llm import (
    BaseLLMClient,
    MockLLM,
    RuleBasedPlanner,
    describe_llm_client,
    query_llm_structured,
)
from synpassport.agent.prompts import (
    SYSTEM_PROMPT,
    format_agent_context,
    sanitize_schema_summary,
)
from synpassport.agent.repairs import normalize_target_generator, validate_repair_action
from synpassport.agent.tools import AgentToolRegistry
from synpassport.checks.run import run_checks_pipeline
from synpassport.checks.splitter import split_train_holdout
from synpassport.generators.base import BaseGenerator
from synpassport.generators.sdv_wrapper import CTGANGenerator, GaussianCopulaGenerator
from synpassport.passport.builder import EvidencePassport, build_passport, get_code_version
from synpassport.passport.canonical import hash_dataset_file
from synpassport.policy.engine import evaluate_policy_detailed
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

    def _load_replay(
        self,
        cache_key: str,
        real_data_path: str | Path,
        out_dir: Path,
        seed: int,
        signing_key: Any = None,
    ) -> dict[str, Any] | None:
        """Return a cached bundle in replay mode, or None to run live.

        The cached passport is only reused if the candidate CSV it is bound to can be
        reproduced byte-for-byte; otherwise the run proceeds live instead of returning a
        passport that would fail verification.
        """
        if not (self.replay_mode and self.replay_cache.has(cache_key)):
            return None
        cached = self.replay_cache.get(cache_key)
        if cached is None:
            return None

        passport = cached.get("passport") or {}
        dataset_block = passport.get("dataset") or {}
        cand_name = Path(str(dataset_block.get("name", ""))).name
        expected_sha = str(dataset_block.get("sha256", ""))
        if not cand_name or not expected_sha:
            return None

        # Regenerate the cached best candidate with the generator and seed it used.
        best_id = str(cached.get("best_candidate_id", ""))
        best = next(
            (c for c in cached.get("candidates", []) if c.get("candidate_id") == best_id),
            None,
        )
        if best is not None and best.get("generator") != "GaussianCopula":
            return None  # only the deterministic copula can be replayed exactly
        try:
            cand_index = int(best_id.rsplit("_", 1)[-1]) - 1
        except ValueError:
            return None
        cand_seed = seed + cand_index * 10

        cand_dest = out_dir / cand_name
        real_df = pd.read_csv(real_data_path)
        split = split_train_holdout(real_df, train_ratio=0.5, seed=seed)
        generator = GaussianCopulaGenerator(
            seed=cand_seed,
            regenerate_identifiers=bool(best.get("regenerate_identifiers")) if best else False,
        )
        generator.fit(split.train_df)
        generator.sample(num_rows=len(split.train_df), seed=cand_seed).to_csv(
            cand_dest, index=False, lineterminator="\n"
        )
        if hash_dataset_file(cand_dest) != expected_sha:
            cand_dest.unlink(missing_ok=True)
            self._emit(
                "step",
                {"phase": "replay", "message": "Replay cache stale for this data; running live"},
            )
            return None

        # Re-sign with the current key so replayed passports verify against it.
        if signing_key is not None:
            replayed = EvidencePassport(passport)
            replayed.sign(signing_key)
            cached = {**cached, "passport": replayed.to_dict()}

        self._emit("step", {"phase": "replay", "message": "Loaded run from replay cache"})
        for c in cached.get("candidates", []):
            self._emit(
                "candidate",
                {"candidate_id": c.get("candidate_id"), "verdicts": c.get("verdicts", {})},
            )
        for r in cached.get("repairs", []):
            self._emit("repair", r)
        for rej in cached.get("agent_rejections", []):
            self._emit("rejection", rej)
        self._emit(
            "finalized",
            {"best_candidate_id": best_id, "verdicts": cached.get("verdicts", {})},
        )
        return cached

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

        self._emit(
            "step",
            {
                "phase": "plan",
                "message": (
                    "Planning assurance run. Repair decisions by "
                    f"{describe_llm_client(self.llm_client)}."
                ),
            },
        )

        # Check replay cache (keyed on the input dataset too, so a different upload
        # with the same mission can never receive another dataset's passport)
        cache_key = compute_replay_key(
            mission=mission,
            policy_id=policy_id,
            seed=seed,
            dataset_sha256=hash_dataset_file(real_data_path),
        )
        cached_bundle = self._load_replay(cache_key, real_data_path, out_dir, seed, signing_key)
        if cached_bundle is not None:
            return cached_bundle

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

        # Evaluate the mission's first declared critical subgroup (default: age >= 65)
        mission_subgroups = mission.get("critical_subgroups") or []
        subgroup_query = str(mission_subgroups[0]) if mission_subgroups else "age >= 65"

        current_generator = "GaussianCopula"
        current_params: dict[str, Any] = {}
        regenerate_ids = False
        last_check_states: dict[str, str] = {}

        def rule_decision() -> dict[str, Any]:
            return RuleBasedPlanner.decide(
                current_generator,
                current_params,
                check_states=last_check_states,
                regenerating_identifiers=regenerate_ids,
            )
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
                gen = CTGANGenerator(
                    epochs=int(current_params.get("epochs", 50)),
                    batch_size=int(current_params.get("batch_size", 100)),
                    regenerate_identifiers=regenerate_ids,
                    seed=cand_seed,
                )
            else:
                gen = GaussianCopulaGenerator(
                    seed=cand_seed, regenerate_identifiers=regenerate_ids
                )

            gen.fit(train_df)
            # Record the model that actually produced the data (CTGAN may fall back).
            actual_generator = str(getattr(gen, "backend", current_generator))
            fallback_reason = getattr(gen, "fallback_reason", None)
            synth_df = gen.sample(num_rows=len(train_df), seed=cand_seed)
            # Fixed "\n" line endings so the signed bytes are identical on every OS.
            synth_df.to_csv(cand_csv, index=False, lineterminator="\n")
            self.candidates_evaluated += 1
            candidate_event: dict[str, Any] = {
                "candidate_id": candidate_id,
                "generator": actual_generator,
            }
            if fallback_reason:
                candidate_event["requested_generator"] = current_generator
                candidate_event["note"] = fallback_reason
            elif getattr(gen, "note", None):
                candidate_event["note"] = str(gen.note)
            if regenerate_ids and "note" not in candidate_event:
                ids = getattr(getattr(gen, "prep", None), "side_cols", [])
                candidate_event["note"] = (
                    f"{len(ids)} identifier column(s) replaced with fresh values in the same "
                    "format; no real identifier copied"
                )
            self._emit("candidate", candidate_event)

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
                subgroup_query=subgroup_query,
            )

            # 4. Deterministic policy engine verdicts
            bundle = evaluate_policy_detailed(policy, evidence_records)
            verdicts = bundle.verdicts
            check_states = {cid: ev.state.value for cid, ev in bundle.check_evaluations.items()}
            last_check_states = check_states
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
                "generator": actual_generator,
                "requested_generator": current_generator,
                "params": copy.deepcopy(current_params),
                "regenerate_identifiers": regenerate_ids,
                "csv_path": str(cand_csv),
                "evidence": evidence_records,
                "verdicts": verdicts,
                "check_states": check_states,
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

            decided_by = describe_llm_client(self.llm_client)
            decision: dict[str, Any] | None
            err_logs: list[str]
            if isinstance(self.llm_client, RuleBasedPlanner):
                decision = rule_decision()
                err_logs = []
            else:
                try:
                    decision, err_logs = query_llm_structured(
                        client=self.llm_client,
                        prompt=context_prompt,
                        system_prompt=SYSTEM_PROMPT,
                        tool_registry=self.tool_registry,
                        max_retries=3,
                        allowed_actions={"propose_repair", "finalize"},
                    )
                except Exception as exc:
                    # Network errors, rate limits or an exhausted quota must not end the run.
                    reason = f"{type(exc).__name__}: {str(exc)[:160]}"
                    self._emit(
                        "step",
                        {
                            "phase": "fallback",
                            "message": (
                                f"{decided_by} unavailable ({reason}). "
                                "Falling back to the rule-based planner."
                            ),
                        },
                    )
                    decided_by = "rule-based planner (LLM fallback)"
                    decision = rule_decision()
                    err_logs = []

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
                self._emit(
                    "step",
                    {
                        "phase": "fallback",
                        "message": (
                            f"{decided_by} gave no valid decision after retries. "
                            "Falling back to the rule-based planner."
                        ),
                    },
                )
                decided_by = "rule-based planner (LLM fallback)"
                decision = rule_decision()

            action = str(decision.get("action"))
            args = decision.get("args") or {}
            thought = str(decision.get("thought_summary") or "").strip()
            if len(thought) > 1200:  # keep events and the passport readable
                thought = thought[:1200].rsplit(" ", 1)[0] + " …"
            chosen = action
            if action == "propose_repair":
                chosen = f"repair: {args.get('action')}"
            self._emit(
                "decision",
                {
                    "message": thought,
                    "decided_by": decided_by,
                    "decision": chosen,
                },
            )

            if action == "finalize":
                break

            if action == "propose_repair":
                repair_action = str(args.get("action"))
                repair_params = args.get("params") or {}

                # Validate proposal against strict whitelist
                is_valid, reason = validate_repair_action(repair_action, repair_params)
                if (
                    is_valid
                    and repair_action == "switch_generator"
                    and normalize_target_generator(repair_params) == current_generator
                ):
                    is_valid, reason = False, f"Already using {current_generator}"
                if is_valid and repair_action == "regenerate_identifiers" and regenerate_ids:
                    is_valid, reason = False, "Identifiers are already being regenerated"
                if not is_valid:
                    self.agent_rejections.append({
                        "proposal": f"{repair_action}: {repair_params}",
                        "reason": reason,
                    })
                    self._emit("rejection", {"proposal": repair_action, "reason": reason})
                    # Replace the invalid proposal with the next rule-based repair.
                    fallback = rule_decision()
                    repair_action = str(fallback["args"]["action"])
                    repair_params = dict(fallback["args"]["params"])
                    self._emit(
                        "decision",
                        {
                            "message": fallback["thought_summary"],
                            "decided_by": "rule-based planner (replacing rejected proposal)",
                            "decision": f"repair: {repair_action}",
                        },
                    )

                if repair_action == "switch_generator":
                    # Record the canonical form so the passport shows exactly what ran.
                    repair_params = {"target_generator": normalize_target_generator(repair_params)}

                # Apply whitelisted repair
                repair_entry: dict[str, Any] = {
                    "action": repair_action,
                    "params": repair_params,
                    "candidate_id": candidate_id,
                }
                if repair_action == "tune_hyperparameters" and current_generator != "CTGAN":
                    repair_entry["note"] = (
                        "GaussianCopula has no tunable hyperparameters; these parameters "
                        "only take effect if the generator is switched to CTGAN"
                    )
                self.repairs_log.append(repair_entry)
                self.repairs_attempted += 1
                self._emit("repair", copy.deepcopy(repair_entry))

                if repair_action == "regenerate_identifiers":
                    regenerate_ids = True
                elif repair_action == "tune_hyperparameters":
                    current_params.update(repair_params)
                elif repair_action == "switch_generator":
                    current_generator = str(repair_params["target_generator"])
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
                "regenerate_identifiers": c.get("regenerate_identifiers", False),
                "check_states": c.get("check_states", {}),
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
