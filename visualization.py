"""CSC111 Project 2: Graph visualization utilities.

This module keeps the existing Plotly graph overview function and adds a
Dash Cytoscape recommendation viewer. The recommendation viewer shows
circular ring layout:
- selected movie in the center
- highest recommended movie is located on the top and the remaining movies are ordered in descending similarity clockwise arranged around it
- node size and edge width scaled by similarity score
- click a movie to see score and explanation details

Module Assumptions:
- Graph node keys are internal identifiers; node labels are in Vertex.item.
- The center argument, when provided, is a graph key (not a display label).
"""

from __future__ import annotations

import math
from typing import Optional, List, Tuple

import networkx as nx
import plotly.graph_objects as go

from graph_models import Graph
from recommendation import get_recommendation_explanation

try:
    import dash_cytoscape as cyto
    from dash import Dash, html, Input, Output
    _DASH_AVAILABLE = True
except ImportError:
    cyto = None
    Dash = None
    html = None
    Input = None
    Output = None
    _DASH_AVAILABLE = False


def visualize_graph(graph: Graph,
                    center: Optional[str] = None,
                    max_vertices: int = 500,
                    output_file: str = '') -> None:
    """Display or save an interactive graph visualization.

    If center is provided, a local neighborhood around that item is visualized.
    Otherwise, up to max_vertices from the full graph are shown.

    Preconditions:
    - max_vertices > 0

    Side Effects:
    - Displays an interactive Plotly figure or writes an HTML file.
    """
    if center is None:
        graph_nx = graph.to_networkx(max_vertices=max_vertices)
    else:
        try:
            graph.get_vertex(center)
        except KeyError:
            print('requested center not found')
            return

        nodes_to_keep = {center}
        first_hop = set(graph.get_neighbour_keys(center))
        nodes_to_keep.update(first_hop)

        for neighbour_key in first_hop:
            nodes_to_keep.update(graph.get_neighbour_keys(neighbour_key))

        graph_nx = nx.Graph()
        for node in nodes_to_keep:
            if graph_nx.number_of_nodes() >= max_vertices:
                break
            vertex = graph.get_vertex(node)
            graph_nx.add_node(node)
            graph_nx.nodes[node]['kind'] = vertex.kind
            graph_nx.nodes[node]['subkind'] = vertex.subkind
            for key, value in vertex.attributes.items():
                graph_nx.nodes[node][key] = value

        for node in list(graph_nx.nodes):
            for neighbour_key in graph.get_neighbour_keys(node):
                if neighbour_key in graph_nx.nodes and node != neighbour_key:
                    graph_nx.add_edge(node, neighbour_key)

    if graph_nx.number_of_nodes() == 0:
        print('no nodes to visualize')
        return

    pos = nx.spring_layout(graph_nx)

    edge_x = []
    edge_y = []
    for edge in graph_nx.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = []
    node_y = []
    node_text = []
    for node in graph_nx.nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(graph.get_vertex(node).item))

    fig = go.Figure(data=[
        go.Scatter(x=edge_x, y=edge_y, mode='lines',
                   line=dict(width=0.5, color='gray'), hoverinfo='none'),
        go.Scatter(x=node_x, y=node_y, mode='markers', text=node_text,
                   hoverinfo='text', marker=dict(size=10, color='lightblue'))
    ])

    fig.update_layout(title=f'graph: {graph_nx.number_of_nodes()} nodes',
                      xaxis=dict(showgrid=False, showticklabels=False),
                      yaxis=dict(showgrid=False, showticklabels=False))

    if output_file:
        fig.write_html(output_file)
    else:
        fig.show()


def _build_reason_text(explanation: dict[str, list[str]]) -> str:
    """Return a short explanation sentence from recommendation explanation data.

    >>> explaination = {
    ... 'actors': ['Leonardo DiCaprio', 'Tom Hardy'],
    ... 'directors': ['Christopher Nolan'],
    ... 'writers': [],
    ... 'genres': ['Sci-Fi']
    ... }
    >>> _build_reason_text(explaination)
    '2 shared actors, 1 shared director, 1 shared genre'
    """

    parts = []
    if explanation['actors']:
        count = len(explanation['actors'])
        parts.append(f'{count} shared actor' + ('' if count == 1 else 's'))
    if explanation['directors']:
        count = len(explanation['directors'])
        parts.append(f'{count} shared director' + ('' if count == 1 else 's'))
    if explanation['writers']:
        count = len(explanation['writers'])
        parts.append(f'{count} shared writer' + ('' if count == 1 else 's'))
    if explanation['genres']:
        count = len(explanation['genres'])
        parts.append(f'{count} shared genre' + ('' if count == 1 else 's'))

    if parts:
        return ', '.join(parts)
    return 'No shared features recorded.'


