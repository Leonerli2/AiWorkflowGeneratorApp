import json
import plotly.graph_objects as go
import networkx as nx

def load_json(file_path):
    """
    Load JSON data from the given file path.
    """
    with open(file_path) as f:
        return json.load(f)

def create_flowchart_with_icons(data, scale_factor=5.0, max_nodes_per_column=10, downward_offset=1.0):
    """
    Create a flowchart from JSON data using Plotly, with nodes, S-curve edges, and icons.
    """
    # Initialize the NetworkX graph
    G = nx.DiGraph()

    # Add nodes with their labels and images (if available)
    for shape in data["shapes"]:
        key = shape["key"]
        label = shape.get("text", "Unnamed")
        image_url = shape.get("imageUrl", "")  # Get the image URL for each instruction box

        # Add node to graph
        G.add_node(key, label=label, image=image_url)

    # Add edges (connectors)
    for connector in data["connectors"]:
        start = connector["beginItemKey"]
        end = connector["endItemKey"]
        label = connector.get("texts", {}).get("0.5", "")
        
        # Add edge to graph
        G.add_edge(start, end, label=label)

    # Create the Plotly plot
    edge_x = []
    edge_y = []
    
    pos = {}
    node_count = len(G.nodes)
    
    # Create node positions, wrapping after `max_nodes_per_column` nodes
    for i, node in enumerate(G.nodes()):
        col = i // max_nodes_per_column  # Determine which column the node belongs to
        row = i % max_nodes_per_column   # Determine row within the column
        x = col  # Column is simply the index of the column
        y = node_count - row * 1.5  # Space nodes vertically within the column
        pos[node] = (x, y)

    for start, end in G.edges():
        x0, y0 = pos[start]
        x1, y1 = pos[end]
        
        # If the edge goes from one column to another, create an S-curve with right-angle turns
        if pos[start][0] != pos[end][0]:  # Check if start and end are in different columns
            # Move downward first to avoid the text
            mid_x = (x0 + x1) / 2  # Midpoint in x direction for the curve
            edge_x.extend([x0, x0, mid_x, mid_x, x1])
            edge_y.extend([y0, y0 - downward_offset, y0 - downward_offset, y1, y1])
        else:
            # Direct connection (straight line) if nodes are in the same column
            edge_x.append(x0)
            edge_x.append(x1)
            edge_y.append(y0)
            edge_y.append(y1)

    # Create node positions for display
    node_x = []
    node_y = []
    node_images = []
    node_labels = []
    node_colors = []  # List to store colors for each node

    # Set colors for the nodes
    for node, (x, y) in pos.items():
        node_x.append(x)
        node_y.append(y)
        node_labels.append(G.nodes[node]['label'])
        node_images.append(G.nodes[node]['image'])

        # Determine color based on whether it's a start or end node
        if G.nodes[node]['label'] == "Start":  # If node is a start node
            node_colors.append("lightgreen")
        elif G.nodes[node]['label'] == "End":  # If node is an end node
            node_colors.append("lightcoral")
        else:
            node_colors.append("lightblue")  # Default color for other nodes

    # Create edges
    trace_edges = go.Scatter(
        x=edge_x, 
        y=edge_y,
        mode='lines',
        line=dict(width=2, color='#888'),
        hoverinfo='none'
    )

    # Create nodes with text on the right
    trace_nodes = go.Scatter(
        x=node_x, 
        y=node_y,
        mode='markers+text',
        text=node_labels,
        textposition="middle right",  # Text on the right side of the node
        marker=dict(
            symbol="circle",
            size=40,
            color=node_colors,  # Set color dynamically based on the node type
            line=dict(width=0.5, color='black')
        ),
        hoverinfo='text',
    )

    # Create the image overlay (icons for nodes), scaling by the factor
    layout = go.Layout(
        # title="Flowchart",
        showlegend=False,
        hovermode='closest',
        xaxis=dict(
            showgrid=False, 
            zeroline=False,
            showticklabels=False  # Hide numbers on x-axis
        ),
        yaxis=dict(
            showgrid=False, 
            zeroline=False,
            showticklabels=False  # Hide numbers on y-axis
        ),
        height=800,  # Set the height of the figure
        images=[dict(
            source=img,
            xref="x",
            yref="y",
            x=x,
            y=y,
            sizex=0.1 * scale_factor,  # Scale the image size by the scale factor
            sizey=0.1 * scale_factor,  # Scale the image size by the scale factor
            xanchor="center",
            yanchor="middle",
            opacity=0.7
        ) for img, x, y in zip(node_images, node_x, node_y) if img]
    )

    # Combine traces for display
    fig = go.Figure(data=[trace_edges, trace_nodes], layout=layout)

    return fig
