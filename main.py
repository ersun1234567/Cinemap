"""CSC111 Project 2: Cinemap main runner.

This module provides a simple text-based interface for loading the IMDb-based
graph and exploring recommendations, person similarity, and graph
visualizations.

Module Assumptions:
- User-facing searches and prints use Vertex.item labels.
- Recommendation and visualization calls operate on graph keys.
"""

from data_loader import load_imdb_data
from graph_models import Graph
from recommendation import (
    recommend_movies, recommend_by_people, find_similar_people,
    get_recommendation_explanation
)
from visualization import visualize_graph, visualize_recommendations


def _normalize_text(text: str) -> str:
    """Return normalized user text for consistent matching.

    Normalization trims surrounding whitespace, collapses inner whitespace,
    and lowercases the string.

    >>> _normalize_text('  Tom   Hanks ')
    'tom hanks'
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
    """Return a normalized/canonical genre token.

    Supports common user variants like "science fiction", "sci fi", and
    "rom-com".

    >>> _normalize_genre('Sci Fi')
    'sci-fi'
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


def _split_csv_input(text: str, is_genre: bool = False) -> list[str]:
    """Split a comma-separated input line and normalize each non-empty token.

    If is_genre is True, genre aliases are applied during normalization.
    Otherwise, standard text normalization is applied to each token.

    Returns a list of non-empty, normalized tokens.

    >>> _split_csv_input('Tom Hanks,  Emma Stone')
    ['tom hanks', 'emma stone']
    >>> _split_csv_input('Sci Fi, rom-com', is_genre=True)
    ['sci-fi', 'romance']
    """
    result = []
    for value in text.split(','):
        token = _normalize_genre(value) if is_genre else _normalize_text(value)
        if token:
            result.append(token)
    return result


def main(min_year: int = 2000,
         min_votes: int = 1000,
         max_movies: int = 200,
         max_people: int = 500,
         min_movies_per_person: int = 3) -> None:
    """Run the Cinemap command-line interface.

    The parameters control dataset filtering and graph size before user
    interaction begins.

    Preconditions:
    - min_year >= 0
    - min_votes >= 0
    - max_movies > 0
    - max_people > 0
    - min_movies_per_person >= 0
    """
    print("-" * 50)
    print("Cinemap Movie Discovery Tool")
    print("-" * 50)

    print("loading data")
    graph = load_imdb_data(min_year, min_votes, max_movies, max_people, min_movies_per_person)

    print(f"\nGraph has {graph.num_vertices()} nodes and {graph.num_edges()} edges")

    while True:
        print("\n" + "-" * 30)
        print("Menu:")
        print("1. Movie recommendations")
        print("2. Search by favorite people")
        print("3. Find similar people")
        print("4. View full graph")
        print("5. Exit")

        choice = input("Enter choice (1-5): ")

        if choice == '1':
            _recommendation_mode(graph)
        elif choice == '2':
            _people_mode(graph)
        elif choice == '3':
            _similar_people_mode(graph)
        elif choice == '4':
            _visualization_mode(graph)
        elif choice == '5':
            print("bye bye")
            break
        else:
            print("invalid")


def _recommendation_mode(graph: Graph) -> None:
    """Handle recommendation-by-seed-movie interaction for the user.

    The user searches for a movie title, selects a match, and receives scored
    recommendations with short explanations.
    """
    movies = graph.get_all_vertices(kind='movie')
    if not movies:
        print("no movies in graph")
        return

    print("\nEnter part of a movie title:")
    search = _normalize_text(input("> "))

    matches = []
    for m in movies:
        label = str(graph.get_vertex(m).item)
        if search in _normalize_text(label):
            matches.append(m)

    if not matches:
        print("No matches found")
        return

    if len(matches) > 1:
        print("\nMultiple matches:")
        index = 1
        for m in matches[:10]:
            print(f"{index}. {graph.get_vertex(m).item}")
            index = index + 1

        selection = input("Select number: ")
        if selection.isdigit():
            idx = int(selection) - 1
            if idx < 0 or idx >= len(matches):
                print("Invalid selection")
                return
            selected = matches[idx]
        else:
            print("Invalid input")
            return
    else:
        selected = matches[0]

    print(f"Finding recommendations for: {graph.get_vertex(selected).item}")
    recs = recommend_movies(graph, selected, limit=10)

    if not recs:
        print("No recommendations found")
        return

    print("\nRecommendations:")
    index = 1
    for movie, score in recs:
        vertex = graph.get_vertex(movie)
        year = vertex.attributes.get('year', 'N/A')
        rating = vertex.attributes.get('rating', 'N/A')
        print(f"{index}. {vertex.item} ({year}) - {rating}* (score: {score:.1f})")
        index = index + 1

        exp = get_recommendation_explanation(graph, selected, movie)
        reasons = []
        if exp['actors']:
            reasons.append(f"{len(exp['actors'])} actors")
        if exp['directors']:
            reasons.append(f"{len(exp['directors'])} directors")
        if exp['writers']:
            reasons.append(f"{len(exp['writers'])} writers")
        if exp['genres']:
            reasons.append(f"{len(exp['genres'])} genres")
        if reasons:
            print(f"   Shared: {', '.join(reasons)}")

    viz = input("\nShow visualization? (y/n): ").lower()
    if viz == 'y':
        visualize_recommendations(graph, selected, recs)


