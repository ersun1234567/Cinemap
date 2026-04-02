"""CSC111 Project 2: Recommendation and explanation algorithms.

This module computes movie recommendations from seed movies or user
preferences, and computes person similarity and recommendation explanations.

Module Assumptions:
- Graph movie/person keys are unique stable identifiers.
- Vertex.item is used as the display label for user-facing output.
- Tie-breaking for ranked lists is deterministic.
"""

from __future__ import annotations
from typing import Optional, List, Tuple, Dict
from graph_models import Graph


def _normalize_text(text: str) -> str:
    """Return normalized text for matching names and labels.

    >>> _normalize_text('  Emma   Stone ')
    'emma stone'
    """
    return ' '.join(text.strip().lower().split())


def _normalize_person_text(text: str) -> str:
    """Return a punctuation-insensitive normalized person name.

    >>> _normalize_person_text('Robert Downey, Jr.')
    'robert downey jr'
    """
    simplified = []
    for ch in text.lower():
        if ch.isalnum() or ch.isspace():
            simplified.append(ch)
        else:
            simplified.append(' ')
    return ' '.join(''.join(simplified).split())


def _normalize_genre(genre: str) -> str:
    """Return normalized/canonical genre token.

    >>> _normalize_genre('Science Fiction')
    'sci-fi'
    >>> _normalize_genre('rom-com')
    'romance'
    """
    g = _normalize_text(genre)
    aliases = {
        'science fiction': 'sci-fi',
        'sci fi': 'sci-fi',
        'scifi': 'sci-fi',
        'romcom': 'romance',
        'rom-com': 'romance'
    }
    return aliases.get(g, g)


def _display_label(graph: Graph, item_key: str) -> str:
    """Return the display label for a vertex key.

    Preconditions:
    - item_key is a vertex key in graph
    """
    return str(graph.get_vertex(item_key).item)


def recommend_movies(graph: Graph,
                     seed_movie: str,
                     limit: int = 10) -> List[Tuple[str, float]]:
    """Return top movie recommendations similar to seed_movie.

    Recommendations are ranked by descending similarity score, then by movie
    title as a tie-breaker.

    Preconditions:
    - seed_movie is in graph
    - limit >= 0

        Return Value:
        - list[(movie_key, similarity_score)] sorted by score descending,
            then display label ascending, then key ascending.
    """
    seed_vertex = graph.get_vertex(seed_movie)

    all_movies = graph.get_all_vertices(kind='movie')
    recommendations = []

    for movie in all_movies:
        if movie == seed_movie:
            continue

        movie_vertex = graph.get_vertex(movie)
        similarity = seed_vertex.similarity_score(movie_vertex)

        if similarity > 0:
            recommendations.append((movie, similarity))

    recommendations.sort(key=lambda pair: (-pair[1], _display_label(graph, pair[0]), pair[0]))

    result = []
    for i in range(min(limit, len(recommendations))):
        result.append(recommendations[i])
    return result


def recommend_by_people(graph: Graph,
                        favorite_actors: Optional[List[str]] = None,
                        favorite_directors: Optional[List[str]] = None,
                        favorite_writers: Optional[List[str]] = None,
                        preferred_genres: Optional[List[str]] = None,
                        limit: int = 10) -> List[Tuple[str, float]]:
    """Return movie recommendations based on favorite people and genres.

    Scores are accumulated using weighted matches for actors, directors,
    writers, and genres.

    Preconditions:
    - limit >= 0

        Return Value:
        - list[(movie_key, score)] sorted by score descending,
            then display label ascending, then key ascending.
    """
    if favorite_actors is None:
        favorite_actors = []
    if favorite_directors is None:
        favorite_directors = []
    if favorite_writers is None:
        favorite_writers = []
    if preferred_genres is None:
        preferred_genres = []

    favorite_actor_set = {_normalize_person_text(name) for name in favorite_actors if name.strip() != ''}
    favorite_director_set = {_normalize_person_text(name) for name in favorite_directors if name.strip() != ''}
    favorite_writer_set = {_normalize_person_text(name) for name in favorite_writers if name.strip() != ''}
    preferred_genre_set = {_normalize_genre(genre) for genre in preferred_genres if genre.strip() != ''}

    all_movies = graph.get_all_vertices(kind='movie')
    movie_scores = []

    for movie in all_movies:
        vertex = graph.get_vertex(movie)
        score = 0.0

        movie_actors = []
        movie_directors = []
        movie_writers = []

        for n in vertex.neighbours:
            if n.kind == 'person':
                if n.subkind == 'actor':
                    movie_actors.append(_normalize_person_text(n.item))
                elif n.subkind == 'director':
                    movie_directors.append(_normalize_person_text(n.item))
                elif n.subkind == 'writer':
                    movie_writers.append(_normalize_person_text(n.item))

        for actor in favorite_actor_set:
            if actor in movie_actors:
                score += 1.0

        for director in favorite_director_set:
            if director in movie_directors:
                score += 4.0

        for writer in favorite_writer_set:
            if writer in movie_writers:
                score += 6.0

        if 'genres' in vertex.attributes:
            movie_genres = {_normalize_genre(g) for g in vertex.attributes['genres'].split(',') if g.strip() != ''}
            for genre in preferred_genre_set:
                if genre in movie_genres:
                    score += 3.0

        if score > 0:
            movie_scores.append((movie, score))

    movie_scores.sort(key=lambda pair: (-pair[1], _display_label(graph, pair[0]), pair[0]))

    result = []
    for i in range(min(limit, len(movie_scores))):
        result.append(movie_scores[i])
    return result


