"""Zero-dependency REST API server and static file server for OpenLore Web Studio."""

from __future__ import annotations

import json
import mimetypes
import os
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

from openlore.collaboration.kafka_stream import KafkaEventStream
from openlore.collaboration.resolver import EdgeResolverDaemon
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


class OpenLoreAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler providing REST endpoints and static file hosting for OpenLore."""

    static_dir: Optional[Path] = None
    stage_dir: Path = Path("./stages")
    cas_dir: Path = Path("./data/cas")
    builds_dir: Path = Path("./builds")
    catalog: ProductionCatalog = ProductionCatalog()
    promotion_gate: StagePromotionGate = StagePromotionGate()
    shared_daemon: Optional[EdgeResolverDaemon] = None

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.OK)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, message: str, status: int = HTTPStatus.BAD_REQUEST) -> None:
        self._send_json({"error": message, "status": "ERROR"}, status=status)

    def _read_body_json(self) -> Dict[str, Any]:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # 1. System Status
        if path == "/api/status":
            cas = ContentAddressedStorage(self.cas_dir)
            self._send_json({
                "status": "ONLINE",
                "version": "1.0.0",
                "system": "OpenLore Transmedia Production Backbone",
                "cas_storage_root": str(cas.storage_root.resolve()),
                "services": {
                    "openusd": "Active",
                    "rdf_triplestore": "Active",
                    "crdt_resolver": "Active",
                    "opa_accounting": "Active",
                    "temporal_grid": "Active",
                },
                "studios": [
                    {"id": "studio_london", "location": "London, UK", "role": "Virtual Production Stage (LED Volume)"},
                    {"id": "studio_la", "location": "Los Angeles, USA", "role": "Animation & Game Unreal Integration"},
                    {"id": "studio_tokyo", "location": "Tokyo, Japan", "role": "Cinematic Lighting & MaterialX Lookdev"},
                ],
            })
            return

        # 2. Stage List and Details
        elif path == "/api/stages":
            self.stage_dir.mkdir(parents=True, exist_ok=True)
            stages = []
            for f in self.stage_dir.glob("*.usd*"):
                stat = f.stat()
                stages.append({
                    "name": f.name,
                    "path": str(f.resolve()),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime,
                })
            self._send_json({"stages": stages})
            return

        # 3. Lore Timelines
        elif path == "/api/lore/timelines":
            client = NarrativeGraphClient()
            graph_path = Path("./data/lore/graph.trig")
            if graph_path.is_file():
                client.load_from_file(graph_path)
            tm = TimelineBranchManager(client)
            timelines = [
                {
                    "uri": t.uri,
                    "name": t.name,
                    "is_prime_canon": t.is_prime_canon,
                    "parent_timeline_uri": t.parent_timeline_uri,
                    "created_at": t.created_at.isoformat(),
                }
                for t in tm.list_timelines()
            ]
            self._send_json({"timelines": timelines})
            return

        # 4. Lore Entities & Verification
        elif path == "/api/lore/entities":
            client = NarrativeGraphClient()
            graph_path = Path("./data/lore/graph.trig")
            if graph_path.is_file():
                client.load_from_file(graph_path)

            shapes_path = Path("./schemas/shacl/continuity_shapes.ttl")
            validator = SHACLContinuityValidator(shapes_path)
            report = validator.validate_graph(client.dataset)

            self._send_json({
                "conforms": report.conforms,
                "violations": report.violations,
                "dataset_triples_count": len(client.dataset),
            })
            return

        # 5. Daemon & Collaboration Status
        elif path == "/api/daemon":
            if not self.shared_daemon:
                stream = KafkaEventStream("openlore.stage.web", use_memory_bus=True)
                self.shared_daemon = EdgeResolverDaemon("studio_london", "openlore://stages/root.usda", stream)

            self._send_json({
                "studio_id": self.shared_daemon.studio_id,
                "stage_uri": self.shared_daemon.stage_uri,
                "is_online": self.shared_daemon.is_online,
                "shadow_buffer_size": self.shared_daemon.shadow_buffer_size,
                "vector_clock": self.shared_daemon.local_clock.clock_map,
                "replica_attributes_count": len(self.shared_daemon.replica._attributes),
            })
            return

        # 6. Central Production Catalog
        elif path == "/api/catalog":
            cat_file = self.builds_dir / "catalog.json"
            if cat_file.is_file():
                self.catalog.load_catalog(cat_file)
            self._send_json({"builds": self.catalog.list_all_builds()})
            return

        # 7. Provenance & OPA Royalties
        elif path == "/api/provenance":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            stage_param = query_params.get("stage", ["./stages/hero_scene.usda"])[0]
            stage_path = Path(stage_param)
            if not stage_path.is_file():
                stage_files = list(self.stage_dir.glob("*.usd*"))
                if stage_files:
                    stage_path = stage_files[0]

            if stage_path.is_file():
                from pxr import Usd
                usd_stage = Usd.Stage.Open(str(stage_path))
                harvester = StageDAGHarvester(usd_stage)
                manifest = harvester.create_manifest(f"openlore://stages/{stage_path.name}", "studio-secret-key")
                accounting = RoyaltyAccountingEngine()
                allow_export, unlicensed = accounting.evaluate_export_allowance(manifest)
                splits = accounting.calculate_royalty_splits(manifest)

                self._send_json({
                    "stage_uri": manifest.stage_uri,
                    "total_assets": manifest.total_assets,
                    "digital_signature": manifest.digital_signature,
                    "signature_verified": manifest.verify_signature("studio-secret-key"),
                    "allow_export": allow_export,
                    "unlicensed_prims": unlicensed,
                    "royalty_splits": splits,
                })
                return
            else:
                self._send_json({
                    "stage_uri": "openlore://stages/none",
                    "total_assets": 0,
                    "digital_signature": "N/A",
                    "signature_verified": False,
                    "allow_export": False,
                    "unlicensed_prims": [],
                    "royalty_splits": {},
                })
                return

        # 8. Static Web Frontend Hosting
        if self.static_dir and self.static_dir.is_dir():
            req_path = path.lstrip("/") or "index.html"
            file_path = (self.static_dir / req_path).resolve()

            # Prevent directory traversal
            if not str(file_path).startswith(str(self.static_dir.resolve())):
                self._send_error("Forbidden", HTTPStatus.FORBIDDEN)
                return

            if not file_path.is_file():
                # SPA Fallback to index.html
                file_path = self.static_dir / "index.html"

            if file_path.is_file():
                mime, _ = mimetypes.guess_type(str(file_path))
                data = file_path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(data)
                return

        self._send_error("Endpoint not found", HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        body = self._read_body_json()

        # 1. Branch Narrative Timeline
        if path == "/api/lore/branch":
            client = NarrativeGraphClient()
            graph_path = Path("./data/lore/graph.trig")
            if graph_path.is_file():
                client.load_from_file(graph_path)
            tm = TimelineBranchManager(client)
            new_slug = body.get("new_slug", "branch_reality")
            new_name = body.get("new_name", "Branched Reality Timeline")
            source = body.get("source_timeline", "https://openlore.io/timelines/prime-canon")

            branch = tm.branch_timeline(source, new_slug, new_name)
            graph_path.parent.mkdir(parents=True, exist_ok=True)
            client.save_to_file(graph_path)

            self._send_json({
                "status": "SUCCESS",
                "branch_uri": branch.uri,
                "name": branch.name,
                "parent": branch.parent_timeline_uri,
            })
            return

        # 2. Toggle Daemon Connectivity
        elif path == "/api/daemon/toggle":
            if not self.shared_daemon:
                stream = KafkaEventStream("openlore.stage.web", use_memory_bus=True)
                self.shared_daemon = EdgeResolverDaemon("studio_london", "openlore://stages/root.usda", stream)

            new_state = not self.shared_daemon.is_online
            self.shared_daemon.set_connectivity(new_state)
            self._send_json({
                "status": "SUCCESS",
                "is_online": self.shared_daemon.is_online,
                "shadow_buffer_size": self.shared_daemon.shadow_buffer_size,
            })
            return

        # 3. Record Collaborative Edit
        elif path == "/api/daemon/edit":
            if not self.shared_daemon:
                stream = KafkaEventStream("openlore.stage.web", use_memory_bus=True)
                self.shared_daemon = EdgeResolverDaemon("studio_london", "openlore://stages/root.usda", stream)

            prim_path = body.get("prim_path", "/World/Camera")
            attr_name = body.get("attribute_name", "xformOp:translate")
            val = body.get("value", [10.0, 5.0, 2.0])

            self.shared_daemon.record_local_edit(prim_path, attr_name, val)
            self._send_json({
                "status": "SUCCESS",
                "prim_path": prim_path,
                "attribute_name": attr_name,
                "value": val,
                "shadow_buffer_size": self.shared_daemon.shadow_buffer_size,
            })
            return

        # 4. Inbound Quarantine Linting
        elif path == "/api/partner/lint":
            deliv_path = Path(body.get("deliverable_path", ""))
            max_poly = int(body.get("max_polycount", 500000))
            if not deliv_path.is_file():
                self._send_error(f"Deliverable file not found: {deliv_path}")
                return
            linter = PreFlightUSDValidator(max_polycount_ceiling=max_poly)
            res = linter.validate_deliverable(deliv_path)
            self._send_json({
                "passed": res.passed,
                "total_polycount": res.total_polycount,
                "hierarchy_errors": res.hierarchy_errors,
                "polycount_violations": res.polycount_violations,
                "namespace_violations": res.namespace_violations,
            })
            return

        # 5. TD One-Click Promotion
        elif path == "/api/partner/promote":
            stage_uri = body.get("stage_uri", "openlore://stages/main.usda")
            deliv_path = Path(body.get("deliverable_path", ""))
            prod_path = Path(body.get("production_stage_path", ""))
            td_user = body.get("td_user", "lead_td")

            linter = PreFlightUSDValidator()
            lint_res = linter.validate_deliverable(deliv_path)
            if not lint_res.passed:
                self._send_error("Promotion rejected: Deliverable failed pre-flight linting")
                return

            try:
                token = self.promotion_gate.acquire_promotion_lock(stage_uri, td_user=td_user)
                promoted = self.promotion_gate.promote_to_production(
                    stage_uri=stage_uri,
                    deliverable_path=deliv_path,
                    production_stage_path=prod_path,
                    lint_result=lint_res,
                    lock_token=token,
                )
                self._send_json({
                    "status": "PROMOTED",
                    "stage_uri": stage_uri,
                    "promoted_file": str(deliv_path),
                })
            except Exception as exc:
                self._send_error(str(exc))
            return

        # 6. Worker Grid Downstream Compilation
        elif path == "/api/compile":
            stage_uri = body.get("stage_uri", "openlore://stages/hero_scene.usda")
            stage_path_str = body.get("stage_path", "")
            stage_path = Path(stage_path_str) if stage_path_str else None
            targets = body.get("targets", ["unreal", "unity", "cinematic-cache"])
            out_dir = self.builds_dir

            dispatcher = WorkerGridDispatcher(catalog=self.catalog)
            workflow_id = dispatcher.trigger_compilation_workflow(
                stage_uri=stage_uri,
                target_engines=targets,
                stage_path=stage_path,
                output_dir=out_dir,
            )
            job = dispatcher.get_job_status(workflow_id)
            self._send_json(job)
            return

        self._send_error("Endpoint not found", HTTPStatus.NOT_FOUND)


def run_server(
    port: int = 8000,
    host: str = "127.0.0.1",
    static_dir: Optional[Path] = None,
) -> None:
    """Launch the multi-threaded OpenLore REST API server."""
    OpenLoreAPIHandler.static_dir = static_dir
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, OpenLoreAPIHandler)
    print(f"[OpenLore Web Server] Running at http://{host}:{port}/")
    if static_dir:
        print(f"[OpenLore Web Server] Serving static files from: {static_dir.resolve()}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[OpenLore Web Server] Shutting down...")
        httpd.server_close()
