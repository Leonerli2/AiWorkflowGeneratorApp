import json
import plotly.graph_objects as go
import networkx as nx
import streamlit as st

# Path to your JSON file
JSON_PATH = "data/output/elam/elam50.json"

# Function to parse JSON and create Plotly flowchart with S-curve edges and colored nodes
def create_flowchart_with_icons(data, scale_factor=5.0, max_nodes_per_column=10, downward_offset=1.0):
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
    trace_images = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        marker=dict(
            size=20,  # Keep a base size for the images
            color='black',
            symbol='circle',
            opacity=0,
            showscale=False,
            cmax=1
        ),
        hoverinfo='none',
        customdata=node_images
    )

    # Layout settings
    layout = go.Layout(
        title="Flowchart",
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
    fig = go.Figure(data=[trace_edges, trace_nodes, trace_images], layout=layout)

    return fig

# Main execution
if __name__ == "__main__":
    # Load JSON data
    with open(JSON_PATH) as f:
        data = json.load(f)

    # Generate Plotly flowchart with icons, scaling images by a factor of 2 and wrapping after 10 nodes
    flowchart = create_flowchart_with_icons(data, scale_factor=8.0, max_nodes_per_column=12)

    # Streamlit Integration
    st.title("Flowchart with Icons using Plotly")
    st.plotly_chart(flowchart)




# import json
# import plotly.graph_objects as go
# import networkx as nx
# import streamlit as st

# # Path to your JSON file
# JSON_PATH = "data/output/elam/elam51.json"

# # Function to parse JSON and create Plotly flowchart with column wrapping
# def create_flowchart_with_icons(data, scale_factor=1.0, max_nodes_per_column=10):
#     # Initialize the NetworkX graph
#     G = nx.DiGraph()

#     # Add nodes with their labels and images (if available)
#     for shape in data["shapes"]:
#         key = shape["key"]
#         label = shape.get("text", "Unnamed")
#         image_url = shape.get("imageUrl", "")  # Get the image URL for each instruction box

#         # Add node to graph
#         G.add_node(key, label=label, image=image_url)

#     # Add edges (connectors)
#     for connector in data["connectors"]:
#         start = connector["beginItemKey"]
#         end = connector["endItemKey"]
#         label = connector.get("texts", {}).get("0.5", "")
        
#         # Add edge to graph
#         G.add_edge(start, end, label=label)

#     # Create the Plotly plot
#     edge_x = []
#     edge_y = []
    
#     pos = {}
#     node_count = len(G.nodes)
    
#     # Create node positions, wrapping after `max_nodes_per_column` nodes
#     for i, node in enumerate(G.nodes()):
#         col = i // max_nodes_per_column  # Determine which column the node belongs to
#         row = i % max_nodes_per_column   # Determine row within the column
#         x = col  # Column is simply the index of the column
#         y = node_count - row * 1.5  # Space nodes vertically within the column
#         pos[node] = (x, y)

#     for start, end in G.edges():
#         x0, y0 = pos[start]
#         x1, y1 = pos[end]
#         edge_x.append(x0)
#         edge_x.append(x1)
#         edge_y.append(y0)
#         edge_y.append(y1)

#     # Create node positions for display
#     node_x = []
#     node_y = []
#     node_images = []
#     node_labels = []
#     for node, (x, y) in pos.items():
#         node_x.append(x)
#         node_y.append(y)
#         node_labels.append(G.nodes[node]['label'])
#         node_images.append(G.nodes[node]['image'])

#     # Create edges
#     trace_edges = go.Scatter(
#         x=edge_x, 
#         y=edge_y,
#         mode='lines',
#         line=dict(width=0.5, color='#888'),
#         hoverinfo='none'
#     )

#     # Create nodes with text on the right
#     trace_nodes = go.Scatter(
#         x=node_x, 
#         y=node_y,
#         mode='markers+text',
#         text=node_labels,
#         textposition="middle right",  # Text on the right side of the node
#         marker=dict(
#             symbol="circle",
#             size=40,
#             color="lightblue",
#             line=dict(width=0.5, color='black')
#         ),
#         hoverinfo='text',
#     )

#     # Create the image overlay (icons for nodes), scaling by the factor
#     trace_images = go.Scatter(
#         x=node_x,
#         y=node_y,
#         mode='markers',
#         marker=dict(
#             size=20,  # Keep a base size for the images
#             color='black',
#             symbol='circle',
#             opacity=0,
#             showscale=False,
#             cmax=1
#         ),
#         hoverinfo='none',
#         customdata=node_images
#     )

#     # Layout settings
#     layout = go.Layout(
#         title="Flowchart",
#         showlegend=False,
#         hovermode='closest',
#         xaxis=dict(
#             showgrid=False, 
#             zeroline=False,
#             showticklabels=False  # Hide numbers on x-axis
#         ),
#         yaxis=dict(
#             showgrid=False, 
#             zeroline=False,
#             showticklabels=False  # Hide numbers on y-axis
#         ),
#         height=800,  # Set the height of the figure
#         images=[dict(
#             source=img,
#             xref="x",
#             yref="y",
#             x=x,
#             y=y,
#             sizex=0.1 * scale_factor,  # Scale the image size by the scale factor
#             sizey=0.1 * scale_factor,  # Scale the image size by the scale factor
#             xanchor="center",
#             yanchor="middle",
#             opacity=0.7
#         ) for img, x, y in zip(node_images, node_x, node_y) if img]
#     )

#     # Combine traces for display
#     fig = go.Figure(data=[trace_edges, trace_nodes, trace_images], layout=layout)

#     return fig

# # Main execution
# if __name__ == "__main__":
#     # Load JSON data
#     with open(JSON_PATH) as f:
#         data = json.load(f)

#     # Generate Plotly flowchart with icons, scaling images by a factor of 2 and wrapping after 10 nodes
#     scale_factor = 2.0  # Set this to the scale factor you want
#     flowchart = create_flowchart_with_icons(data, scale_factor=scale_factor, max_nodes_per_column=10)

#     # Streamlit Integration
#     st.title("Flowchart with Icons using Plotly")
#     st.plotly_chart(flowchart)


# # import json
# # import plotly.graph_objects as go
# # import networkx as nx
# # import streamlit as st

# # # Path to your JSON file
# # JSON_PATH = "data/output/elam/elam50.json"

# # # Function to parse JSON and create Plotly flowchart
# # def create_flowchart_with_icons(data, scale_factor=1.0):
# #     # Initialize the NetworkX graph
# #     G = nx.DiGraph()

# #     # Add nodes with their labels and images (if available)
# #     for shape in data["shapes"]:
# #         key = shape["key"]
# #         label = shape.get("text", "Unnamed")
# #         image_url = shape.get("imageUrl", "")  # Get the image URL for each instruction box

# #         # Add node to graph
# #         G.add_node(key, label=label, image=image_url)

# #     # Add edges (connectors)
# #     for connector in data["connectors"]:
# #         start = connector["beginItemKey"]
# #         end = connector["endItemKey"]
# #         label = connector.get("texts", {}).get("0.5", "")
        
# #         # Add edge to graph
# #         G.add_edge(start, end, label=label)

# #     # Create a vertical layout for nodes
# #     node_count = len(G.nodes)
# #     vertical_spacing = 1  # Adjust the vertical distance between nodes

# #     pos = {}
# #     for i, node in enumerate(G.nodes()):
# #         pos[node] = (0, node_count - i * vertical_spacing)  # Place nodes in a vertical line

# #     # Create the Plotly plot
# #     edge_x = []
# #     edge_y = []
# #     for start, end in G.edges():
# #         x0, y0 = pos[start]
# #         x1, y1 = pos[end]
# #         edge_x.append(x0)
# #         edge_x.append(x1)
# #         edge_y.append(y0)
# #         edge_y.append(y1)

# #     # Create node positions for display
# #     node_x = []
# #     node_y = []
# #     node_images = []
# #     node_labels = []
# #     for node, (x, y) in pos.items():
# #         node_x.append(x)
# #         node_y.append(y)
# #         node_labels.append(G.nodes[node]['label'])
# #         node_images.append(G.nodes[node]['image'])

# #     # Create edges
# #     trace_edges = go.Scatter(
# #         x=edge_x, 
# #         y=edge_y,
# #         mode='lines',
# #         line=dict(width=0.5, color='#888'),
# #         hoverinfo='none'
# #     )

# #     # Create nodes with text on the right
# #     trace_nodes = go.Scatter(
# #         x=node_x, 
# #         y=node_y,
# #         mode='markers+text',
# #         text=node_labels,
# #         textposition="middle right",  # Text on the right side of the node
# #         marker=dict(
# #             symbol="circle",
# #             size=40,
# #             color="lightblue",
# #             line=dict(width=0.5, color='black')
# #         ),
# #         hoverinfo='text',
# #     )

# #     # Create the image overlay (icons for nodes), scaling by the factor
# #     trace_images = go.Scatter(
# #         x=node_x,
# #         y=node_y,
# #         mode='markers',
# #         marker=dict(
# #             size=20,  # Keep a base size for the images
# #             color='black',
# #             symbol='circle',
# #             opacity=0,
# #             showscale=False,
# #             cmax=1
# #         ),
# #         hoverinfo='none',
# #         customdata=node_images
# #     )

# #     # Layout settings
# #     layout = go.Layout(
# #         title="Flowchart",
# #         showlegend=False,
# #         hovermode='closest',
# #         xaxis=dict(
# #             showgrid=False, 
# #             zeroline=False,
# #             showticklabels=False  # Hide numbers on x-axis
# #         ),
# #         yaxis=dict(
# #             showgrid=False, 
# #             zeroline=False,
# #             showticklabels=False  # Hide numbers on y-axis
# #         ),
# #         height=800,  # Set the height of the figure
# #         images=[dict(
# #             source=img,
# #             xref="x",
# #             yref="y",
# #             x=x,
# #             y=y,
# #             sizex=0.1 * scale_factor,  # Scale the image size by the scale factor
# #             sizey=0.1 * scale_factor,  # Scale the image size by the scale factor
# #             xanchor="center",
# #             yanchor="middle",
# #             opacity=0.7
# #         ) for img, x, y in zip(node_images, node_x, node_y) if img]
# #     )

# #     # Combine traces for display
# #     fig = go.Figure(data=[trace_edges, trace_nodes, trace_images], layout=layout)

# #     return fig

# # # Main execution
# # if __name__ == "__main__":
# #     # Load JSON data
# #     with open(JSON_PATH) as f:
# #         data = json.load(f)

# #     # Generate Plotly flowchart with icons, scaling images by a factor of 2
# #     scale_factor = 5.0  # Set this to the scale factor you want
# #     flowchart = create_flowchart_with_icons(data, scale_factor=scale_factor)

# #     # Streamlit Integration
# #     st.title("Flowchart with Icons using Plotly")
# #     st.plotly_chart(flowchart)











# # # import json
# # # import graphviz
# # # import streamlit as st

# # # # Path to your JSON file
# # # JSON_PATH = "data/output/elam/elam50.json"

# # # # Function to parse JSON and create Graphviz flowchart
# # # def create_graphviz_flowchart(data):
# # #     # Initialize Graphviz Digraph
# # #     dot = graphviz.Digraph(format="svg")
# # #     dot.attr(rankdir="TB", splines="true", fontsize="12", size="8,10")  # Adjust overall graph size

# # #     # Adjust the size of the graph and node separation
# # #     dot.attr(nodesep="0.1", ranksep="0.3")  # Reduce node and rank separation

# # #     # Group nodes into columns: After 5 nodes, start a new column
# # #     column_counter = 0
# # #     nodes_in_current_column = 0

# # #     for shape in data["shapes"]:
# # #         key = shape["key"]
# # #         label = shape.get("text", "Unnamed")

# # #         # Start a new subgraph (i.e., column) after every 5 nodes
# # #         if nodes_in_current_column == 5:
# # #             column_counter += 1  # Increment column counter
# # #             nodes_in_current_column = 0  # Reset node count for the new column
# # #             dot.attr(rankdir="TB", rank="same")  # Same rank for nodes in the same column

# # #         # Add the node with increased font size, same box size
# # #         dot.node(key, label, shape="rect", style="filled", color="lightgrey", fontname="Arial", 
# # #                  fontsize="18", width="1", height="0.4", margin="0.1", group=str(column_counter))

# # #         # Increment the counter for nodes in the current column
# # #         nodes_in_current_column += 1

# # #     # Add edges (connectors)
# # #     for connector in data["connectors"]:
# # #         start = connector["beginItemKey"]
# # #         end = connector["endItemKey"]
# # #         label = connector.get("texts", {}).get("0.5", "")
# # #         dot.edge(start, end, label=label, fontname="Arial", fontsize="12")

# # #     return dot

# # # # Main execution
# # # if __name__ == "__main__":
# # #     # Load JSON data
# # #     with open(JSON_PATH) as f:
# # #         data = json.load(f)
    
# # #     # Generate Graphviz flowchart
# # #     flowchart = create_graphviz_flowchart(data)

# # #     # Streamlit Integration
# # #     st.title("Graphviz Flowchart")
# # #     # Display flowchart as SVG in Streamlit
# # #     st.graphviz_chart(flowchart.source)



# # # import json
# # # import graphviz
# # # import streamlit as st

# # # # Path to your JSON file
# # # JSON_PATH = "data/output/elam/elam50.json"

# # # # Function to parse JSON and create Graphviz flowchart
# # # def create_graphviz_flowchart(data):
# # #     # Initialize Graphviz Digraph
# # #     dot = graphviz.Digraph(format="svg")
# # #     dot.attr(rankdir="TB", splines="true", fontsize="12", size="5,5")  # Adjust size for overall graph

# # #     # Adjust the size of the graph and node separation
# # #     dot.attr(nodesep="0.05", ranksep="0.15")  # Reduce node and rank separation to make boxes closer

# # #     # Add nodes (shapes) with bigger text size, same box size
# # #     for shape in data["shapes"]:
# # #         key = shape["key"]
# # #         label = shape.get("text", "Unnamed")
# # #         # Increase the font size without changing node size
# # #         dot.node(key, label, shape="rect", style="filled", color="lightgrey", fontname="Arial", 
# # #                  fontsize="18", width="1", height="0.4", margin="0.1")  # Increase fontsize for text

# # #     # Add edges (connectors)
# # #     for connector in data["connectors"]:
# # #         start = connector["beginItemKey"]
# # #         end = connector["endItemKey"]
# # #         label = connector.get("texts", {}).get("0.5", "")
# # #         dot.edge(start, end, label=label, fontname="Arial", fontsize="12")

# # #     return dot

# # # # Main execution
# # # if __name__ == "__main__":
# # #     # Load JSON data
# # #     with open(JSON_PATH) as f:
# # #         data = json.load(f)
    
# # #     # Generate Graphviz flowchart
# # #     flowchart = create_graphviz_flowchart(data)

# # #     # Streamlit Integration
# # #     st.title("Graphviz Flowchart")
# # #     # Display flowchart as SVG in Streamlit
# # #     st.graphviz_chart(flowchart.source)





# # # import json
# # # import plotly.graph_objects as go

# # # # Path to your JSON file
# # # JSON_PATH = "data/output/elam/elam50.json"

# # # # Function to parse JSON into graph structure
# # # def parse_json_to_graph(data):
# # #     nodes = []
# # #     edges = []
    
# # #     # Extract shapes as nodes
# # #     for shape in data["shapes"]:
# # #         key = shape["key"]
# # #         label = shape.get("text", "Unnamed")
# # #         x, y = shape["x"], shape["y"]
# # #         nodes.append({"key": key, "label": label, "x": x, "y": y})
    
# # #     # Extract connectors as edges
# # #     for connector in data["connectors"]:
# # #         start = connector["beginItemKey"]
# # #         end = connector["endItemKey"]
# # #         label = connector.get("texts", {}).get("0.5", "")
# # #         edges.append({"start": start, "end": end, "label": label})
    
# # #     return nodes, edges

# # # # Function to create flowchart with Plotly
# # # def create_plotly_flowchart(nodes, edges):
# # #     fig = go.Figure()

# # #     # Add edges (lines in the background)
# # #     for edge in edges:
# # #         start_node = next(node for node in nodes if node["key"] == edge["start"])
# # #         end_node = next(node for node in nodes if node["key"] == edge["end"])
# # #         fig.add_trace(
# # #             go.Scatter(
# # #                 x=[start_node["x"], end_node["x"]],
# # #                 y=[-start_node["y"], -end_node["y"]],
# # #                 mode="lines",
# # #                 line=dict(color="black", width=2),
# # #                 hoverinfo="none"
# # #             )
# # #         )

# # #     # Add nodes (rectangles with text inside)
# # #     for node in nodes:
# # #         x, y = node["x"], -node["y"]  # Invert y for correct visualization
# # #         label = node["label"]
        
# # #         # Compute rectangle size based on text length
# # #         text_length = len(label)
# # #         rect_width = max(1, text_length * 0.15)  # Adjust scaling as needed
# # #         rect_height = 0.5

# # #         # Add rectangle as an annotation
# # #         fig.add_shape(
# # #             type="rect",
# # #             x0=x - rect_width / 2,
# # #             y0=y - rect_height / 2,
# # #             x1=x + rect_width / 2,
# # #             y1=y + rect_height / 2,
# # #             line=dict(color="black"),
# # #             fillcolor="lightgrey",
# # #             layer="below"
# # #         )

# # #         # Add text on top of the rectangle
# # #         fig.add_trace(
# # #             go.Scatter(
# # #                 x=[x],
# # #                 y=[y],
# # #                 text=label,
# # #                 mode="text",
# # #                 textfont=dict(size=12, color="black"),
# # #                 hoverinfo="none"
# # #             )
# # #         )

# # #     # Update layout
# # #     fig.update_layout(
# # #         title="Flowchart",
# # #         showlegend=False,
# # #         xaxis=dict(visible=False),
# # #         yaxis=dict(visible=False),
# # #         margin=dict(l=20, r=20, t=40, b=20),
# # #         plot_bgcolor="white"
# # #     )

# # #     return fig

# # # # Main execution
# # # if __name__ == "__main__":
# # #     # Load JSON data
# # #     with open(JSON_PATH) as f:
# # #         data = json.load(f)
    
# # #     # Parse JSON into graph components
# # #     nodes, edges = parse_json_to_graph(data)
    
# # #     # Create Plotly figure
# # #     flowchart = create_plotly_flowchart(nodes, edges)
    
# #     # # Show interactive plot
# #     # flowchart.show()


# # # import json
# # # import matplotlib.pyplot as plt
# # # import networkx as nx

# # # JSON_PATH = "data/input_sample_json/flowchart-1.json"
# # # JSON_PATH = "data/output/elam/elam50.json"

# # # def parse_json_to_graph(data):
# # #     G = nx.DiGraph()
# # #     shape_dict = {}
    
# # #     # Parse shapes as nodes
# # #     for shape in data["shapes"]:
# # #         key = shape["key"]
# # #         label = shape.get("text", "Unnamed")
# # #         x, y = shape["x"], shape["y"]
# # #         shape_dict[key] = (x, y)  # Store positions for layout
# # #         G.add_node(key, label=label, pos=(x, -y))  # Use -y to invert y-axis for matplotlib

# # #     # Parse connectors as edges
# # #     for connector in data["connectors"]:
# # #         start = connector["beginItemKey"]
# # #         end = connector["endItemKey"]
# # #         label = connector.get("texts", {}).get("0.5", "")
# # #         G.add_edge(start, end, label=label)
    
# # #     return G, shape_dict

# # # def draw_flowchart(G, shape_dict):
# # #     pos = nx.get_node_attributes(G, 'pos')
# # #     labels = nx.get_node_attributes(G, 'label')
# # #     edge_labels = nx.get_edge_attributes(G, 'label')
    
# # #     # Draw nodes
# # #     plt.figure(figsize=(12, 8))
# # #     nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="lightblue", edgecolors="black")
# # #     nx.draw_networkx_labels(G, pos, labels, font_size=10, font_color="black")
    
# # #     # Draw edges
# # #     nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="->", connectionstyle="arc3,rad=0.2")
# # #     nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red", font_size=8)
    
# # #     # Display plot
# # #     plt.title("Flowchart")
# # #     plt.axis("off")
# # #     plt.show()





# # # if __name__ == "__main__":
# # #     with open(JSON_PATH) as f:
# # #         data = json.load(f)
    
# # #     G, shape_dict = parse_json_to_graph(data)
# # #     draw_flowchart(G, shape_dict)

