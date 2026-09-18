# OpenLore: Comprehensive Phase-by-Phase Checklist

> *Tagline: "Git for 3D worlds, game lore, and Hollywood pipelines."*  
> Tracking roadmap for progressive implementation across all 9 architectural phases.

---

## Phase 1: Repository Foundation & Core Scaffolding
- [x] Create standardized project directory layout (`src/openlore`, `schemas`, `workflows`, `tests`).
- [x] Configure version control rules and local cache ignores ([.gitignore](.gitignore)).
- [x] Set up Python packaging targeting up-to-date Python (`>=3.12`) ([pyproject.toml](pyproject.toml)).
- [x] Configure GitHub Dependabot for automatic weekly dependency monitoring ([.github/dependabot.yml](.github/dependabot.yml)).
- [x] Configure GitHub Actions CI workflow ([.github/workflows/ci.yml](.github/workflows/ci.yml)).
- [x] Set up Docker Compose topology for local services (Kafka, Temporal, OPA, Jena Fuseki) ([docker-compose.yml](docker-compose.yml)).
- [x] Author base schemas (OWL 2 ontology, SHACL shapes, OPA royalties policy, MaterialX surface).
- [x] Author workflow templates (Temporal multi-step compilation, Argo containerized job).
- [x] Create core domain exceptions and global configuration manager ([src/openlore/config.py](src/openlore/config.py), [src/openlore/exceptions.py](src/openlore/exceptions.py)).
- [x] Build the OpenLore CLI skeleton ([src/openlore/cli/main.py](src/openlore/cli/main.py)).
- [x] Verify module compilation and base test discovery (9/9 unit tests passing).

---

## Phase 2: Core Foundation & Content-Addressed Storage (CAS)
- [x] **BLAKE3 Cryptographic Hashing Engine**:
  - [x] Implement fast streaming BLAKE3 chunk hashing in [src/openlore/core/cas.py](src/openlore/core/cas.py).
  - [x] Implement cryptographic verification of raw byte buffers and large file streams.
  - [x] Add fallback mechanism for environments where native BLAKE3 C extensions are absent.
- [x] **Immutable CAS Repository**:
  - [x] Implement two-level shard directory tree storage (`storage_root/objects/ab/cd/hash`).
  - [x] Implement deduplication logic ensuring identical meshes/caches are stored only once.
  - [x] Implement streaming retrieval and chunk integrity checksum validation.
  - [x] Enforce read-only permissions (`0o444`) for strict file immutability.
- [x] **Layered OpenUSD Stage Composition**:
  - [x] Installed and integrated official Pixar OpenUSD Python API (`pxr.Usd`, `pxr.Sdf`, `pxr.UsdGeom`).
  - [x] Implement OpenUSD composition stage manager in [src/openlore/core/stage.py](src/openlore/core/stage.py).
  - [x] Support programmatic creation and loading of `.usda` (ASCII) and `.usdc` (Crate binary) stages.
  - [x] Implement sublayer composition hierarchy and layer ordering rules.
  - [x] Implement Prim attribute bindings pointing to immutable CAS BLAKE3 hashes.
- [x] **Transactional Edit Isolation**:
  - [x] Implement `TransactionManager` and `TransactionSession` in [src/openlore/core/transaction.py](src/openlore/core/transaction.py).
  - [x] Separate lightweight metadata property deltas from heavy binary payloads.
  - [x] Implement deterministic commit ID calculation, commit JSON log persistence, and `HEAD` reference tracking.
  - [x] Implement commit rollback and linear commit history retrieval (`get_commit_history`).
- [x] **Tests & Verification**:
  - [x] Write CAS chunking, deduplication, immutability, and corruption detection tests in [tests/unit/test_cas.py](tests/unit/test_cas.py).
  - [x] Write stage layer composition and CAS asset binding tests in [tests/unit/test_stage.py](tests/unit/test_stage.py).
  - [x] Write transaction session lifecycle, delta tracking, and rollback tests in [tests/unit/test_transaction.py](tests/unit/test_transaction.py).
  - [x] Verified full unit test pass (20/20 tests passing in 0.06s).

---

