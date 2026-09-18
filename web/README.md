# OpenLore Studio — Desktop & Web Cockpit

OpenLore Studio is the visual frontend and cross-platform desktop application for OpenLore, connecting interactive 3D content creation, visual effects pipelines, and narrative multiverse knowledge graphs.

Built with **React 19**, **Three.js**, **TailwindCSS**, and **Electron 44**, it provides an industrial 9-workspace environment designed for visual effects producers, technical directors, and 3D character animators.

---

## 🚀 Quick Start

### 1. Development Mode (Browser)
```bash
# From web/ directory:
npm install
npm run dev
# Starts Vite dev server at http://localhost:5173
```

### 2. Desktop Development Mode (Electron + Hot Reload)
```bash
# Launches Vite dev server and Electron desktop runtime with auto-reconnect
npm run electron:dev
```

### 3. Package Standalone Production Desktop App
```bash
# Compiles Vite production bundle and packages native OS application
npm run electron:pack

# macOS output:
# dist-electron/mac-arm64/OpenLore Studio.app
```

### 4. Build Distribution Installers (.dmg, .exe, .AppImage)
```bash
npm run electron:dist
```

---

## 🎨 9 Production Workspaces

OpenLore Studio is organized into 9 dedicated visual effects production workspaces:

| Workspace | Badge | Description |
|---|---|---|
| **3D Layout & Staging** | `USD 24.11` | OpenUSD stage outliner hierarchy, raycast mesh picking, BoxHelper bounding boxes, live shading modes (Shaded, Wireframe, Lookdev Clay), and Maya/Houdini-style Channel Box Transform Matrix inputs (`Translate`, `Rotate`, `Scale`). |
| **Animation & Scenegraph** | `24 FPS` | 3D character skeleton hierarchy, bone lines, joint spheres, interactive cubic Bézier curve Graph Editor, Dope Sheet, Pose Library with 1-click rig application, FK/IK blend sliders, dynamic Squash & Stretch, and Onion Skinning (cyan/magenta ghosting). |
| **Shot Review (Producer)** | `ShotGrid` | Sequence `SQ042` shot management with live status tracking (`In Progress`, `In Review`, `Approved`, `Blocked`), thumbnails, frame ranges, lead artists, and 1-click stage loading. |
| **Lookdev & Shading Studio** | `MaterialX` | 360° turntable stage with ACEScg lighting presets (**Studio Neutral 5600K**, **Golden Sunset 3200K**, **Cyberpunk LED Volume**, **High-Key Rim**) and real-time MaterialX/PBR parameters. |
| **Multi-Studio Sync** | `CRDT` | Real-time CRDT vector clock monitors, live mutation broadcaster, network severance simulator, and UE5 Live Link status. |
| **Render Farm & Grid** | `Deadline` | AWS Deadline 10 and ASWF OpenCue GPU farm dispatch, multi-target compilation (.pak, .unitypackage, .usdc), and central production catalog ledger. |
| **Narrative Multiverse** | `SHACL` | W3C RDF 1.1 temporal lore graph, SHACL continuity validation, and interactive SPARQL Graph RAG narrative assistant. |
| **Provenance Ledger** | `BLAKE3` | Cryptographic BLAKE3 CAS hashes, HMAC-SHA256 signatures, harvested USD DAG trees, and OPA Rego automated royalty splits. |
| **Partner Enclave** | `Cleanroom` | Outbound 1%–100% IP decimation controls, quarantine pre-flight linter, TD 1-click promotion gate, and eBPF zero-egress kernel security. |

---

## ⏱️ Hollywood Standard Transport Timeline

* **Standard VFX Frame Range**: Frame `1001` through `1150` running at **24.00 FPS**.
* **SMPTE Timecode Readout**: Live conversion of current frame to standard SMPTE timecode (e.g. `00:00:43:10`).
* **Keyframe Indicators**: Diamond markers (`◆`) indicating existing animation keys.
* **Playback Controls**: Spacebar play/pause, left/right arrow step, and real-time frame scrubbing.

---

## 🧭 Accessible Workspace Navigation

* **Horizontal Scroll Chevrons**: `<ChevronLeft />` and `<ChevronRight />` for fluid scrolling across all 9 workspaces at any window width.
* **Auto-Centering on Tab Selection**: Active tab automatically smooth-scrolls into the center of the viewport.
* **Persistent "Workspaces (9) ▾" Dropdown**: Direct 1-click access to any workspace from the navigation bar.
* **Keyboard Hotkeys**: Press `⌥1`–`⌥9` (macOS) or `Alt+1`–`Alt+9` (Windows/Linux) to switch between workspaces instantly.
* **macOS Drag Region Isolation**: `-webkit-app-region: drag` is strictly scoped to non-interactive header background space, preventing macOS window movement from capturing clicks on tabs, buttons, or inputs.

---

## 🏛️ Project Directory Structure

```text
web/
├── electron/
│   ├── backendManager.cjs      # Background Python daemon supervisor
│   ├── dev-runner.cjs          # Concurrently manages Vite + Electron in development
│   ├── main.cjs                # Electron main entrypoint, native window, session routing
│   └── preload.cjs             # Secure IPC bridge (window.openloreDesktop)
├── src/
│   ├── components/
│   │   ├── ShotProductionTracker.jsx   # ShotGrid-style shot review breakdown
│   │   ├── ThreeViewport.jsx           # Three.js 3D viewport with mesh raycasting
│   │   ├── USDAttributeInspector.jsx   # Channel Box transform matrix & variant sets
│   │   ├── USDOutliner.jsx             # OpenUSD Prim scenegraph hierarchy tree
│   │   └── VFXTransportTimeline.jsx    # Hollywood standard frame 1001-1150 transport
│   ├── views/
│   │   ├── AnimationScenegraphView.jsx # Dedicated character rig & Graph Editor workspace
│   │   ├── CollaborationView.jsx       # Multi-studio CRDT vector clock sync
│   │   ├── CompilationGridView.jsx     # Render farm & worker grid dispatch
│   │   ├── LookdevShadingView.jsx      # MaterialX turntable studio
│   │   ├── NarrativeLoreView.jsx       # W3C RDF 1.1 lore graph & SPARQL assistant
│   │   ├── PartnerEnclaveView.jsx      # IP decimation & quarantine cleanroom
│   │   ├── ProvenanceLedgerView.jsx    # BLAKE3 hashes & OPA royalties
│   │   └── StageViewportView.jsx       # 3D Layout & master assembly stage
│   ├── App.jsx                         # Main application layout, pipeline header, nav bar
│   ├── index.css                       # TailwindCSS + dark theme + drag isolation styles
│   └── main.jsx                        # React 19 DOM entrypoint
├── package.json                        # Scripts, dependencies, and electron-builder config
└── vite.config.js                      # Vite configuration & dev server proxy
```
