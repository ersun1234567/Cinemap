from __future__ import annotations
from typing import Any, Optional
import networkx as nx


class Vertex:
    item: Any
    kind: str
    subkind: Optional[str]
    attributes: dict[str, Any]
    neighbours: dict[Vertex, float]

    def __init__(self, item: Any, kind: str, subkind: Optional[str] = None,
                 attributes: Optional[dict[str, Any]] = None) -> None:
        self.item = item
        self.kind = kind
        self.subkind = subkind
        if attributes is not None:
            self.attributes = attributes
        else:
            self.attributes = {}
        self.neighbours = {}

    def degree(self) -> int:
        return len(self.neighbours)

    def add_neighbour(self, other: Vertex, weight: float = 1.0) -> None:
        self.neighbours[other] = weight

    def similarity_score(self, other: Vertex) -> float:
        if self.kind != other.kind:
            return 0.0

        if self.kind == 'movie':
            return self._movie_similarity(other)
        else:
            return self._person_similarity(other)

    def _movie_similarity(self, other: Vertex) -> float:
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
    _vertices: dict[Any, Vertex]

    def __init__(self) -> None:
        self._vertices = {}

    def add_vertex(self, item: Any, kind: str, subkind: Optional[str] = None,
                   attributes: Optional[dict[str, Any]] = None) -> None:
        if item not in self._vertices:
            self._vertices[item] = Vertex(item, kind, subkind, attributes)

    def add_edge(self, item1: Any, item2: Any, weight: float = 1.0) -> None:
        if item1 not in self._vertices or item2 not in self._vertices:
            raise ValueError("vertex not found")

        v1 = self._vertices[item1]
        v2 = self._vertices[item2]

        v1.add_neighbour(v2, weight)
        v2.add_neighbour(v1, weight)

    def get_vertex(self, item: Any) -> Vertex:
        return self._vertices[item]

    def get_all_vertices(self, kind: str = '', subkind: str = '') -> list[Any]:
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
        return len(self._vertices)

    def num_edges(self) -> int:
        total = 0
        for v in self._vertices.values():
            total += v.degree()
        return total // 2

    def to_networkx(self, max_vertices: int = 5000) -> nx.Graph:
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