## Phase 3: Narrative Ontology & Continuity Enforcement
- [x] **W3C RDF 1.1 Triplestore Client**:
  - [x] Integrated production `rdflib` (7.6.0) dataset with W3C Named Graph context isolation in [src/openlore/narrative/graph.py](src/openlore/narrative/graph.py).
  - [x] Implemented entity insertion, asset binding triples, and SPARQL 1.1 query engine.
  - [x] Implemented dataset serialization and persistence in W3C TriG (`.trig`) and Turtle (`.ttl`) quad formats.
- [x] **OWL 2 Narrative & Character Models**:
  - [x] Implemented typed dataclass models in [src/openlore/narrative/ontology.py](src/openlore/narrative/ontology.py) (`TimelineModel`, `CharacterEntity`, `NarrativeEvent`, `AssetBindingRecord`).
  - [x] Mapped character lifecycles (`birthTime`, `deathTime`, `status`) and causal event predicates (`participatedIn`, `causes`, `divergesAt`).
- [x] **Asynchronous SHACL Continuity Validator**:
  - [x] Integrated `pyshacl` (0.40.1) engine in [src/openlore/narrative/validator.py](src/openlore/narrative/validator.py).
  - [x] Enforced strict 64-character hexadecimal BLAKE3 hashes on all 3D asset bindings via SHACL shapes.
  - [x] Built temporal spatiotemporal lifecycle validator catching impossible narrative events (pre-birth or post-death participation).
  - [x] Raised `ContinuityViolationError` blocking invalid edits.
- [x] **Multiverse Timeline Branching Engine**:
  - [x] Implemented `TimelineBranchManager` in [src/openlore/narrative/timeline.py](src/openlore/narrative/timeline.py).
  - [x] Enabled non-destructive branching from Prime Canon into isolated alternate continuity namespaces (`https://openlore.io/timelines/<slug>`).
  - [x] Verified that spin-off modifications do not mutate or invalidate prime canon.
- [x] **Tests & Verification**:
  - [x] Comprehensive unit tests in [tests/unit/test_narrative.py](tests/unit/test_narrative.py) covering model serialization, SPARQL querying, SHACL validation pass/fail, lifecycle violations, and multiverse isolation.
  - [x] Verified all 25 unit tests passing in 0.18s across the repository.
  - [x] Verified CLI commands (`openlore lore list`, `verify`, `branch`).

---

## Phase 4: Distributed Collaboration & Event Messaging
- [x] **Deterministic Causal Ordering**:
  - [x] Implemented complete Vector Clock engine in [src/openlore/collaboration/vector_clock.py](src/openlore/collaboration/vector_clock.py).
  - [x] Implemented pairwise max merging, domination detection, and concurrency detection.
- [x] **Sparse CRDT State Representations**:
  - [x] Implemented Last-Write-Wins (LWW) registers with deterministic 3-level conflict resolution (causal dominance -> timestamp -> studio ID) in [src/openlore/collaboration/crdt.py](src/openlore/collaboration/crdt.py).
  - [x] Implemented Observed-Remove Sets (`ORSet`) with unique observation tokens.
  - [x] Built `CRDTSceneReplica` managing sparse prim attributes.
- [x] **Apache Kafka Event Streaming Engine**:
  - [x] Installed `confluent-kafka` (2.15.1) and built `KafkaEventStream` in [src/openlore/collaboration/kafka_stream.py](src/openlore/collaboration/kafka_stream.py).
  - [x] Built embedded in-memory broadcast bus fallback for offline simulation and isolated testing.
  - [x] Enforced binary payload filtering: rejected payloads exceeding 64 KB with `SecurityPolicyError`.
- [x] **Edge Resolver Daemon & Shadow Buffering**:
  - [x] Implemented `EdgeResolverDaemon` in [src/openlore/collaboration/resolver.py](src/openlore/collaboration/resolver.py).
  - [x] Built offline shadow buffering accumulating edits during studio network outages.
  - [x] Built automated causal state reconciliation flushing buffered edits upon reconnection.
- [x] **Tests & Verification**:
  - [x] Unit tests in [tests/unit/test_crdt.py](tests/unit/test_crdt.py) verifying vector clocks, LWW registers, ORSets, and binary payload rejection.
  - [x] Integration test in [tests/integration/test_resolver_convergence.py](tests/integration/test_resolver_convergence.py) verifying multi-studio offline severance, shadow buffering, and 100% causal convergence.
  - [x] Verified all 32 tests passing in 0.19s across the repository.
  - [x] Verified CLI commands (`openlore daemon start`, `status`, `stop`).

