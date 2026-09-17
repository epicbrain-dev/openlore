# OpenLore: Comprehensive Instruction & Operations Manual

_Tagline: "Git for 3D worlds, game lore, and Hollywood pipelines."_  
_Document Version: 1.0.2 (Production Release)_  
_Target Audience: Pipeline TDs, Lead 3D Artists, Narrative Directors, Game Developers, DevOps Engineers, and Studio Systems Administrators._

---

# Table of Contents

1. [System Architecture & Theoretical Foundation](#1-system-architecture--theoretical-foundation)
   - [1.1 The Cross-Media Production Problem](#11-the-cross-media-production-problem)
   - [1.2 The OpenLore Architecture](#12-the-openlore-architecture)
   - [1.3 Core Technical Pillars](#13-core-technical-pillars)
2. [Prerequisites, Installation & Environment Setup](#2-prerequisites-installation--environment-setup)
   - [2.1 Operating System & Runtime Requirements](#21-operating-system--runtime-requirements)
   - [2.2 CLI Installation (Global & Local)](#22-cli-installation-global--local)
   - [2.3 Environment Variables Reference](#23-environment-variables-reference)
   - [2.4 Web Studio Cockpit Build](#24-web-studio-cockpit-build)
3. [OpenLore CLI Command Reference](#3-openlore-cli-command-reference)
   - [3.1 openlore init](#31-openlore-init)
   - [3.2 openlore stage](#32-openlore-stage)
   - [3.3 openlore lore](#33-openlore-lore)
   - [3.4 openlore daemon](#34-openlore-daemon)
   - [3.5 openlore partner](#35-openlore-partner)
   - [3.6 openlore compile](#36-openlore-compile)
   - [3.7 openlore catalog](#37-openlore-catalog)
   - [3.8 openlore export](#38-openlore-export)
   - [3.9 openlore web](#39-openlore-web)
   - [3.10 openlore livelink](#310-openlore-livelink)
   - [3.11 openlore auth](#311-openlore-auth)
   - [3.12 openlore dcc](#312-openlore-dcc)
4. [Web Studio Cockpit Operator Guide](#4-web-studio-cockpit-operator-guide)
   - [4.1 Starting the Cockpit](#41-starting-the-cockpit)
   - [4.2 Tab 1: Stage Viewport & Real-Time Telemetry](#42-tab-1-stage-viewport--real-time-telemetry)
   - [4.3 Tab 2: Stage & Collaborative CRDT Synchronization](#43-tab-2-stage--collaborative-crdt-synchronization)
   - [4.4 Tab 3: Narrative Lore Graph & SPARQL Canon Auditing](#44-tab-3-narrative-lore-graph--sparql-canon-auditing)
   - [4.5 Tab 4: Partner Enclave Isolation & Sanitization](#45-tab-4-partner-enclave-isolation--sanitization)
   - [4.6 Tab 5: Provenance Ledger & OPA Smart Contract Accounting](#46-tab-5-provenance-ledger--opa-smart-contract-accounting)
   - [4.7 Tab 6: Temporal Compilation Grid & Multi-Target Packaging](#47-tab-6-temporal-compilation-grid--multi-target-packaging)
5. [3D DCC & Game Engine Integration Manual](#5-3d-dcc--game-engine-integration-manual)
   - [5.1 Blender 4.x Integration Guide](#51-blender-4x-integration-guide)
   - [5.2 Autodesk Maya Integration Guide](#52-autodesk-maya-integration-guide)
   - [5.3 Unreal Engine 5 Live Link Integration Guide](#53-unreal-engine-5-live-link-integration-guide)
   - [5.4 SideFX Houdini 20 (Solaris / USD LOPs) Integration Guide](#54-sidefx-houdini-20-solaris--usd-lops-integration-guide)
   - [5.5 Unity 6 Live Link Integration Guide](#55-unity-6-live-link-integration-guide)
6. [Enterprise Security, RBAC & OPA Rego Policies](#6-enterprise-security-rbac--opa-rego-policies)
   - [6.1 Role-Based Access Control (RBAC)](#61-role-based-access-control-rbac)
   - [6.2 Cryptographic DAG Manifests & Verification](#62-cryptographic-dag-manifests--verification)
   - [6.3 Customizing OPA Rego Policy Rules](#63-customizing-opa-rego-policy-rules)
   - [6.4 Network Isolation & Egress Filtering](#64-network-isolation--egress-filtering)
7. [Deployment, Staging & Production Runbook](#7-deployment-staging--production-runbook)
   - [7.1 Local Development Profile (:8000)](#71-local-development-profile-8000)
   - [7.2 Multi-Container Docker Staging Profile (:8080)](#72-multi-container-docker-staging-profile-8080)
   - [7.3 Production Kubernetes Deployment via Helm](#73-production-kubernetes-deployment-via-helm)
8. [Troubleshooting & Diagnostics](#8-troubleshooting--diagnostics)
   - [8.1 CLI Command Not Found](#81-cli-command-not-found)
   - [8.2 Port Conflicts (8000 / 8080)](#82-port-conflicts-8000--8080)
   - [8.3 Live Link UDP Stream Not Showing in UE5](#83-live-link-udp-stream-not-showing-in-ue5)
   - [8.4 OPA Licensing Gate Export Violations](#84-opa-licensing-gate-export-violations)
   - [8.5 Triplestore SHACL Validation Errors](#85-triplestore-shacl-validation-errors)

---

# 1. System Architecture & Theoretical Foundation

## 1.1 The Cross-Media Production Problem

Modern entertainment properties (e.g. Marvel Cinematic Universe, Star Wars, Riot Games Runeterra, CD PROJEKT RED Cyberpunk) no longer operate in single software silos. A major production simultaneously requires:

1. **Feature Film & Virtual Production**: OpenUSD non-destructive composition stacks, MaterialX shading, 8K UDIM textures, and sub-frame Alembic/USD point caches.
2. **AAA Video Games**: Real-time skeletal meshes, physics assets, Nanite geometry, collision hulls, and engine-optimized runtime packages (`.pak`, `.unitypackage`).
3. **Cross-Media Lore & Continuity**: Character ages, status (alive, deceased, ascended), relationship graphs, temporal milestones, and canonical constraints historically buried in disparate wikis, Word docs, and Jira tickets.
4. **Outsourced Vendor Co-Development**: Multiple global partner studios simultaneously contributing assets without risking intellectual property leaks or corrupting the master assembly stage.

Prior to OpenLore, synchronizing these assets required manual asset conversion, error-prone file renames, and expensive pipeline reconciliation meetings.

## 1.2 The OpenLore Architecture

OpenLore acts as the central production backbone, unifying OpenUSD scene graph management, cryptographic content addressing, semantic knowledge graphs, real-time distributed synchronization, and automated build packaging:

```text
                                  [ OpenLore Studio Cockpit (Web SPA / Three.js Viewport) ]
                                                            │
                       ┌────────────────────────────────────┼────────────────────────────────────┐
                       │                                    │                                    │
                       ▼                                    ▼                                    ▼
             [ REST API & WebSockets ]              [ OpenUSD Wasm ]                 [ SPARQL Graph RAG ]
            (Python ThreadingHTTPServer)           (In-Browser USDA)                  (Dynamic Assistant)
                       │                                    │                                    │
       ┌───────────────┴───────────────┐                    │                                    │
       ▼                               ▼                    │                                    ▼
[ Core Storage & Stages ]    [ Real-Time Sync ]             │                        [ Narrative Knowledge ]
 • BLAKE3 CAS (Local / S3)    • Apache Kafka Stream         │                         • W3C RDF 1.1 Named Graphs
 • OpenUSD Stage Manager      • Vector Clocks (T=N)         │                         • OWL 2 Universe Ontology
 • Atomic Commit Engine       • Sparse CRDT (LWW / ORSet)   │                         • SHACL Continuity Engine
       │                      • Edge Shadow Buffering       │                         • Prime vs. Alternate Timelines
       │                               │                    │                                    │
       ├───────────────────────────────┴────────────────────┴────────────────────────────────────┤
       ▼                                                                                         ▼
[ Partner Enclave Security ]                                                            [ Cross-Media Grid ]
 • Outbound Decimation (1% - 100%)                                                       • Unreal Engine 5 Live Link (UDP)
 • Neutral Clay Shader Override                                                          • Blender 4.x & Maya Connectors
 • Quarantined Pre-Flight Linter                                                         • OPA Rego Royalty Evaluator
 • TD 1-Click Optimistic Lock Gate                                                       • Temporal / Argo Compilation Grid
 • eBPF Zero-Egress Kernel Filters                                                       • Production Catalog (PostgreSQL)
```

## 1.3 Core Technical Pillars

| Subsystem | Underlying Technology | Operational Purpose |
| :--- | :--- | :--- |
| **Storage Engine** | Pure-Python BLAKE3 CAS & S3 SigV4 | Cryptographically dedupes heavy binary assets (meshes, textures) separate from lightweight USD text composition layers. |
| **Composition Layer** | OpenUSD (`pxr.Usd` / `.usda` / `.usdc`) | Non-destructive sublayering, variant sets, and atomic transaction staging. |
| **Lore Engine** | W3C RDF 1.1 Triplestore & SHACL | Stores character lifecycles, locations, and events in named graphs. Asynchronously flags temporal contradictions (e.g. post-mortem event attendance). |
| **Graph RAG** | Dynamic SPARQL Reasoning Engine | Synthesizes graph queries from plain English, validating bounds before returning structured canon citations to scriptwriters. |
| **Collaborative Sync** | CRDTs (LWW-Register, OR-Set) & Vector Clocks | Resolves multi-studio concurrent transform edits across remote nodes without central locking bottlenecks. |
| **Partner Sandbox** | Outbound Decimation & eBPF Filtering | Strips internal proprietary USD attributes, decimates geometry by 1% to 100%, applies neutral clay shaders, and quenches IP egress. |
| **Provenance Ledger** | HMAC-SHA256 & OPA Rego | Computes cryptographic stage DAG manifests, verifies licensing compliance, and automates percentage-based royalty distributions. |
| **Compilation Grid** | Temporal Activities & Argo Workflows | Compiles raw OpenUSD master stages into production-ready game packages (`.pak`, `.unitypackage`) and 24 FPS shot point caches. |

---

# 2. Prerequisites, Installation & Environment Setup

## 2.1 Operating System & Runtime Requirements

- **Operating Systems Supported**: macOS (ARM64 Apple Silicon & Intel x86_64), Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+), Windows 10/11 via WSL2.
- **Python**: Python 3.9, 3.10, 3.11, 3.12, or 3.13. Standard library zero-dependency core ensures installation on restricted studio workstations.
- **Node.js**: Node.js v18+ and npm v9+ (required only if modifying or recompiling the Web Studio Cockpit SPA).
- **Optional Services**:
  - Docker & Docker Compose (for staging containerized services: PostgreSQL 16, MinIO, Redpanda Kafka, Jena Fuseki).
  - Blender 4.0+ (for DCC sidecar testing).
  - Autodesk Maya 2024 / 2025 (for Maya bridge testing).
  - Unreal Engine 5.3 / 5.4+ (for Live Link streaming and C++ plugin compilation).

## 2.2 CLI Installation (Global & Local)

### Option A: Immediate Repository Usage (Zero-Install)
From the root of the cloned repository:
```bash
./openlore --help
```

### Option B: User-Level Editable Installation
Registers the `openlore` binary into your user Python site-packages:
```bash
python3 setup.py develop --user
```

### Option C: System PATH Integration
Ensure the following directories are in your shell startup file (`~/.zshrc` or `~/.bashrc`):
```bash
export PATH="/Users/$USER/.antigravity-ide/antigravity-ide/bin:/Users/$USER/.gemini/antigravity/bin:/Users/$USER/Library/Python/3.9/bin:$PATH"
```
Reload your active shell:
```bash
source ~/.zshrc
which openlore
```

## 2.3 Environment Variables Reference

| Variable Name | Default Value | Valid Options | Description |
| :--- | :--- | :--- | :--- |
| `OPENLORE_ENV` | `development` | `development`, `staging`, `production` | Active runtime profile. Modifies log verbosity and backend bindings. |
| `OPENLORE_HOST` | `127.0.0.1` | IP address or `0.0.0.0` | Host interface for REST API, WebSockets, and Cockpit HTTP server. |
| `OPENLORE_PORT` | `8000` | Any valid TCP port | Listening port for the Web Cockpit server. |
| `OPENLORE_CAS_BACKEND` | `filesystem` | `filesystem`, `s3` | Storage backend for Content-Addressed Storage. |
| `OPENLORE_CAS_ROOT` | `./data/cas` | Filesystem path | Local root directory for two-level BLAKE3 sharded storage. |
| `OPENLORE_S3_ENDPOINT` | `http://localhost:9000` | URL string | MinIO or AWS S3 endpoint URL when `OPENLORE_CAS_BACKEND=s3`. |
| `OPENLORE_S3_BUCKET` | `openlore-cas` | String | S3 bucket name. |
| `OPENLORE_S3_ACCESS_KEY`| `minioadmin` | String | AWS / MinIO Access Key ID. |
| `OPENLORE_S3_SECRET_KEY`| `minioadmin` | String | AWS / MinIO Secret Access Key. |
| `OPENLORE_CATALOG_BACKEND`| `json` | `json`, `sql` | Central Production Catalog storage engine. |
| `OPENLORE_DATABASE_URL`| `sqlite:///./data/catalog.db` | SQLite URI or PostgreSQL URL | Database connection string when `OPENLORE_CATALOG_BACKEND=sql`. |
| `OPENLORE_LIVELINK_PORT`| `11111` | UDP port number | Default UDP port for Unreal Engine 5 Live Link frame broadcasts. |

## 2.4 Web Studio Cockpit Build

The web interface is authored in React 19, Tailwind CSS 4, Three.js, and Vite. The compiled static distribution is bundled in `web/dist/`. To recompile:
```bash
cd web
npm install
npm run build
```

---

# 3. OpenLore CLI Command Reference

All subcommands are accessible via `openlore <subcommand> [arguments]`.

## 3.1 openlore init
Initializes a new OpenLore production repository in the current directory, generating standard directory trees (`data/cas`, `data/stages`, `data/lore`, `schemas/opa`) and configuration files.

```bash
openlore init [--path <path>]
```
- `--path`: Root path to initialize (defaults to current working directory `.`).

## 3.2 openlore stage
Commands for authoring, inspecting, and committing OpenUSD composition stages.

```bash
# Create a new USD root stage
openlore stage create openlore://stages/hero_intro.usda --format usda

# Add an external sublayer into the layer stack
openlore stage sublayer openlore://stages/hero_intro.usda --sublayer ./assets/lighting_rig.usda

# Inspect stage hierarchy and referenced CAS assets
openlore stage inspect openlore://stages/hero_intro.usda

# Commit staged layer modifications to the transactional provenance log
openlore stage commit openlore://stages/hero_intro.usda -m "Lighting lookdev approved by Director" --author "elara_vance"

# Display Git-style provenance commit history
openlore stage log openlore://stages/hero_intro.usda
```

## 3.3 openlore lore
Manages W3C RDF 1.1 triplestores, named graph branching, and SHACL narrative validation.

```bash
# Query narrative entities (characters, events, locations)
openlore lore query --timeline prime-canon

# Fork a timeline into an alternate continuity branch
openlore lore branch --source prime-canon --target quantum_spin_off_02 --label "What-If Divergence"

# Validate narrative integrity against SHACL shapes
openlore lore validate --timeline prime-canon

# Query the GraphRAG narrative assistant via CLI
openlore lore assistant "Did Elara Vance participate in the Battle of Nova?"
```

## 3.4 openlore daemon
Controls background synchronization daemons and edge resolver nodes.

```bash
# Start edge resolver daemon in background
openlore daemon start --studio studio_london --kafka-broker 127.0.0.1:9092

# Check edge resolver daemon status
openlore daemon status

# Force flush local shadow buffer to central Kafka log
openlore daemon sync --force
```

## 3.5 openlore partner
Sandbox isolation commands for third-party co-development and outsourcing vendors.

```bash
# Decimate stage geometry and apply clay proxy shader
openlore partner decimate openlore://stages/hero_intro.usda --ratio 0.25 --apply-clay --output ./partner_sandbox/hero_decimated.usda

# Run pre-flight USD geometry and security linter
openlore partner lint ./partner_sandbox/hero_delivery.usda --quarantine-dir ./data/quarantine

# TD Promotion Gate: Merge approved partner delivery into internal master stage
openlore partner promote ./partner_sandbox/hero_delivery.usda --target openlore://stages/hero_intro.usda --author "pipeline_td"
```

## 3.6 openlore compile
Submits OpenUSD stages to the distributed Temporal / Argo worker grid.

```bash
# Dispatch build jobs for Unreal Engine 5 and Unity 6
openlore compile dispatch openlore://stages/hero_intro.usda --targets unreal unity cinematic-cache

# Check compilation job status
openlore compile status --job-id workflow-compilation-76b8080a
```

## 3.7 openlore catalog
Interacts with the Central Production Catalog ledger.

```bash
# List all registered downstream packages
openlore catalog list

# Inspect a specific catalog artifact
openlore catalog inspect --id cat-a8f9c1b2

# Export complete catalog ledger to JSON
openlore catalog export --output ./production_catalog_export.json
```

## 3.8 openlore export
Validates OPA licensing compliance and packages downstream production archives.

```bash
# Validate licensing and package stage for engine distribution
openlore export package openlore://stages/hero_intro.usda --target unreal --output ./releases/hero_v1.pak
```

## 3.9 openlore web
Launches the OpenLore Web Studio Cockpit and REST API server.

```bash
openlore web --port 8000 --host 127.0.0.1 --static-dir ./web/dist
```
- `--port`: HTTP port (default `8000`).
- `--host`: Bind address (default `127.0.0.1`).
- `--static-dir`: Directory containing compiled React assets (default `./web/dist`).

## 3.10 openlore livelink
Unreal Engine 5 Live Link integration and plugin generation.

```bash
# Scaffold the complete UE5 C++ plugin
openlore livelink export-plugin --output-dir ./unreal_plugin

# Stream live UDP transforms to Unreal Engine 5 on port 11111
openlore livelink stream --subject CineCameraActor --fps 60 --port 11111

# Broadcast continuous sinusoidal mock telemetry for stage testing
openlore livelink mock-broadcast --subject CineCamera_Main --port 11111 --rate 60
```

## 3.11 openlore auth
Generates and audits enterprise Role-Based Access Control tokens.

```bash
# Generate access token for a Pipeline TD
openlore auth generate-token --role pipeline_td --user "alex.turner" --studio studio_london

# Verify token permissions
openlore auth verify-token --token "<token_string>"
```

## 3.12 openlore dcc
Exports native sidecar connectors for 3D digital content creation applications.

```bash
# Export Blender 4.x Add-on
openlore dcc export-blender --output-dir ./dcc_exports/blender

# Export Autodesk Maya Python Bridge
openlore dcc export-maya --output-dir ./dcc_exports/maya

# Export all DCC sidecars simultaneously
openlore dcc all --output-dir ./dcc_exports
```

---

# 4. Web Studio Cockpit Operator Guide

The Web Studio Cockpit provides a unified single-page interface for interacting with all facets of the OpenLore platform.

## 4.1 Starting the Cockpit

Launch the server from your terminal:
```bash
openlore web --port 8000
```
Open your browser and navigate to: **`http://localhost:8000`**

The cockpit consists of a top navigation bar showing system online status, cluster environment, and 6 specialized workflow tabs.

---

## 4.2 Tab 1: Stage Viewport & Real-Time Telemetry

The Viewport tab provides real-time 3D scene preview and Live Link streaming telemetry.

```text
┌───────────────────────────────────────────────────────────────────────────┬────────────────────────────────┐
│  Three.js Viewport (Wasm USD Hydra / WebGL Preview)                      │ USD Prim Hierarchy Inspector   │
│                                                                           ├────────────────────────────────┤
│  [Grid Floor]               [Hero Character Mesh]                         │ ▾ /World                       │
│                                                                           │   ▸ /Environment               │
│                                [Virtual Camera]                           │   ▾ /Characters                │
│                                                                           │     • /HeroArmor [Mesh]        │
│  HUD: Live Link UDP (60 FPS) | X: 120.4 Y: -32.1 Z: 45.0                  │     • /Pauldrons [Mesh]        │
│  Shading: PBR Realistic     | Camera: CineCameraActor                     │   • /CineCamera [Camera]       │
└───────────────────────────────────────────────────────────────────────────┴────────────────────────────────┘
```

### Key Controls & Capabilities:
1. **Engine Toggle**:
   - **`USD-WASM Hydra Viewer`**: Client-side lexer parses raw `.usda` stage definitions, reconstructing `point3f[]` vertex buffers and PBR materials directly in WebAssembly.
   - **`WebGL Standard Viewport`**: High-frame-rate procedural preview.
2. **Camera Controls**:
   - **Orbit**: Left Click + Drag.
   - **Pan**: Right Click + Drag (or Shift + Left Click).
   - **Zoom**: Mouse Scroll Wheel.
3. **Scenegraph Inspector (Right Panel)**:
   - Click any prim (e.g. `/World/Characters/HeroArmor`) to inspect vertex count, face index offsets, display colors, and CAS content hash.
4. **Live Link Telemetry HUD (Bottom Bar)**:
   - Displays incoming UDP frame rates, Euler rotation (`pitch`, `yaw`, `roll`), and camera field of view.

---

## 4.3 Tab 2: Stage & Collaborative CRDT Synchronization

Manages real-time multi-studio concurrent authoring across distributed geographic sites without locking conflicts.

### Workflow:
1. **Multi-Studio Topology Matrix**:
   - Displays real-time connection state for **Studio London** (Virtual Production LED Volume), **Studio Los Angeles** (Animation & Unreal), and **Studio Tokyo** (Lighting & Lookdev).
2. **Recording a Collaborative Edit**:
   - Select the active studio from the dropdown.
   - Modify the transform coordinates (Translation X/Y/Z, Rotation).
   - Click **`Record Collaborative Edit`**.
   - An event is immediately dispatched across the CRDT vector clock log.
3. **Conflict Resolution**:
   - Observe how conflicting simultaneous transformations are deterministically ordered using Last-Write-Wins (LWW) and Observed-Removed Sets (OR-Set) without user-visible lock delays.

---

## 4.4 Tab 3: Narrative Lore Graph & SPARQL Canon Auditing

Houses the semantic multiverse triplestore, enforcing narrative continuity and powering the dynamic GraphRAG assistant.

### Features:
1. **Named Graph Reality Switcher**:
   - Switch between **Prime Canon** (`openlore:canon:prime`) and branched alternate realities (e.g. **Quantum Spin-Off Reality**).
2. **GraphRAG Narrative Assistant**:
   - Click one of the quick prompt chips or type a question:
     - *"Audit timeline for paradoxes"*
     - *"Show all events attended by Elara Vance"*
     - *"Trace branching divergence of Quantum Spin-Off"*
   - Click **`Ask GraphRAG Copilot`**.
   - The engine dynamically synthesizes a SPARQL query, queries the W3C RDF triplestore, evaluates character lifecycle intervals, and outputs the verified answer accompanied by explicit RDF triple citations.
3. **Contradiction Detection**:
   - If a scriptwriter attempts to place a character into a battle taking place after their canonical death, the assistant displays a red **`CONTRADICTION DETECTED`** banner citing the exact violating triples.

---

## 4.5 Tab 4: Partner Enclave Isolation & Sanitization

The vendor sandbox prevents intellectual property leaks when sharing 3D stages with third-party outsourcing vendors.

### Operational Steps:
1. **Outbound IP Decimation**:
   - Adjust the **Decimation Ratio** slider from **1%** (ultra-low proxy) up to **100%** (full master resolution).
2. **Clay Proxy Mode**:
   - Toggle **`Apply Neutral Clay Proxy Material`** to strip proprietary lookdev textures and MaterialX node graphs, replacing them with a uniform neutral albedo shader.
3. **Pre-Flight Linter & Quarantine Sandbox**:
   - When a partner uploads a scene delivery, the pre-flight linter scans for non-manifold edges, inverted normals, unlinked sublayers, and malicious embedded scripts.
   - Any failing mesh is automatically diverted to the `/data/quarantine` sandbox.
4. **TD 1-Click Promotion Gate**:
   - Pipeline TDs review the linter clean report and click **`Promote to Master Assembly`** to merge partner geometry into the prime OpenUSD stage.

---

## 4.6 Tab 5: Provenance Ledger & OPA Smart Contract Accounting

Automates royalty distribution and licensing compliance using Open Policy Agent (OPA) Rego rules.

### Capabilities:
1. **HMAC-SHA256 DAG Verification**:
   - Top banner displays the cryptographic manifest signature verifying that all scene prims originate from authorized content-addressed hashes.
2. **Automated Royalty Splits**:
   - Visual progress bars illustrate percentage allocations across contributing studios (e.g., London 18.5%, LA 12.0%, Tokyo 9.5%, Montreal Rigging 5.0%).
3. **OPA Rego Policy Compliance**:
   - Audits the scene against `schemas/opa/royalties.rego`. If any prim references an unlicensed asset, export allowance is automatically revoked.
4. **Download Provenance Manifest**:
   - Click **`Download Manifest`** in the top banner to export `hero_scene_provenance_manifest.json` containing the complete cryptographically signed prim tree.

---

## 4.7 Tab 6: Temporal Compilation Grid & Multi-Target Packaging

Orchestrates distributed container worker pools compiling raw OpenUSD stages into runtime game packages and cinematic caches.

### Operational Steps:
1. **Select Target Formats**:
   - Check the desired target formats:
     - **Unreal Engine 5.4 Package** (`.pak` with Nanite & PCD3D_SM6 shaders).
     - **Unity 6000.0 Package** (`.unitypackage` with URP/HDRP prefabs).
     - **Offline Shot Point Cache** (24 FPS time-sampled `.usdc`).
2. **Dispatch Distributed Pipeline**:
   - Click **`Dispatch Compilation Pipeline (Temporal / Argo)`**.
   - Watch the activity stepper transition through:
     `validate_stage` -> `compile_unreal_package` -> `compile_unity_package` -> `bake_shot_point_cache` -> `register_production_catalog`.
3. **Central Production Catalog Ledger**:
   - Upon completion, a new catalog entry is registered with an immutable BLAKE3 hash and unique catalog ID (e.g. `cat-XXXXXXXX`).
4. **Download Manifests**:
   - **Per-Row**: Click **`Download Manifest`** next to any build to download its engine-specific manifest (e.g. `HeroAsset_unreal.pak.manifest.json`).
   - **Full Catalog**: Click **`Download Full Catalog Manifest`** at the top right of the table to download `openlore_production_catalog.json` containing the entire catalog state.

---

# 5. 3D DCC & Game Engine Integration Manual

## 5.1 Blender 4.x Integration Guide

The OpenLore Blender Add-on connects Blender 4.0+ directly to the OpenLore platform via bidirectional WebSockets.

### Step 1: Export the Addon
Generate the add-on script using the OpenLore CLI:
```bash
openlore dcc export-blender --output-dir ./dcc_exports/blender
```
This produces `dcc_exports/blender/openlore_blender_addon.py`.

### Step 2: Install into Blender
1. Launch **Blender 4.x**.
2. Navigate to **Edit -> Preferences -> Add-ons**.
3. Click the downward arrow in the top right and select **Install from Disk...**.
4. Select `dcc_exports/blender/openlore_blender_addon.py`.
5. Enable the checkbox next to **3D View: OpenLore Production Bridge**.

### Step 3: Operating the OpenLore N-Panel
1. In the 3D Viewport, press **`N`** on your keyboard to toggle the sidebar.
2. Click the **OpenLore** tab.
3. Configure settings:
   - **Server URL**: `ws://localhost:8000/ws/telemetry`
   - **Studio Node**: `studio_london`
   - **Stage URI**: `openlore://stages/hero_scene.usda`
4. Click **`Connect to OpenLore Gateway`**. The status indicator will switch from `DISCONNECTED` to `CONNECTED (60 Hz)`.

### Step 4: Live Synchronization
- **Live Camera Sync**: Check **`Sync Active Camera`**. Moving or rotating your Blender camera broadcasts sub-frame transform updates over the WebSocket bridge.
- **Commit Scene to CAS**: Click **`Commit Active Scene`**. The addon computes BLAKE3 checksums for active mesh objects and uploads them directly to the OpenLore CAS server.

---

## 5.2 Autodesk Maya Integration Guide

The OpenLore Maya Bridge connects Autodesk Maya 2024 / 2025 to OpenLore stages.

### Step 1: Export the Maya Bridge Script
```bash
openlore dcc export-maya --output-dir ./dcc_exports/maya
```
This produces `dcc_exports/maya/openlore_maya_bridge.py`.

### Step 2: Load into Maya
1. Launch **Autodesk Maya**.
2. Open the **Script Editor** (**Windows -> General Editors -> Script Editor**).
3. Create a new **Python** tab.
4. Copy and paste the contents of `openlore_maya_bridge.py` into the editor.
5. Highlight the code and click **Execute** (or press `Ctrl + Enter`).
6. Optionally, drag the script to your **Custom Shelf** for single-click execution.

### Step 3: Maya Shelf Commands
```python
import openlore_maya_bridge as ol_bridge

# Connect to the local OpenLore REST API
bridge = ol_bridge.OpenLoreMayaBridge(host="127.0.0.1", port=8000)

# Import an OpenLore stage as an active Maya USD Proxy node
bridge.load_stage("openlore://stages/hero_scene.usda")

# Export selected DAG transforms back to OpenLore transactional stage
bridge.commit_selection(author="maya_animator", message="Adjusted shoulder pivot")
```

---

## 5.3 Unreal Engine 5 Live Link Integration Guide

The OpenLore Live Link integration streams real-time 60 FPS transform frames directly from OpenLore into Unreal Engine 5 via UDP socket datagrams.

### Step 1: Generate the UE5 C++ Plugin
Run the Live Link plugin generator:
```bash
openlore livelink export-plugin --output-dir ./unreal_plugin
```
This generates a complete Unreal Engine 5 plugin structure:
```text
unreal_plugin/
├── OpenLoreLiveLink.uplugin
├── Source/
│   └── OpenLoreLiveLink/
│       ├── OpenLoreLiveLink.Build.cs
│       ├── Public/
│       │   ├── OpenLoreLiveLink.h
│       │   └── OpenLoreLiveLinkSource.h
│       └── Private/
│           ├── OpenLoreLiveLink.cpp
│           └── OpenLoreLiveLinkSource.cpp
├── Scripts/
│   └── openlore_livelink_editor.py
└── README.md
```

### Step 2: Install into Your Unreal Engine Project
1. Close the Unreal Editor.
2. In your Unreal project root folder (e.g. `MyProject/`), create a `Plugins/` directory if one does not already exist.
3. Copy the generated `unreal_plugin` folder into `MyProject/Plugins/OpenLoreLiveLink`:
   ```bash
   cp -R ./unreal_plugin /path/to/MyProject/Plugins/OpenLoreLiveLink
   ```
4. If working with a Blueprint-only project, right-click `MyProject.uproject` and select **Generate Visual Studio / Xcode project files**, then compile the project.

### Step 3: Enable the Plugin in Unreal Editor
1. Open your project in **Unreal Editor 5.3+**.
2. Go to **Edit -> Plugins**.
3. In the search box, type `OpenLore`.
4. Check **Enabled** on the **OpenLore Live Link Bridge** plugin.
5. Restart the editor if prompted.

### Step 4: Configure Live Link Source
1. Open the Live Link panel in Unreal: **Window -> Virtual Production -> Live Link**.
2. Click the **`+ Source`** button.
3. Select **OpenLore Live Link -> OpenLore Live Link Source**.
4. In the configuration dialog, verify:
   - **UDP Port**: `11111`
   - **Local IP**: `127.0.0.1`
5. Click **Ok**. The source `OpenLoreLiveLink (127.0.0.1:11111)` will appear in the Live Link window with a green status indicator.

### Step 5: Stream Live Transforms from OpenLore
In your terminal, start the Live Link broadcaster:
```bash
openlore livelink mock-broadcast --subject CineCameraActor --port 11111 --rate 60
```
In Unreal Editor:
1. Drag a **Cine Camera Actor** into your level.
2. In the **Details** panel, click **`Add Component`** and select **`Live Link Controller`**.
3. Under the Live Link Controller settings, set **Subject Representation** to `CineCameraActor`.
4. Observe the Cine Camera in your level actively translating and rotating in real time matching the 60 FPS OpenLore stream.

---

## 5.4 SideFX Houdini 20 (Solaris / USD LOPs) Integration Guide

The OpenLore Houdini Bridge connects SideFX Houdini 20 Solaris LOP stages and standard `/obj` scene cameras to OpenLore's real-time UDP Live Link stream.

### Step 1: Export the Houdini Bridge & Solaris Shelf Tool
```bash
python3 -c "from openlore.dcc.houdini import HoudiniBridgeScaffolder; from pathlib import Path; HoudiniBridgeScaffolder.export(Path('./dcc_exports/houdini'))"
```
This produces:
- `dcc_exports/houdini/openlore_houdini_bridge.py`: Python telemetry bridge and dialog UI.
- `dcc_exports/houdini/openlore_solaris_shelf.shelf`: Native Houdini shelf definition.

### Step 2: Install into Houdini Solaris
1. Launch **SideFX Houdini 20**.
2. Open the Solaris workspace (**Desktop -> Solaris**).
3. Open the **Houdini Python Source Editor** (**Windows -> Python Source Editor**) and append:
   ```python
   import sys
   sys.path.append("/path/to/openlore/dcc_exports/houdini")
   ```
4. Alternatively, load the shelf: In the Shelf area, click the `+` icon -> **Open Shelf File...** -> select `dcc_exports/houdini/openlore_solaris_shelf.shelf`.

### Step 3: Interactive Streaming & Playbar Callback
Click the **OpenLore Live Link** button on your shelf, or run in the Houdini Python Shell:
```python
import openlore_houdini_bridge
openlore_houdini_bridge.show_ui()
```
1. Set **Host** (`127.0.0.1`), **Port** (`11111`), and **Subject Name** (`Houdini_SolarisCam`).
2. Click **Start Stream**.
3. Scrub the playbar timeline or hit Play: Houdini automatically emits camera coordinates, focal length, aperture, and FOV to OpenLore over UDP with automated coordinate conversion ($X \times 100$, $-Y \times 100$, $Z \times 100$).

### Step 4: Headless Offline Verification
For CI/CD pipelines or headless rendering farm nodes where Houdini is not installed, verify the bridge using the automated test suite:
```bash
python3 scripts/verify_houdini_bridge.py
```

---

## 5.5 Unity 6 Live Link Integration Guide

The OpenLore Unity 6 Bridge enables real-time transform streaming and camera tracking ingestion directly into Unity scenes over UDP datagrams.

### Step 1: Export the Unity Package
```bash
python3 -c "from openlore.dcc.unity import UnityBridgeScaffolder; from pathlib import Path; UnityBridgeScaffolder.export(Path('./dcc_exports/unity'))"
```
This produces:
- `dcc_exports/unity/OpenLoreLiveLinkClient.cs`: Unity C# `MonoBehaviour` client.
- `dcc_exports/unity/package.json`: Unity Package Manager (UPM) package manifest (`com.openlore.livelink`).

### Step 2: Install into Your Unity Project
1. Open your Unity 6 project.
2. In the menu, select **Window -> Package Manager**.
3. Click the **`+`** icon in the upper-left corner of Package Manager.
4. Select **Add package from disk...** and choose `dcc_exports/unity/package.json`.
5. Unity will import the OpenLore Live Link package into your project under `Packages/OpenLore Live Link Bridge`.

### Step 3: Attach Client to Camera or GameObject
1. Select your Main Camera or a CineCamera in the Hierarchy.
2. In the Inspector, click **`Add Component`** and search for **`OpenLore Live Link Client`**.
3. Configure the component:
   - **Listen Port**: `11111`
   - **Target Subject Name**: `Camera_StageA` (or subject name matching your live stream)
   - **Target Camera**: Drag the Camera component here to drive FOV and focal length.
4. Enter Play mode or view in Edit mode: the camera will follow the real-time OpenLore stream with automated coordinate conversion ($X \times 0.01$, $Y \times 0.01$, $Z \times 0.01$).

### Step 4: Headless Offline Verification
Verify Unity coordinate conversion and network ingestion without launching the Unity Editor:
```bash
python3 scripts/verify_unity_bridge.py
```

---

# 6. Enterprise Security, RBAC & OPA Rego Policies

## 6.1 Role-Based Access Control (RBAC)

OpenLore implements four strict hierarchical roles:

| Role | Permissions | Scope |
| :--- | :--- | :--- |
| **`admin`** | Full permissions, user provisioning, cluster configuration, OPA policy edits. | Studio-wide |
| **`pipeline_td`** | Stage creation, partner promotion gate approval, compile grid dispatch, CAS write. | Project-wide |
| **`artist`** | Staging transactions, local CAS read/write, WebSocket viewport streaming, CRDT edit. | Assigned stages |
| **`partner_auditor`** | Read-only access to decimated proxies and OPA royalty accounting reports. | Enclave only |

Generate tokens using the CLI:
```bash
openlore auth generate-token --role pipeline_td --user "pipeline.td" --studio studio_la
```
Pass the token in HTTP API requests:
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/stages
```

## 6.2 Cryptographic DAG Manifests & Verification

Every OpenUSD stage in OpenLore is an immutable Directed Acyclic Graph (DAG) of prims and assets. When a stage is published, OpenLore crawls the DAG, hashes every referenced mesh and texture with BLAKE3, and computes an HMAC-SHA256 signature using the studio private master key.

Verification is performed before any downstream build or game engine release. If a single byte of a geometry asset is altered, the HMAC signature verification fails immediately, aborting the build pipeline.

## 6.3 Customizing OPA Rego Policy Rules

OpenLore evaluates production stages using Open Policy Agent (OPA). The master policy file resides at `schemas/opa/royalties.rego`:

```rego
package openlore.royalties

default allow_export = false

# Allow export only if all referenced prims are approved and total royalties equal 100%
allow_export {
    not any_unlicensed_assets
    valid_royalty_allocation
}

any_unlicensed_assets {
    asset := input.assets[_]
    asset.status != "Approved"
}

valid_royalty_allocation {
    total := sum([split | split := input.royalty_splits[_]])
    total <= 100.0
}
```

To validate policies locally before deploying:
```bash
openlore export verify-license openlore://stages/hero_scene.usda --policy ./schemas/opa/royalties.rego
```

## 6.4 Network Isolation & Egress Filtering

When partner enclaves are spun up for external vendors, OpenLore enforces eBPF kernel-level socket filtering rules (`openlore.partner.ebpf_rules`). All network connections originating from the partner container are dropped unless explicitly matching the OpenLore secure proxy gateway address:
- Outbound port 80/443 (General Internet): **BLOCKED**
- SSH / FTP / SCP: **BLOCKED**
- Inbound to OpenLore Gateway Port 8000: **ALLOWED (Authenticated & Sanitized)**

---

# 7. Deployment, Staging & Production Runbook

## 7.1 Local Development Profile (:8000)

The standard lightweight single-process development server uses filesystem storage and standard library SQLite:

```bash
export OPENLORE_ENV=development
export OPENLORE_PORT=8000
openlore web
```
- Web Cockpit: `http://localhost:8000`
- REST API: `http://localhost:8000/api/status`
- WebSocket Telemetry: `ws://localhost:8000/ws/telemetry`

## 7.2 Multi-Container Docker Staging Profile (:8080)

The staging environment deploys production-equivalent microservices in isolated Docker containers:

```bash
docker compose -f docker-compose.staging.yml up -d
```

### Services Deployed in Staging:
- **`openlore-api-staging`** (Port 8080): OpenLore core server running with `OPENLORE_ENV=staging`.
- **`postgres-staging`** (Port 5432): PostgreSQL 16 database storing production catalog records.
- **`minio-cas-staging`** (Port 9000 & 9001): High-performance S3 Content-Addressed Storage.
- **`redpanda-staging`** (Port 9092): Apache Kafka-compatible real-time event streaming broker.
- **`fuseki-staging`** (Port 3030): Apache Jena Fuseki SPARQL 1.1 W3C RDF triplestore.
- **`opa-staging`** (Port 8181): Dedicated Open Policy Agent daemon.

Verify staging cluster health:
```bash
./scripts/deploy_staging.sh
```

## 7.3 Production Kubernetes Deployment via Helm

For multi-studio enterprise deployment across cloud or hybrid bare-metal clusters, use the official Helm chart:

```bash
helm upgrade --install openlore ./helm/openlore   --namespace openlore-prod   --create-namespace   --values ./helm/openlore/values-prod.yaml
```

Production features configured via Helm:
- Multi-replica API deployments with Horizontal Pod Autoscaling (HPA).
- Distributed MinIO with erasure coding across multi-region NVMe pools.
- PostgreSQL 16 cluster with streaming replication and automated failover.
- Zero-trust mTLS mutual authentication between edge studio resolvers and central Kubernetes ingress.

---

# 8. Troubleshooting & Diagnostics

## 8.1 CLI Command Not Found
**Symptom**: Running `openlore` outputs `zsh: command not found: openlore`.  
**Cause**: The executable path is not in your current terminal session $PATH variable, or zsh has not refreshed its command cache.  
**Resolution**:
1. Run with local executable from repo root:
   ```bash
   ./openlore <command>
   ```
2. Or refresh your shell configuration:
   ```bash
   source ~/.zshrc
   rehash
   ```

## 8.2 Port Conflicts (8000 / 8080)
**Symptom**: `OSError: [Errno 48] Address already in use`.  
**Cause**: A previous OpenLore server daemon or background process is already bound to port 8000.  
**Resolution**:
Find and terminate the process holding the port:
```bash
lsof -i :8000 -t | xargs kill -9
openlore web --port 8000
```

## 8.3 Live Link UDP Stream Not Showing in UE5
**Symptom**: Unreal Engine Live Link source is added, but no subjects or frame numbers appear.  
**Cause**: Firewall blocking UDP packets or port mismatch.  
**Resolution**:
1. Ensure the broadcaster is running on UDP port 11111:
   ```bash
   openlore livelink stream --port 11111
   ```
2. On macOS, ensure terminal has permission to broadcast local network packets (System Settings -> Privacy & Security -> Local Network).
3. In Unreal Editor Live Link window, ensure the Source settings specify IP `127.0.0.1` and Port `11111`.

## 8.4 OPA Licensing Gate Export Violations
**Symptom**: `Export allowance revoked: Unlicensed assets found in stage DAG`.  
**Cause**: One or more prims in the USD layer stack references an asset without approved provenance licensing in the manifest ledger.  
**Resolution**:
1. Run `openlore export verify-license openlore://stages/<stage_name>.usda`.
2. Inspect the returned unlicensed prim paths.
3. Update the asset license status in the provenance ledger or replace the asset with an approved CAS hash.

## 8.5 Triplestore SHACL Validation Errors
**Symptom**: `SHACL Validation Error: Post-mortem event participation detected`.  
**Cause**: A character is attached to a timeline event occurring at timestamp after their death.  
**Resolution**:
1. Query the character canonical lifespan:
   ```bash
   openlore lore query --character ElaraVance
   ```
2. Adjust the event timestamp in the narrative editor to precede the character demise, or fork into an alternate continuity timeline:
   ```bash
   openlore lore branch --source prime-canon --target alternate_universe_01
   ```

---

_OpenLore Production Manual (c) 2026 EpicBrain Systems Inc. Released under the Apache 2.0 License._