def find_similar_people(graph: Graph,
                        person_name: str,
                        limit: int = 5) -> List[Tuple[str, float]]:
    """Return people similar to person_name by shared movie overlap.

    Similarity uses a Jaccard-style ratio over movies connected to each person.

    Preconditions:
    - person_name is in graph
    - limit >= 0

        Return Value:
        - list[(person_key, similarity)] sorted by score descending,
            then display label ascending, then key ascending.
    """
    person = graph.get_vertex(person_name)

    all_people = graph.get_all_vertices(kind='person')
    similar_people = []

    person_movies = set()
    for n in person.neighbours:
        if n.kind == 'movie':
            person_movies.add(n)

    if len(person_movies) == 0:
        return []

    for other_name in all_people:
        if other_name == person_name:
            continue

        other = graph.get_vertex(other_name)
        other_movies = set()
        for n in other.neighbours:
            if n.kind == 'movie':
                other_movies.add(n)

        if len(other_movies) > 0:
            intersection = len(person_movies.intersection(other_movies))

            union = len(person_movies) + len(other_movies) - intersection
            similarity = intersection / union

            if similarity > 0:
                similar_people.append((other_name, similarity))

    similar_people.sort(key=lambda pair: (-pair[1], _display_label(graph, pair[0]), pair[0]))

    result = []
    for i in range(min(limit, len(similar_people))):
        result.append(similar_people[i])
    return result


def get_recommendation_explanation(graph: Graph,
                                  seed_movie: str,
                                  recommended_movie: str) -> Dict[str, List[str]]:
    """Return shared actors/directors/writers/genres for two movies.

    The returned dictionary has keys 'actors', 'directors', 'writers', and
    'genres', each mapped to a list of shared values.

    Preconditions:
    - seed_movie is in graph
    - recommended_movie is in graph

    Return Value:
    - Dictionary with keys 'actors', 'directors', 'writers', 'genres'.
    """
    seed = graph.get_vertex(seed_movie)
    rec = graph.get_vertex(recommended_movie)

    explanation = {
        'actors': [],
        'directors': [],
        'writers': [],
        'genres': []
    }

    seed_actors = []
    seed_directors = []
    seed_writers = []
    rec_actors = []
    rec_directors = []
    rec_writers = []

    for n in seed.neighbours:
        if n.kind == 'person':
            if n.subkind == 'actor':
                seed_actors.append(n.item)
            elif n.subkind == 'director':
                seed_directors.append(n.item)
            elif n.subkind == 'writer':
                seed_writers.append(n.item)

    for n in rec.neighbours:
        if n.kind == 'person':
            if n.subkind == 'actor':
                rec_actors.append(n.item)
            elif n.subkind == 'director':
                rec_directors.append(n.item)
            elif n.subkind == 'writer':
                rec_writers.append(n.item)

    for a in seed_actors:
        actor_found = False
        for ra in rec_actors:
            if a == ra:
                actor_found = True
                break
        if actor_found:
            explanation['actors'].append(a)

    for d in seed_directors:
        director_found = False
        for rd in rec_directors:
            if d == rd:
                director_found = True
                break
        if director_found:
            explanation['directors'].append(d)

    for w in seed_writers:
        writer_found = False
        for rw in rec_writers:
            if w == rw:
                writer_found = True
                break
        if writer_found:
            explanation['writers'].append(w)

    if 'genres' in seed.attributes and 'genres' in rec.attributes:
        seed_genres = [g.strip().lower() for g in seed.attributes['genres'].split(',')]
        rec_genres = [g.strip().lower() for g in rec.attributes['genres'].split(',')]
        for g in seed_genres:
            genre_found = False
            for rg in rec_genres:
                if g == rg and g != '':
                    genre_found = True
                    break
            if genre_found:
                explanation['genres'].append(g)

    return explanation


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': [],
        'max-line-length': 120
    })
