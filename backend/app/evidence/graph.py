"""
SVA Evidence Graph
==================

In-memory graph structure representing evidence relationships.
"""

from dataclasses import dataclass, field


@dataclass
class EvidenceNode:
    node_id: str
    node_type: str   # "requirement" | "contract" | "target" | "entity" | "evidence" | "result"
    label: str


@dataclass
class EvidenceEdge:
    from_id: str
    to_id: str
    relationship: str   # e.g. "HAS_CONTRACT", "HAS_TARGET", "HAS_EVIDENCE", "MAPS_TO"


class EvidenceGraph:
    """
    In-memory directed graph of evidence relationships.

    Requirement → Contract → Target → [CodeEntity] → Evidence → Result
    """

    def __init__(self) -> None:
        self.nodes: dict[str, EvidenceNode] = {}
        self.edges: list[EvidenceEdge] = []

    def add_node(self, node: EvidenceNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: EvidenceEdge) -> None:
        self.edges.append(edge)

    def neighbors(self, node_id: str) -> list[EvidenceNode]:
        return [
            self.nodes[e.to_id]
            for e in self.edges
            if e.from_id == node_id and e.to_id in self.nodes
        ]

    def find_evidence_for_contract(self, contract_id: str) -> list[str]:
        """Return evidence node IDs reachable from a contract node."""
        result = []
        for edge in self.edges:
            if edge.from_id == contract_id and edge.relationship == "HAS_EVIDENCE":
                result.append(edge.to_id)
        return result
