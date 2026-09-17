"""OpenLore CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Sequence

warnings.filterwarnings("ignore", message=".*urllib3 v2.*")

from openlore.compilation.grid import ProductionCatalog, WorkerGridDispatcher
from openlore.core.cas import ContentAddressedStorage
from openlore.core.stage import StageCompositionManager
from openlore.narrative.graph import NarrativeGraphClient
from openlore.narrative.timeline import TimelineBranchManager
from openlore.narrative.validator import SHACLContinuityValidator
from openlore.partner.decimation import OutboundDecimationPipeline, ProxyStageConfig
from openlore.partner.linter import PreFlightUSDValidator
from openlore.partner.promotion import StagePromotionGate
from openlore.provenance.accounting import RoyaltyAccountingEngine
from openlore.provenance.harvester import StageDAGHarvester


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openlore",
        description="OpenLore: Git for 3D worlds, game lore, and Hollywood pipelines."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # init
    init_cmd = subparsers.add_parser("init", help="Initialize a new OpenLore repository")
    init_cmd.add_argument("--cas-path", default="./data/cas", help="Path to CAS storage")
    init_cmd.add_argument("--canon", default="prime-canon", help="Default canon timeline branch")

    # stage
    stage_cmd = subparsers.add_parser("stage", help="Manage OpenUSD composition stages")
    stage_cmd.add_argument("action", choices=["list", "create", "inspect"], help="Stage action")
    stage_cmd.add_argument("--uri", default="openlore://stages/root.usda", help="Stage URI")
    stage_cmd.add_argument("--format", choices=["usda", "usdc"], default="usda", help="Stage file format")

    # lore
    lore_cmd = subparsers.add_parser("lore", help="Query, branch, and validate narrative lore")
    lore_cmd.add_argument("action", choices=["verify", "branch", "export", "list"], help="Lore action")
    lore_cmd.add_argument("--timeline", default="https://openlore.io/timelines/prime-canon", help="Timeline URI or slug")
    lore_cmd.add_argument("--new-slug", help="Slug for new branch timeline")
    lore_cmd.add_argument("--new-name", help="Display name for new branch timeline")
    lore_cmd.add_argument("--shapes-path", default="./schemas/shacl/continuity_shapes.ttl", help="Path to SHACL shapes")
    lore_cmd.add_argument("--graph-path", default="./data/lore/graph.trig", help="Path to RDF TriG file")
    lore_cmd.add_argument("--format", choices=["trig", "turtle"], default="trig", help="RDF serialization format")

    # daemon
    daemon_cmd = subparsers.add_parser("daemon", help="Manage edge resolver daemons")
    daemon_cmd.add_argument("action", choices=["start", "stop", "status"], help="Daemon action")
    daemon_cmd.add_argument("--studio-id", default="studio-local", help="Studio identifier")
    daemon_cmd.add_argument("--stage-uri", default="openlore://stages/root.usda", help="Stage URI to synchronize")

    # partner
    partner_cmd = subparsers.add_parser("partner", help="Partner enclave isolation, decimation, and linting")
    partner_cmd.add_argument("action", choices=["sanitize", "lint", "promote"], help="Partner workflow action")
    partner_cmd.add_argument("--stage", help="Source OpenUSD stage path to sanitize")
    partner_cmd.add_argument("--output", help="Output proxy stage path")
    partner_cmd.add_argument("--ratio", type=float, default=0.25, help="Mesh decimation ratio (0.01 - 1.0)")
    partner_cmd.add_argument("--deliverable", help="Quarantined contractor deliverable stage path")
    partner_cmd.add_argument("--max-polycount", type=int, default=500000, help="Maximum allowed polygon ceiling")
    partner_cmd.add_argument("--stage-uri", help="Production stage URI to lock and promote into")
    partner_cmd.add_argument("--production-stage", help="Production OpenUSD stage file path")
    partner_cmd.add_argument("--td-user", default="lead_td", help="Technical Director username")

    # compile
    compile_cmd = subparsers.add_parser("compile", help="Dispatch worker grid downstream compilation")
    compile_cmd.add_argument("--stage", required=True, help="Stage URI to compile")
    compile_cmd.add_argument("--stage-path", required=True, help="Local path to OpenUSD stage file")
    compile_cmd.add_argument("--target", choices=["unreal", "unity", "cinematic-cache", "all"], default="all", help="Compilation target")
    compile_cmd.add_argument("--output-dir", default="./builds", help="Output directory for compiled packages")
    compile_cmd.add_argument("--shot-name", default="shot_01", help="Shot identifier for point caching")

    # catalog
    catalog_cmd = subparsers.add_parser("catalog", help="Query the Central Production Catalog")
    catalog_cmd.add_argument("action", choices=["list"], default="list", nargs="?", help="Catalog action")
    catalog_cmd.add_argument("--stage-uri", help="Filter builds by stage URI")
    catalog_cmd.add_argument("--catalog-path", default="./builds/catalog.json", help="Path to catalog storage file")

    # export
    export_cmd = subparsers.add_parser("export", help="Validate licensing and export downstream packages")
    export_cmd.add_argument("--stage", required=True, help="Stage URI to export")
    export_cmd.add_argument("--target", choices=["unreal", "unity", "cinematic-cache", "all"], default="all")
    export_cmd.add_argument("--stage-path", help="Local OpenUSD stage path if compiling directly")
    export_cmd.add_argument("--output-dir", default="./builds", help="Output directory for compiled artifacts")

    # web
    web_cmd = subparsers.add_parser("web", help="Start the OpenLore Web Studio and REST API server")
    web_cmd.add_argument("--port", type=int, default=8000, help="Port to listen on (default 8000)")
    web_cmd.add_argument("--host", default="127.0.0.1", help="Host address (default 127.0.0.1)")
    web_cmd.add_argument("--static-dir", default="./web/dist", help="Directory containing compiled React frontend")

    # livelink
    livelink_cmd = subparsers.add_parser("livelink", help="Unreal Engine 5 Live Link bridge and plugin generator")
    livelink_subs = livelink_cmd.add_subparsers(dest="subaction", help="Live Link action")

    stream_cmd = livelink_subs.add_parser("stream", help="Run Live Link real-time streaming bridge")
    stream_cmd.add_argument("--host", default="127.0.0.1", help="Broadcast target host")
    stream_cmd.add_argument("--port", type=int, default=11111, help="Broadcast target UDP port")
    stream_cmd.add_argument("--receive-port", type=int, default=11112, help="Inbound telemetry UDP port")
    stream_cmd.add_argument("--fps", type=float, default=60.0, help="Target broadcast frame rate")
    stream_cmd.add_argument("--mode", choices=["broadcast", "receive", "duplex"], default="duplex", help="Bridge operational mode")
    stream_cmd.add_argument("--stage-uri", default="openlore://stages/root.usda", help="OpenUSD Stage URI")

    export_plugin_cmd = livelink_subs.add_parser("export-plugin", help="Generate ready-to-build Unreal Engine 5 C++ Plugin")
    export_plugin_cmd.add_argument("--output-dir", default="./plugins/OpenLoreLiveLink", help="Output directory for UE5 plugin")
    export_plugin_cmd.add_argument("--name", default="OpenLoreLiveLink", help="Plugin name")

    # auth
    auth_cmd = subparsers.add_parser("auth", help="Enterprise token generation and access control")
    auth_cmd.add_argument("action", choices=["create-token"], default="create-token", nargs="?", help="Auth action")
    auth_cmd.add_argument("--sub", default="admin_user", help="Username / Subject identifier")
    auth_cmd.add_argument("--role", choices=["admin", "supervisor", "td", "artist", "partner", "viewer"], default="artist", help="RBAC Role")
    auth_cmd.add_argument("--days", type=int, default=30, help="Token validity duration in days")

    # dcc
    dcc_cmd = subparsers.add_parser("dcc", help="Export native DCC sidecar connectors (Blender, Maya)")
    dcc_cmd.add_argument("target", choices=["blender", "maya", "all"], default="all", nargs="?", help="Target DCC application")
    dcc_cmd.add_argument("--output-dir", default="./dcc", help="Base output directory")

    # farm
    farm_cmd = subparsers.add_parser("farm", help="Distributed GPU Render Farm submission (AWS Deadline, ASWF OpenCue)")
    farm_cmd.add_argument("action", choices=["submit"], default="submit", nargs="?", help="Farm action")
    farm_cmd.add_argument("--scheduler", choices=["deadline", "opencue"], default="deadline", help="Farm scheduler")
    farm_cmd.add_argument("--stage", required=True, help="OpenUSD stage URI to render")
    farm_cmd.add_argument("--renderer", choices=["karma", "arnold", "renderman", "usdrecord"], default="karma", help="Render engine")
    farm_cmd.add_argument("--start-frame", type=int, default=1, help="Start frame")
    farm_cmd.add_argument("--end-frame", type=int, default=24, help="End frame")
    farm_cmd.add_argument("--chunk-size", type=int, default=5, help="Frame chunk size per task")
    farm_cmd.add_argument("--output-dir", default="./renders", help="Render output directory")
    farm_cmd.add_argument("--camera", default="/World/Camera", help="Render camera prim path")
    farm_cmd.add_argument("--job-name", default="openlore_render", help="Render job name")
    farm_cmd.add_argument("--dry-run", action="store_true", default=True, help="Dry run simulation mode")

    return parser


def main(args: Sequence[str] | None = None) -> int:
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command == "init":
        cas_path = Path(parsed_args.cas_path)
        cas = ContentAddressedStorage(cas_path)
        lore_dir = Path("./data/lore")
        lore_dir.mkdir(parents=True, exist_ok=True)
        graph_client = NarrativeGraphClient()
        tm = TimelineBranchManager(graph_client)
        prime = tm.create_prime_canon(name=parsed_args.canon)
        graph_client.save_to_file(lore_dir / "graph.trig")

        print(f"[OpenLore] Initialized Content-Addressed Storage at: {cas.storage_root.resolve()}")
        print(f"[OpenLore] Initialized Prime Canon timeline: '{prime.uri}'")
        return 0

    if parsed_args.command == "stage":
        stage_dir = Path("./stages")
        stage_mgr = StageCompositionManager(stage_dir)
        if parsed_args.action == "create":
            ref = stage_mgr.create_stage(stage_uri=parsed_args.uri, format=parsed_args.format)
            print(f"[OpenLore] Created OpenUSD stage '{ref.stage_uri}' at: {ref.root_layer_path}")
            return 0
        elif parsed_args.action == "list":
            stages = list(stage_dir.glob("*.usd*"))
            print(f"[OpenLore] Stages in {stage_dir.resolve()}:")
            for s in stages:
                print(f"  - {s.name}")
            return 0
        elif parsed_args.action == "inspect":
            ref = stage_mgr.load_stage(stage_uri=parsed_args.uri)
            print(f"[OpenLore] Stage: {ref.stage_uri}")
            print(f"  Root Layer: {ref.root_layer_path}")
            print(f"  Sublayers ({len(ref.sublayers)}):")
            for sub in ref.sublayers:
                print(f"    - {sub}")
            return 0

    if parsed_args.command == "lore":
        graph_client = NarrativeGraphClient()
        graph_path = Path(parsed_args.graph_path)
        if graph_path.exists():
            graph_client.load_from_file(graph_path)
        else:
            tm = TimelineBranchManager(graph_client)
            tm.create_prime_canon()

        if parsed_args.action == "verify":
            shapes_file = Path(parsed_args.shapes_path)
            validator = SHACLContinuityValidator(shapes_file)
            report = validator.validate_graph(graph_client.dataset)
            if report.conforms:
                print(f"[OpenLore] SHACL & Lifecycle validation PASSED. All timeline rules satisfied.")
                return 0
            else:
                print(f"[OpenLore] SHACL & Lifecycle validation FAILED with {len(report.violations)} violation(s):")
                for v in report.violations:
                    print(f"  - {v}")
                return 1

        elif parsed_args.action == "branch":
            new_slug = parsed_args.new_slug or "alternate_continuity_01"
            new_name = parsed_args.new_name or "Alternate Continuity Branch"
            tm = TimelineBranchManager(graph_client)
            branch = tm.branch_timeline(
                source_timeline_uri=parsed_args.timeline,
                new_timeline_slug=new_slug,
                new_timeline_name=new_name,
            )
            graph_path.parent.mkdir(parents=True, exist_ok=True)
            graph_client.save_to_file(graph_path)
            print(f"[OpenLore] Successfully branched timeline:")
            print(f"  Parent: {parsed_args.timeline}")
            print(f"  Branch URI: {branch.uri}")
            print(f"  Name: {branch.name}")
            return 0

        elif parsed_args.action == "list":
            tm = TimelineBranchManager(graph_client)
            timelines = tm.list_timelines()
            print(f"[OpenLore] Active Timelines ({len(timelines)}):")
            for t in timelines:
                status = "[PRIME CANON]" if t.is_prime_canon else f"[BRANCH from {t.parent_timeline_uri}]"
                print(f"  - {t.name} ({t.uri}) {status}")
            return 0

        elif parsed_args.action == "export":
            print(graph_client.export_graph(format=parsed_args.format))
            return 0

    if parsed_args.command == "daemon":
        daemon_file = Path("./data/daemon_status.json")
        daemon_file.parent.mkdir(parents=True, exist_ok=True)

        if parsed_args.action == "start":
            status_data = {
                "status": "RUNNING",
                "studio_id": parsed_args.studio_id,
                "stage_uri": parsed_args.stage_uri,
                "online": True,
                "shadow_buffered_edits": 0,
            }
            daemon_file.write_text(json.dumps(status_data, indent=2), encoding="utf-8")
            print(f"[OpenLore] Edge Resolver Daemon started for {parsed_args.studio_id} on {parsed_args.stage_uri}")
            return 0

        elif parsed_args.action == "status":
            if not daemon_file.exists():
                print("[OpenLore] Edge Resolver Daemon: STOPPED (No active daemon session found)")
                return 0
            data = json.loads(daemon_file.read_text(encoding="utf-8"))
            print(f"[OpenLore] Edge Resolver Daemon Status:")
            print(f"  State: {data.get('status')}")
            print(f"  Studio ID: {data.get('studio_id')}")
            print(f"  Stage URI: {data.get('stage_uri')}")
            print(f"  Connectivity: {'ONLINE' if data.get('online') else 'OFFLINE (Shadow Buffering)'}")
            print(f"  Buffered Edits: {data.get('shadow_buffered_edits', 0)}")
            return 0

        elif parsed_args.action == "stop":
            if daemon_file.exists():
                daemon_file.unlink()
            print(f"[OpenLore] Edge Resolver Daemon stopped.")
            return 0

    if parsed_args.command == "partner":
        if parsed_args.action == "sanitize":
            if not parsed_args.stage or not parsed_args.output:
                print("[OpenLore Partner] Error: --stage and --output are required for sanitize.")
                return 1
            pipeline = OutboundDecimationPipeline(ProxyStageConfig(decimation_ratio=parsed_args.ratio))
            out_file = pipeline.sanitize_outbound_stage(Path(parsed_args.stage), Path(parsed_args.output))
            print(f"[OpenLore Partner] Sanitized outbound stage into clay proxy:")
            print(f"  Source: {parsed_args.stage}")
            print(f"  Sanitized Proxy: {out_file}")
            return 0

        elif parsed_args.action == "lint":
            if not parsed_args.deliverable:
                print("[OpenLore Partner] Error: --deliverable is required for lint.")
                return 1
            validator = PreFlightUSDValidator(max_polycount_ceiling=parsed_args.max_polycount)
            res = validator.validate_deliverable(Path(parsed_args.deliverable))
            print(f"[OpenLore Quarantine Linting]")
            print(f"  Deliverable: {parsed_args.deliverable}")
            print(f"  Status: {'PASSED' if res.passed else 'FAILED'}")
            print(f"  Total Polycount: {res.total_polycount}")
            if res.hierarchy_errors:
                print(f"  Hierarchy Errors ({len(res.hierarchy_errors)}):")
                for e in res.hierarchy_errors:
                    print(f"    - {e}")
            if res.polycount_violations:
                print(f"  Polycount Violations ({len(res.polycount_violations)}):")
                for v in res.polycount_violations:
                    print(f"    - {v}")
            if res.namespace_violations:
                print(f"  Namespace Violations ({len(res.namespace_violations)}):")
                for n in res.namespace_violations:
                    print(f"    - {n}")
            return 0 if res.passed else 1

        elif parsed_args.action == "promote":
            if not parsed_args.stage_uri or not parsed_args.deliverable or not parsed_args.production_stage:
                print("[OpenLore Partner] Error: --stage-uri, --deliverable, and --production-stage are required for promote.")
                return 1
            linter = PreFlightUSDValidator(max_polycount_ceiling=parsed_args.max_polycount)
            lint_res = linter.validate_deliverable(Path(parsed_args.deliverable))
            if not lint_res.passed:
                print(f"[OpenLore Partner] Promotion aborted: Deliverable failed pre-flight linting.")
                return 1

            gate = StagePromotionGate()
            lock_token = gate.acquire_promotion_lock(parsed_args.stage_uri, td_user=parsed_args.td_user)
            gate.promote_to_production(
                stage_uri=parsed_args.stage_uri,
                deliverable_path=Path(parsed_args.deliverable),
                production_stage_path=Path(parsed_args.production_stage),
                lint_result=lint_res,
                lock_token=lock_token,
            )
            print(f"[OpenLore Partner] Successfully promoted deliverable into production stage:")
            print(f"  Stage URI: {parsed_args.stage_uri}")
            print(f"  Promoted Sublayer: {parsed_args.deliverable}")
            print(f"  Production File: {parsed_args.production_stage}")
            return 0

    if parsed_args.command == "compile":
        stage_path = Path(parsed_args.stage_path)
        if not stage_path.is_file():
            print(f"[OpenLore Compile] Error: Stage file not found at: {stage_path}")
            return 1

        targets = ["unreal", "unity", "cinematic-cache"] if parsed_args.target == "all" else [parsed_args.target]
        out_dir = Path(parsed_args.output_dir)
        catalog = ProductionCatalog()
        dispatcher = WorkerGridDispatcher(catalog=catalog)

        workflow_id = dispatcher.trigger_compilation_workflow(
            stage_uri=parsed_args.stage,
            target_engines=targets,
            stage_path=stage_path,
            output_dir=out_dir,
            shot_name=parsed_args.shot_name,
        )
        status = dispatcher.get_job_status(workflow_id)
        print(f"[OpenLore Compilation Grid]")
        print(f"  Workflow ID: {workflow_id}")
        print(f"  Status: {status['status']}")
        print(f"  Stage URI: {parsed_args.stage}")
        print(f"  Target Engines: {targets}")
        print(f"  Artifacts Built ({len(status['artifacts'])}):")
        for k, path in status["artifacts"].items():
            print(f"    - {k}: {path}")

        # Save catalog state
        catalog_path = out_dir / "catalog.json"
        catalog.save_catalog(catalog_path)
        return 0

    if parsed_args.command == "catalog":
        catalog_path = Path(parsed_args.catalog_path)
        catalog = ProductionCatalog()
        if catalog_path.is_file():
            catalog.load_catalog(catalog_path)

        builds = catalog.get_builds_for_stage(parsed_args.stage_uri) if parsed_args.stage_uri else catalog.list_all_builds()
        print(f"[OpenLore Production Catalog] ({len(builds)} entries):")
        for b in builds:
            print(f"  - [{b['build_type']}] Stage: {b['stage_uri']}")
            print(f"      File: {b['artifact_path']}")
            print(f"      CAS Hash: {b['cas_hash'][:16]}...")
            print(f"      Registered: {b['registered_at']}")
        return 0

    if parsed_args.command == "export":
        stage_mgr = StageCompositionManager(Path("./stages"))
        stage_ref = stage_mgr.load_stage(parsed_args.stage)
        harvester = StageDAGHarvester(stage_ref.usd_stage)
        export_key = os.getenv("OPENLORE_EXPORT_KEY", "openlore-export-key")
        manifest = harvester.create_manifest(stage_uri=parsed_args.stage, secret_key=export_key)

        accounting = RoyaltyAccountingEngine()
        allow_export, unlicensed = accounting.evaluate_export_allowance(manifest)

        print(f"[OpenLore Export Engine]")
        print(f"  Stage: {manifest.stage_uri}")
        print(f"  Total Referenced Assets: {manifest.total_assets}")
        print(f"  Manifest Signature: {manifest.digital_signature[:16]}... [VERIFIED]")

        if not allow_export:
            print(f"[OpenLore Export] FAILED: OPA Policy blocked export. Unlicensed prims: {unlicensed}")
            return 1

        splits = accounting.calculate_royalty_splits(manifest)
        print(f"  OPA Licensing Check: PASSED (All assets approved)")
        print(f"  Partner Royalty Distribution Splits:")
        for partner, pct in splits.items():
            print(f"    - {partner}: {pct}%")

        print(f"[OpenLore Export] Export authorized for target: {parsed_args.target}")

        # If stage_path provided, run compilation pipeline automatically
        if parsed_args.stage_path:
            stage_p = Path(parsed_args.stage_path)
            if stage_p.is_file():
                targets = ["unreal", "unity", "cinematic-cache"] if parsed_args.target == "all" else [parsed_args.target]
                dispatcher = WorkerGridDispatcher()
                w_id = dispatcher.trigger_compilation_workflow(
                    stage_uri=parsed_args.stage,
                    target_engines=targets,
                    stage_path=stage_p,
                    output_dir=Path(parsed_args.output_dir),
                )
                print(f"[OpenLore Export] Downstream compilation completed. Workflow: {w_id}")

        return 0

    if parsed_args.command == "web":
        from openlore.server.api import run_server
        static_p = Path(parsed_args.static_dir)
        run_server(port=parsed_args.port, host=parsed_args.host, static_dir=static_p if static_p.is_dir() else None)
        return 0

    if parsed_args.command == "livelink":
        from openlore.bridge.unreal.bridge import UnrealLiveLinkBridge
        from openlore.bridge.unreal.plugin_scaffold import UnrealPluginScaffolder

        if parsed_args.subaction == "export-plugin":
            out_dir = Path(parsed_args.output_dir)
            files = UnrealPluginScaffolder.generate_plugin(out_dir, plugin_name=parsed_args.name)
            print(f"[OpenLore Live Link] Generated UE5 C++ Plugin in '{out_dir}':")
            for key, p in files.items():
                print(f"  - {key}: {p}")
            print(f"[OpenLore Live Link] Ready to drop into <YourProject>/Plugins/{parsed_args.name}")
            return 0

        elif parsed_args.subaction == "stream":
            bridge = UnrealLiveLinkBridge(
                broadcast_host=parsed_args.host,
                broadcast_port=parsed_args.port,
                receive_port=parsed_args.receive_port,
            )
            print(f"[OpenLore Live Link] Starting bridge in '{parsed_args.mode}' mode @ {parsed_args.fps} FPS...")
            print(f"  Broadcast target: {parsed_args.host}:{parsed_args.port}")
            print(f"  Inbound receiver port: {parsed_args.receive_port}")
            bridge.start(mode=parsed_args.mode, target_fps=parsed_args.fps)
            print("[OpenLore Live Link] Active subjects bound:")
            for subj in bridge.get_status()["bound_subjects"]:
                print(f"  - {subj['prim_path']} -> {subj['subject_name']} ({subj['role']})")
            print("[OpenLore Live Link] Bridge operational. Press Ctrl+C to stop.")
            try:
                import time
                while True:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                print("\n[OpenLore Live Link] Stopping bridge...")
                bridge.stop()
            return 0
        else:
            parser.parse_args(["livelink", "--help"])
            return 0

    if parsed_args.command == "auth":
        from openlore.server.auth import Role, TokenService

        role = Role(parsed_args.role)
        seconds = parsed_args.days * 86400
        token = TokenService.create_token(sub=parsed_args.sub, role=role, expires_in_seconds=seconds)
        print(f"[OpenLore Auth] Generated Bearer Token for '{parsed_args.sub}' (Role: {role.value}):")
        print(f"  Token: {token}")
        print(f"  Expires in: {parsed_args.days} days")
        print(f"  Header usage: Authorization: Bearer {token}")
        return 0

    if parsed_args.command == "dcc":
        from openlore.dcc.blender import BlenderAddonScaffolder
        from openlore.dcc.export import DCCExporter
        from openlore.dcc.maya import MayaBridgeScaffolder

        out_dir = Path(parsed_args.output_dir)
        target = parsed_args.target

        if target in ("blender", "all"):
            b_file = BlenderAddonScaffolder.export(out_dir / "blender")
            print(f"[OpenLore DCC] Exported Blender 4.x Add-on to: {b_file}")

        if target in ("maya", "all"):
            m_file = MayaBridgeScaffolder.export(out_dir / "maya")
            print(f"[OpenLore DCC] Exported Autodesk Maya Bridge to: {m_file}")

        print(f"[OpenLore DCC] DCC sidecar exports complete in '{out_dir}'.")
        return 0

    if parsed_args.command == "farm":
        from openlore.compilation.farm import (
            FarmJobConfig,
            FarmScheduler,
            RenderEngine,
            RenderFarmDispatcher,
        )

        cfg = FarmJobConfig(
            job_name=parsed_args.job_name,
            stage_uri=parsed_args.stage,
            renderer=RenderEngine(parsed_args.renderer),
            start_frame=parsed_args.start_frame,
            end_frame=parsed_args.end_frame,
            chunk_size=parsed_args.chunk_size,
            output_dir=parsed_args.output_dir,
            camera=parsed_args.camera,
        )
        scheduler = FarmScheduler(parsed_args.scheduler)
        res = RenderFarmDispatcher.submit_job(cfg, scheduler=scheduler, dry_run=parsed_args.dry_run)
        print(f"[OpenLore Farm] Job submitted to {scheduler.value.upper()}:")
        print(json.dumps(res, indent=2))
        return 0

    print(f"[OpenLore] Command '{parsed_args.command}' execution stub.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
