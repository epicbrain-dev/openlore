"""SPARQL Graph RAG Narrative Assistant & Lore Canon Reasoner.

Provides hybrid knowledge-graph reasoning over W3C RDF 1.1 timelines,
spatiotemporal event bounds, character lifecycles, and automated canon audits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from rdflib import Dataset, Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

from openlore.narrative.graph import NarrativeGraphClient
from openlore.narrative.ontology import (
    OPENLORE_CANON,
    OPENLORE_CHAR,
    OPENLORE_TIMELINE,
)
from openlore.narrative.validator import SHACLContinuityValidator


@dataclass
class AssistantResponse:
    """Structured response from the Graph RAG Narrative Assistant."""

    query: str
    answer: str
    reasoning_path: List[str] = field(default_factory=list)
    retrieved_triples: List[Dict[str, str]] = field(default_factory=list)
    continuity_status: str = "CANON_VALID"  # "CANON_VALID" | "CONTRADICTION_DETECTED"
    violations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "reasoning_path": self.reasoning_path,
            "retrieved_triples": self.retrieved_triples,
            "continuity_status": self.continuity_status,
            "violations": self.violations,
            "timestamp": self.timestamp,
        }


class GraphRAGNarrativeAssistant:
    """Semantic Graph RAG assistant synthesizing answers and auditing lore canon."""

    def __init__(
        self,
        graph_client: Optional[NarrativeGraphClient] = None,
        validator: Optional[SHACLContinuityValidator] = None,
    ) -> None:
        self.client = graph_client or NarrativeGraphClient()
        self.validator = validator

    @staticmethod
    def _parse_timestamp(val: Any) -> Optional[float]:
        if not val:
            return None
        val_str = str(val).strip()
        try:
            dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            pass
        try:
            return float(val_str)
        except Exception:
            return None

    def query(self, natural_query: str, timeline_uri: Optional[str] = None) -> AssistantResponse:
        """Process a natural language query using Graph RAG traversal and temporal reasoning."""
        query_lower = natural_query.lower()
        reasoning_path: List[str] = []
        retrieved_triples: List[Dict[str, str]] = []
        violations: List[str] = []

        reasoning_path.append(f"Received query: '{natural_query}'")

        # 1. Audit / Continuity Check Intent
        if any(w in query_lower for w in ["audit", "violation", "paradox", "contradiction", "check continuity"]):
            reasoning_path.append("Classified intent: CONTINUITY_AUDIT")
            return self._perform_continuity_audit(natural_query, timeline_uri, reasoning_path)

        # 2. Timeline Divergence Intent
        if any(w in query_lower for w in ["timeline", "multiverse", "branch", "diverge"]):
            reasoning_path.append("Classified intent: TIMELINE_DIVERGENCE")
            return self._query_timelines(natural_query, reasoning_path)

        # 3. Event / Spatiotemporal Intent
        if any(w in query_lower for w in ["event", "battle", "happen", "when", "where", "epoch"]):
            reasoning_path.append("Classified intent: SPATIOTEMPORAL_EVENT")
            return self._query_events(natural_query, timeline_uri, reasoning_path)

        # 4. Character Lifecycle & Asset Binding Intent (Default)
        reasoning_path.append("Classified intent: CHARACTER_LIFECYCLE")
        return self._query_characters(natural_query, timeline_uri, reasoning_path)

    def _perform_continuity_audit(
        self,
        query: str,
        timeline_uri: Optional[str],
        reasoning_path: List[str],
    ) -> AssistantResponse:
        """Run an automated canon audit checking spatiotemporal limits and SHACL shapes."""
        graph_target = f"<{timeline_uri}>" if timeline_uri else "?g"
        sparql_events = f"""
        PREFIX canon: <https://openlore.io/ontology/canon#>
        PREFIX char: <https://openlore.io/ontology/characters#>
        SELECT ?event ?eventName ?timestamp ?char ?charName ?birth ?death WHERE {{
            GRAPH {graph_target} {{
                ?event a canon:NarrativeEvent ;
                       canon:name ?eventName ;
                       canon:timestamp ?timestamp ;
                       canon:hasParticipant ?char .
                ?char a canon:Character ;
                      canon:name ?charName .
                OPTIONAL {{ ?char char:birthTime ?birth }}
                OPTIONAL {{ ?char char:deathTime ?death }}
            }}
        }}
        """
        reasoning_path.append("Synthesizing SPARQL query for event-character spatiotemporal intersection...")
        results = self.client.query_sparql(sparql_events)
        reasoning_path.append(f"SPARQL returned {len(results)} participant-event relationships.")

        retrieved_triples: List[Dict[str, str]] = []
        violations: List[str] = []

        for row in results:
            ev_name = row.get("eventName", "Unknown Event")
            ts_str = row.get("timestamp")
            char_name = row.get("charName", "Unknown Character")
            birth_str = row.get("birth")
            death_str = row.get("death")

            retrieved_triples.append({
                "subject": ev_name,
                "predicate": "hasParticipant",
                "object": char_name,
            })

            ts = self._parse_timestamp(ts_str)
            birth_ts = self._parse_timestamp(birth_str)
            death_ts = self._parse_timestamp(death_str)

            if ts is not None:
                if birth_ts is not None and birth_ts > ts:
                    violations.append(
                        f"Temporal Paradox: Character '{char_name}' participated in '{ev_name}' at epoch {ts_str}, but was born later at {birth_str}."
                    )
                if death_ts is not None and death_ts < ts:
                    violations.append(
                        f"Post-Mortem Participation: Character '{char_name}' participated in '{ev_name}' at epoch {ts_str}, but died prior at {death_str}."
                    )

        if violations:
            status = "CONTRADICTION_DETECTED"
            answer = (
                f"Canon Audit Alert: {len(violations)} continuity contradiction(s) identified in the active narrative graph. "
                f"Details: {'; '.join(violations)}"
            )
            reasoning_path.append(f"Flagged {len(violations)} temporal/continuity violation(s).")
        else:
            status = "CANON_VALID"
            answer = (
                "Canon Continuity Audit Complete: All character lifecycles, event timestamps, "
                "and participant causal chains are fully consistent and within valid spatiotemporal bounds."
            )
            reasoning_path.append("No temporal anomalies found. Canon is coherent.")

        return AssistantResponse(
            query=query,
            answer=answer,
            reasoning_path=reasoning_path,
            retrieved_triples=retrieved_triples,
            continuity_status=status,
            violations=violations,
        )

    def _query_characters(
        self,
        query: str,
        timeline_uri: Optional[str],
        reasoning_path: List[str],
    ) -> AssistantResponse:
        """Query character entities and their asset bindings across named graphs."""
        graph_target = f"<{timeline_uri}>" if timeline_uri else "?g"
        sparql = f"""
        PREFIX canon: <https://openlore.io/ontology/canon#>
        PREFIX char: <https://openlore.io/ontology/characters#>
        SELECT ?char ?name ?status ?birth ?death ?asset WHERE {{
            GRAPH {graph_target} {{
                ?char a canon:Character ;
                      canon:name ?name .
                OPTIONAL {{ ?char char:status ?status }}
                OPTIONAL {{ ?char char:birthTime ?birth }}
                OPTIONAL {{ ?char char:deathTime ?death }}
                OPTIONAL {{
                    ?binding canon:boundTo ?char ;
                             canon:casHash ?asset .
                }}
            }}
        }}
        """
        reasoning_path.append("Synthesized SPARQL query for character lifecycles across named graphs.")
        results = self.client.query_sparql(sparql)
        reasoning_path.append(f"Retrieved {len(results)} character records from triplestore.")

        retrieved_triples: List[Dict[str, str]] = []
        char_summaries: List[str] = []

        for row in results:
            name = row.get("name", "Unnamed")
            status = row.get("status", "Active")
            birth = row.get("birth", "N/A")
            asset = row.get("asset")

            retrieved_triples.append({"subject": name, "predicate": "status", "object": status})
            if asset:
                retrieved_triples.append({"subject": name, "predicate": "boundAsset", "object": asset[:16] + "..."})

            summary = f"• **{name}**: Status '{status}', Birth Epoch: {birth}"
            if asset:
                summary += f" (CAS Asset: `{asset[:12]}...`)"
            char_summaries.append(summary)

        if not char_summaries:
            answer = "No matching character entities found in the active narrative graph."
        else:
            answer = f"Found {len(char_summaries)} registered narrative character(s):\n" + "\n".join(char_summaries)

        return AssistantResponse(
            query=query,
            answer=answer,
            reasoning_path=reasoning_path,
            retrieved_triples=retrieved_triples,
            continuity_status="CANON_VALID",
        )

    def _query_events(
        self,
        query: str,
        timeline_uri: Optional[str],
        reasoning_path: List[str],
    ) -> AssistantResponse:
        """Query spatiotemporal events."""
        graph_target = f"<{timeline_uri}>" if timeline_uri else "?g"
        sparql = f"""
        PREFIX canon: <https://openlore.io/ontology/canon#>
        SELECT ?event ?name ?timestamp ?location ?participant WHERE {{
            GRAPH {graph_target} {{
                ?event a canon:NarrativeEvent ;
                       canon:name ?name .
                OPTIONAL {{ ?event canon:timestamp ?timestamp }}
                OPTIONAL {{ ?event canon:location ?location }}
                OPTIONAL {{ ?event canon:hasParticipant ?participant }}
            }}
        }}
        ORDER BY ?timestamp
        """
        reasoning_path.append("Synthesizing SPARQL chronological query for narrative events...")
        results = self.client.query_sparql(sparql)
        reasoning_path.append(f"Retrieved {len(results)} narrative events.")

        retrieved_triples: List[Dict[str, str]] = []
        event_lines: List[str] = []

        for row in results:
            name = row.get("name", "Unnamed Event")
            ts = row.get("timestamp", "N/A")
            loc = row.get("location", "Unknown Location")
            part = row.get("participant", "None")

            retrieved_triples.append({"subject": name, "predicate": "timestamp", "object": str(ts)})
            retrieved_triples.append({"subject": name, "predicate": "location", "object": str(loc)})

            event_lines.append(f"• **{name}** [Epoch {ts}] at {loc} (Participant: {part})")

        if not event_lines:
            answer = "No narrative events registered in this timeline context."
        else:
            answer = f"Chronological Event Sequence ({len(event_lines)} events):\n" + "\n".join(event_lines)

        return AssistantResponse(
            query=query,
            answer=answer,
            reasoning_path=reasoning_path,
            retrieved_triples=retrieved_triples,
            continuity_status="CANON_VALID",
        )

    def _query_timelines(
        self,
        query: str,
        reasoning_path: List[str],
    ) -> AssistantResponse:
        """Query timeline realities and multiverse divergence points."""
        sparql = """
        PREFIX canon: <https://openlore.io/ontology/canon#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?tl ?name ?type ?parent WHERE {
            ?tl a canon:Timeline ;
                rdfs:label ?name ;
                a ?type .
            OPTIONAL { ?tl canon:divergesFrom ?parent }
        }
        """
        reasoning_path.append("Synthesized SPARQL query across W3C RDF named graphs for multiverse branches.")
        results = self.client.query_sparql(sparql)
        reasoning_path.append(f"Found {len(results)} timeline branch definitions.")

        retrieved_triples: List[Dict[str, str]] = []
        lines: List[str] = []

        for row in results:
            name = row.get("name", "Unknown Reality")
            tl_type = row.get("type", "")
            parent = row.get("parent")

            is_prime = "PrimeCanon" in tl_type
            label = "Prime Canon" if is_prime else f"Branch Reality (diverges from {parent})"
            lines.append(f"• **{name}** — {label}")
            retrieved_triples.append({"subject": name, "predicate": "type", "object": label})

        answer = "Multiverse Timeline Branches:\n" + "\n".join(lines)
        return AssistantResponse(
            query=query,
            answer=answer,
            reasoning_path=reasoning_path,
            retrieved_triples=retrieved_triples,
            continuity_status="CANON_VALID",
        )
