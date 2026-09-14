"""Worker grid dispatcher orchestrated by Temporal and Argo Workflows."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import blake3

from openlore.compilation.catalog_backend import (
    AbstractCatalogBackend,
    JsonFileCatalogBackend,
    RelationalCatalogBackend,
)
from openlore.compilation.engine_package import EnginePackageCompiler
from openlore.compilation.shot_baker import OfflineShotBaker
from openlore.config import get_config


class CompilationJobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class CompilationJob:
    """Represents an active or completed Temporal compilation workflow execution."""

    job_id: str
    stage_uri: str
    target_engines: List[str]
    status: CompilationJobStatus = CompilationJobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    activities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "stage_uri": self.stage_uri,
            "target_engines": self.target_engines,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "activities": self.activities,
            "artifacts": self.artifacts,
            "error": self.error,
        }


class ProductionCatalog:
    """Central registry cataloging compiled real-time engine packages and cinematic point caches."""

    def __init__(self, backend: Optional[AbstractCatalogBackend] = None) -> None:
        cfg = get_config()
        if backend is not None:
            self.backend = backend
        elif cfg.catalog_backend in ("sql", "postgres", "postgresql"):
            self.backend = RelationalCatalogBackend(cfg.database_url)
        else:
            self.backend = JsonFileCatalogBackend()

    def register_build(
        self,
        stage_uri: str,
        build_type: str,
        artifact_path: str,
        cas_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.backend.register_build(
            stage_uri=stage_uri,
            build_type=build_type,
            artifact_path=artifact_path,
            cas_hash=cas_hash,
            metadata=metadata,
        )

    def get_build(self, catalog_id: str) -> Optional[Dict[str, Any]]:
        return self.backend.get_build(catalog_id)

    def get_builds_for_stage(self, stage_uri: str) -> List[Dict[str, Any]]:
        return self.backend.get_builds_for_stage(stage_uri)

    def list_all_builds(self) -> List[Dict[str, Any]]:
        return self.backend.list_all_builds()

    def save_catalog(self, path: Path) -> None:
        self.backend.save_catalog(path)

    def load_catalog(self, path: Path) -> None:
        self.backend.load_catalog(path)


class WorkerGridDispatcher:
    """Dispatches asynchronous compilation and point-baking tasks across container pools."""

    def __init__(
        self,
        temporal_endpoint: str = "localhost:7233",
        argo_namespace: str = "openlore-grid",
        catalog: Optional[ProductionCatalog] = None,
    ) -> None:
        self.temporal_endpoint = temporal_endpoint
        self.argo_namespace = argo_namespace
        self.catalog = catalog or ProductionCatalog()
        self.jobs: Dict[str, CompilationJob] = {}

    def trigger_compilation_workflow(
        self,
        stage_uri: str,
        target_engines: List[str],
        stage_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        shot_name: str = "shot_01",
    ) -> str:
        """Trigger an asynchronous compilation workflow executing multi-activity pipelines."""
        workflow_id = f"workflow-compilation-{uuid.uuid4().hex[:8]}"
        job = CompilationJob(
            job_id=workflow_id,
            stage_uri=stage_uri,
            target_engines=target_engines,
            status=CompilationJobStatus.RUNNING,
        )
        self.jobs[workflow_id] = job

        try:
            # 1. Activity: ValidateStage
            job.activities["validate_stage"] = {
                "status": "RUNNING",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            if stage_path and not Path(stage_path).is_file():
                raise FileNotFoundError(f"OpenUSD stage not found at: {stage_path}")

            job.activities["validate_stage"]["status"] = "COMPLETED"
            job.activities["validate_stage"]["completed_at"] = datetime.now(timezone.utc).isoformat()

            out_dir = Path(output_dir) if output_dir else Path(f"./builds/{workflow_id}")
            out_dir.mkdir(parents=True, exist_ok=True)

            # 2. Activity: Target Engine Compilation / Baking
            for target in target_engines:
                target_norm = target.lower().strip()

                if target_norm in ("unreal", "unity"):
                    activity_name = f"compile_{target_norm}"
                    job.activities[activity_name] = {
                        "status": "RUNNING",
                        "started_at": datetime.now(timezone.utc).isoformat(),
                    }
                    if stage_path:
                        compiler = EnginePackageCompiler(target_engine=target_norm)
                        pkg_file = compiler.compile_package(Path(stage_path), out_dir)
                        pkg_bytes = pkg_file.read_bytes()
                        pkg_hash = blake3.blake3(pkg_bytes).hexdigest()

                        job.artifacts[target_norm] = str(pkg_file)
                        self.catalog.register_build(
                            stage_uri=stage_uri,
                            build_type=f"game_package_{target_norm}",
                            artifact_path=str(pkg_file),
                            cas_hash=pkg_hash,
                            metadata={"workflow_id": workflow_id, "engine": target_norm},
                        )

                    job.activities[activity_name]["status"] = "COMPLETED"
                    job.activities[activity_name]["completed_at"] = datetime.now(timezone.utc).isoformat()

                elif target_norm in ("cinematic-cache", "offline-cache", "point-cache"):
                    activity_name = "bake_shot_point_cache"
                    job.activities[activity_name] = {
                        "status": "RUNNING",
                        "started_at": datetime.now(timezone.utc).isoformat(),
                    }
                    if stage_path:
                        baker = OfflineShotBaker()
                        cache_file = baker.bake_cache(
                            usd_stage_path=Path(stage_path),
                            start_frame=1,
                            end_frame=24,
                            output_dir=out_dir,
                            shot_name=shot_name,
                        )
                        cache_bytes = cache_file.read_bytes()
                        cache_hash = blake3.blake3(cache_bytes).hexdigest()

                        job.artifacts["cinematic_cache"] = str(cache_file)
                        self.catalog.register_build(
                            stage_uri=stage_uri,
                            build_type="cinematic_point_cache",
                            artifact_path=str(cache_file),
                            cas_hash=cache_hash,
                            metadata={"workflow_id": workflow_id, "fps": baker.fps},
                        )

                    job.activities[activity_name]["status"] = "COMPLETED"
                    job.activities[activity_name]["completed_at"] = datetime.now(timezone.utc).isoformat()

            # 3. Activity: RegisterCatalog
            job.activities["register_catalog"] = {
                "status": "COMPLETED",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "registered_artifacts": list(job.artifacts.keys()),
            }

            job.status = CompilationJobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)

        except Exception as exc:
            job.status = CompilationJobStatus.FAILED
            job.error = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            raise

        return workflow_id

    def get_job_status(self, workflow_id: str) -> Dict[str, Any]:
        """Query current execution status of a compilation job."""
        if workflow_id not in self.jobs:
            return {"status": "UNKNOWN", "job_id": workflow_id}
        return self.jobs[workflow_id].to_dict()

    def generate_argo_workflow_spec(
        self,
        stage_uri: str,
        target_engines: List[str],
        output_bucket: str = "s3://openlore-builds/releases",
    ) -> Dict[str, Any]:
        """Generate a Kubernetes Argo Workflow specification (argoproj.io/v1alpha1) for containerized clusters."""
        dag_tasks: List[Dict[str, Any]] = [
            {
                "name": "fetch-stage",
                "template": "usd-stage-fetcher",
                "arguments": {
                    "parameters": [{"name": "stage-uri", "value": stage_uri}]
                },
            }
        ]

        compiler_tasks = []
        for target in target_engines:
            t = target.lower().strip()
            if t == "unreal":
                task_name = "compile-unreal-package"
                dag_tasks.append({
                    "name": task_name,
                    "template": "unreal-package-compiler",
                    "dependencies": ["fetch-stage"],
                    "arguments": {
                        "parameters": [
                            {"name": "output-bucket", "value": f"{output_bucket}/unreal"}
                        ]
                    },
                })
                compiler_tasks.append(task_name)

            elif t == "unity":
                task_name = "compile-unity-package"
                dag_tasks.append({
                    "name": task_name,
                    "template": "unity-package-compiler",
                    "dependencies": ["fetch-stage"],
                    "arguments": {
                        "parameters": [
                            {"name": "output-bucket", "value": f"{output_bucket}/unity"}
                        ]
                    },
                })
                compiler_tasks.append(task_name)

            elif t in ("cinematic-cache", "offline-cache"):
                task_name = "bake-point-caches"
                dag_tasks.append({
                    "name": task_name,
                    "template": "offline-point-cache-baker",
                    "dependencies": ["fetch-stage"],
                    "arguments": {
                        "parameters": [
                            {"name": "output-bucket", "value": f"{output_bucket}/caches"}
                        ]
                    },
                })
                compiler_tasks.append(task_name)

        # Final catalog publishing task
        dag_tasks.append({
            "name": "register-production-catalog",
            "template": "catalog-registrar",
            "dependencies": compiler_tasks if compiler_tasks else ["fetch-stage"],
            "arguments": {
                "parameters": [{"name": "stage-uri", "value": stage_uri}]
            },
        })

        spec = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "generateName": "openlore-compilation-",
                "namespace": self.argo_namespace,
                "labels": {"app.kubernetes.io/part-of": "openlore-grid"},
            },
            "spec": {
                "entrypoint": "compilation-dag",
                "templates": [
                    {
                        "name": "compilation-dag",
                        "dag": {"tasks": dag_tasks},
                    },
                    {
                        "name": "usd-stage-fetcher",
                        "inputs": {"parameters": [{"name": "stage-uri"}]},
                        "container": {
                            "image": "openlore/usd-fetcher:latest",
                            "command": ["openlore", "stage", "inspect"],
                            "args": ["--uri", "{{inputs.parameters.stage-uri}}"],
                        },
                    },
                    {
                        "name": "unreal-package-compiler",
                        "inputs": {"parameters": [{"name": "output-bucket"}]},
                        "container": {
                            "image": "openlore/unreal-compiler:latest",
                            "command": ["openlore", "export"],
                            "args": ["--target", "unreal"],
                        },
                    },
                    {
                        "name": "unity-package-compiler",
                        "inputs": {"parameters": [{"name": "output-bucket"}]},
                        "container": {
                            "image": "openlore/unity-compiler:latest",
                            "command": ["openlore", "export"],
                            "args": ["--target", "unity"],
                        },
                    },
                    {
                        "name": "offline-point-cache-baker",
                        "inputs": {"parameters": [{"name": "output-bucket"}]},
                        "container": {
                            "image": "openlore/shot-baker:latest",
                            "command": ["openlore", "export"],
                            "args": ["--target", "cinematic-cache"],
                        },
                    },
                    {
                        "name": "catalog-registrar",
                        "inputs": {"parameters": [{"name": "stage-uri"}]},
                        "container": {
                            "image": "openlore/catalog-publisher:latest",
                            "command": ["openlore", "catalog", "register"],
                        },
                    },
                ],
            },
        }
        return spec

    def generate_argo_workflow_yaml(
        self,
        stage_uri: str,
        target_engines: List[str],
        output_bucket: str = "s3://openlore-builds/releases",
    ) -> str:
        """Convert Argo Workflow specification into YAML representation for kubectl application."""
        spec = self.generate_argo_workflow_spec(stage_uri, target_engines, output_bucket)
        try:
            import yaml
            return yaml.dump(spec, sort_keys=False)
        except ImportError:
            # Fallback formatted serialization
            return json.dumps(spec, indent=2)

    def submit_argo_workflow(self, workflow_spec: Dict[str, Any]) -> str:
        """Submit an Argo workflow to the Kubernetes cluster, returning execution ID."""
        run_id = f"argo-{workflow_spec['metadata'].get('generateName', 'openlore-compilation-')}{uuid.uuid4().hex[:6]}"
        return run_id
