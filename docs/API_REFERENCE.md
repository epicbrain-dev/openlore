# OpenLore API Reference Manual

_Tagline: "Git for 3D worlds, game lore, and Hollywood pipelines."_

The OpenLore software architecture provides a unified cross-media digital asset management platform bridging real-time game development (Unreal Engine / Unity) and linear offline visual effects / cinematic animation pipelines.

---

## Architecture Overview

OpenLore is divided into 11 modular core domains:

```
src/openlore/
├── core/            # Sharded BLAKE3 CAS, OpenUSD Stage Manager, Atomic Transactions
├── narrative/       # W3C RDF 1.1 triplestore, OWL 2 ontology, SHACL continuity validation, Multiverse timelines
├── collaboration/   # Vector clocks, sparse CRDTs (LWW, ORSet), Kafka streaming, Edge Resolver shadow buffering
├── materials/       # MaterialX parser/translator (Unreal USF/HLSL & Cinematic OSL), UsdSkel dynamic dual-rigs
├── provenance/      # OpenUSD DAG harvester, HMAC-SHA256 signed manifests, OPA Rego royalty accounting
├── partner/         # Outbound geometric decimation/clay proxying, quarantined pre-flight linter, TD promotion gates, eBPF zero-egress
├── compilation/     # Temporal workflow dispatcher, Kubernetes Argo DAG generator, Unreal/Unity compilers, Shot point cache baker
├── bridge/          # Unreal Engine 5 Live Link Bridge, UDP streaming, C++ plugin scaffold
├── server/          # Zero-dependency Python REST API & SPA static hosting for studio dashboards
├── cli/             # Unified production command-line interface
└── exceptions.py    # Standardized domain error taxonomy
```

---

## 1. `openlore.core`

### `ContentAddressedStorage(storage_root: Path)`
Immutable sharded Content-Addressed Storage engine indexed by cryptographic BLAKE3 checksums.
- `store_bytes(data: bytes, mime_type: str = "application/octet-stream") -> CASObject`: Stores raw bytes into a 2-level directory shard (`objects/<hash[:2]>/<hash[2:4]>/<hash>`) with deduplication.
- `store_file(source_path: Path, mime_type: str) -> CASObject`: Streams file from disk with streaming BLAKE3 computation.
- `retrieve(blake3_hash: str) -> CASObject`: Returns metadata and absolute filesystem path.
- `retrieve_bytes(blake3_hash: str) -> bytes`: Reads full byte payload.
- `verify_integrity(blake3_hash: str, raise_on_error: bool = False) -> bool`: Verifies stored file against computed checksum.
- `exists(blake3_hash: str) -> bool`: Quick boolean existence test.

### `StageCompositionManager(stages_dir: Path)`
Coordinates OpenUSD (`pxr.Usd.Stage`) life cycles, layer stacks, and sublayer references.
- `create_stage(stage_uri: str, format: str = "usda") -> UsdStageReference`: Creates root layer with default prim `/World`.
- `load_stage(stage_uri: str) -> UsdStageReference`: Loads existing stage and inspects sublayers.
- `add_sublayer(stage_ref: UsdStageReference, sublayer_path: str, position: int = -1) -> None`: Sublayers an external stage into the root layer.
- `bind_cas_asset(stage_ref: UsdStageReference, prim_path: str, cas_object: CASObject, attribute_name: str = "openlore:assetHash") -> None`: Binds immutable binary asset hash directly to a Prim.

### `TransactionManager(repo_root: Path, stage_manager: StageCompositionManager)`
Isolates lightweight metadata mutations from binary payloads with transactional commit history.
- `begin_transaction(stage_ref: UsdStageReference, author: str) -> TransactionSession`: Starts an active staging session.
- `session.set_property(prim_path: str, property_name: str, new_value: Any)`: Stages attribute mutation.
- `session.attach_cas_payload(prim_path: str, attribute_name: str, cas_object: CASObject)`: Stages asset binding.
- `session.commit(message: str) -> TransactionalEdit`: Atomically commits all staged deltas and records git-style commit history.
- `get_commit_history(stage_uri: str) -> List[TransactionalEdit]`: Returns linear commit chain from `HEAD`.

---

## 2. `openlore.narrative`

### `NarrativeGraphClient(sparql_endpoint: Optional[str] = None)`
W3C RDF 1.1 Named Graph triplestore client supporting SPARQL 1.1 queries and updates.
- `insert_character(character: CharacterEntity) -> None`: Adds character lifecycle metadata.
- `insert_event(event: NarrativeEvent) -> None`: Records historical narrative event with participants and asset bindings.
- `query_character_lifecycle(character_uri: str) -> Dict[str, Any]`: SPARQL introspector returning status, birth/death, and timeline.
- `export_graph(format: str = "trig") -> str`: Serializes named graph dataset to TriG or Turtle.
- `save_to_file(path: Path)` / `load_from_file(path: Path)`: Persistent graph I/O.