---

## Phase 5: Cross-Media Material & Dynamic Rigging Standards
- [x] **MaterialX Translation Engine**:
  - [x] Installed official `materialx` (1.39.5) and built `MaterialXTranslator` in [src/openlore/materials/materialx.py](src/openlore/materials/materialx.py).
  - [x] Implemented parsing of vendor-neutral `.mtlx` documents into `SurfaceAppearance`.
  - [x] Implemented shader translation to Unreal Engine USF/HLSL parameters and shader structs.
  - [x] Implemented shader translation to offline cinematic Open Shading Language (OSL) closures.
- [x] **UsdSkel Skeletal Hierarchies & Dynamic Rigging**:
  - [x] Implemented `DynamicRigManager` in [src/openlore/materials/rigging.py](src/openlore/materials/rigging.py) leveraging `pxr.UsdSkel` and `pxr.UsdGeom`.
  - [x] Authored skeletal hierarchies with joint tokens and child collision capsules (`UsdGeom.Capsule`).
- [x] **Switchable VariantSets (Film vs. Game)**:
  - [x] Authored standardized `rigMode` OpenUSD VariantSet on character prims.
  - [x] Implemented switching between:
    - `cinematic_cache`: Pre-baked point cache CAS hash binding for deterministic film playback.
    - `game_collision`: Interactive UsdSkel hierarchy and collision capsules for real-time engines.
- [x] **Tests & Verification**:
  - [x] Unit tests in [tests/unit/test_materials.py](tests/unit/test_materials.py) verifying MaterialX parsing, Unreal HLSL export, OSL export, UsdSkel dual-rig setup, and VariantSet switching.
  - [x] Verified all 35 tests passing in 0.19s across the repository.

---

## Phase 6: Provenance Tracking & Financial Accounting
- [x] **USD Stage DAG Harvester**:
  - [x] Implemented recursive stage introspector in [src/openlore/provenance/harvester.py](src/openlore/provenance/harvester.py) traversing Prims and sublayers.
  - [x] Extracted prim paths, cryptographic BLAKE3 hashes, partner IDs, and royalty percentages.
- [x] **Asset Provenance Manifest Generator**:
  - [x] Implemented manifest data model in [src/openlore/provenance/manifest.py](src/openlore/provenance/manifest.py).
  - [x] Implemented HMAC-SHA256 cryptographic digital signing and tampering verification (`sign_manifest`, `verify_signature`).
- [x] **Open Policy Agent (OPA) Integration**:
  - [x] Implemented `RoyaltyAccountingEngine` in [src/openlore/provenance/accounting.py](src/openlore/provenance/accounting.py).
  - [x] Evaluated export allowance against Rego policy rules ([schemas/opa/royalties.rego](schemas/opa/royalties.rego)), rejecting unlicensed assets with `StagePromotionError`.
  - [x] Automated downstream financial royalty distributions calculated per partner studio.
- [x] **Tests & Verification**:
  - [x] Unit tests in [tests/unit/test_provenance.py](tests/unit/test_provenance.py) covering DAG harvesting, HMAC signature verification/tampering detection, OPA allowance pass/fail, and royalty splits.
  - [x] Verified CLI export integration (`openlore export --stage <uri> --target <target>`).
  - [x] Verified all 39 tests passing in 0.25s across the repository.

---

## Phase 7: Partner Isolation & Ingestion Workflows
- [x] **Outbound IP Decimation Pipeline**:
  - [x] Implemented automated geometric flattening in [src/openlore/partner/decimation.py](src/openlore/partner/decimation.py).
  - [x] Implemented mesh decimation to low-resolution proxies.
  - [x] Replaced proprietary shaders with generic neutral clay materials (`(0.7, 0.7, 0.7)`).
  - [x] Stripped proprietary internal attributes (`openlore:pointCacheHash`, `openlore:assetHash`, `openlore:royaltyPercentage`).
- [x] **Inbound Pre-Flight Linting Sandbox**:
  - [x] Implemented air-gapped quarantine validator in [src/openlore/partner/linter.py](src/openlore/partner/linter.py).
  - [x] Verified scene hierarchy (`/World`, `/Root`, `/Asset`), polycount ceilings, and studio namespace conventions.
