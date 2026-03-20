"""CSC111 Project 2: IMDb data loading utilities.

This module loads and filters IMDb TSV datasets, then constructs a graph of
movie and person vertices with edges representing participation relationships.
"""

import csv
from typing import Optional
from graph_models import Graph


def _open_file(filepath: str):
    """Return an open file handle for filepath.

    This helper centralizes file opening to make I/O calls easier to track.
    """
    return open(filepath)


def load_imdb_data(min_year: int = 2000,
                   min_votes: int = 1000,
                   max_movies: int = 200,
                   max_people: int = 500,
                   min_movies_per_person: int = 3) -> Graph:
    """Load IMDb data files and build a graph of movies and people.

    The graph contains movie vertices and person vertices (actors, directors,
    and writers), with edges connecting people to movies they worked on.

    Preconditions:
    - min_year >= 0
    - min_votes >= 0
    - max_movies > 0
    - max_people > 0
    - min_movies_per_person >= 0
    """
    graph = Graph()

    basics_path = 'data/title.basics.tsv'
    ratings_path = 'data/title.ratings.tsv'
    name_path = 'data/name.basics.tsv'
    principals_path = 'data/title.principals.tsv'

    print("loading movies")
    movies = _load_movies(basics_path, min_year, max_movies)
    print(f"loaded {len(movies)} movies")

    if len(movies) == 0:
        print("no movies found")
        return graph

    print("loading ratings")
    movies_with_ratings = _filter_by_votes(ratings_path, movies, min_votes)
    print(f"{len(movies_with_ratings)} with enough votes")

    print("adding movies to graph...")
    movie_count = 0
    movie_by_tconst = {}
    movie_titles = {}

    for tconst, movie_data in movies_with_ratings.items():
        if movie_count >= max_movies:
            break

        rating = movie_data.get('averageRating', 0.0)
        votes = movie_data.get('numVotes', 0)
        movie_title = movie_data['primaryTitle']
        movie_titles[tconst] = movie_title

        graph.add_vertex(
            item=movie_title,
            kind='movie',
            attributes={
                'tconst': tconst,
                'year': movie_data['startYear'],
                'genres': movie_data['genres'],
                'rating': rating,
                'votes': votes
            }
        )
        movie_by_tconst[tconst] = movie_title
        movie_count += 1

    print(f"added {movie_count} movies to graph")

    print("loading people data")
    all_people = _load_people(name_path)
    print(f"loaded {len(all_people)} people from names file")

    person_movie_count = {}
    connections = []

    with _open_file(principals_path) as f:
        lines = f.readlines()
        header = lines[0].split('\t')
        tconst_idx = header.index('tconst')
        nconst_idx = header.index('nconst')
        category_idx = header.index('category')

        for line in lines[1:]:
            row = line.split('\t')
            if len(row) <= max(tconst_idx, nconst_idx, category_idx):
                continue

            tconst = row[tconst_idx]
            nconst = row[nconst_idx]
            category = row[category_idx]

            if tconst not in movie_titles:
                continue
            if category not in ['actor', 'actress', 'director', 'writer']:
                continue

            if nconst not in person_movie_count:
                person_movie_count[nconst] = 0
            person_movie_count[nconst] += 1
            connections.append((nconst, tconst, category))

    print(f"found {len(person_movie_count)} people with connections to our movies")

    popular_nconsts = set()
    for nconst, count in person_movie_count.items():
        if count >= min_movies_per_person:
            popular_nconsts.add(nconst)

    print(f"{len(popular_nconsts)} people have worked on at least {min_movies_per_person} movies")

    print("adding popular people to graph...")
    person_count = 0
    person_by_nconst = {}

    for nconst in popular_nconsts:
        if person_count >= max_people:
            break
        if nconst not in all_people:
            continue

        person_data = all_people[nconst]
        professions = person_data.get('primaryProfession', '').split(',')

        for prof in ['actor', 'actress', 'director', 'writer']:
            if prof in professions:
                if prof in ['actor', 'actress']:
                    subkind = 'actor'
                else:
                    subkind = prof
                person_name = person_data['primaryName']
                graph.add_vertex(
                    item=person_name,
                    kind='person',
                    subkind=subkind,
                    attributes={'nconst': nconst}
                )
                person_by_nconst[nconst] = person_name
                person_count += 1
                break

    print(f"added {person_count} popular people to graph")
    print("adding edges")
    edge_count = 0

    for nconst, tconst, category in connections:
        if edge_count >= 10000:
            break
        if nconst in person_by_nconst and tconst in movie_titles:
            graph.add_edge(person_by_nconst[nconst], movie_titles[tconst])
            edge_count += 1

    print(f"added {edge_count} edges")
    print(f"graph has {graph.num_vertices()} vertices and {graph.num_edges()} edges")
    return graph


