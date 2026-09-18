# OpenLore: Complete System Documentation

_Tagline: "Git for 3D worlds, game lore, and Hollywood pipelines."_

- `openusd`  
- `materialx`  
- `game-dev`  
- `vfx-pipeline`  
- `crdt`  
- `knowledge-graph`  
- `rdf`  
- `digital-asset-management`  
- `pipeline-td`  
- `virtual-production`  
- `transmedia`  
- `creative-tooling`

### Core Foundation & Asset Storage Architecture

The Cross-Media IP Canon and Asset Synchronization Suite establishes a unified production backbone connecting interactive game development with linear film and television visual effects pipelines.

Lightweight transactional edits are strictly isolated from heavy binary files across the entire infrastructure. Real-time digital content creation viewports and game engines read structural scene arrangements directly from layered [OpenUSD (Universal Scene Description)](https://openusd.org/release/index.html) composition stages. All underlying 3D geometry meshes, textures, and point caches reside in an immutable, content-addressed storage repository indexed by cryptographic [BLAKE3](https://github.com/BLAKE3-team/BLAKE3) hashes.

### Narrative Ontology & Continuity Enforcement

The narrative lore layer guarantees story continuity across transmedia releases by modeling character lifecycles, spatiotemporal bounds, and asset bindings inside an enterprise [W3C RDF 1.1](https://www.w3.org/TR/rdf11-concepts/) semantic graph. Complex narrative rules and continuity constraints are formalized using [W3C Web Ontology Language (OWL 2)](https://www.w3.org/TR/owl2-overview/) and verified via asynchronous [W3C Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/) engines. When creative leaders adapt an established property into an alternate continuity, the system branches the underlying semantic graph into an isolated timeline namespace, ensuring derivative spin-offs evolve without invalidating prime canon.

### Distributed Collaboration & Event Messaging

Live collaborative scene modifications travel across distributed studios through an append-only event stream managed by [Apache Kafka](https://kafka.apache.org/). Artist modifications to scene properties, variant choices, and asset references convert into sparse conflict-free replicated data types paired with vector clocks to maintain deterministic causal order across remote sites. Because high-frequency geometric transformations and massive point caches bypass this messaging layer entirely, the event stream maintains high throughput across corporate firewalls without saturating network bandwidth.

### Cross-Media Material & Dynamic Rigging Standards

Physical and visual consistency across different media formats relies on standardized material and dynamic representations. Surface appearances are defined through vendor-neutral [MaterialX](https://materialx.org/) node graphs that translate cleanly between offline cinematic renderers and real-time game viewports. Dynamic character rigs utilize [OpenUSD UsdSkel](https://openusd.org/release/api/usd_skel_page_front.html) skeletal hierarchies paired with switchable [OpenUSD VariantSets](https://www.google.com/search?q=https://openusd.org/release/glossary.html%23usdglossary-variantset), allowing production teams to alternate between an immutable, pre-baked geometry cache for deterministic film playback and interactive collision primitives for real-time game engines.

### Provenance Tracking & Financial Accounting

To automate royalty calculations and downstream financial splits, pipeline workers introspect the complete directed acyclic graph of every production USD stage at export time. The harvest engine extracts the full tree of referenced sublayers, prim paths, and cryptographic hashes, feeding this asset provenance manifest directly into an [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) evaluation engine linked to enterprise financial accounting systems.

### Partner Isolation & Ingestion Workflows

External partner studios and contractors operate within isolated, air-gapped cloud environments to protect unreleased intellectual property. Outbound stages undergo automated geometric flattening and mesh decimation, replacing proprietary character models with low-resolution proxies and complex shaders with generic clay materials. Incoming contractor deliverables are quarantined inside a pre-flight linting sandbox using the [OpenUSD Python API](https://openusd.org/release/api/usd_page_front.html) to verify scene hierarchy, polycount ceilings, and namespace conventions before presenting an internal technical director with a one-click promotion interface.

### Automated Downstream Compilation

Once an asset receives technical and narrative approval, downstream compilation executes through an event-driven worker grid orchestrated by [Temporal](https://temporal.io/) and [Argo Workflows](https://argoproj.github.io/workflows/). Containerized worker pools automatically compile real-time engine packages, bake offline shot point caches, and register completed builds into the central production catalog.

### OpenLore Studio Desktop & VFX Pipeline Cockpit

OpenLore Studio is packaged as a standalone cross-platform desktop application powered by [Electron](https://www.electronjs.org/), [React 19](https://react.dev/), and [Three.js](https://threejs.org/). Engineered specifically to align with the visual workflow, ergonomic conventions, and muscle memory of visual effects producers and 3D animators (mirroring Autodesk Maya, SideFX Houdini Solaris, Unreal Engine 5, and Autodesk ShotGrid), the cockpit provides 9 dedicated production workspaces:

1. **3D Layout & Staging (`USD 24.11`)**: Direct OpenUSD scenegraph hierarchy browsing via the USD Outliner, 3D viewport raycast selection with gold bounding box highlights (`THREE.BoxHelper`), live shading switches (**USD Shaded**, **Wireframe**, **Lookdev Clay**), and Maya/Houdini-style Channel Box numeric matrix transforms (`Translate`, `Rotate`, `Scale`).
2. **Animation & Scenegraph (`24 FPS`)**: 3D character skeleton and joint hierarchy visualization, interactive Graph Editor with cubic Bézier curves and tangent interpolation handles (**Smooth**, **Linear**, **Step**), Dope Sheet mode, Pose Library with 1-click rig application (`Combat Idle`, `Sandworm Dodge`, `Crysknife Strike`, `Tactical Landing`), FK/IK blending, dynamic Squash & Stretch scaling, and multi-frame Onion Skinning (cyan/magenta ghosting).
3. **Shot Review & Production Tracking (`ShotGrid`)**: Sequence `SQ042` shot management with live status tracking (`In Progress`, `In Review`, `Approved`, `Blocked`), thumbnail previews, frame count ranges, lead artist assignments, and 1-click stage loading into the 3D viewport.
4. **Lookdev & Shading Studio (`MaterialX`)**: 360° turntable stage with ACEScg lighting presets (**Studio Neutral 5600K**, **Golden Sunset 3200K**, **Cyberpunk LED Volume**, **High-Key Rim**) and real-time MaterialX/PBR parameter tuning (Base Color, Metallic, Roughness, Normal, IOR).
5. **Multi-Studio Collaborative Sync (`CRDT`)**: Real-time CRDT vector clock topology, live mutation broadcast, network severance simulator, and UE5 Live Link status.
6. **Render Farm & Comp Grid (`Deadline`)**: GPU farm dispatch for AWS Deadline 10 and ASWF OpenCue, multi-target engine compilers (.pak, .unitypackage, .usdc), and central production catalog ledger.
7. **Narrative Multiverse (`SHACL`)**: W3C RDF 1.1 temporal lore graph, SHACL continuity validation, and interactive SPARQL Graph RAG narrative assistant.
8. **Provenance Ledger (`BLAKE3`)**: Cryptographic BLAKE3 CAS hashes, HMAC-SHA256 signatures, harvested USD DAG trees, and OPA Rego automated royalty splits.
9. **Partner Enclave (`Cleanroom`)**: Outbound 1%–100% IP decimation controls, quarantine pre-flight linter, TD 1-click promotion gate, and eBPF zero-egress kernel security.

### Hollywood Standard Transport Timeline & Navigation

The studio interface integrates a standardized Hollywood animation transport timeline initialized to industry standard frame `1001` through `1150` at **24.00 FPS**, complete with SMPTE timecode readout (`00:00:43:10`), diamond keyframe indicators (`◆`), spacebar play/pause, and real-time frame scrubbing.

Workspace access is guaranteed at all display resolutions through an accessible navigation bar featuring horizontal scroll chevrons (`<ChevronLeft />`, `<ChevronRight />`), automatic centering of the active tab, a persistent **"Workspaces (9) ▾"** quick dropdown menu, standard DCC keyboard shortcuts (`⌥1`–`⌥9` / `Alt+1`–`Alt+9`), and strict macOS window-drag isolation (`-webkit-app-region: no-drag !important`).

### Turnkey Desktop Distribution & Engine Bootstrapper

To maximize accessibility across creative studios and minimize friction for 3D animators and producers, OpenLore desktop packages (`.dmg`, `.exe`, `.AppImage`, `.deb`) are distributed as self-contained binaries. The core Python engine wheel is bundled directly within the desktop application bundle. When launched on workstations lacking pre-installed Python environments, the supervisor daemon automatically invokes the embedded bootstrapper to provision an isolated local runtime, ensuring instant out-of-the-box operation without manual terminal interaction.

### System Resilience & Recovery Protocols

System resilience and error recovery depend on several distinct operational protocols:

- Distributed edge resolver daemons switch to local shadow buffering during network outages, reconciling edits through causal state convergence once connectivity returns.

- Stage promotion gates enforce optimistic locking to prevent merge operations until background narrative validation rules confirm complete timeline consistency.

- Isolated partner enclaves enforce zero-egress network policies via [eBPF](https://ebpf.io/) kernel packet filters, restricting contractor data transfers entirely to signed inspection endpoints.

### Licensing & Legal Terms

This platform is released under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

Copyright 2026 EpicBrain-Dev.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this software except in compliance with the License. You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0).

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

The [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) provides an express grant of patent rights and permits commercial modification, private distribution, and embedding within proprietary game runtimes or closed-source digital content creation plugins without requiring downstream production code to be open-sourced.