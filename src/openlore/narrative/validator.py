"""Asynchronous W3C SHACL Continuity Validator with Spatiotemporal Bounds Checking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

from rdflib import Graph
import pyshacl

from openlore.exceptions import ContinuityViolationError


@dataclass
class ValidationReport:
    """Result of a SHACL and lifecycle continuity validation run."""

    conforms: bool
    violations: List[str] = field(default_factory=list)
    report_text: str = ""
    timeline_uri: Optional[str] = None


class SHACLContinuityValidator:
    """Validates narrative graphs against formal SHACL shape rules and spatiotemporal rules."""

    def __init__(self, shapes_path: Path) -> None:
        self.shapes_path = Path(shapes_path)
        if not self.shapes_path.exists():
            raise FileNotFoundError(f"SHACL shapes file not found: {self.shapes_path}")
        self.shapes_graph = Graph()
        self.shapes_graph.parse(str(self.shapes_path), format="turtle")

    def validate_graph(
        self,
        data_graph: Union[Graph, str],
        timeline_uri: Optional[str] = None,
    ) -> ValidationReport:
        """Validate a graph against SHACL shapes and spatiotemporal bounds."""
        target_graph = Graph()
        if isinstance(data_graph, str):
            target_graph.parse(data=data_graph, format="turtle")
        elif hasattr(data_graph, "graphs") or hasattr(data_graph, "contexts"):
            # If a ConjunctiveGraph/Dataset is passed, extract the specific timeline or union
            if timeline_uri:
                from rdflib import URIRef
                if hasattr(data_graph, "graph"):
                    target_graph = data_graph.graph(URIRef(timeline_uri))
                else:
                    target_graph = data_graph.get_context(timeline_uri)
            else:
                for triple in data_graph.triples((None, None, None)):
                    target_graph.add(triple)
        else:
            target_graph = data_graph

        conforms, results_graph, results_text = pyshacl.validate(
            data_graph=target_graph,
            shacl_graph=self.shapes_graph,
            inference="rdfs",
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True,
            meta_shacl=False,
            advanced=False,
            js=False,
            debug=False,
        )

        violations: List[str] = []
        if not conforms:
            # Parse violation messages from results_text
            for line in results_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("Message:") or stripped.startswith("Constraint Violation"):
                    violations.append(stripped)

            if not violations:
                violations.append("SHACL validation constraint failure detected.")

        # Temporal Lifecycle Continuity Verification
        temporal_violations = self._verify_temporal_lifecycle_bounds(target_graph)
        if temporal_violations:
            conforms = False
            violations.extend(temporal_violations)

        return ValidationReport(
            conforms=conforms,
            violations=violations,
            report_text=results_text,
            timeline_uri=timeline_uri,
        )

    def _verify_temporal_lifecycle_bounds(self, graph: Graph) -> List[str]:
        """Verify that characters do not participate in events outside their birth/death bounds."""
        violations: List[str] = []
        query = """
        PREFIX canon: <https://openlore.io/ontology/canon#>
        PREFIX char: <https://openlore.io/ontology/characters#>
        SELECT ?event ?eventName ?eventTime ?char ?charName ?birth ?death WHERE {
            ?event a canon:NarrativeEvent ;
                   canon:name ?eventName ;
                   canon:timestamp ?eventTime ;
                   canon:hasParticipant ?char .
            ?char a canon:Character ;
                  canon:name ?charName .
            OPTIONAL { ?char char:birthTime ?birth }
            OPTIONAL { ?char char:deathTime ?death }
        }
        """
        results = graph.query(query)
        for row in results:
            event_name = str(row["eventName"])
            char_name = str(row["charName"])
            event_time_str = str(row["eventTime"])
            event_dt = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))

            if row["birth"]:
                birth_dt = datetime.fromisoformat(str(row["birth"]).replace("Z", "+00:00"))
                if event_dt < birth_dt:
                    violations.append(
                        f"Temporal violation: Character '{char_name}' participates in event '{event_name}' at {event_dt.isoformat()}, which precedes birth at {birth_dt.isoformat()}."
                    )

            if row["death"]:
                death_dt = datetime.fromisoformat(str(row["death"]).replace("Z", "+00:00"))
                if event_dt > death_dt:
                    violations.append(
                        f"Temporal violation: Character '{char_name}' participates in event '{event_name}' at {event_dt.isoformat()}, which occurs after death at {death_dt.isoformat()}."
                    )

        return violations

    def assert_valid(
        self,
        data_graph: Union[Graph, str],
        timeline_uri: Optional[str] = None,
    ) -> ValidationReport:
        """Run validation and raise ContinuityViolationError if validation fails."""
        report = self.validate_graph(data_graph, timeline_uri=timeline_uri)
        if not report.conforms:
            msg = f"Narrative continuity validation failed with {len(report.violations)} violation(s):\n" + "\n".join(
                f" - {v}" for v in report.violations
            )
            raise ContinuityViolationError(msg)
        return report