def _load_movies(tsv_file: str, min_year: int, max_movies: Optional[int]) -> dict:
    """Return movie records from tsv_file filtered by year.

    The result maps each movie tconst to a dictionary containing title, start
    year, and genres.

    Preconditions:
    - min_year >= 0
    - max_movies is None or max_movies > 0
    """
    movies = {}

    with _open_file(tsv_file) as f:
        lines = f.readlines()
        header = lines[0].split('\t')

        # Strip newline characters from header
        header = [h.strip() for h in header]

        # Check for possible column names
        tconst_idx = header.index('tconst')
        title_type_idx = header.index('titleType')
        primary_title_idx = header.index('primaryTitle')
        start_year_idx = header.index('startYear')

        # Try different possible names for genres column
        genres_idx = None
        possible_genres_names = ['genres', 'genre']
        for name in possible_genres_names:
            try:
                genres_idx = header.index(name)
                break
            except ValueError:
                continue

        # If no genres column found, use a placeholder
        if genres_idx is None:
            print("Warning: No genres column found in the file")
            genres_idx = -1  # Use -1 to indicate no genres column

        for line in lines[1:]:
            if max_movies is not None:
                if len(movies) >= max_movies * 3:
                    break

            row = line.split('\t')
            if len(row) <= max(tconst_idx, title_type_idx, primary_title_idx, start_year_idx):
                continue

            if row[title_type_idx] != 'movie':
                continue
            if row[start_year_idx] == r'\N':
                continue

            try:
                year = int(row[start_year_idx])
            except ValueError:
                continue

            if year < min_year:
                continue

            # Handle genres if column exists
            if genres_idx != -1 and genres_idx < len(row):
                genres_value = row[genres_idx] if row[genres_idx] != r'\N' else ''
            else:
                genres_value = ''

            movies[row[tconst_idx]] = {
                'primaryTitle': row[primary_title_idx],
                'startYear': year,
                'genres': genres_value
            }

    return movies


def _filter_by_votes(tsv_file: str, movies: dict, min_votes: int) -> dict:
    """Return subset of movies that meet a minimum vote threshold.

    This function augments each returned movie dictionary with average rating
    and vote count fields from the ratings dataset.

    Preconditions:
    - min_votes >= 0
    """
    movies_with_ratings = {}

    with _open_file(tsv_file) as f:
        lines = f.readlines()
        header = lines[0].split('\t')
        header = [h.strip() for h in header]

        tconst_idx = header.index('tconst')

        # Try to find rating and votes columns
        avg_rating_idx = None
        num_votes_idx = None

        possible_rating_names = ['averageRating', 'average_rating', 'rating']
        possible_votes_names = ['numVotes', 'num_votes', 'votes']

        for name in possible_rating_names:
            try:
                avg_rating_idx = header.index(name)
                break
            except ValueError:
                continue

        for name in possible_votes_names:
            try:
                num_votes_idx = header.index(name)
                break
            except ValueError:
                continue

        if avg_rating_idx is None or num_votes_idx is None:
            print("Warning: Could not find rating or votes columns")
            return movies_with_ratings

        for line in lines[1:]:
            row = line.split('\t')
            if len(row) <= max(tconst_idx, avg_rating_idx, num_votes_idx):
                continue

            tconst = row[tconst_idx]
            if tconst in movies:
                if row[num_votes_idx] != r'\N':
                    try:
                        num_votes = int(row[num_votes_idx])
                    except ValueError:
                        num_votes = 0
                else:
                    num_votes = 0

                if num_votes >= min_votes:
                    movie_data = movies[tconst].copy()

                    if row[avg_rating_idx] != r'\N':
                        try:
                            movie_data['averageRating'] = float(row[avg_rating_idx])
                        except ValueError:
                            movie_data['averageRating'] = 0.0
                    else:
                        movie_data['averageRating'] = 0.0

                    movie_data['numVotes'] = num_votes
                    movies_with_ratings[tconst] = movie_data

    return movies_with_ratings


def _load_people(tsv_file: str) -> dict:
    """Return people records parsed from tsv_file.

    The result maps each nconst to a dictionary containing primary name and
    primary profession values.
    """
    people = {}

    with _open_file(tsv_file) as f:
        lines = f.readlines()
        header = lines[0].split('\t')
        header = [h.strip() for h in header]

        nconst_idx = header.index('nconst')
        primary_name_idx = header.index('primaryName')

        # Try to find profession column
        profession_idx = None
        possible_profession_names = ['primaryProfession', 'profession', 'primary_profession']
        for name in possible_profession_names:
            try:
                profession_idx = header.index(name)
                break
            except ValueError:
                continue

        if profession_idx is None:
            print("Warning: No profession column found")
            return people

        for line in lines[1:]:
            row = line.split('\t')
            if len(row) <= max(nconst_idx, primary_name_idx, profession_idx):
                continue

            if row[profession_idx] != r'\N':
                people[row[nconst_idx]] = {
                    'primaryName': row[primary_name_idx],
                    'primaryProfession': row[profession_idx]
                }

    return people
