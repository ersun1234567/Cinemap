from data_loader import load_imdb_data
from graph_models import Graph
from recommendation import (
    recommend_movies, recommend_by_people, find_similar_people,
    get_recommendation_explanation
)
from visualization import visualize_graph, visualize_recommendations


def main(min_year: int = 2000,
         min_votes: int = 1000,
         max_movies: int = 200,
         max_people: int = 500,
         min_movies_per_person: int = 3) -> None:
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
        print("4. View graph")
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
    movies = graph.get_all_vertices(kind='movie')
    if not movies:
        print("no movies in graph")
        return

    print("\nEnter part of a movie title:")
    search = input("> ").lower()

    matches = []
    for m in movies:
        if search in m.lower():
            matches.append(m)

    if not matches:
        print("No matches found")
        return

    if len(matches) > 1:
        print("\nMultiple matches:")
        index = 1
        for m in matches[:10]:
            print(f"{index}. {m}")
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

    print(f"Finding recommendations for: {selected}")
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
        print(f"{index}. {movie} ({year}) - {rating}* (score: {score:.1f})")
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
    print("\nEnter favorite actors (comma separated, or press Enter to skip):")
    actors_input = input("> ")
    actors = []
    if actors_input:
        for a in actors_input.split(','):
            actors.append(a)

    print("Enter favorite directors (comma separated, or press Enter to skip):")
    directors_input = input("> ")
    directors = []
    if directors_input:
        for d in directors_input.split(','):
            directors.append(d)

    print("Enter favorite writers (comma separated, or press Enter to skip):")
    writers_input = input("> ")
    writers = []
    if writers_input:
        for w in writers_input.split(','):
            writers.append(w)

    print("Enter favorite genres (comma separated, or press Enter to skip):")
    genres_input = input("> ")
    genres = []
    if genres_input:
        for g in genres_input.split(','):
            genres.append(g)

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
        print(f"{index}. {movie} ({year}) - {rating}* (score: {score:.1f})")
        index = index + 1


def _similar_people_mode(graph: Graph) -> None:
    people = graph.get_all_vertices(kind='person')
    if not people:
        print("No people in graph")
        return

    print("\nEnter part of a person's name:")
    search = input("> ").lower()

    matches = []
    for p in people:
        if search in p.lower():
            matches.append(p)

    if not matches:
        print("No matches found")
        return

    if len(matches) > 1:
        print("\nMultiple matches:")
        index = 1
        for m in matches[:10]:
            print(f"{index}. {m}")
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
    print(f"\n{selected} ({vertex.subkind})")

    similar = find_similar_people(graph, selected, limit=10)

    if not similar:
        print("No similar people found")
        return

    print("\nSimilar people:")
    index = 1
    for person, score in similar:
        p_vertex = graph.get_vertex(person)
        print(f"{index}. {person} ({p_vertex.subkind}) - similarity: {score:.3f}")
        index = index + 1


def _visualization_mode(graph: Graph) -> None:
    print("\nVisualization options:")
    print("1. Full graph")
    print("2. Movie network")
    print("3. Person network")

    choice = input("Enter choice (1-3): ")

    if choice == '1':
        print("Generating visualization...")
        visualize_graph(graph, max_vertices=300)
    elif choice == '2':
        movies = graph.get_all_vertices(kind='movie')
        search = input("Enter movie title: ").lower()
        matches = []
        for m in movies:
            if search in m.lower():
                matches.append(m)
        if matches:
            visualize_graph(graph, center=matches[0], max_vertices=100)
        else:
            print("Movie not found")
    elif choice == '3':
        people = graph.get_all_vertices(kind='person')
        search = input("Enter person name: ").lower()
        matches = []
        for p in people:
            if search in p.lower():
                matches.append(p)
        if matches:
            visualize_graph(graph, center=matches[0], max_vertices=100)
        else:
            print("Person not found")
    else:
        print("Invalid choice")


if __name__ == '__main__':
    main(min_year=2000, min_votes=1000, max_movies=200, max_people=1000, min_movies_per_person=3)
