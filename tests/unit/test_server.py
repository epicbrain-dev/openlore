"""Unit tests for OpenLore REST API server."""

from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from openlore import __version__
from openlore.server.api import OpenLoreAPIHandler


class TestOpenLoreAPIServer(unittest.TestCase):
    server: ThreadingHTTPServer
    server_thread: threading.Thread
    base_url: str

    @classmethod
    def setUpClass(cls) -> None:
        # Bind to port 0 for automatic available ephemeral port allocation
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), OpenLoreAPIHandler)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def _get_json(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode("utf-8"))

    def _post_json(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode("utf-8"))

    def test_status_endpoint(self) -> None:
        data = self._get_json("/api/status")
        self.assertEqual(data["status"], "ONLINE")
        self.assertIn("cas_storage_root", data)
        self.assertIn("services", data)
        self.assertEqual(data["services"]["openusd"], "Active")

    def test_stages_endpoint(self) -> None:
        data = self._get_json("/api/stages")
        self.assertIn("stages", data)

    def test_lore_timelines_and_branch_endpoint(self) -> None:
        data = self._get_json("/api/lore/timelines")
        self.assertIn("timelines", data)

        branch_res = self._post_json("/api/lore/branch", {
            "source_timeline": "https://openlore.io/timelines/prime-canon",
            "new_slug": "api_test_branch_01",
            "new_name": "API Test Branched Timeline",
        })
        self.assertEqual(branch_res["status"], "SUCCESS")
        self.assertIn("api_test_branch_01", branch_res["branch_uri"])

    def test_daemon_and_collaboration_endpoints(self) -> None:
        data = self._get_json("/api/daemon")
        self.assertIn("studio_id", data)
        self.assertIn("is_online", data)

        edit_res = self._post_json("/api/daemon/edit", {
            "prim_path": "/World/Camera",
            "attribute_name": "xformOp:translate",
            "value": [12.0, 4.0, 2.0],
        })
        self.assertEqual(edit_res["status"], "SUCCESS")
        self.assertEqual(edit_res["prim_path"], "/World/Camera")

    def test_catalog_endpoint(self) -> None:
        data = self._get_json("/api/catalog")
        self.assertIn("builds", data)

    def test_provenance_endpoint(self) -> None:
        data = self._get_json("/api/provenance")
        self.assertIn("stage_uri", data)
        self.assertIn("royalty_splits", data)

    def test_livelink_endpoints(self) -> None:
        # 1. GET status
        status_data = self._get_json("/api/livelink/status")
        self.assertIn("status", status_data)
        self.assertIn("bound_subjects", status_data)
        self.assertIn("coordinate_settings", status_data)

        # 2. POST start
        start_res = self._post_json("/api/livelink/start", {"mode": "duplex", "fps": 30.0})
        self.assertEqual(start_res["status"], "ONLINE")
        self.assertEqual(start_res["mode"], "duplex")

        # 3. POST stop
        stop_res = self._post_json("/api/livelink/stop", {})
        self.assertEqual(stop_res["status"], "STOPPED")
        self.assertEqual(stop_res["mode"], "stopped")

    def test_narrative_assistant_endpoint(self) -> None:
        payload = {"query": "Audit timeline for temporal paradoxes"}
        res = self._post_json("/api/narrative/assistant", payload)
        self.assertIn("query", res)
        self.assertIn("answer", res)
        self.assertIn("continuity_status", res)
        self.assertIn(res["continuity_status"], ["CANON_VALID", "CONTRADICTION_DETECTED"])

    def test_health_probes(self) -> None:
        for probe_path in ("/health", "/api/health"):
            data = self._get_json(probe_path)
            self.assertEqual(data["status"], "UP")
            self.assertEqual(data["version"], __version__)

    def test_not_found_endpoint(self) -> None:
        url = f"{self.base_url}/api/nonexistent_route"
        try:
            urllib.request.urlopen(url)
            self.fail("Expected HTTP 404")
        except urllib.error.HTTPError as err:
            self.assertEqual(err.code, 404)


if __name__ == "__main__":
    unittest.main()
