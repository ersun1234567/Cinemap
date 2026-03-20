"""CSC111 Project 2: Graph data model.

This module defines the vertex and graph classes used to represent movies,
people, and their relationships, along with similarity computations.
"""

from __future__ import annotations
from typing import Any, Optional
import networkx as nx


class Vertex:
    """A vertex in the movie-people graph.

    Each vertex stores an item label, a kind/subkind classification, arbitrary
    attributes, and weighted edges to neighbouring vertices.
    """
    item: Any
    kind: str
    subkind: Optional[str]
    attributes: dict[str, Any]
    neighbours: dict[Vertex, float]

    def __init__(self, item: Any, kind: str, subkind: Optional[str] = None,
                 attributes: Optional[dict[str, Any]] = None) -> None:
        """Initialize a new vertex with metadata and no neighbours."""
        self.item = item
        self.kind = kind
        self.subkind = subkind
        if attributes is not None:
            self.attributes = attributes
        else:
            self.attributes = {}
        self.neighbours = {}

    def degree(self) -> int:
        """Return the number of neighbours connected to this vertex."""
        return len(self.neighbours)

    def add_neighbour(self, other: Vertex, weight: float = 1.0) -> None:
        """Add or update an edge from this vertex to other with given weight."""
        self.neighbours[other] = weight

    def similarity_score(self, other: Vertex) -> float:
        """Return a similarity score between this vertex and other.

        Vertices of different kinds have similarity 0. Movies are compared by
        shared people and genres; people are compared by shared movies.
        """
        if self.kind != other.kind:
            return 0.0

        if self.kind == 'movie':
            return self._movie_similarity(other)
        else:
            return self._person_similarity(other)

    def _movie_similarity(self, other: Vertex) -> float:
        """Return movie-to-movie similarity using shared contributors/genres."""
        self_actors = []
        other_actors = []
        self_directors = []
        other_directors = []
        self_writers = []
        other_writers = []

        for n in self.neighbours:
            if n.subkind == 'actor':
                self_actors.append(n.item)
            elif n.subkind == 'director':
                self_directors.append(n.item)
            elif n.subkind == 'writer':
                self_writers.append(n.item)

        for n in other.neighbours:
            if n.subkind == 'actor':
                other_actors.append(n.item)
            elif n.subkind == 'director':
                other_directors.append(n.item)
            elif n.subkind == 'writer':
                other_writers.append(n.item)

        shared_actors = 0
        for a in self_actors:
            if a in other_actors:
                shared_actors += 1

        shared_directors = 0
        for d in self_directors:
            if d in other_directors:
                shared_directors += 1

        shared_writers = 0
        for w in self_writers:
            if w in other_writers:
                shared_writers += 1

        shared_genres = 0
        if 'genres' in self.attributes and 'genres' in other.attributes:
            self_genres = self.attributes['genres'].split(',')
            other_genres = other.attributes['genres'].split(',')
            for g in self_genres:
                if g in other_genres and g != '':
                    shared_genres += 1

        return (shared_actors * 1.0 + shared_directors * 4.0 +
                shared_writers * 6.0 + shared_genres * 3.0)

    def _person_similarity(self, other: Vertex) -> float:
        """Return person-to-person similarity using Jaccard movie overlap."""
        self_movies = []
        other_movies = []

        for n in self.neighbours:
            if n.kind == 'movie':
                self_movies.append(n.item)

        for n in other.neighbours:
            if n.kind == 'movie':
                other_movies.append(n.item)

        if len(self_movies) == 0 or len(other_movies) == 0:
            return 0.0

        intersection = 0
        for m in self_movies:
            if m in other_movies:
                intersection += 1

        union = len(self_movies) + len(other_movies) - intersection

        if union == 0:
            return 0.0
        return intersection / union


class Graph:
    """An undirected graph of movie and person vertices."""
    _vertices: dict[Any, Vertex]

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._vertices = {}

    def add_vertex(self, item: Any, kind: str, subkind: Optional[str] = None,
                   attributes: Optional[dict[str, Any]] = None) -> None:
        """Add a vertex identified by item if it does not already exist."""
        if item not in self._vertices:
            self._vertices[item] = Vertex(item, kind, subkind, attributes)

    def add_edge(self, item1: Any, item2: Any, weight: float = 1.0) -> None:
        """Add an undirected edge between two existing vertices.

        Raise ValueError if either endpoint is missing.
        """
        if item1 not in self._vertices or item2 not in self._vertices:
            raise ValueError("vertex not found")

        v1 = self._vertices[item1]
        v2 = self._vertices[item2]

        v1.add_neighbour(v2, weight)
        v2.add_neighbour(v1, weight)

    def get_vertex(self, item: Any) -> Vertex:
        """Return the vertex associated with item."""
        return self._vertices[item]

    def get_all_vertices(self, kind: str = '', subkind: str = '') -> list[Any]:
        """Return all vertex items matching optional kind/subkind filters."""
        result = []
        for item, vertex in self._vertices.items():
            kind_match = True
            subkind_match = True

            if kind:
                if vertex.kind == kind:
                    kind_match = True
                else:
                    kind_match = False

            if subkind:
                if vertex.subkind == subkind:
                    subkind_match = True
                else:
                    subkind_match = False

            if kind_match and subkind_match:
                result.append(item)
        return result

    def get_neighbours(self, item: Any, kind: str = '') -> list[Any]:
        """Return neighbours of item, optionally filtered by neighbour kind.

        Raise ValueError if item is not a vertex in this graph.
        """
        if item not in self._vertices:
            raise ValueError("vertex not found")

        vertex = self._vertices[item]
        result = []
        for n in vertex.neighbours:
            if kind == '':
                result.append(n.item)
            elif n.kind == kind:
                result.append(n.item)
        return result

    def num_vertices(self) -> int:
        """Return the number of vertices in this graph."""
        return len(self._vertices)

    def num_edges(self) -> int:
        """Return the number of undirected edges in this graph."""
        total = 0
        for v in self._vertices.values():
            total += v.degree()
        return total // 2

    def to_networkx(self, max_vertices: int = 5000) -> nx.Graph:
        """Return a NetworkX graph view of up to max_vertices vertices.

        Node attributes are copied from stored vertex metadata.
        """
        graph_nx = nx.Graph()

        count = 0
        for item, vertex in self._vertices.items():
            if count >= max_vertices:
                break

            graph_nx.add_node(item)

            graph_nx.nodes[item]['kind'] = vertex.kind
            graph_nx.nodes[item]['subkind'] = vertex.subkind
            for key, value in vertex.attributes.items():
                graph_nx.nodes[item][key] = value

            count += 1

            for neighbour in vertex.neighbours:
                if neighbour.item in graph_nx.nodes:
                    graph_nx.add_edge(item, neighbour.item)

        return graph_nx
