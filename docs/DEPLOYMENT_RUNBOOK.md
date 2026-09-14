# OpenLore Production Deployment Runbook

This runbook guides pipeline engineers, DevOps/SRE teams, and studio systems administrators through the deployment, operational management, and disaster recovery of the **OpenLore** production cluster.

---

## 1. System Architecture & Component Grid

```mermaid
graph TD
    Client["DCC / Viewport (Unreal / Maya / Houdini)"] -->|OpenUSD Stages| CAS["CAS Storage (BLAKE3)"]
    Client -->|Sparse CRDT Edits (<64KB)| Kafka["Kafka / Redpanda Cluster"]
    Client -->|SPARQL / SHACL Queries| Fuseki["Apache Jena Fuseki (Lore Graph)"]
    
    Kafka --> Edge["Edge Resolver Daemons (Studio Nodes)"]
    Edge -->|Local Shadow Buffer| Client
    
    TD["Technical Director"] -->|One-Click Promotion| Gate["Stage Promotion Gate"]
    Gate -->|Quarantine Sandbox| Linter["Pre-Flight USD Validator"]
    
    Promote["Approved Production Stage"] --> Harvester["DAG Harvester & HMAC Signer"]
    Harvester --> OPA["Open Policy Agent (OPA)"]
    OPA -->|Export Authorized| Temporal["Temporal Workflow Orchestration"]
    
    Temporal --> Worker1["Unreal Engine Compiler (.pak)"]
    Temporal --> Worker2["Unity Bundle Compiler (.unitypackage)"]
    Temporal --> Worker3["Offline Shot Baker (.usdc)"]
    
    Worker1 --> Catalog["Central Production Catalog"]
    Worker2 --> Catalog
    Worker3 --> Catalog
```

---

## 2. Infrastructure Prerequisites

| Component | Minimum Version | Recommended Spec (Production) | Port Bindings |
|---|---|---|---|
| **Python** | `3.12+` | Python 3.12 / 3.13 | N/A |
| **OpenUSD (`pxr`)** | `24.05+` | Native C++ build / `usd-core` | N/A |
| **Apache Kafka / Redpanda** | `v23.3+` | 3-node HA Redpanda Cluster | `9092`, `9644` |
| **Open Policy Agent (OPA)** | `v0.65+` | Distributed sidecar / daemonset | `8181` |
| **Apache Jena Fuseki** | `v5.0+` | Persistent TDB2 storage | `3030` |
| **Temporal Server** | `v1.24+` | Clustered Postgres/Cassandra backend | `7233`, `8080` (UI) |
| **Argo Workflows** | `v3.5+` | Kubernetes 1.28+ cluster | `2746` |
| **Linux Kernel** | `5.15+` | Kernel with eBPF TC classifier support | N/A |

---

## 3. Local & Staging Deployment (Docker Compose)

