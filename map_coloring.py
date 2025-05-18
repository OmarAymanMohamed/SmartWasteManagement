import networkx as nx
import matplotlib.pyplot as plt
from models import District

def create_district_graph(districts):
    """Create a graph representing districts and their adjacencies"""
    G = nx.Graph()
    
    # Add nodes
    for district in districts:
        G.add_node(district.district_id, district=district)
    
    # Add edges for adjacent districts
    for district in districts:
        for adj_district in district.adjacent_districts:
            G.add_edge(district.district_id, adj_district.district_id)
    
    return G

def map_coloring(districts, colors=None):
    """
    Assign colors to districts such that no adjacent districts have the same color
    using a greedy algorithm.
    """
    if colors is None:
        colors = ["red", "green", "blue", "yellow"]
    
    # Sort districts by degree (number of adjacent districts)
    graph = create_district_graph(districts)
    sorted_districts = sorted(
        districts, 
        key=lambda d: len(d.adjacent_districts), 
        reverse=True
    )
    
    for district in sorted_districts:
        # Get colors of adjacent districts
        used_colors = {
            adj_district.color for adj_district in district.adjacent_districts
            if adj_district.color is not None
        }
        
        # Find first available color
        for color in colors:
            if color not in used_colors:
                district.color = color
                break
    
    return districts

def visualize_districts(districts, show_plot=True):
    """Visualize the district map with colors"""
    G = create_district_graph(districts)
    
    # Get position for nodes - this is simplified and would need real coordinates in a real system
    pos = nx.spring_layout(G)
    
    # Get colors for nodes
    colors = [districts[i-1].color for i in G.nodes]
    
    plt.figure(figsize=(10, 8))
    nx.draw(
        G, 
        pos, 
        node_color=colors,
        with_labels=True, 
        node_size=1500, 
        font_size=10,
        font_weight='bold'
    )
    plt.title("District Map Coloring")
    plt.savefig("district_map.png")
    
    if show_plot:
        plt.show()
    else:
        plt.close() 