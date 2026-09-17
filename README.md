<p align="center">
  <img src="assets/hero-banner.jpg" alt="OpenLore — Version Control & Lore Engine for 3D Worlds" width="100%" />
</p>

# OpenLore

<p align="center">
  <strong>Git for 3D worlds, game lore, and Hollywood pipelines.</strong>
</p>

<p align="center">
  <a href="#license"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0" /></a>
  <a href="#python"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+" /></a>
  <a href="#openusd"><img src="https://img.shields.io/badge/OpenUSD-Pixar%20%2F%20AOUSD-orange.svg" alt="OpenUSD" /></a>
  <a href="#w3c-rdf"><img src="https://img.shields.io/badge/W3C-RDF%201.1%20%7C%20SHACL-005A9C.svg?logo=w3c&logoColor=white" alt="W3C RDF / SHACL" /></a>
  <a href="#kafka"><img src="https://img.shields.io/badge/Streaming-Kafka%20%7C%20CRDT-231F20.svg?logo=apachekafka&logoColor=white" alt="Kafka CRDT" /></a>
  <a href="#opa"><img src="https://img.shields.io/badge/Policy-OPA%20Rego-green.svg" alt="OPA Rego" /></a>
  <a href="#temporal"><img src="https://img.shields.io/badge/Grid-Temporal%20%7C%20Argo-red.svg" alt="Temporal / Argo" /></a>
  <a href="#tests"><img src="https://img.shields.io/badge/Tests-127%20Passing-brightgreen.svg" alt="127 Tests Passing" /></a>
</p>

<p align="center">
  <a href="docs/MANUAL.md"><strong>📖 Comprehensive Instruction Manual</strong></a> &bull;
  <a href="docs/API_REFERENCE.md"><strong>📚 API Reference</strong></a> &bull;
  <a href="docs/DEPLOYMENT_RUNBOOK.md"><strong>🚀 Deployment Runbook</strong></a>
</p>

---

## Overview

Modern entertainment franchises span feature films, AAA games, television series, virtual production stages, and consumer merchandise. Yet digital asset management remains fractured:

