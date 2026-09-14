"""W3C RDF 1.1 Semantic Graph Client with Named Graph Timeline Isolation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from rdflib import Dataset, Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from openlore.narrative.ontology import (
    AssetBindingRecord,
    CharacterEntity,
    NarrativeEntity,
    NarrativeEvent,
    OPENLORE_CANON,
    OPENLORE_CHAR,
    OPENLORE_TIMELINE,
    TimelineModel,
)


class NarrativeGraphClient:
    """Enterprise W3C RDF 1.1 triplestore client supporting isolated timeline named graphs."""

    def __init__(self, endpoint_url: Optional[str] = None) -> None:
        self.endpoint_url = endpoint_url
        self.dataset = Dataset()
        self._bind_namespaces(self.dataset)

    def _bind_namespaces(self, target_graph: Graph) -> None:
        target_graph.bind("canon", OPENLORE_CANON)
        target_graph.bind("char", OPENLORE_CHAR)
        target_graph.bind("timeline", OPENLORE_TIMELINE)
        target_graph.bind("owl", OWL)
        target_graph.bind("rdf", RDF)
        target_graph.bind("rdfs", RDFS)
        target_graph.bind("xsd", XSD)

    def get_timeline_context(self, timeline_uri: str) -> Graph:
        """Get or create the specific named graph context for a timeline."""
        context_graph = self.dataset.graph(URIRef(timeline_uri))
        self._bind_namespaces(context_graph)
        return context_graph

    def insert_timeline(self, timeline: TimelineModel) -> None:
        """Register a timeline and write its metadata into the default graph and its own named graph."""
        context = self.get_timeline_context(timeline.uri)
        for s, p, o in timeline.to_triples():
            context.add((s, p, o))
            self.dataset.add((s, p, o))

    def insert_character(self, character: CharacterEntity) -> None:
        """Insert character triples into the designated timeline named graph."""
        context = self.get_timeline_context(character.timeline_uri)
        for s, p, o in character.to_triples():
            context.add((s, p, o))

    def insert_event(self, event: NarrativeEvent) -> None:
        """Insert narrative event, participants, and causal links into the timeline graph."""
        context = self.get_timeline_context(event.timeline_uri)
        for s, p, o in event.to_triples():
            context.add((s, p, o))

    def bind_asset_to_entity(
        self,
        entity_uri: str,
        prim_path: str,
        blake3_hash: str,
        timeline_uri: str,
    ) -> AssetBindingRecord:
        """Bind an immutable CAS BLAKE3 hash to a narrative entity within a timeline."""
        binding_uri = f"{entity_uri}/binding/{blake3_hash[:8]}"
        binding = AssetBindingRecord(
            uri=binding_uri,
            prim_path=prim_path,
            blake3_hash=blake3_hash,
            timeline_uri=timeline_uri,
            entity_uri=entity_uri,
        )
        context = self.get_timeline_context(timeline_uri)
        for s, p, o in binding.to_triples():
            context.add((s, p, o))
        return binding

    def query_sparql(self, sparql_query: str, timeline_uri: Optional[str] = None) -> List[Dict[str, Any]]:
        """Execute a SPARQL query against either a specific timeline graph or the entire dataset."""
        target_graph = self.get_timeline_context(timeline_uri) if timeline_uri else self.dataset
        results = target_graph.query(sparql_query)

        rows: List[Dict[str, Any]] = []
        for row in results:
            if hasattr(row, "asdict"):
                row_dict = {str(k): str(v) for k, v in row.asdict().items()}
                rows.append(row_dict)
            else:
                rows.append({f"col_{i}": str(val) for i, val in enumerate(row)})
        return rows

    def get_character_lifecycles(self, timeline_uri: str) -> List[Dict[str, Any]]:
        """Retrieve all characters and their lifecycles within a given timeline."""
        query = f"""
        PREFIX canon: <https://openlore.io/ontology/canon#>
        PREFIX char: <https://openlore.io/ontology/characters#>
        SELECT ?char ?name ?status ?birth ?death WHERE {{
            GRAPH <{timeline_uri}> {{
                ?char a canon:Character ;
                      canon:name ?name ;
                      char:status ?status .
                OPTIONAL {{ ?char char:birthTime ?birth }}
                OPTIONAL {{ ?char char:deathTime ?death }}
            }}
        }}
        """
        return self.query_sparql(query)

    def get_timeline_events(self, timeline_uri: str) -> List[Dict[str, Any]]:
        """Retrieve all events in chronological order for a timeline."""
        query = f"""
        PREFIX canon: <https://openlore.io/ontology/canon#>
        SELECT ?event ?name ?timestamp ?participant WHERE {{
            GRAPH <{timeline_uri}> {{
                ?event a canon:NarrativeEvent ;
                       canon:name ?name ;
                       canon:timestamp ?timestamp .
                OPTIONAL {{ ?event canon:hasParticipant ?participant }}
            }}
        }}
        ORDER BY ?timestamp
        """
        return self.query_sparql(query)

    def export_graph(self, timeline_uri: Optional[str] = None, format: str = "trig") -> str:
        """Export serialized graph data (TriG for datasets with named graphs, Turtle for single timeline)."""
        if timeline_uri:
            context = self.get_timeline_context(timeline_uri)
            return context.serialize(format="turtle")
        return self.dataset.serialize(format=format)

    def save_to_file(self, path: Path, timeline_uri: Optional[str] = None, format: str = "trig") -> None:
        """Save graph serialization to file."""
        content = self.export_graph(timeline_uri=timeline_uri, format=format)
        Path(path).write_text(content, encoding="utf-8")

    def load_from_file(self, path: Path, format: str = "trig") -> None:
        """Load dataset from TriG or Turtle file."""
        self.dataset.parse(str(path), format=format)