The repository provides a turnkey [docker-compose.yml](file:///Volumes/External/Labs/openlore/docker-compose.yml) starting the core backend services:

```bash
# 1. Start all infrastructure services in the background
docker-compose up -d

# 2. Check service health
docker-compose ps

# Expected output:
# NAME                   STATUS              PORTS
# openlore-kafka         Up (healthy)        0.0.0.0:9092->9092/tcp, 0.0.0.0:9644->9644/tcp
# openlore-opa           Up                  0.0.0.0:8181->8181/tcp
# openlore-triplestore   Up                  0.0.0.0:3030->3030/tcp
# openlore-temporal      Up                  0.0.0.0:7233->7233/tcp
# openlore-temporal-ui   Up                  0.0.0.0:8080->8080/tcp
```

### Initializing the OpenLore Repository
```bash
# Set repository environment
export PYTHONPATH=src

# Initialize Content-Addressed Storage and Prime Canon
openlore init --cas-path ./data/cas --canon prime-canon

# Initialize background Edge Resolver Daemon for local studio
openlore daemon start --studio-id studio_london --stage-uri openlore://stages/root.usda
```

---

## 4. Production Kubernetes Deployment (Argo Workflows)

For downstream compilation across scalable GPU/CPU worker pools, deploy the Argo Workflows cluster.

### 1. Install Argo Controller & Server
```bash
kubectl create namespace argo
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.5/install.yaml

# Configure ServiceAccount permissions for OpenLore grid
kubectl create namespace openlore-grid
kubectl create rolebinding openlore-admin --clusterrole=admin --serviceaccount=openlore-grid:default -n openlore-grid
```

### 2. Generate and Submit Compilation DAGs
Use the OpenLore dispatcher to generate the cluster workflow manifest:

```python
from openlore.compilation.grid import WorkerGridDispatcher

dispatcher = WorkerGridDispatcher(argo_namespace="openlore-grid")
yaml_manifest = dispatcher.generate_argo_workflow_yaml(
    stage_uri="openlore://stages/feature_film_seq01.usda",
    target_engines=["unreal", "unity", "cinematic-cache"],
    output_bucket="s3://openlore-builds/releases/seq01",
)

with open("compilation_workflow.yaml", "w") as f:
    f.write(yaml_manifest)
```

Apply to the cluster:
```bash
kubectl apply -n openlore-grid -f compilation_workflow.yaml
argo watch @latest -n openlore-grid
```

---

## 5. eBPF Zero-Egress Network Policy Deployment

To enforce zero egress on contractor cloud workstations and isolate partner enclaves:

### 1. Generate Kernel Filter
```python
from openlore.partner.ebpf_rules import EBPFNetworkPolicyManager

mgr = EBPFNetworkPolicyManager(allowed_inspection_endpoints=["10.0.0.50:443"])
c_source = mgr.generate_tc_filter_rules()
with open("tc_egress_filter.c", "w") as f:
    f.write(c_source)
```

### 2. Compile eBPF Object File
```bash
clang -O2 -target bpf -c tc_egress_filter.c -o tc_egress_filter.o
```

### 3. Attach Traffic Control Classifier
```bash
# Attach eBPF classifier to the contractor egress interface (eth0)
sudo ip link set dev eth0 up
sudo tc qdisc replace dev eth0 clsact
sudo tc filter replace dev eth0 egress bpf da obj tc_egress_filter.o sec tc_egress

# Verify loaded program
sudo bpftool prog show name openlore_tc_egress_filter
```

---

## 6. Disaster Recovery & Disconnection Runbook

When a remote studio experiences a WAN outage or high packet loss:

### Phase 1: Outage Detection
The `EdgeResolverDaemon` automatically detects disconnection and switches into offline shadow buffering mode:
```bash
openlore daemon status
# Output:
# Connectivity: OFFLINE (Shadow Buffering)
# Buffered Edits: 14
```
- Local artists continue modifying scene properties, camera framing, and variant selections with zero UI latency.
- High-frequency mutations accumulate in deterministic causal order within the local memory replica and shadow storage.

### Phase 2: Reconnection & Causal Convergence
Once network connectivity is restored:
```bash
# Edge daemon reconnects and flushes shadow buffer automatically
openlore daemon start --studio-id studio_london --stage-uri openlore://stages/root.usda
```
- Reconnection triggers an atomic flush of all buffered mutations over the Kafka event stream.
- All remote peer nodes receive the stream and resolve any concurrent property edits via `LWWRegister` (causal vector dominance $\rightarrow$ timestamp $\rightarrow$ studio ID).
- Replicas converge to identical states with zero data loss and zero manual merge conflict resolution.

---

## 7. Monitoring & Operational Health Checks

### Health Verification Endpoints

| Service | Check Command / Endpoint | Expected Response |
|---|---|---|
| **OPA Policies** | `curl -s http://localhost:8181/v1/data/openlore/royalties` | `{"result": {"allow_export": true, ...}}` |
| **RDF Triplestore**| `curl -s http://localhost:3030/$/ping` | HTTP 200 OK |
| **Redpanda Kafka** | `rpk cluster health` | `Healthy: true` |
| **Temporal Server**| `temporal workflow list --address localhost:7233` | Workflow inventory list |

---

## 8. Verification & Acceptance Testing

Before certifying a new deployment or environment, execute the end-to-end integration test suite:

```bash
# Run full automated test suite (54 unit + integration tests)
PYTHONPATH=src python3 -m unittest discover -s tests

# Expected Result:
# Ran 54 tests in ~0.25s
# OK
# [OpenLore Integration] All 9 architectural pillars successfully executed and verified end-to-end!
```