def _normalize_score(score: float, min_score: float, max_score: float) -> float:
    """Return score normalized to [0, 1]."""
    if max_score == min_score:
        return 1.0
    return (score - min_score) / (max_score - min_score)


def _make_recommendation_elements(graph: Graph,
                                  seed_movie: str,
                                  recommendations: List[Tuple[str, float]]) -> list[dict]:
    """Return Cytoscape elements for the recommendation viewer."""
    top_recs = recommendations[:10]
    seed_vertex = graph.get_vertex(seed_movie)

    elements = [{
        'data': {
            'id': seed_movie,
            'label': str(seed_vertex.item),
            'is_center': True,
            'score': 0,
            'year': seed_vertex.attributes.get('year', 'N/A'),
            'rating': seed_vertex.attributes.get('rating', 'N/A'),
            'votes': seed_vertex.attributes.get('votes', 'N/A'),
            'reason': 'Selected movie',
            'size': 95
        },
        'position': {'x': 0, 'y': 0},
        'classes': 'center'
    }]

    if not top_recs:
        return elements

    scores = [score for _, score in top_recs]
    min_score = min(scores)
    max_score = max(scores)

    radius = 320
    count = len(top_recs)

    for i, (movie_key, score) in enumerate(top_recs):
        movie_vertex = graph.get_vertex(movie_key)
        explanation = get_recommendation_explanation(graph, seed_movie, movie_key)
        normalized = _normalize_score(score, min_score, max_score)
        node_size = 45 + normalized * 30
        edge_width = 2 + normalized * 10
        angle = (2 * math.pi * i / count) - (math.pi / 2)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        elements.append({
            'data': {
                'id': movie_key,
                'label': str(movie_vertex.item),
                'score': round(score, 2),
                'year': movie_vertex.attributes.get('year', 'N/A'),
                'rating': movie_vertex.attributes.get('rating', 'N/A'),
                'votes': movie_vertex.attributes.get('votes', 'N/A'),
                'reason': _build_reason_text(explanation),
                'shared_actors': len(explanation['actors']),
                'shared_directors': len(explanation['directors']),
                'shared_writers': len(explanation['writers']),
                'shared_genres': len(explanation['genres']),
                'actor_names': ', '.join(str(name) for name in explanation['actors']) or 'None',
                'director_names': ', '.join(str(name) for name in explanation['directors']) or 'None',
                'writer_names': ', '.join(str(name) for name in explanation['writers']) or 'None',
                'genre_names': ', '.join(str(name) for name in explanation['genres']) or 'None',
                'size': node_size
            },
            'position': {'x': x, 'y': y},
            'classes': 'movie'
        })

        elements.append({
            'data': {
                'id': f'{seed_movie}->{movie_key}',
                'source': seed_movie,
                'target': movie_key,
                'width': edge_width
            }
        })

    return elements


def _details_children(node_data: Optional[dict]) -> list:
    """Return right-panel content for the clicked node."""
    if node_data is None:
        return [
            html.H3('Movie details'),
            html.P('Click a movie node to see its similarity score and explanation.'),
            html.P('Use your mouse to zoom and drag to move around the graph.')
        ]

    if node_data.get('is_center', False):
        return [
            html.H3(str(node_data['label'])),
            html.P('This is the selected movie in the center.'),
            html.P(f"Year: {node_data['year']}"),
            html.P(f"Rating: {node_data['rating']}"),
            html.P(f"Votes: {node_data['votes']}")
        ]

    return [
        html.H3(str(node_data['label'])),
        html.P(f"Similarity score: {node_data['score']}"),
        html.P(f"Year: {node_data['year']}"),
        html.P(f"IMDb rating: {node_data['rating']}"),
        html.P(f"Votes: {node_data['votes']}"),
        html.H4('Why it is similar'),
        html.P(str(node_data['reason'])),
        html.H4('Breakdown'),
        html.P(f"Shared actors: {node_data['shared_actors']}"),
        html.P(f"Shared directors: {node_data['shared_directors']}"),
        html.P(f"Shared writers: {node_data['shared_writers']}"),
        html.P(f"Shared genres: {node_data['shared_genres']}"),
        html.H4('Shared names'),
        html.P(f"Actors: {node_data['actor_names']}"),
        html.P(f"Directors: {node_data['director_names']}"),
        html.P(f"Writers: {node_data['writer_names']}"),
        html.P(f"Genres: {node_data['genre_names']}")
    ]


