"""Unit tests for Enterprise Kubernetes Helm Chart."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HELM_ROOT = REPO_ROOT / "helm" / "openlore"


class TestOpenLoreHelmChart(unittest.TestCase):
    """Test suite ensuring Helm chart structure, metadata, and templates meet enterprise standards."""

    def test_chart_metadata(self) -> None:
        chart_file = HELM_ROOT / "Chart.yaml"
        self.assertTrue(chart_file.exists(), "Chart.yaml must exist")
        data = yaml.safe_load(chart_file.read_text(encoding="utf-8"))

        self.assertEqual(data["name"], "openlore")
        self.assertEqual(data["version"], "1.5.0")
        self.assertEqual(data["appVersion"], "1.5.0")

    def test_values_configuration(self) -> None:
        values_file = HELM_ROOT / "values.yaml"
        self.assertTrue(values_file.exists(), "values.yaml must exist")
        data = yaml.safe_load(values_file.read_text(encoding="utf-8"))

        self.assertEqual(data["image"]["tag"], "1.5.0")
        self.assertEqual(data["probes"]["livenessPath"], "/health")
        self.assertEqual(data["probes"]["readinessPath"], "/health")
        self.assertTrue(data["autoscaling"]["enabled"])
        self.assertEqual(data["autoscaling"]["minReplicas"], 2)
        self.assertEqual(data["autoscaling"]["maxReplicas"], 10)
        self.assertTrue(data["persistence"]["cas"]["enabled"])
        self.assertIn("authSecret", data["secrets"])
        self.assertIn("signingKey", data["secrets"])

    def test_deployment_template(self) -> None:
        deploy_file = HELM_ROOT / "templates" / "deployment.yaml"
        self.assertTrue(deploy_file.exists(), "templates/deployment.yaml must exist")
        content = deploy_file.read_text(encoding="utf-8")

        # Probes must use /health to prevent CrashLoopBackOff under RBAC
        self.assertIn('/health', content)
        self.assertNotIn('/api/status', content)

        # Secrets must be referenced
        self.assertIn('OPENLORE_AUTH_SECRET', content)
        self.assertIn('OPENLORE_SIGNING_KEY', content)
        self.assertIn('secretKeyRef', content)

        # Persistence volume mounts
        self.assertIn('cas-volume', content)

    def test_secret_template(self) -> None:
        secret_file = HELM_ROOT / "templates" / "secret.yaml"
        self.assertTrue(secret_file.exists(), "templates/secret.yaml must exist")
        content = secret_file.read_text(encoding="utf-8")
        self.assertIn("kind: Secret", content)
        self.assertIn("OPENLORE_AUTH_SECRET", content)
        self.assertIn("OPENLORE_SIGNING_KEY", content)

    def test_pvc_template(self) -> None:
        pvc_file = HELM_ROOT / "templates" / "pvc.yaml"
        self.assertTrue(pvc_file.exists(), "templates/pvc.yaml must exist")
        content = pvc_file.read_text(encoding="utf-8")
        self.assertIn("kind: PersistentVolumeClaim", content)
        self.assertIn("cas-pvc", content)

    def test_hpa_template(self) -> None:
        hpa_file = HELM_ROOT / "templates" / "hpa.yaml"
        self.assertTrue(hpa_file.exists(), "templates/hpa.yaml must exist")
        content = hpa_file.read_text(encoding="utf-8")
        self.assertIn("kind: HorizontalPodAutoscaler", content)
        self.assertIn("scaleTargetRef", content)


if __name__ == "__main__":
    unittest.main()