- [x] **TD One-Click Promotion Gate**:
  - [x] Implemented optimistic locking gate in [src/openlore/partner/promotion.py](src/openlore/partner/promotion.py).
  - [x] Prevented stage merge until background narrative validation and linting checks pass.
  - [x] Atomically promoted approved deliverables into production USD stage sublayer stack.
- [x] **eBPF Zero-Egress Network Isolation**:
  - [x] Implemented eBPF Traffic Control (`tc`) kernel packet classifier generation in [src/openlore/partner/ebpf_rules.py](src/openlore/partner/ebpf_rules.py).
  - [x] Implemented automated `bpftool` and `tc` command generation.
  - [x] Implemented active socket compliance auditing catching unauthorized egress attempts.
- [x] **Tests & Verification**:
  - [x] Unit tests in [tests/unit/test_partner.py](tests/unit/test_partner.py) verifying decimation, clay shader assignment, pre-flight linting pass/fail, optimistic locks, sublayer promotion, eBPF C generation, and socket audits.
  - [x] Verified all 45 tests passing in 0.21s across the repository.

---

## Phase 8: Automated Downstream Compilation Grid
- [x] **Worker Grid Dispatcher**:
  - [x] Implemented Temporal multi-activity workflow dispatcher in [src/openlore/compilation/grid.py](src/openlore/compilation/grid.py).
  - [x] Implemented Kubernetes Argo Workflow DAG specification generator (`argoproj.io/v1alpha1`) and YAML exporter.
  - [x] Implemented `ProductionCatalog` registering completed real-time and cinematic builds with BLAKE3 hashes.
- [x] **Real-Time Game Engine Compiler**:
  - [x] Implemented Unreal Engine packaging worker (`.pak` archive with `content_manifest.json`, extracted geometry, collision physics assets, and shader manifests) in [src/openlore/compilation/engine_package.py](src/openlore/compilation/engine_package.py).
  - [x] Implemented Unity packaging worker (`.unitypackage` archive with prefabs, materials, and scene definitions).
- [x] **Offline Cinematic Shot Baker**:
  - [x] Implemented geometry point cache baking worker in [src/openlore/compilation/shot_baker.py](src/openlore/compilation/shot_baker.py).
  - [x] Sampled time-dependent vertex point deformation and bounding extents over arbitrary frame ranges in OpenUSD (`.usdc`/`.usda`).
  - [x] Automated BLAKE3 point cache cryptographic hashing and cache manifest generation.
- [x] **Tests & Verification**:
  - [x] Unit tests in [tests/unit/test_compilation.py](tests/unit/test_compilation.py) covering Unreal/Unity compilation, offline point caching with time samples, workflow activity execution, Argo spec generation, and catalog persistence.
  - [x] Verified all 54 tests passing in 0.26s across the repository.

---

## Phase 9: System Resilience, Integration & End-to-End Hardening
- [x] **Full Asset Pipeline Integration**:
  - [x] Implemented comprehensive end-to-end integration test in [tests/integration/test_pipeline_flow.py](tests/integration/test_pipeline_flow.py) validating the complete workflow across all 9 pillars:
    - Asset ingestion -> CAS storage -> USD stage composition & atomic transaction -> narrative lore modeling & SHACL verification -> multiverse branching -> Kafka CRDT sync -> partner IP decimation & TD promotion -> OPA provenance & royalties -> worker grid compilation -> production catalog.
- [x] **Disconnected Studio Severance Simulation**:
  - [x] Implemented simulation test in [tests/integration/test_resolver_convergence.py](tests/integration/test_resolver_convergence.py):
    - Severed connection -> accumulated local edits in offline shadow buffer -> restored connection -> verified 100% deterministic causal convergence.
- [x] **CLI & Production Tooling Polish**:
  - [x] Wired up all CLI commands in [src/openlore/cli/main.py](src/openlore/cli/main.py) (`init`, `stage`, `lore`, `daemon`, `partner`, `compile`, `catalog`, `export`, `livelink`, `auth`, `dcc`, `farm`).
  - [x] Generated complete API reference documentation in [docs/API_REFERENCE.md](docs/API_REFERENCE.md).
  - [x] Generated enterprise production deployment and disaster recovery runbooks in [docs/DEPLOYMENT_RUNBOOK.md](docs/DEPLOYMENT_RUNBOOK.md).
  - [x] Verified full unit and integration test suites (139/139 passing across 26 modules).