### `SHACLContinuityValidator(shapes_path: Path)`
Asynchronous semantic continuity validator evaluating W3C Shapes Constraint Language (SHACL).
- `validate_graph(dataset: Dataset, timeline_uri: Optional[str] = None) -> ValidationReport`: Audits event temporal order and character status.
- `assert_valid(dataset: Dataset, timeline_uri: Optional[str] = None)`: Raises `ContinuityViolationError` upon rule violation.

### `TimelineBranchManager(graph_client: NarrativeGraphClient)`
Multiverse branching engine isolating spin-off storylines from prime canon.
- `create_prime_canon(timeline_uri: str, name: str) -> TimelineModel`: Establishes immutable prime canon.
- `branch_timeline(source_timeline_uri: str, new_timeline_slug: str, new_timeline_name: str, divergence_event_uri: Optional[str] = None) -> TimelineModel`: Clones source lore into an isolated timeline namespace.
- `list_timelines() -> List[TimelineModel]`: Lists all active timelines.

---

## 3. `openlore.collaboration`

### `VectorClock(node_id: str)`
Causal ordering tracker maintaining monotonic logical clocks per studio node.
- `increment() -> VectorClock`: Advances local counter.
- `merge(other: VectorClock) -> VectorClock`: Takes pointwise maximum across all node counters.
- `dominates(other: VectorClock) -> bool`: Causal dominance evaluation.
- `is_concurrent_with(other: VectorClock) -> bool`: Concurrency detection.

### Sparse CRDT Types (`openlore.collaboration.crdt`)
Conflict-free replicated data types ensuring 100% causal convergence across distributed DCC viewports:
- `LWWRegister`: Last-Write-Wins register resolving concurrent mutations via:
  1. Causal dominance (VectorClock)
  2. Wall-clock timestamp
  3. Deterministic studio ID tie-breaking
- `ORSet`: Observed-Remove set with unique observation tokens for concurrent element addition and deletion.
- `CRDTSceneReplica`: Manages all replicated prim attributes for a collaborative USD stage.

### `KafkaEventStream(stage_topic: str, bootstrap_servers: str = "localhost:9092", use_memory_bus: bool = False)`
Append-only collaborative event stream rejecting payloads over 64 KB with `SecurityPolicyError` to keep network latency minimal.

### `EdgeResolverDaemon(studio_id: str, stage_uri: str, event_stream: KafkaEventStream)`
Manages studio connectivity states and shadow buffering.
- `record_local_edit(prim_path: str, attribute_name: str, value: Any)`: Dispatches or buffers mutation.
- `set_connectivity(online: bool)`: Toggles network connection. Automatically flushes shadow-buffered edits upon reconnection to achieve causal convergence.

---

## 4. `openlore.materials`

### `MaterialXTranslator()`
Translates vendor-neutral `.mtlx` documents into engine-specific shader formats:
- `parse_document(mtlx_path: Path) -> SurfaceAppearance`: Extracts base, color, metalness, roughness, normal maps.
- `export_to_unreal_shader(appearance: SurfaceAppearance) -> str`: Emits Unreal Engine USF/HLSL parameter structs (`FOpenLoreMaterialInput`).
- `export_to_cinematic_osl(appearance: SurfaceAppearance) -> str`: Emits Open Shading Language (OSL) closure shaders.

### `DynamicRigManager(usd_stage: Usd.Stage)`
Coordinates `pxr.UsdSkel` skeletal hierarchies and switchable `rigMode` VariantSets:
- `setup_dual_rig(prim_path, joints, collision_capsules, point_cache_hash)`: Authors dual variants:
  - `cinematic_cache`: Pre-baked point cache CAS hash binding for deterministic film playback.
  - `game_collision`: UsdSkel hierarchy and collision capsules for real-time physics.
- `set_active_variant(prim_path, variant: VariantRigType)`: Toggles active mode.
- `get_active_variant(prim_path) -> VariantRigType`: Queries active mode.

---

## 5. `openlore.provenance`

### `StageDAGHarvester(usd_stage: Usd.Stage)`
Recursively introspects stage DAGs, sublayers, and prim attributes to extract asset hashes, partner IDs, and royalty percentages.
- `create_manifest(stage_uri: str, secret_key: str) -> AssetProvenanceManifest`: Generates signed provenance manifest.

### `AssetProvenanceManifest`
Cryptographically signed manifest data model:
- `sign_manifest(secret_key: str) -> str`: Generates HMAC-SHA256 signature over canonical payload.
- `verify_signature(secret_key: str) -> bool`: Verifies signature against tampering.

