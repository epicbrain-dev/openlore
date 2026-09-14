"""Multiverse timeline branching and isolation manager."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from rdflib import RDF, RDFS, URIRef

from openlore.narrative.graph import NarrativeGraphClient
from openlore.narrative.ontology import (
    OPENLORE_CANON,
    OPENLORE_TIMELINE,
    TimelineModel,
)


class TimelineBranchManager:
    """Manages multiverse timeline branching without mutating or invalidating prime canon."""

    def __init__(self, graph_client: NarrativeGraphClient) -> None:
        self.graph_client = graph_client

    def create_prime_canon(
        self,
        timeline_uri: str = "https://openlore.io/timelines/prime-canon",
        name: str = "Prime Canon",
    ) -> TimelineModel:
        """Initialize and register the definitive root prime canon timeline."""
        prime = TimelineModel(
            uri=timeline_uri,
            name=name,
            is_prime_canon=True,
            parent_timeline_uri=None,
        )
        self.graph_client.insert_timeline(prime)
        return prime

    def branch_timeline(
        self,
        source_timeline_uri: str,
        new_timeline_slug: str,
        new_timeline_name: str,
        divergence_event_uri: Optional[str] = None,
    ) -> TimelineModel:
        """Branch an existing timeline into an isolated alternate continuity namespace.

        Copies current graph state from source timeline into the new timeline named graph,
        allowing independent evolution without invalidating the source timeline.
        """
        new_timeline_uri = f"https://openlore.io/timelines/{new_timeline_slug}"

        branch = TimelineModel(
            uri=new_timeline_uri,
            name=new_timeline_name,
            is_prime_canon=False,
            parent_timeline_uri=source_timeline_uri,
            divergence_event_uri=divergence_event_uri,
        )

        # 1. Register new timeline metadata
        self.graph_client.insert_timeline(branch)

        # 2. Deep-copy existing triples from source timeline context to the new context
        source_context = self.graph_client.get_timeline_context(source_timeline_uri)
        new_context = self.graph_client.get_timeline_context(new_timeline_uri)

        for s, p, o in source_context.triples((None, None, None)):
            # Retain entities and events up to divergence point
            new_context.add((s, p, o))

        return branch

    def list_timelines(self) -> List[TimelineModel]:
        """List all active narrative timeline branches in the knowledge graph."""
        query = """
        PREFIX canon: <https://openlore.io/ontology/canon#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?timeline ?name ?type ?parent ?event WHERE {
            ?timeline a canon:Timeline ;
                      rdfs:label ?name ;
                      a ?type .
            FILTER (?type IN (canon:PrimeCanon, canon:AlternateContinuity))
            OPTIONAL { ?timeline canon:divergesFrom ?parent }
            OPTIONAL { ?timeline canon:divergenceEvent ?event }
        }
        """
        rows = self.graph_client.query_sparql(query)
        timelines: List[TimelineModel] = []
        for row in rows:
            uri = row["timeline"]
            name = row["name"]
            is_prime = "PrimeCanon" in row["type"]
            parent = row.get("parent")
            divergence_event = row.get("event")
            timelines.append(
                TimelineModel(
                    uri=uri,
                    name=name,
                    is_prime_canon=is_prime,
                    parent_timeline_uri=parent,
                    divergence_event_uri=divergence_event,
                )
            )
        return timelines

    def get_timeline_divergence(self, timeline_uri: str) -> Dict[str, Any]:
        """Retrieve the parent timeline and divergence event information."""
        query = f"""
        PREFIX canon: <https://openlore.io/ontology/canon#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?name ?parent ?parentName ?event ?eventName WHERE {{
            <{timeline_uri}> a canon:Timeline ;
                            rdfs:label ?name .
            OPTIONAL {{
                <{timeline_uri}> canon:divergesFrom ?parent .
                OPTIONAL {{ ?parent rdfs:label ?parentName }}
            }}
            OPTIONAL {{
                <{timeline_uri}> canon:divergenceEvent ?event .
                OPTIONAL {{ ?event canon:name ?eventName }}
            }}
        }}
        """
        rows = self.graph_client.query_sparql(query)
        return rows[0] if rows else {}