---

## Phase 10: Enterprise Production Hardening & Complete Lifecycle (The Final 2%)
- [x] **Enterprise Kubernetes Helm Chart & Autoscaling**:
  - [x] Configured unauthenticated `/health` and `/api/health` probes in [helm/openlore/templates/deployment.yaml](helm/openlore/templates/deployment.yaml), preventing RBAC pod crashloops.
  - [x] Implemented Kubernetes Secret templates for master bearer authentication and HMAC manifest signing keys ([helm/openlore/templates/secret.yaml](helm/openlore/templates/secret.yaml)).
  - [x] Implemented PersistentVolumeClaims allocating resilient storage for CAS object cache, USD stages, and builds ([helm/openlore/templates/pvc.yaml](helm/openlore/templates/pvc.yaml)).
  - [x] Implemented HorizontalPodAutoscaler scaling between 2 and 10 API replicas based on CPU/memory load ([helm/openlore/templates/hpa.yaml](helm/openlore/templates/hpa.yaml)).
  - [x] Authored dedicated Helm chart test suite in [tests/unit/test_helm.py](tests/unit/test_helm.py).
- [x] **Native C++ DCC Live Link SDK**:
  - [x] Built header-only, zero-dependency C++17 library in [include/openlore/openlore.hpp](include/openlore/openlore.hpp).
  - [x] Implemented cross-platform binary UDP frame parsing and serialization (`LiveLinkFrame`).
  - [x] Implemented native Vector Clock causal domination and CAS BLAKE3 hash representation.
  - [x] Built UDP broadcast and telemetry receiver client for C++ DCC plugins (Maya, Houdini HDK, Unreal).
  - [x] Authored cross-language binary interoperability test in [tests/unit/test_cpp_sdk.py](tests/unit/test_cpp_sdk.py) compiling under `-Wall -Wextra -Werror`.
  - [x] Packaged `openlore-cpp-sdk-v1.0.2.zip` in release automation with SHA-256 checksums.
- [x] **Distributed GPU Farm Dispatcher**:
  - [x] Implemented `RenderFarmDispatcher` in [src/openlore/compilation/farm.py](src/openlore/compilation/farm.py).
  - [x] Generated AWS Deadline 10 / Deadline Cloud `job_info.job` and `plugin_info.job` bundles for Karma, Arnold, RenderMan, and usdrecord.
  - [x] Generated Academy Software Foundation (ASWF) OpenCue XML outline specifications (`opencue_outline.xml`) with GPU reservations.
  - [x] Integrated farm dispatching into `WorkerGridDispatcher` and CLI (`openlore farm submit`).
  - [x] Authored comprehensive unit tests in [tests/unit/test_farm.py](tests/unit/test_farm.py).

---

## Phase 11: Security Hardening & v1.0.2 Release
- [x] **CodeQL CWE-22 Path Traversal Remediation**:
  - [x] Implemented centralized path containment boundary utility in [src/openlore/core/path_safety.py](src/openlore/core/path_safety.py) with canonical symlink resolution and explicit root confinement checks.
  - [x] Remediated all 20 CodeQL High Severity path injection alerts across REST API handlers, quarantine linter, compilation worker grid, engine packager, and shot point cache baker.
  - [x] Added rigorous security test suite in [tests/unit/test_path_safety.py](tests/unit/test_path_safety.py) and regression tests in [tests/unit/test_server.py](tests/unit/test_server.py).
  - [x] Rebuilt frontend bundle (`web/dist/`) and bumped version to `1.0.2` across Python, C++ SDK, Helm, Docker, and Web assets.
- [x] Verified 100% test pass rate (139/139 passing across 26 modules).

---