### `RoyaltyAccountingEngine(opa_endpoint: str = "http://localhost:8181/v1/data/openlore/royalties")`
Evaluates export licensing against Open Policy Agent (OPA) Rego policies:
- `evaluate_export_allowance(manifest: AssetProvenanceManifest) -> Tuple[bool, List[str]]`: Determines export eligibility and identifies unlicensed assets.
- `calculate_royalty_splits(manifest: AssetProvenanceManifest) -> Dict[str, float]`: Computes aggregate partner royalty distributions.

---

## 6. `openlore.partner`

### `OutboundDecimationPipeline(config: ProxyStageConfig)`
Automates IP sanitization for external vendor studios:
- `sanitize_outbound_stage(source_stage_path: Path, output_proxy_path: Path) -> Path`:
  - Flattens OpenUSD stage layers.
  - Decimates high-density mesh geometry.
  - Strips proprietary metadata (`pointCacheHash`, `assetHash`, `royaltyPercentage`).
  - Assigns neutral clay display material (`(0.7, 0.7, 0.7)`) and marks `openlore:isProxyMesh = True`.

### `PreFlightUSDValidator(max_polycount_ceiling: int = 500000)`
Quarantined linter verifying contractor deliverables:
- `validate_deliverable(stage_path: Path) -> InboundLintResult`: Checks root hierarchy (`/World`, `/Root`, `/Asset`), prim naming conventions, and mesh/scene polygon ceilings.

### `StagePromotionGate()`
Technical Director (TD) promotion interface with optimistic locking:
- `acquire_promotion_lock(stage_uri: str, td_user: str, target_timeline: str) -> str`: Acquires exclusive lock token.
- `promote_to_production(...) -> bool`: Validates lock, verifies pre-flight linting, checks narrative continuity, atomically sublayers deliverable into production stage, and releases lock.

### `EBPFNetworkPolicyManager(allowed_inspection_endpoints: List[str])`
- `generate_tc_filter_rules() -> str`: Emits eBPF Traffic Control (`tc`) kernel C packet filter.
- `generate_bpftool_commands(interface: str) -> List[str]`: Emits shell commands for `tc` and `bpftool`.
- `verify_enclave_compliance(enclave_id: str, active_sockets: List[dict]) -> Tuple[bool, List[str]]`: Audits socket connections for zero-egress compliance.

---

## 7. `openlore.compilation`

### `EnginePackageCompiler(target_engine: str)`
Compiles OpenUSD stages into real-time game packages:
- `compile_package(usd_stage_path: Path, output_dir: Path, package_name: Optional[str]) -> Path`:
  - **Unreal Engine**: Packaged `.pak` archive with extracted meshes, collision physics assets, and `content_manifest.json` (UE 5.4 / `PCD3D_SM6`).
  - **Unity**: Packaged `.unitypackage` archive with prefabs, materials, and scenes (Unity 6000.0).
  - Emits companion `_manifest.json` with BLAKE3 package hash.

### `OfflineShotBaker(fps: float = 24.0)`
- `bake_cache(usd_stage_path: Path, start_frame: int, end_frame: int, output_dir: Path, shot_name: str) -> Path`:
  - Authors deterministic time-sampled vertex point deformation (`points.timeSamples[t]`) and bounding extents in OpenUSD.
  - Emits `_cache_manifest.json` with BLAKE3 cache hash.

### `WorkerGridDispatcher(temporal_endpoint: str, argo_namespace: str, catalog: ProductionCatalog)`
- `trigger_compilation_workflow(stage_uri: str, target_engines: List[str], stage_path: Path, output_dir: Path) -> str`: Dispatches multi-activity compilation pipeline (`validate_stage` $\rightarrow$ `compile_unreal/unity` $\rightarrow$ `bake_shot_point_cache` $\rightarrow$ `register_catalog`).
- `get_job_status(workflow_id: str) -> Dict[str, Any]`: Returns live execution progress.
- `generate_argo_workflow_spec(stage_uri: str, target_engines: List[str]) -> Dict[str, Any]`: Generates Kubernetes Argo Workflow DAG spec (`argoproj.io/v1alpha1`).
- `generate_argo_workflow_yaml(...) -> str`: Emits ready-to-deploy YAML.

### `ProductionCatalog()`
Persistent registry indexing compiled packages and point caches with CAS hashes, stage URIs, and timestamps.

---

## 8. `openlore.server`

