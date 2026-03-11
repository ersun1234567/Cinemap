from __future__ import annotations
from typing import Optional, List, Tuple, Dict
from graph_models import Graph


def recommend_movies(graph: Graph,
                     seed_movie: str,
                     limit: int = 10) -> List[Tuple[str, float]]:
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

    for i in range(len(recommendations)):
        for j in range(i + 1, len(recommendations)):
            if recommendations[i][1] < recommendations[j][1]:
                temp_movie = recommendations[i][0]
                temp_score = recommendations[i][1]
                recommendations[i] = (recommendations[j][0], recommendations[j][1])
                recommendations[j] = (temp_movie, temp_score)
            elif recommendations[i][1] == recommendations[j][1]:
                if recommendations[i][0] < recommendations[j][0]:
                    temp_movie = recommendations[i][0]
                    temp_score = recommendations[i][1]
                    recommendations[i] = (recommendations[j][0], recommendations[j][1])
                    recommendations[j] = (temp_movie, temp_score)

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
    if favorite_actors is None:
        favorite_actors = []
    if favorite_directors is None:
        favorite_directors = []
    if favorite_writers is None:
        favorite_writers = []
    if preferred_genres is None:
        preferred_genres = []

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
                    movie_actors.append(n.item)
                elif n.subkind == 'director':
                    movie_directors.append(n.item)
                elif n.subkind == 'writer':
                    movie_writers.append(n.item)

        for actor in favorite_actors:
            actor_found = False
            for ma in movie_actors:
                if actor == ma:
                    actor_found = True
                    break
            if actor_found:
                score += 1.0

        for director in favorite_directors:
            director_found = False
            for md in movie_directors:
                if director == md:
                    director_found = True
                    break
            if director_found:
                score += 4.0

        for writer in favorite_writers:
            writer_found = False
            for mw in movie_writers:
                if writer == mw:
                    writer_found = True
                    break
            if writer_found:
                score += 6.0

        if 'genres' in vertex.attributes:
            movie_genres = vertex.attributes['genres'].split(',')
            for genre in preferred_genres:
                genre_found = False
                for mg in movie_genres:
                    if genre == mg:
                        genre_found = True
                        break
                if genre_found:
                    score += 3.0

        if score > 0:
            movie_scores.append((movie, score))

    for i in range(len(movie_scores)):
        for j in range(i + 1, len(movie_scores)):
            if movie_scores[i][1] < movie_scores[j][1]:
                temp_movie = movie_scores[i][0]
                temp_score = movie_scores[i][1]
                movie_scores[i] = (movie_scores[j][0], movie_scores[j][1])
                movie_scores[j] = (temp_movie, temp_score)

    result = []
    for i in range(min(limit, len(movie_scores))):
        result.append(movie_scores[i])
    return result


def find_similar_people(graph: Graph,
                        person_name: str,
                        limit: int = 5) -> List[Tuple[str, float]]:
    person = graph.get_vertex(person_name)

    all_people = graph.get_all_vertices(kind='person')
    similar_people = []

    person_movies = []
    for n in person.neighbours:
        if n.kind == 'movie':
            person_movies.append(n.item)

    if len(person_movies) == 0:
        return []

    for other_name in all_people:
        if other_name == person_name:
            continue

        other = graph.get_vertex(other_name)
        other_movies = []
        for n in other.neighbours:
            if n.kind == 'movie':
                other_movies.append(n.item)

        if len(other_movies) > 0:
            intersection = 0
            for m in person_movies:
                movie_found = False
                for om in other_movies:
                    if m == om:
                        movie_found = True
                        break
                if movie_found:
                    intersection += 1

            union = len(person_movies) + len(other_movies) - intersection
            similarity = intersection / union

            if similarity > 0:
                similar_people.append((other_name, similarity))

    for i in range(len(similar_people)):
        for j in range(i + 1, len(similar_people)):
            if similar_people[i][1] < similar_people[j][1]:
                temp_person = similar_people[i][0]
                temp_score = similar_people[i][1]
                similar_people[i] = (similar_people[j][0], similar_people[j][1])
                similar_people[j] = (temp_person, temp_score)

    result = []
    for i in range(min(limit, len(similar_people))):
        result.append(similar_people[i])
    return result


def get_recommendation_explanation(graph: Graph,
                                  seed_movie: str,
                                  recommended_movie: str) -> Dict[str, List[str]]:
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
        seed_genres = seed.attributes['genres'].split(',')
        rec_genres = rec.attributes['genres'].split(',')
        for g in seed_genres:
            genre_found = False
            for rg in rec_genres:
                if g == rg and g != '':
                    genre_found = True
                    break
            if genre_found:
                explanation['genres'].append(g)

    return explanation