## Phase 12: Cross-Platform Installer Suite & Adoption Polish
- [x] **Universal Cross-Platform Python Installer**:
  - [x] Built zero-dependency, standalone installer engine in [installer.py](installer.py) supporting macOS, Linux, and Windows.
  - [x] Integrated preflight environment detection (OS, architecture, Python >= 3.9, DCC tools).
  - [x] Implemented isolated virtual environment provisioning (`~/.openlore/env`).
  - [x] Implemented Web Studio cockpit assets deployment (`~/.openlore/web/dist`).
  - [x] Built executable launcher shims: `openlore` (Unix bash), `openlore.cmd` (Windows batch), and `openlore.ps1` (PowerShell).
  - [x] Automated persistent user shell PATH configuration (`.zshrc`, `.bashrc`, Windows User Environment).
  - [x] Implemented non-interactive scripted modes (`--yes`, `--prefix`, `--with-dcc`, `--launch-web`, `--no-modify-path`).
  - [x] Implemented complete clean uninstaller (`installer.py --uninstall`).
- [x] **1-Line Shell Installers**:
  - [x] Authored macOS / Linux turnkey script in [install.sh](install.sh) (`curl -fsSL https://raw.githubusercontent.com/epicbrain-dev/openlore/main/install.sh | bash`).
  - [x] Authored Windows PowerShell script in [install.ps1](install.ps1) (`irm https://raw.githubusercontent.com/epicbrain-dev/openlore/main/install.ps1 | iex`).
- [x] **System Doctor & Web Asset Fallbacks**:
  - [x] Added `openlore doctor` in [src/openlore/cli/main.py](src/openlore/cli/main.py) diagnosing OS, CAS permissions, dependencies, ports, and DCCs with optional `--json` export.
  - [x] Added multi-path static asset resolution in `openlore web` enabling seamless execution from any working directory.
- [x] **Release Packaging & Automated Tests**:
  - [x] Updated [scripts/package_release.py](scripts/package_release.py) to bundle `openlore-installer-unix-v1.5.0.tar.gz` and `openlore-installer-windows-v1.5.0.zip` with SHA-256 verification.
  - [x] Created comprehensive unit test suite in [tests/unit/test_installer.py](tests/unit/test_installer.py) and expanded [tests/unit/test_cli.py](tests/unit/test_cli.py).
  - [x] Verified full regression pass rate (152/152 tests passing across 27 modules).

---

## Phase 13: Standalone Desktop Application & 9-Workspace VFX Studio Cockpit
- [x] **Cross-Platform Electron Runtime Architecture**:
  - [x] Built `web/electron/main.cjs` desktop entrypoint with single-instance lock and lifecycle hooks.
  - [x] Implemented secure context bridge in `web/electron/preload.cjs` exposing `window.openloreDesktop`.
  - [x] Implemented background Python daemon supervisor in `web/electron/backendManager.cjs`.
  - [x] Configured native macOS window styling (`hiddenInset`, `trafficLightPosition: { x: 14, y: 14 }`).
  - [x] Implemented native OS file dialogs for OpenUSD stage files (`Cmd+O` / `File -> Open Stage...`).
  - [x] Configured transparent session redirect routing `file:///api/*` to `http://127.0.0.1:8000/api/*`.
- [x] **VFX Producer & 3D Animator Pipeline Alignment**:
  - [x] Redesigned cockpit with dark neutral graphite theme matching Maya, Houdini Solaris, UE5, and ShotGrid.
  - [x] Built Global VFX Pipeline Bar with Show/Seq/Shot/Dept breadcrumbs and DCC bridges status (Maya, Houdini, UE5 Live Link, Blender).
  - [x] Created 9 distinct, fully functional workspaces:
    - [x] **3D Layout & Staging** (USD Outliner tree, Three.js raycast picking, BoxHelper bounding boxes, Shaded/Wireframe/Clay modes, Maya Channel Box transforms, Variant Sets, MaterialX bindings).
    - [x] **Animation & Scenegraph** (3D Character Rig viewport, bone lines, joint spheres, interactive Bézier curve Graph Editor, Dope Sheet mode, Pose Library with 1-click rig application, FK/IK blend sliders, dynamic Squash & Stretch, Onion Skinning ghosting, and Motion Arc Trails).
    - [x] **Shot Review (Producer)** (Sequence SQ042 ShotGrid breakdown, status tracking, thumbnails, frame ranges, and 1-click stage loading).
    - [x] **Lookdev & Shading Studio** (360° turntable, ACEScg studio lighting presets, real-time MaterialX/PBR controls).
    - [x] **Multi-Studio Sync** (CRDT vector clock monitors, live mutation broadcaster, offline shadow buffer).
    - [x] **Render Farm & Grid** (AWS Deadline 10 & ASWF OpenCue GPU farm dispatch, multi-target compilation).
    - [x] **Narrative Multiverse** (W3C RDF 1.1 lore graph, SHACL continuity validator, SPARQL Graph RAG copilot).
    - [x] **Provenance Ledger** (BLAKE3 CAS hashes, HMAC-SHA256 signatures, harvested USD DAGs, OPA Rego royalties).
    - [x] **Partner Enclave** (1%–100% IP decimation, quarantine pre-flight linter, TD 1-click promotion gate, eBPF security).