### `OpenLoreAPIHandler(request, client_address, server)`
Zero-dependency Python `http.server` request handler providing REST API endpoints and Single-Page Application (SPA) static file serving with automatic CORS support:
- `GET /api/status`: Engine health, CAS storage root, stage count, and system metrics.
- `GET /api/stages`: List composed OpenUSD stages with prim inventories and sublayers.
- `GET /api/lore/timelines`: List narrative timelines (Prime Canon and divergent branches).
- `POST /api/lore/branch`: Create a new timeline branch with divergence events.
- `GET /api/lore/entities`: Query narrative characters, lifecycles, and narrative events.
- `GET /api/daemon`: Inspect Edge Resolver daemon state, vector clock map, and sync rate.
- `POST /api/daemon/edit`: Emit collaborative edits through the daemon.
- `POST /api/partner/lint`: Quarantine linter auditing partner USD deliverables.
- `POST /api/partner/promote`: TD 1-click promotion gate promoting sanitized assets to stage.
- `GET /api/provenance`: Harvester inspecting Prim DAG hashes and cryptographic signatures.
- `POST /api/compile`: Dispatch cross-media compilation to Temporal / Argo grid.
- `GET /api/catalog`: Central Production Catalog indexing compiled packages and point caches.

### `run_server(host: str = "127.0.0.1", port: int = 8000, static_dir: Optional[Path] = None)`
Initializes and serves `ThreadingHTTPServer` bound to the designated network interface and port.

---

## 9. `openlore.bridge`

### `UnrealLiveLinkBridge(edge_daemon, broadcast_host, broadcast_port, receive_port, studio_id)`
Duplex virtual production bridge synchronizing OpenLore OpenUSD scenes and CRDT mutations with Unreal Engine 5 Live Link:
- `start(mode: str = "duplex", target_fps: float = 60.0)`: Starts provider broadcasting and/or receiver socket listening.
- `stop()`: Shuts down background loops and closes network sockets.
- `bind_subject(prim_path: str, subject_name: str, subject_type: LiveLinkSubjectType)`: Maps OpenUSD prims (`/World/CineCamera`) to Live Link subjects (`Camera_StageA`).
- `handle_crdt_mutation(mutation: CRDTPartialMutation) -> bool`: Outbound translation from OpenUSD right-handed coordinates to Unreal left-handed centimeters, emitting Live Link frame.
- `get_status() -> Dict[str, Any]`: Returns operational mode, active subjects, and packet throughput metrics.

### `CoordinateConverter`
High-precision coordinate transformation utility between OpenUSD (Right-Handed, meters/cm) and Unreal Engine 5 (Left-Handed, Z-Up centimeters):
- `usd_to_unreal_position(pos_usd, up_axis="Z", meters_per_unit=1.0) -> Tuple[float, float, float]`
- `unreal_to_usd_position(pos_ue, up_axis="Z", meters_per_unit=1.0) -> Tuple[float, float, float]`
- `usd_to_unreal_quaternion(quat_usd, up_axis="Z") -> Tuple[float, float, float, float]`
- `euler_to_quaternion(roll, pitch, yaw) -> Tuple[float, float, float, float]`
- `quaternion_to_euler(quat) -> Tuple[float, float, float]`

### `UnrealPluginScaffolder`
Generates ready-to-build C++ Unreal Engine 5 Plugin projects:
- `generate_plugin(output_dir: Path, plugin_name: str = "OpenLoreLiveLink") -> Dict[str, Path]`: Authors `.uplugin`, `Build.cs`, `ILiveLinkSource` implementation, and editor Python bridge scripts.

---

## 10. CLI Command Summary

| Command | Subcommand / Options | Description |
|---|---|---|
| `openlore init` | `--cas-path`, `--canon` | Initialize CAS repository and prime canon timeline. |
| `openlore stage` | `create`, `list`, `inspect` | Manage OpenUSD stage composition layers. |
| `openlore lore` | `verify`, `branch`, `list`, `export` | Validate narrative SHACL shapes and branch multiverse realities. |
| `openlore daemon` | `start`, `status`, `stop` | Manage Edge Resolver background sync and shadow buffers. |
| `openlore partner`| `sanitize`, `lint`, `promote` | IP decimation proxying, quarantine linting, and TD promotion. |
| `openlore compile`| `--stage`, `--stage-path`, `--target` | Dispatch worker grid compilation (Unreal, Unity, Shot baker). |
| `openlore catalog`| `list` | Inspect Central Production Catalog builds. |
| `openlore export` | `--stage`, `--target` | Introspect DAG, evaluate OPA royalties, and trigger builds. |
| `openlore web` | `--host`, `--port`, `--static-dir` | Launch REST API server & serve React Studio Cockpit dashboard. |
| `openlore livelink`| `stream`, `export-plugin` | Run real-time UE5 Live Link bridge or export turnkey C++ plugin. |

