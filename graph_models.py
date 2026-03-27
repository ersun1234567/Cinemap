"""CSC111 Project 2: Graph data model.

This module defines the vertex and graph classes used to represent movies,
people, and their relationships, along with similarity computations.

Module Assumptions:
- Movie vertices use kind == 'movie'.
- Person vertices use kind == 'person'.
- Graph keys are unique identifiers (for example, tconst/nconst).
- Vertex.item is a display label and may be non-unique.
"""

from __future__ import annotations
from typing import Any, Optional
import networkx as nx


class Vertex:
    """A vertex in the movie-people graph.

    Each vertex stores an item label, a kind/subkind classification, arbitrary
    attributes, and weighted edges to neighbouring vertices.

    Representation Invariants:
    - self.kind in {'movie', 'person'}
    - self.subkind is None or self.subkind in {'actor', 'director', 'writer'}
    - all(weight >= 0 for weight in self.neighbours.values())

    >>> v = Vertex('The Matrix', 'movie')
    >>> v.degree()
    0
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
        """Add or update an edge from this vertex to other with given weight.

        Preconditions:
        - weight >= 0
        """
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
        self_actors = set()
        other_actors = set()
        self_directors = set()
        other_directors = set()
        self_writers = set()
        other_writers = set()

        for n in self.neighbours:
            if n.subkind == 'actor':
                self_actors.add(n)
            elif n.subkind == 'director':
                self_directors.add(n)
            elif n.subkind == 'writer':
                self_writers.add(n)

        for n in other.neighbours:
            if n.subkind == 'actor':
                other_actors.add(n)
            elif n.subkind == 'director':
                other_directors.add(n)
            elif n.subkind == 'writer':
                other_writers.add(n)

        shared_actors = len(self_actors.intersection(other_actors))
        shared_directors = len(self_directors.intersection(other_directors))
        shared_writers = len(self_writers.intersection(other_writers))

        shared_genres = 0
        if 'genres' in self.attributes and 'genres' in other.attributes:
            self_genres = [g.strip().lower() for g in self.attributes['genres'].split(',')]
            other_genres = [g.strip().lower() for g in other.attributes['genres'].split(',')]
            for g in self_genres:
                if g in other_genres and g != '':
                    shared_genres += 1

        return (shared_actors * 1.0 + shared_directors * 4.0 +
                shared_writers * 6.0 + shared_genres * 3.0)

    def _person_similarity(self, other: Vertex) -> float:
        """Return person-to-person similarity using Jaccard movie overlap."""
        self_movies = set()
        other_movies = set()

        for n in self.neighbours:
            if n.kind == 'movie':
                self_movies.add(n)

        for n in other.neighbours:
            if n.kind == 'movie':
                other_movies.add(n)

        if len(self_movies) == 0 or len(other_movies) == 0:
            return 0.0

        intersection = len(self_movies.intersection(other_movies))
        union = len(self_movies) + len(other_movies) - intersection

        if union == 0:
            return 0.0
        return intersection / union


class Graph:
    """An undirected graph of movie and person vertices.

    Vertices are stored by a unique key. The Vertex.item field can be a
    display label (e.g., movie title or person name) and is not required to be
    unique.

    Representation Invariants:
    - all(self._vertices[k].kind in {'movie', 'person'} for k in self._vertices)
    - all(weight >= 0 for v in self._vertices.values() for weight in v.neighbours.values())

    >>> g = Graph()
    >>> g.add_vertex(item='Same Title', kind='movie', key='tt1')
    >>> g.add_vertex(item='Same Title', kind='movie', key='tt2')
    >>> g.num_vertices()
    2
    """
    _vertices: dict[Any, Vertex]

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._vertices = {}

    def add_vertex(self, item: Any, kind: str, subkind: Optional[str] = None,
                   attributes: Optional[dict[str, Any]] = None,
                   key: Optional[Any] = None) -> None:
        """Add a vertex if it does not already exist.

        If key is None, item is used as the vertex key.
        """
        vertex_key = item if key is None else key
        if vertex_key not in self._vertices:
            self._vertices[vertex_key] = Vertex(item, kind, subkind, attributes)

    def add_edge(self, item1: Any, item2: Any, weight: float = 1.0) -> None:
        """Add an undirected edge between two existing vertices.

        Raise ValueError if either endpoint is missing.

        Preconditions:
        - weight >= 0
        """
        if item1 not in self._vertices or item2 not in self._vertices:
            raise ValueError("vertex not found")

        v1 = self._vertices[item1]
        v2 = self._vertices[item2]

        v1.add_neighbour(v2, weight)
        v2.add_neighbour(v1, weight)

    def get_vertex(self, item: Any) -> Vertex:
        """Return the vertex associated with item.

        Preconditions:
        - item in self._vertices
        """
        return self._vertices[item]

    def get_all_vertices(self, kind: str = '', subkind: str = '') -> list[Any]:
        """Return all vertex keys matching optional kind/subkind filters.

        >>> g = Graph()
        >>> g.add_vertex(item='A', kind='movie', key='tt1')
        >>> g.add_vertex(item='B', kind='person', subkind='actor', key='nm1')
        >>> g.get_all_vertices(kind='movie')
        ['tt1']
        """
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
        """Return neighbour display labels of item, optionally by neighbour kind.

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

        Nodes in the returned NetworkX graph are the internal graph keys.
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


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': ['networkx'],
        'allowed-io': [],
        'max-line-length': 120
    })
