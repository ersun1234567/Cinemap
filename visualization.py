"""CSC111 Project 2: Graph visualization utilities.

This module renders interactive visualizations of the project graph and movie
recommendation subsets using NetworkX layouts and Plotly figures.
"""

import networkx as nx
import plotly.graph_objects as go
from typing import Optional, List, Tuple

from graph_models import Graph


def visualize_graph(graph: Graph,
                    center: Optional[str] = None,
                    max_vertices: int = 500,
                    output_file: str = '') -> None:
    """Display or save an interactive graph visualization.

    If center is provided, a local neighborhood around that item is visualized.
    Otherwise, up to max_vertices from the full graph are shown.
    """
    graph_nx = graph.to_networkx(max_vertices=max_vertices)

    if graph_nx.number_of_nodes() == 0:
        print("no nodes to visualize")
        return

    if center is not None:
        if center in graph_nx.nodes:
            nodes_to_keep = {center}
            for n in graph_nx.neighbors(center):
                nodes_to_keep.add(n)

            temp_list = []
            for n in nodes_to_keep:
                temp_list.append(n)
            for n in temp_list:
                if n != center:
                    for n2 in graph_nx.neighbors(n):
                        nodes_to_keep.add(n2)
            graph_nx = graph_nx.subgraph(nodes_to_keep)

    pos = nx.spring_layout(graph_nx)

    edge_x = []
    edge_y = []
    for edge in graph_nx.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    node_x = []
    node_y = []
    node_text = []
    for node in graph_nx.nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    fig = go.Figure(data=[
        go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=0.5, color='gray'), hoverinfo='none'),
        go.Scatter(x=node_x, y=node_y, mode='markers', text=node_text, hoverinfo='text',
                   marker=dict(size=10, color='lightblue'))
    ])

    fig.update_layout(title=f'graph: {graph_nx.number_of_nodes()} nodes',
                      xaxis=dict(showgrid=False, showticklabels=False),
                      yaxis=dict(showgrid=False, showticklabels=False))

    if output_file:
        fig.write_html(output_file)
    else:
        fig.show()


def visualize_recommendations(graph: Graph,
                              seed_movie: str,
                              recommendations: List[Tuple[str, float]]) -> None:
    """Display a small graph focused on seed_movie and top recommendations.

    The seed movie is highlighted in red, top recommendations in orange, and
    other connected nodes in light blue. Up to the top five recommended movies
    are included in the rendered subgraph.

    Preconditions:
    - seed_movie is in graph
    - each tuple in recommendations is (movie_name, similarity_score)
    """
    if len(recommendations) == 0:
        print("no recommendations to visualize")
        return

    top_recs = []
    for i in range(min(5, len(recommendations))):
        top_recs.append(recommendations[i])

    rec_movies = []
    for r in top_recs:
        rec_movies.append(r[0])

    nodes_to_include = [seed_movie]
    for m in rec_movies:
        nodes_to_include.append(m)

    graph_nx = nx.Graph()

    for node in nodes_to_include:
        graph_nx.add_node(node)

    for node in nodes_to_include:
        vertex = graph.get_vertex(node)
        for n in vertex.neighbours:
            if n.item in nodes_to_include:
                graph_nx.add_edge(node, n.item)

    pos = nx.spring_layout(graph_nx)

    edge_x = []
    edge_y = []
    for edge in graph_nx.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    node_x = []
    node_y = []
    node_colors = []
    for node in graph_nx.nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        if node == seed_movie:
            node_colors.append('red')
        else:
            in_rec = False
            for rm in rec_movies:
                if node == rm:
                    in_rec = True
                    break
            if in_rec:
                node_colors.append('orange')
            else:
                node_colors.append('lightblue')

    fig = go.Figure(data=[
        go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=0.5, color='gray'), hoverinfo='none'),
        go.Scatter(x=node_x, y=node_y, mode='markers+text', text=nodes_to_include,
                   textposition="top center", marker=dict(size=12, color=node_colors))
    ])

    fig.update_layout(title=f'recommendations for: {seed_movie}',
                      xaxis=dict(showgrid=False, showticklabels=False),
                      yaxis=dict(showgrid=False, showticklabels=False))

    fig.show()


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': ['networkx', 'plotly.graph_objects'],
        'allowed-io': ['visualize_graph', 'visualize_recommendations'],
        'max-line-length': 120
    })