def _people_mode(graph: Graph) -> None:
    """Handle recommendation-by-favorite-people interaction.

    The user provides favorite actors, directors, writers, and genres, then the
    program computes matching movie recommendations.
    """
    print("\nEnter favorite actors (comma-separated names, e.g., Tom Hanks, Emma Stone):")
    actors_input = input("> ")
    actors = _split_csv_input(actors_input)

    print("Enter favorite directors (comma-separated names, or press Enter to skip):")
    directors_input = input("> ")
    directors = _split_csv_input(directors_input)

    print("Enter favorite writers (comma-separated names, or press Enter to skip):")
    writers_input = input("> ")
    writers = _split_csv_input(writers_input)

    print("Enter favorite genres (comma-separated, e.g., drama, comedy, sci-fi, thriller):")
    print("Tip: sci fi / science fiction / Sci-Fi are all accepted.")
    genres_input = input("> ")
    genres = _split_csv_input(genres_input, is_genre=True)

    if not (actors or directors or writers or genres):
        print("No preferences entered")
        return

    recs = recommend_by_people(graph, actors, directors, writers, genres, limit=10)

    if not recs:
        print("No recommendations found")
        return

    print("\nRecommendations:")
    index = 1
    for movie, score in recs:
        vertex = graph.get_vertex(movie)
        year = vertex.attributes.get('year', 'N/A')
        rating = vertex.attributes.get('rating', 'N/A')
        print(f"{index}. {vertex.item} ({year}) - {rating}* (score: {score:.1f})")
        index = index + 1


def _similar_people_mode(graph: Graph) -> None:
    """Handle person-similarity lookup interaction.

    The user searches for a person, selects one match, and receives a ranked
    list of similar people based on shared movie participation.
    """
    people = graph.get_all_vertices(kind='person')
    if not people:
        print("No people in graph")
        return

    print("\nEnter part of a person's name:")
    search = _normalize_person_text(input("> "))

    matches = []
    for p in people:
        label = str(graph.get_vertex(p).item)
        if search in _normalize_person_text(label):
            matches.append(p)

    if not matches:
        print("No matches found")
        return

    if len(matches) > 1:
        print("\nMultiple matches:")
        index = 1
        for m in matches[:10]:
            print(f"{index}. {graph.get_vertex(m).item}")
            index = index + 1

        selection = input("Select number: ")
        if selection.isdigit():
            idx = int(selection) - 1
            if idx < 0 or idx >= len(matches):
                print("Invalid selection")
                return
            selected = matches[idx]
        else:
            print("Invalid input")
            return
    else:
        selected = matches[0]

    vertex = graph.get_vertex(selected)
    print(f"\n{vertex.item} ({vertex.subkind})")

    similar = find_similar_people(graph, selected, limit=10)

    if not similar:
        print("No similar people found")
        return

    print("\nSimilar people:")
    index = 1
    for person, score in similar:
        p_vertex = graph.get_vertex(person)
        print(f"{index}. {p_vertex.item} ({p_vertex.subkind}) - similarity: {score:.3f}")
        index = index + 1


def _visualization_mode(graph: Graph) -> None:
    """Handle visualization-related interaction options.

    The user can open either a full-graph view or a smaller neighborhood view
    around a chosen movie or person.
    """

    print("Generating visualization...")
    visualize_graph(graph, max_vertices=300)



if __name__ == '__main__':
    main(min_year=2000, min_votes=1000, max_movies=200, max_people=1000, min_movies_per_person=3)
