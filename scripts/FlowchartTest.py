import json
import matplotlib.pyplot as plt
import networkx as nx

JSON_PATH = "data/input_sample_json/flowchart-2.json"

def parse_json_to_graph(data):
    G = nx.DiGraph()
    shape_dict = {}
    
    # Parse shapes as nodes
    for shape in data["shapes"]:
        key = shape["key"]
        label = shape.get("text", "Unnamed")
        x, y = shape["x"], shape["y"]
        shape_dict[key] = (x, y)  # Store positions for layout
        G.add_node(key, label=label, pos=(x, -y))  # Use -y to invert y-axis for matplotlib

    # Parse connectors as edges
    for connector in data["connectors"]:
        start = connector["beginItemKey"]
        end = connector["endItemKey"]
        label = connector.get("texts", {}).get("0.5", "")
        G.add_edge(start, end, label=label)
    
    return G, shape_dict

def draw_flowchart(G, shape_dict):
    pos = nx.get_node_attributes(G, 'pos')
    labels = nx.get_node_attributes(G, 'label')
    edge_labels = nx.get_edge_attributes(G, 'label')
    
    # Draw nodes
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_size=3000, node_color="lightblue", edgecolors="black")
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_color="black")
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="->", connectionstyle="arc3,rad=0.2")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red", font_size=8)
    
    # Display plot
    plt.title("Flowchart")
    plt.axis("off")
    plt.show()



if __name__ == "__main__":
    with open(JSON_PATH) as f:
        data = json.load(f)
    
    G, shape_dict = parse_json_to_graph(data)
    draw_flowchart(G, shape_dict)