- [x] **Hollywood Standard Animation Transport Timeline**:
  - [x] Configured standard Hollywood frame range: `1001` through `1150` running at `24.00 FPS`.
  - [x] Implemented real-time SMPTE timecode display (e.g. `00:00:43:10`).
  - [x] Added diamond keyframe markers (`◆`), spacebar play/pause, and real-time frame scrubbing synchronized with viewport deformations.
- [x] **Window Sizing & Accessible Navigation Bar**:
  - [x] Integrated `ResizeObserver` across Three.js viewports ensuring fluid resizing without overlap or bounding box clipping.
  - [x] Added smooth horizontal scroll chevrons (`<ChevronLeft />` and `<ChevronRight />`) flanking the tab bar.
  - [x] Implemented automatic smooth-scrolling centering the active tab upon selection.
  - [x] Added persistent **"Workspaces (9) ▾"** dropdown selector guaranteeing 1-click access to all workspaces at any resolution.
  - [x] Added standard DCC keyboard shortcuts (`⌥1` through `⌥9` / `Alt+1` through `Alt+9`).
  - [x] Implemented macOS window-drag region isolation (`-webkit-app-region: no-drag !important` on all interactive tabs and controls).
- [x] **Desktop App Packaging & Multi-Platform CI/CD**:
  - [x] Configured `electron-builder` in `web/package.json` for macOS (`.dmg`, `.app`), Windows (`.exe`), and Linux (`.AppImage`, `.deb`).
  - [x] Hardened background daemon supervisor in `web/electron/backendManager.cjs` for cross-platform execution.
  - [x] Added multi-platform GitHub Actions release workflow matrix (`windows-latest`, `ubuntu-latest`, `macos-latest`) publishing desktop installers to tagged releases.
  - [x] Cut and tagged OpenLore v2.0.0 release suite with all DCC sidecars, universal wheels, and installers.
  - [x] Verified 100% test pass rate (152/152 tests passing in `pytest tests/`).

---

## Phase 14: Streamlined Desktop Distribution & In-App Engine Bootstrapper (v2.0.1)
- [x] **Zero-Clutter GitHub Releases Distribution**:
  - [x] Cleaned GitHub release asset list by removing raw wheels, source tarballs, and DCC `.zip` sidecar bundles from user download views.
  - [x] Standardized release downloads exclusively on turnkey, platform-native desktop installers (`.exe`, `.dmg`, `.AppImage`, `.deb`).
- [x] **Self-Contained Bundled Python Engine Wheel**:
  - [x] Pre-built universal `openlore-2.0.1-py3-none-any.whl` (124 KB) directly embedded inside `web/electron/` desktop application packages.
  - [x] Enhanced [installer.py](installer.py) and `web/electron/installer.py` with bundled wheel discovery (`script_dir.glob("*.whl")`) to eliminate external network dependencies for engine setup.
- [x] **In-App 1-Click Environment Bootstrapper**:
  - [x] When launched on systems without Python or local OpenLore environments, the desktop app supervisor detects missing dependencies and automatically runs the embedded bootstrapper.
  - [x] DCC connectors (Blender, Maya, Houdini, Unreal, Unity) remain accessible directly within the studio app or via CLI export, removing the need for auxiliary zip downloads.
- [x] **Documentation & Test Suite Integrity**:
  - [x] Updated README, Manual, Deployment Runbook, and Architectural Documentation to reflect the streamlined desktop-first installation flow.
  - [x] Verified full test suite passes (152/152 tests) and clean build pipeline across all targets.