def visualize_recommendations(graph: Graph,
                              seed_movie: str,
                              recommendations: List[Tuple[str, float]]) -> None:
    """Launch an interactive Dash Cytoscape recommendation viewer.

    The selected movie is shown in the center and the top 10 recommended
    movies are placed in a ring around it. Node size and edge width are scaled
    by similarity score. Clicking a movie updates the side panel with the score
    and explanation breakdown.

    Preconditions:
    - seed_movie is in graph
    - each tuple in recommendations is (movie_key, similarity_score)

    Side Effects:
    - Starts a local Dash server and opens an interactive viewer in the browser.
    """
    if len(recommendations) == 0:
        print('no recommendations to visualize')
        return

    if not _DASH_AVAILABLE:
        print('Dash visualization requires dash and dash-cytoscape.')
        print('Install them with: pip install dash dash-cytoscape')
        return

    elements = _make_recommendation_elements(graph, seed_movie, recommendations)
    title = f"Cinemap recommendations for: {graph.get_vertex(seed_movie).item}"

    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.H2(title, style={'margin': '0 0 16px 0'}),
            html.Div(
                [
                    html.Div(
                        [
                            cyto.Cytoscape(
                                id='movie-graph',
                                elements=elements,
                                layout={'name': 'preset'},
                                style={'width': '100%', 'height': '760px'},
                                minZoom=0.35,
                                maxZoom=2.8,
                                zoomingEnabled=True,
                                userZoomingEnabled=True,
                                panningEnabled=True,
                                userPanningEnabled=True,
                                autoungrabify=False,
                                boxSelectionEnabled=False,
                                stylesheet=[
                                    {
                                        'selector': 'node',
                                        'style': {
                                            'label': 'data(label)',
                                            'text-wrap': 'wrap',
                                            'text-max-width': 95,
                                            'text-valign': 'center',
                                            'text-halign': 'center',
                                            'font-size': 10,
                                            'width': 'data(size)',
                                            'height': 'data(size)',
                                            'background-color': '#63b3ed',
                                            'color': '#1a202c',
                                            'border-width': 2,
                                            'border-color': '#2d3748'
                                        }
                                    },
                                    {
                                        'selector': '.center',
                                        'style': {
                                            'background-color': '#f56565',
                                            'font-size': 14,
                                            'font-weight': 'bold',
                                            'width': 95,
                                            'height': 95
                                        }
                                    },
                                    {
                                        'selector': 'edge',
                                        'style': {
                                            'width': 'data(width)',
                                            'curve-style': 'bezier',
                                            'line-color': '#718096',
                                            'target-arrow-shape': 'none'
                                        }
                                    }
                                ]
                            )
                        ],
                        style={
                            'width': '72%',
                            'display': 'inline-block',
                            'verticalAlign': 'top'
                        }
                    ),
                    html.Div(
                        id='details-panel',
                        children=_details_children(None),
                        style={
                            'width': '26%',
                            'display': 'inline-block',
                            'verticalAlign': 'top',
                            'padding': '16px',
                            'margin-left': '1%',
                            'border': '1px solid #cbd5e0',
                            'border-radius': '10px',
                            'background-color': '#f7fafc',
                            'height': '760px',
                            'overflow-y': 'auto',
                            'box-sizing': 'border-box'
                        }
                    )
                ]
            )
        ],
        style={'padding': '18px', 'font-family': 'Arial, sans-serif'}
    )

    @app.callback(Output('details-panel', 'children'), Input('movie-graph', 'tapNodeData'))
    def _update_details(node_data: Optional[dict]) -> list:
        return _details_children(node_data)

    print('Starting Dash Cytoscape viewer...')
    print('Open the local server URL in your browser if it does not open automatically.')
    app.run(debug=False)


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': ['networkx', 'plotly.graph_objects', 'recommendation'],
        'allowed-io': ['visualize_graph', 'visualize_recommendations'],
        'max-line-length': 120,
        'generated-members': ['dash.*', 'dash_cytoscape.*']
    })