* **VFX & Film Pipelines** rely on non-linear [OpenUSD (Universal Scene Description)](https://openusd.org/) layer stacks, MaterialX lookdev, and multi-gigabyte shot caches.
* **Game Engines (Unreal / Unity)** require flattened skeletal hierarchies, collision physics, engine packages (`.pak` / `.unitypackage`), and sub-millisecond runtime performance.
* **Narrative Lore & Continuity** is traditionally siloed in wikis and spreadsheets with zero automated verification of character lifecycles, timeline branches, or canonical constraints.
* **Distributed Multi-Studio Teams** struggle with file-locking bottlenecks, lack Git-style branching, and risk conflicting overrides across remote sites.

**OpenLore** bridges this cross-media disconnect. It is an enterprise production platform combining **OpenUSD composition stages** and **cryptographic BLAKE3 Content-Addressed Storage (CAS)** with **semantic W3C RDF 1.1 lore graphs**, **Kafka CRDT real-time vector clock synchronization**, **eBPF partner enclave sandboxing**, **OPA Rego royalty accounting**, and **Temporal/Argo compilation grids**.

---

## System Architecture

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

---

## Core Features

### 1. OpenUSD Storage & BLAKE3 Content-Addressed Storage (CAS)
* **Separation of Concerns**: Lightweight transactional edits (metadata, transform deltas, variant switches) are isolated from massive binary payloads (geometry meshes, 8K UDIM textures, Alembic caches).
* **Cryptographic Sharding**: Pure Python, zero-dependency CAS indexed by 256-bit BLAKE3 hashes with 2-level directory sharding (`objects/aa/bb/aabb...`).
* **Cloud S3 Adapter**: Native zero-dependency AWS SigV4 request signing supporting AWS S3, Cloudflare R2, MinIO, and Ceph.
* **Atomic Layer Composition**: Non-destructive layer stacks, sublayer referencing, and commit chains with full git-style SHA-1 provenance log.

### 2. Narrative Multiverse & SPARQL Graph RAG
* **W3C Semantic Lore Graphs**: Narrative lore, character lifecycles, and asset bindings modeled as RDF 1.1 triples inside Named Graphs (`openlore:canon:prime`).
* **SHACL Continuity Engine**: Asynchronous validation enforcing temporal invariants (e.g., characters cannot participate in battles before birth or after death).
* **Multiverse Branching**: Fork prime canon into isolated timeline namespaces (`openlore:branch:dark_timeline`) for alternate adaptations without polluting prime continuity.
* **Studio Copilot Graph RAG**: Natural language query assistant powered by dynamic SPARQL synthesis, extracting relevant triples, verifying temporal bounds, and formatting verified context for writers.

### 3. Distributed Collaboration & CRDT Vector Clocks
* **Sparse CRDT Registers**: Last-Write-Wins (LWW) registers resolving concurrent multi-studio edits deterministically using:
  1. Causal dominance via monotonic **Vector Clocks**
  2. Nanosecond wall-clock timestamps
  3. Deterministic studio ID tie-breaking
* **High-Throughput Streaming**: Real-time mutation broadcast over Apache Kafka / Redpanda. High-frequency transformations travel as compact JSON payloads (<64 KB).
* **Offline Resilience**: When connectivity drops, the local **Edge Resolver Daemon** buffers edits in shadow storage. Upon reconnect, buffered edits flush atomically and converge without data loss.

### 4. Unreal Engine 5 Live Link Bridge & DCC Connectors
* **Duplex Live Link Telemetry**: Real-time UDP broadcasting (port `11111` at 60 FPS) translating OpenUSD right-handed coordinates into Unreal Engine left-handed centimeters (Z-up).
* **C++ Plugin Scaffolding**: Turnkey Unreal Engine 5 plugin generator (`.uplugin`, `Build.cs`, `ILiveLinkSource`, Python bridge).
* **DCC Connectors**: Zero-dependency turnkey modal add-ons for **Blender 4.x** and **Autodesk Maya 2024/2025** streaming active viewport camera transforms into OpenLore stages.

### 5. Partner Enclave Security & Ingestion
* **Outbound IP Sanitization**: Dynamic mesh decimation slider (**1% to 100%**) with presets (`10%`, `25%`, `50%`, `75%`, `100%`), stripping proprietary attributes (`assetHash`, `pointCacheHash`, `royaltyPercentage`) and replacing lookdev with neutral clay shaders.
* **Inbound Quarantined Linter**: Pre-flight USD sandbox auditing external deliverables against polycount ceilings, scene hierarchy rules (`/World`, `/Root`), and naming conventions.
* **TD 1-Click Promotion Gate**: Technical Directors acquire an optimistic concurrency lock token, verify SHACL lore compliance, and atomically append approved deliverables into the production USD stage stack.
* **eBPF Zero-Egress Kernel Security**: Generates Linux TC eBPF programs blocking unauthorized contractor outbound network packets at the socket level.

### 6. Automated Asset Provenance & OPA Royalties
* **Stage DAG Harvester**: Introspects the entire directed acyclic graph of active USD stages, extracting all referenced sublayers, asset hashes, prim paths, and contributing studio IDs.
* **HMAC-SHA256 Signatures**: Tamper-proof manifest signing ensuring supply chain integrity.
* **OPA Rego Royalty Compliance**: Evaluates manifests against Open Policy Agent Rego rules, calculating automated percentage splits (e.g., London VFX, LA Game, Tokyo Lookdev, Montreal Rigging) and gating downstream commercial release.

### 7. Compilation Grid & Production Catalog
* **Temporal Orchestration & Argo DAGs**: Automated downstream compilation into targeted game engine packages (`.pak` for Unreal Engine 5, `.unitypackage` for Unity 6) and cinematic USD point caches.
* **Relational Production Catalog**: Industrial ledger backed by SQLite (local development) or PostgreSQL 16 (staging/production) with indexed lookups on stage URI, build type, and BLAKE3 CAS hash.

### 8. OpenLore Studio Cockpit (Web UI)
* Full-featured React 19 single-page application served directly by OpenLore embedded web server:
  - **3D Stage Viewport**: In-browser Three.js viewport powered by a client-side OpenUSD WebAssembly parser and Prim Scenegraph Inspector.
  - **Narrative Multiverse**: Timeline manager, SHACL integrity monitor, and interactive SPARQL Graph RAG narrative assistant.
  - **Studio Collaboration**: Multi-studio vector clock monitors, CRDT broadcaster, network severance simulator, and UE5 Live Link status.
  - **Partner Enclave**: 1%–100% IP decimation controls, presets, quarantine linter, and 1-Click TD promotion gate.
  - **Provenance & OPA**: Cryptographic signature verifier, partner royalty progress bars, and harvested USD DAG tree.
  - **Compilation Grid**: Multi-target engine selection, live Temporal activity tracker, and Central Production Catalog.

---

## Quickstart Guide

### Prerequisites
* **Python**: `3.11` or higher.
* **Modern Web Browser**: Chrome, Firefox, Safari, or Edge.
* *Note: Pre-built web assets are included in `web/dist`—no Node.js installation is required to run the cockpit.*

### Step 1: Clone & Install

```bash
git clone git@github.com:epicbrain-dev/openlore.git
cd openlore
pip install -e .
```

To install optional developer tools (pytest, ruff, mypy):
```bash
pip install -e ".[dev]"
```

### Pre-Packaged Releases & DCC Sidecars

Pre-compiled packages and standalone DCC bridge archives are available on each [GitHub Release](https://github.com/epicbrain-dev/openlore/releases/latest):

| Distribution Package | Target Environment | Description |
|---|---|---|
| `openlore-1.0.1-py3-none-any.whl` | Python 3.9+ | Universal wheel containing CLI, server, and core SDK |
| `openlore-blender-addon-v1.0.1.zip` | Blender 4.x | Standard Blender zip add-on for Live Link & CAS sync |
| `openlore-maya-bridge-v1.0.1.zip` | Autodesk Maya 2024+ | Maya scriptJob telemetry connector |
| `openlore-houdini-solaris-v1.0.1.zip` | SideFX Houdini 20 | Solaris USD LOPs shelf tool and telemetry bridge |
| `openlore-unreal-livelink-v1.0.1.zip` | Unreal Engine 5.3 / 5.4 | Turnkey C++ Live Link plugin (`Plugins/OpenLoreLiveLink`) |
| `openlore-unity-livelink-v1.0.1.zip` | Unity 6 / 2023 LTS | Unity Package Manager (UPM) client |
| `openlore-cpp-sdk-v1.0.1.zip` | C++17 Engines / DCCs | Zero-dependency header-only C++ SDK (`openlore.hpp`) |


### Step 2: Launch the Studio Cockpit

Start the embedded REST API server and web application:
```bash
openlore web --port 8000
```

Open your browser and navigate to:
```
http://localhost:8000
```

### Step 3: Verify System Health

Verify the service mesh and connected studio nodes directly from your terminal:
```bash
curl -s http://localhost:8000/api/status | python3 -m json.tool
```

```json
{
    "status": "ONLINE",
    "version": "1.0.1",
    "environment": "development",
    "cas_backend": "filesystem",
    "catalog_backend": "json",
    "system": "OpenLore Transmedia Production Backbone",
    "services": {
        "openusd": "Active",
        "rdf_triplestore": "Active",
        "crdt_resolver": "Active",
        "opa_accounting": "Active",
        "temporal_grid": "Active",
        "graph_rag": "Active"
    }
}
```

---

## CLI Command Reference

| Command | Action / Arguments | Description |
| :--- | :--- | :--- |
| `openlore init` | `--cas-path <DIR> --canon <NAME>` | Initialize CAS repository structure and prime canon lore graph. |
| `openlore stage` | `create`, `list`, `inspect` | Create OpenUSD stages, inspect prims, and manage sublayer stacks. |
| `openlore lore` | `verify`, `branch`, `list`, `export` | Validate SHACL narrative shapes, branch alternate timelines, export TriG. |
| `openlore daemon` | `start`, `status`, `stop` | Manage Edge Resolver daemon, vector clocks, and offline shadow buffers. |
| `openlore partner` | `sanitize`, `lint`, `promote` | Execute 1%-100% IP decimation, quarantine linting, and TD promotion. |
| `openlore compile` | `--stage <URI> --target <ENGINES>` | Dispatch Temporal compilation workflows (Unreal, Unity, Shot caches). |
| `openlore catalog` | `list` | Inspect registered builds and BLAKE3 CAS hashes in production catalog. |
| `openlore export` | `--stage <URI> --target <ENGINE>` | Introspect USD DAG, evaluate OPA royalties, and compile packages. |
| `openlore web` | `--host <IP> --port <PORT>` | Launch embedded REST server, WebSocket gateway, and Web Cockpit. |
| `openlore livelink`| `stream`, `export-plugin` | Run real-time UE5 Live Link bridge or export turnkey C++ plugin project. |
| `openlore auth` | `create-token` | Generate HMAC-SHA256 bearer tokens with RBAC permission scopes. |
| `openlore dcc` | `blender`, `maya`, `all` | Export turnkey telemetry bridge add-ons for Blender and Maya. |
| `openlore farm` | `submit` | Dispatch GPU render farm jobs to AWS Deadline 10 or ASWF OpenCue. |

---

## Python SDK Examples

### Composing OpenUSD Stages & Binding CAS Assets

```python
from pathlib import Path
from openlore.core.cas import ContentAddressedStorage
from openlore.core.stage import StageCompositionManager
from openlore.core.transaction import TransactionManager

# 1. Store immutable geometry mesh into CAS
cas = ContentAddressedStorage(Path("./data/cas"))
hero_mesh_cas = cas.store_bytes(b"SOLID_GEOMETRY_BUFFER_BYTES", mime_type="model/vnd.usda")
print(f"Stored Mesh CAS Hash: {hero_mesh_cas.blake3_hash}")

# 2. Compose OpenUSD stage
stage_mgr = StageCompositionManager(Path("./data/stages"))
stage_ref = stage_mgr.create_stage("openlore://stages/hero_scene.usda")

# 3. Transactional authoring & asset binding
tx_mgr = TransactionManager(Path("./data"), stage_mgr)
session = tx_mgr.begin_transaction(stage_ref, author="alice_lead_td")
session.set_property("/World/Hero", "xformOp:translate", [0.0, 10.0, 0.0])
session.attach_cas_payload("/World/Hero", "openlore:assetHash", hero_mesh_cas)
commit_record = session.commit("Add Hero character with CAS bound mesh")
print(f"Committed Transaction: {commit_record.commit_id}")
```

### Querying Lore via SPARQL Graph RAG Assistant

```python
from openlore.narrative.rag import NarrativeGraphRAG

# Initialize Graph RAG assistant
assistant = NarrativeGraphRAG(graph_path="data/lore/graph.trig")

# Query lore continuity
response = assistant.answer_query(
    "What events did Commander Vance participate in, and what are the timeline constraints?"
)

print("Synthesized SPARQL Query:
", response["sparql_query"])
print("Retrieved Triples:
", response["triples"])
print("Continuity Analysis:
", response["answer"])
```

### Real-Time CRDT Collaborative Edits

```python
from openlore.collaboration.daemon import EdgeResolverDaemon
from openlore.collaboration.stream import KafkaEventStream

stream = KafkaEventStream("openlore.stage.hero", use_memory_bus=True)
daemon = EdgeResolverDaemon("studio_london", "openlore://stages/hero_scene.usda", stream)

# Record local edit (broadcasting over Kafka with Vector Clock)
daemon.record_local_edit("/World/Hero", "xformOp:translate", [15.0, 10.0, 5.0])
print(f"Current Vector Clock: {daemon.vector_clock.clocks}")

# Simulate network severance -> automatic shadow buffering
daemon.sever_network()
daemon.record_local_edit("/World/Hero", "xformOp:translate", [16.0, 10.0, 5.0])
print(f"Buffered Edits in Shadow Storage: {daemon.shadow_buffer_size}")

# Restore network -> atomic flush and causal state convergence
daemon.restore_network()
print(f"Buffer flushed! Online status: {daemon.is_online}")
```

---

## Staging & Container Deployment

### Multi-Container Staging Stack (`docker compose`)

The staging profile orchestrates:
- **OpenLore Server & Cockpit** (Port `8080`)
- **PostgreSQL 16** (Central Production Catalog)
- **MinIO S3** (Scalable Object Storage for CAS)
- **Redpanda** (High-throughput Kafka-compatible event streaming)
- **Open Policy Agent (OPA)** (Royalty policy evaluation)
- **Apache Jena Fuseki** (RDF SPARQL 1.1 Triplestore)

To spin up the entire staging stack:
```bash
docker compose -f docker-compose.staging.yml up -d
```

### Automated Staging Deployment Script
```bash
./scripts/deploy_staging.sh
```

### Kubernetes Helm Deployment
```bash
helm upgrade --install openlore ./helm/openlore   --namespace openlore-staging --create-namespace   -f ./helm/openlore/values-staging.yaml
```

---

## Repository Structure

```text
openlore/
├── assets/                       # Hero header banner and visual assets
│   ├── hero-banner.jpg
│   └── thumbnails/
├── data/                         # Canonical lore graph & seed data
│   └── lore/
│       └── graph.trig
├── docker/                       # Container definitions for runtime components
│   ├── Dockerfile.server
│   └── Dockerfile.worker
├── docs/                         # Detailed architecture documentation
│   ├── MANUAL.md                 # Exhaustive instruction and operator manual
│   ├── API_REFERENCE.md          # Complete Python and REST API reference
│   └── DEPLOYMENT_RUNBOOK.md     # Production deployment and operational runbook
├── helm/                         # Kubernetes Helm charts
│   └── openlore/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── values-staging.yaml
├── schemas/                      # Formal W3C OWL 2, SHACL, and OPA Rego schemas
│   ├── opa/
│   │   └── royalties.rego
│   └── shacl/
│       └── continuity_rules.ttl
├── scripts/                      # Deployment and pipeline orchestration scripts
│   ├── deploy_staging.sh
│   └── seed_graph.py
├── src/
│   └── openlore/                 # Core Python runtime package
│       ├── bridge/               # Unreal Live Link bridge & DCC connectors
│       ├── cli/                  # Production command-line interface
│       ├── collaboration/        # CRDTs, Vector Clocks, Kafka & Edge Daemons
│       ├── compilation/          # Temporal workflows, Argo DAGs & Catalog Backends
│       ├── core/                 # BLAKE3 CAS (Local & S3), USD Stages, Transactions
│       ├── dcc/                  # Blender 4.x and Autodesk Maya sidecars
│       ├── materials/            # MaterialX translators & UsdSkel dual-rigs
│       ├── narrative/            # RDF triplestore, OWL 2, SHACL & Graph RAG
│       ├── partner/              # IP decimation (1%-100%), quarantine linter, TD gates
│       ├── provenance/           # OpenUSD DAG harvester, HMAC manifests, OPA
│       ├── server/               # HTTP REST API, WebSocket gateway & SPA host
│       └── config.py             # Environment configuration (Dev, Staging, Prod)
├── tests/                        # Comprehensive test suite (101/101 passing)
│   ├── integration/
│   └── unit/
├── web/                          # OpenLore Studio Cockpit (React 19 + Three.js)
│   ├── dist/                     # Pre-compiled static production bundle
│   └── src/
│       ├── components/
│       ├── utils/                # Client-side OpenUSD WebAssembly parser
│       └── views/                # Six production cockpit views
├── docker-compose.yml            # Local development orchestration
├── docker-compose.staging.yml    # Full enterprise staging environment profile
├── pyproject.toml                # Standard PEP 517/518 build configuration
└── Documentation.md              # Complete technical whitepaper
```

---

## Test Suite & Verification

OpenLore includes a rigorous unit and integration test suite covering all domains:

```bash
PYTHONPATH=src python3 -m unittest discover tests/
```

```text
Ran 101 tests in 3.06s
OK

[OpenLore Integration] All 10 architectural pillars successfully executed and verified end-to-end!
```

---

## License

This project is licensed under the **Apache License 2.0**. See [Documentation.md](Documentation.md#licensing--legal-terms) for complete legal terms.

```text
Copyright 2026 EpicBrain-Dev

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```
