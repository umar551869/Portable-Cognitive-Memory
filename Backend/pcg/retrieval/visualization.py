import networkx as nx
import plotly.graph_objects as go
import numpy as np
from typing import List

from pcg.memory.models import Node as ORMNode, Edge as ORMEdge

async def create_3d_graph_visualization(nodes: List[ORMNode], edges: List[ORMEdge]):
    """Creates an interactive 3D graph visualization of the PCG."""

    G = nx.Graph()

    node_id_to_index = {node.id: i for i, node in enumerate(nodes)}

    # Add nodes to the graph
    for node in nodes:
        G.add_node(node.id, label=node.canonical_name, type=node.type)

    # Add edges to the graph
    for edge in edges:
        if edge.source in G and edge.target in G:
            G.add_edge(edge.source, edge.target, relation=edge.relation)

    # Use a 3D spring layout for positioning
    pos = nx.spring_layout(G, dim=3, k=0.5, iterations=50)

    # Prepare node data for Plotly
    node_x = [pos[node.id][0] for node in nodes]
    node_y = [pos[node.id][1] for node in nodes]
    node_z = [pos[node.id][2] for node in nodes]
    node_labels = [f"{node.canonical_name} ({node.type})" for node in nodes]

    # Prepare edge data for Plotly
    edge_x = []
    edge_y = []
    edge_z = []
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    # Create Plotly traces
    edge_trace = go.Scatter3d(
        x=edge_x,
        y=edge_y,
        z=edge_z,
        mode='lines',
        line=dict(color='gray', width=0.5),
        hoverinfo='none'
    )

    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            line=dict(width=0)
        )
    )

    # Color nodes by type
    unique_types = list(set(node.type for node in nodes))
    type_to_color_map = {node_type: i for i, node_type in enumerate(unique_types)}
    node_colors = [type_to_color_map[node.type] for node in nodes]
    node_trace.marker.color = node_colors

    node_trace.text = node_labels

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='Portable Cognitive Graph (3D)',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 ) ],
                        scene=dict(
                            xaxis=dict(showbackground=False, showticklabels=False, zeroline=False, title=''),
                            yaxis=dict(showbackground=False, showticklabels=False, zeroline=False, title=''),
                            zaxis=dict(showbackground=False, showticklabels=False, zeroline=False, title='')
                        )
                    ))
    fig.show()