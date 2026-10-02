# SynPassport — Detailed Commit & Change History

> **Last Updated**: `2026-10-02 23:40:21`  
> **Auto-Update**: Enabled via `.githooks/pre-commit` and `scripts/update_changelog.py`  

This document tracks every commit, feature addition, architectural improvement, security enhancement, and bug fix across the SynPassport codebase over time.

---

## Commit Overview Summary

| Commit | Date | Author | Description | Impact |
| :--- | :--- | :--- | :--- | :--- |
| [`1da945b`](#commit-1da945b) | 2026-10-02 | vansh-09 | readme and loophole patching | 2066 insertions(+), 157 deletions(-) |
| [`dfc4aea`](#commit-dfc4aea) | 2026-10-01 | vansh-09 | ui change | 6757 insertions(+), 1935 deletions(-) |
| [`ec0e866`](#commit-ec0e866) | 2026-10-01 | nishankkhadpe7-afk | 50% | 593 insertions(+), 42 deletions(-) |
| [`7a5e793`](#commit-7a5e793) | 2026-09-30 | nishankkhadpe7-afk | fix(readme): quote mermaid diagram node labels and sanitize delimiters | 18 insertions(+), 18 deletions(-) |
| [`a754d83`](#commit-a754d83) | 2026-09-30 | nishankkhadpe7-afk | 50% | 4793 insertions(+), 141 deletions(-) |
| [`11279e5`](#commit-11279e5) | 2026-09-30 | nishankkhadpe7-afk | 50% | 4730 insertions(+) |
| [`ac8862f`](#commit-ac8862f) | 2026-09-30 | nishankkhadpe7-afk | Beta1 | 5722 insertions(+) |

---

## Detailed Commit Log

### Commit `1da945b` — readme and loophole patching
- **Hash**: `1da945b9989991c6becf9145cb16a5d7f86736b7`
- **Author**: vansh-09 (`vanshkjain09@gmail.com`)
- **Date**: `2026-10-02 23:34:19`
- **Stats**: `34 files changed, 2066 insertions(+), 157 deletions(-)`

#### Component Breakdown
- **Assurance & Statistical Checks** (3 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/README.md)
  - `Modified` [privacy.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/privacy.py)
  - `Modified` [run.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/run.py)
- **Autonomous Assurance Agent** (4 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/README.md)
  - `Modified` [loop.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/loop.py)
  - `Modified` [prompts.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/prompts.py)
  - `Modified` [repairs.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/repairs.py)
- **Command-Line Interface (CLI)** (2 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/README.md)
  - `Modified` [main.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/main.py)
- **Configuration & Infrastructure** (3 files):
  - `Added` [2f1d335a2a117c31253f6ee6f80f2e8b9a8d119b88bc935eea5329014825e652.json](file:///Users/vanshjain/Desktop/SynPassport/replay/2f1d335a2a117c31253f6ee6f80f2e8b9a8d119b88bc935eea5329014825e652.json)
  - `Modified` [7e6fcb00490eda5fb5a6ff9a4a52e7e321489dd564356f8cc1c9ad7048a731ca.json](file:///Users/vanshjain/Desktop/SynPassport/replay/7e6fcb00490eda5fb5a6ff9a4a52e7e321489dd564356f8cc1c9ad7048a731ca.json)
  - `Modified` [c9cd4bb03dd28959a9ff1152f4bf2ecb670f71300ab1ee312ed5bcd72de97ebc.json](file:///Users/vanshjain/Desktop/SynPassport/replay/c9cd4bb03dd28959a9ff1152f4bf2ecb670f71300ab1ee312ed5bcd72de97ebc.json)
- **Documentation** (4 files):
  - `Modified` [README.md](file:///Users/vanshjain/Desktop/SynPassport/README.md)
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/docs/README.md)
  - `Added` [SECURITY.md](file:///Users/vanshjain/Desktop/SynPassport/docs/SECURITY.md)
  - `Added` [TRUST_MODEL.md](file:///Users/vanshjain/Desktop/SynPassport/docs/TRUST_MODEL.md)
- **Evidence Store** (2 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/README.md)
  - `Modified` [models.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/models.py)
- **Mission Profile** (1 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/mission/README.md)
- **Passport & Cryptography** (6 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/README.md)
  - `Modified` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/__init__.py)
  - `Modified` [builder.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/builder.py)
  - `Modified` [canonical.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/canonical.py)
  - `Modified` [signer.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/signer.py)
  - `Added` [trust.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/trust.py)
- **Policy Engine** (1 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/README.md)
- **REST API & Server** (4 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/README.md)
  - `Modified` [models.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/models.py)
  - `Modified` [runs.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/runs.py)
  - `Modified` [verify.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/verify.py)
- **Synthetic Data Generators** (1 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/README.md)
- **Verification SDK & Guard** (3 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/README.md)
  - `Modified` [guard.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/guard.py)
  - `Modified` [verify.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/verify.py)

---

### Commit `dfc4aea` — ui change
- **Hash**: `dfc4aeacf637781d393cc0d2113b9e63938786df`
- **Author**: vansh-09 (`vanshkjain09@gmail.com`)
- **Date**: `2026-10-01 20:44:49`
- **Stats**: `32 files changed, 6757 insertions(+), 1935 deletions(-)`

#### Component Breakdown
- **Configuration & Infrastructure** (16 files):
  - `Added` [code.html](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_evidence/code.html)
  - `Added` [screen.png](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_evidence/screen.png)
  - `Added` [code.html](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_mission_setup/code.html)
  - `Added` [screen.png](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_mission_setup/screen.png)
  - `Added` [code.html](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_passport/code.html)
  - `Added` [screen.png](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_passport/screen.png)
  - `Added` [code.html](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_run_view/code.html)
  - `Added` [screen.png](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_run_view/screen.png)
  - `Added` [code.html](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_shield_check_mark/code.html)
  - `Added` [screen.png](file:///Users/vanshjain/Desktop/SynPassport/design/synpassport_shield_check_mark/screen.png)
  - *... and 6 more files*
- **Documentation** (1 files):
  - `Added` [DESIGN.md](file:///Users/vanshjain/Desktop/SynPassport/design/terminal_precision/DESIGN.md)
- **Web Dashboard (Next.js)** (15 files):
  - `Modified` [globals.css](file:///Users/vanshjain/Desktop/SynPassport/web/src/app/globals.css)
  - `Modified` [layout.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/app/layout.tsx)
  - `Modified` [page.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/app/page.tsx)
  - `Modified` [EvidenceDrilldown.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/EvidenceDrilldown.tsx)
  - `Modified` [MissionSetup.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/MissionSetup.tsx)
  - `Modified` [Navbar.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/Navbar.tsx)
  - `Modified` [PassportPanel.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/PassportPanel.tsx)
  - `Modified` [RunTimeline.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/RunTimeline.tsx)
  - `Added` [SidebarStepper.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/SidebarStepper.tsx)
  - `Modified` [StateBadge.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/StateBadge.tsx)
  - *... and 5 more files*

---

### Commit `ec0e866` — 50%
- **Hash**: `ec0e866edd254a58f88d5940d35662a942a694a2`
- **Author**: nishankkhadpe7-afk (`nishankkhadpe7@gmail.com`)
- **Date**: `2026-10-01 13:10:21`
- **Stats**: `12 files changed, 593 insertions(+), 42 deletions(-)`

#### Component Breakdown
- **Autonomous Assurance Agent** (1 files):
  - `Modified` [llm.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/llm.py)
- **Configuration & Infrastructure** (5 files):
  - `Modified` [docker-compose.yml](file:///Users/vanshjain/Desktop/SynPassport/docker-compose.yml)
  - `Modified` [pyproject.toml](file:///Users/vanshjain/Desktop/SynPassport/pyproject.toml)
  - `Added` [3c4d3226063ecc67c6a4105bd070c2d9c5e6c4b0d3134f87661c270ad133c7ff.json](file:///Users/vanshjain/Desktop/SynPassport/replay/3c4d3226063ecc67c6a4105bd070c2d9c5e6c4b0d3134f87661c270ad133c7ff.json)
  - `Added` [5d0a5e051ed4d0c165ecf27afde069b4b80444bc2d98c92ea32e3e706f976417.json](file:///Users/vanshjain/Desktop/SynPassport/replay/5d0a5e051ed4d0c165ecf27afde069b4b80444bc2d98c92ea32e3e706f976417.json)
  - `Modified` [7e6fcb00490eda5fb5a6ff9a4a52e7e321489dd564356f8cc1c9ad7048a731ca.json](file:///Users/vanshjain/Desktop/SynPassport/replay/7e6fcb00490eda5fb5a6ff9a4a52e7e321489dd564356f8cc1c9ad7048a731ca.json)
- **REST API & Server** (3 files):
  - `Modified` [config.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/config.py)
  - `Modified` [verify.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/verify.py)
  - `Modified` [store.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/store.py)
- **Synthetic Data Generators** (1 files):
  - `Modified` [sdv_wrapper.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/sdv_wrapper.py)
- **Web Dashboard (Next.js)** (2 files):
  - `Modified` [page.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/app/page.tsx)
  - `Modified` [PassportPanel.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/components/PassportPanel.tsx)

---

### Commit `7a5e793` — fix(readme): quote mermaid diagram node labels and sanitize delimiters
- **Hash**: `7a5e793cb652ebb87c392c29918b6729a0008326`
- **Author**: nishankkhadpe7-afk (`nishankkhadpe7@gmail.com`)
- **Date**: `2026-09-30 22:16:30`
- **Stats**: `1 file changed, 18 insertions(+), 18 deletions(-)`

#### Component Breakdown
- **Documentation** (1 files):
  - `Modified` [README.md](file:///Users/vanshjain/Desktop/SynPassport/README.md)

---

### Commit `a754d83` — 50%
- **Hash**: `a754d83ecb21f8dc73f3ba50ff36b21d11c6f196`
- **Author**: nishankkhadpe7-afk (`nishankkhadpe7@gmail.com`)
- **Date**: `2026-09-30 22:00:45`
- **Stats**: `39 files changed, 4793 insertions(+), 141 deletions(-)`

#### Component Breakdown
- **Assurance & Statistical Checks** (2 files):
  - `Modified` [fidelity.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/fidelity.py)
  - `Modified` [privacy.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/privacy.py)
- **Autonomous Assurance Agent** (8 files):
  - `Modified` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/__init__.py)
  - `Added` [cache.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/cache.py)
  - `Added` [explanation.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/explanation.py)
  - `Added` [llm.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/llm.py)
  - `Modified` [loop.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/loop.py)
  - `Modified` [prompts.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/prompts.py)
  - `Modified` [repairs.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/repairs.py)
  - `Modified` [tools.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/tools.py)
- **Command-Line Interface (CLI)** (2 files):
  - `Modified` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/__init__.py)
  - `Modified` [main.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/main.py)
- **Configuration & Infrastructure** (7 files):
  - `Modified` [action.yml](file:///Users/vanshjain/Desktop/SynPassport/.github/actions/verify/action.yml)
  - `Modified` [docker-compose.yml](file:///Users/vanshjain/Desktop/SynPassport/docker-compose.yml)
  - `Added` [7e6fcb00490eda5fb5a6ff9a4a52e7e321489dd564356f8cc1c9ad7048a731ca.json](file:///Users/vanshjain/Desktop/SynPassport/replay/7e6fcb00490eda5fb5a6ff9a4a52e7e321489dd564356f8cc1c9ad7048a731ca.json)
  - `Added` [819400d6b3fdbbe792fbafd6a161f9dcad65e5661bb052371baa765730d10330.json](file:///Users/vanshjain/Desktop/SynPassport/replay/819400d6b3fdbbe792fbafd6a161f9dcad65e5661bb052371baa765730d10330.json)
  - `Added` [c9cd4bb03dd28959a9ff1152f4bf2ecb670f71300ab1ee312ed5bcd72de97ebc.json](file:///Users/vanshjain/Desktop/SynPassport/replay/c9cd4bb03dd28959a9ff1152f4bf2ecb670f71300ab1ee312ed5bcd72de97ebc.json)
  - `Added` [run_pipeline.py](file:///Users/vanshjain/Desktop/SynPassport/scripts/run_pipeline.py)
  - `Modified` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/__init__.py)
- **Documentation** (1 files):
  - `Modified` [README.md](file:///Users/vanshjain/Desktop/SynPassport/README.md)
- **Mission Profile** (2 files):
  - `Modified` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/mission/__init__.py)
  - `Modified` [schema.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/mission/schema.py)
- **Passport & Cryptography** (1 files):
  - `Modified` [builder.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/builder.py)
- **Policy Engine** (1 files):
  - `Modified` [engine.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/engine.py)
- **REST API & Server** (9 files):
  - `Modified` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/__init__.py)
  - `Added` [config.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/config.py)
  - `Added` [logging.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/logging.py)
  - `Modified` [main.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/main.py)
  - `Added` [models.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/models.py)
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/__init__.py)
  - `Added` [runs.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/runs.py)
  - `Added` [verify.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/verify.py)
  - `Added` [store.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/store.py)
- **Test Suite** (3 files):
  - `Added` [test_agent.py](file:///Users/vanshjain/Desktop/SynPassport/tests/test_agent.py)
  - `Added` [test_api.py](file:///Users/vanshjain/Desktop/SynPassport/tests/test_api.py)
  - `Added` [test_sdk_and_cli.py](file:///Users/vanshjain/Desktop/SynPassport/tests/test_sdk_and_cli.py)
- **Verification SDK & Guard** (3 files):
  - `Modified` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/__init__.py)
  - `Modified` [guard.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/guard.py)
  - `Modified` [verify.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/verify.py)

---

### Commit `11279e5` — 50%
- **Hash**: `11279e5ca17307cb03ae693e9cf300c4610c3828`
- **Author**: nishankkhadpe7-afk (`nishankkhadpe7@gmail.com`)
- **Date**: `2026-09-30 21:56:53`
- **Stats**: `24 files changed, 4730 insertions(+)`

#### Component Breakdown
- **Web Dashboard (Next.js)** (24 files):
  - `Added` [Dockerfile](file:///Users/vanshjain/Desktop/SynPassport/web/Dockerfile)
  - `Added` [next-env.d.ts](file:///Users/vanshjain/Desktop/SynPassport/web/next-env.d.ts)
  - `Added` [next.config.mjs](file:///Users/vanshjain/Desktop/SynPassport/web/next.config.mjs)
  - `Added` [package-lock.json](file:///Users/vanshjain/Desktop/SynPassport/web/package-lock.json)
  - `Added` [package.json](file:///Users/vanshjain/Desktop/SynPassport/web/package.json)
  - `Added` [postcss.config.js](file:///Users/vanshjain/Desktop/SynPassport/web/postcss.config.js)
  - `Added` [.gitkeep](file:///Users/vanshjain/Desktop/SynPassport/web/public/.gitkeep)
  - `Added` [globals.css](file:///Users/vanshjain/Desktop/SynPassport/web/src/app/globals.css)
  - `Added` [layout.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/app/layout.tsx)
  - `Added` [page.tsx](file:///Users/vanshjain/Desktop/SynPassport/web/src/app/page.tsx)
  - *... and 14 more files*

---

### Commit `ac8862f` — Beta1
- **Hash**: `ac8862f8f682ea59e180b003b2b29032ffe75404`
- **Author**: nishankkhadpe7-afk (`nishankkhadpe7@gmail.com`)
- **Date**: `2026-09-30 03:50:52`
- **Stats**: `67 files changed, 5722 insertions(+)`

#### Component Breakdown
- **Assurance & Statistical Checks** (11 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/__init__.py)
  - `Added` [base.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/base.py)
  - `Added` [bootstrap.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/bootstrap.py)
  - `Added` [fidelity.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/fidelity.py)
  - `Added` [privacy.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/privacy.py)
  - `Added` [run.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/run.py)
  - `Added` [schema.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/schema.py)
  - `Added` [splitter.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/splitter.py)
  - `Added` [subgroups.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/subgroups.py)
  - `Added` [sufficiency.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/sufficiency.py)
  - *... and 1 more files*
- **Autonomous Assurance Agent** (5 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/__init__.py)
  - `Added` [loop.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/loop.py)
  - `Added` [prompts.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/prompts.py)
  - `Added` [repairs.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/repairs.py)
  - `Added` [tools.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/tools.py)
- **Command-Line Interface (CLI)** (2 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/__init__.py)
  - `Added` [main.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/main.py)
- **Configuration & Infrastructure** (11 files):
  - `Added` [.env.example](file:///Users/vanshjain/Desktop/SynPassport/.env.example)
  - `Added` [action.yml](file:///Users/vanshjain/Desktop/SynPassport/.github/actions/verify/action.yml)
  - `Added` [.gitignore](file:///Users/vanshjain/Desktop/SynPassport/.gitignore)
  - `Added` [Dockerfile](file:///Users/vanshjain/Desktop/SynPassport/Dockerfile)
  - `Added` [docker-compose.yml](file:///Users/vanshjain/Desktop/SynPassport/docker-compose.yml)
  - `Added` [Dockerfile](file:///Users/vanshjain/Desktop/SynPassport/docker/Dockerfile)
  - `Added` [pyproject.toml](file:///Users/vanshjain/Desktop/SynPassport/pyproject.toml)
  - `Added` [pyrightconfig.json](file:///Users/vanshjain/Desktop/SynPassport/pyrightconfig.json)
  - `Added` [.gitkeep](file:///Users/vanshjain/Desktop/SynPassport/replay/.gitkeep)
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/__init__.py)
  - *... and 1 more files*
- **Documentation** (5 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/README.md)
  - `Added` [architecture.md](file:///Users/vanshjain/Desktop/SynPassport/docs/architecture.md)
  - `Added` [design.md](file:///Users/vanshjain/Desktop/SynPassport/docs/design.md)
  - `Added` [instructions.md](file:///Users/vanshjain/Desktop/SynPassport/docs/instructions.md)
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/policies/README.md)
- **Evidence Store** (3 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/__init__.py)
  - `Added` [models.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/models.py)
  - `Added` [store.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/store.py)
- **Mission Profile** (2 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/mission/__init__.py)
  - `Added` [schema.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/mission/schema.py)
- **Passport & Cryptography** (5 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/__init__.py)
  - `Added` [builder.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/builder.py)
  - `Added` [canonical.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/canonical.py)
  - `Added` [keygen.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/keygen.py)
  - `Added` [signer.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/signer.py)
- **Policy Engine** (4 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/__init__.py)
  - `Added` [engine.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/engine.py)
  - `Added` [loader.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/loader.py)
  - `Added` [models.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/models.py)
- **Policy Files** (3 files):
  - `Added` [ml-prototyping.yaml](file:///Users/vanshjain/Desktop/SynPassport/policies/ml-prototyping.yaml)
  - `Added` [ml-sensitive-v1.yaml](file:///Users/vanshjain/Desktop/SynPassport/policies/ml-sensitive-v1.yaml)
  - `Added` [software-testing.yaml](file:///Users/vanshjain/Desktop/SynPassport/policies/software-testing.yaml)
- **REST API & Server** (2 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/__init__.py)
  - `Added` [main.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/main.py)
- **Synthetic Data Generators** (3 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/__init__.py)
  - `Added` [base.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/base.py)
  - `Added` [sdv_wrapper.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/sdv_wrapper.py)
- **Test Suite** (7 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/tests/__init__.py)
  - `Added` [conftest.py](file:///Users/vanshjain/Desktop/SynPassport/tests/conftest.py)
  - `Added` [golden_passport_canonical.json](file:///Users/vanshjain/Desktop/SynPassport/tests/fixtures/golden_passport_canonical.json)
  - `Added` [test_checks.py](file:///Users/vanshjain/Desktop/SynPassport/tests/test_checks.py)
  - `Added` [test_passport.py](file:///Users/vanshjain/Desktop/SynPassport/tests/test_passport.py)
  - `Added` [test_policy_engine.py](file:///Users/vanshjain/Desktop/SynPassport/tests/test_policy_engine.py)
  - `Added` [test_scaffold.py](file:///Users/vanshjain/Desktop/SynPassport/tests/test_scaffold.py)
- **Verification SDK & Guard** (3 files):
  - `Added` [__init__.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/__init__.py)
  - `Added` [guard.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/guard.py)
  - `Added` [verify.py](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/verify.py)
- **Web Dashboard (Next.js)** (1 files):
  - `Added` [README.md](file:///Users/vanshjain/Desktop/SynPassport/web/README.md)

---
