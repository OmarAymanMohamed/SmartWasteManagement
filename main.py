import random
import csv
import matplotlib.pyplot as plt
import numpy as np
from models import District, WasteBin, Truck
from map_coloring import map_coloring, visualize_districts
from route_optimization import assign_trucks_to_districts, optimize_route_backtracking

def load_districts_from_csv():
    """Load district data from CSV files"""
    districts = {}
    
    # Load districts
    try:
        with open('data/districts.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                district_id = int(row['district_id'])
                districts[district_id] = District(
                    district_id=district_id,
                    name=row['name']
                )
    except FileNotFoundError:
        # Create default districts if file not found
        for i in range(1, 6):
            district_name = {
                1: "Downtown", 
                2: "Westside", 
                3: "Eastside", 
                4: "Northside", 
                5: "Southside"
            }
            districts[i] = District(i, district_name.get(i, f"District {i}"))
    
    # Load adjacency
    try:
        with open('data/district_adjacency.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                d1_id = int(row['district1_id'])
                d2_id = int(row['district2_id'])
                if d1_id in districts and d2_id in districts:
                    districts[d1_id].add_adjacent_district(districts[d2_id])
    except FileNotFoundError:
        # Default adjacency if file not found
        if len(districts) >= 5:
            districts[1].add_adjacent_district(districts[2])  # Downtown - Westside
            districts[1].add_adjacent_district(districts[3])  # Downtown - Eastside
            districts[1].add_adjacent_district(districts[4])  # Downtown - Northside
            districts[1].add_adjacent_district(districts[5])  # Downtown - Southside
            districts[2].add_adjacent_district(districts[4])  # Westside - Northside
            districts[3].add_adjacent_district(districts[4])  # Eastside - Northside
            districts[3].add_adjacent_district(districts[5])  # Eastside - Southside
            
    return list(districts.values())

def load_waste_bins_from_csv():
    """Load waste bin data from Smart_Bin.csv"""
    waste_bins = []
    bin_id = 1
    
    try:
        with open('Smart_Bin.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Generate location - we'll use random coordinates within city bounds
                x = random.uniform(0, 50)
                y = random.uniform(0, 50)
                location = (x, y)
                
                # Extract fill level and waste type from dataset
                fill_level = float(row['FL_B']) if row['FL_B'] else 50  # Use FL_B (fill level before)
                container_type = row['Container Type']
                bin_type = row['Recyclable fraction']
                
                # Create waste bin object
                waste_bin = WasteBin(
                    bin_id=f"bin-{bin_id}",
                    location=location,
                    fill_level=fill_level,
                    capacity=100,  # Assuming 100% max
                    bin_type=bin_type,
                    container_type=container_type
                )
                bin_id += 1
                waste_bins.append(waste_bin)
                
                # Limit to 100 bins for better visualization
                if bin_id > 100:
                    break
                    
    except FileNotFoundError:
        print("Warning: Smart_Bin.csv not found. Using synthetic data.")
        waste_bins = generate_synthetic_waste_bins(30)
        
    return waste_bins

def generate_synthetic_waste_bins(count=30):
    """Generate synthetic waste bins if real data not available"""
    waste_bins = []
    for i in range(1, count+1):
        x = random.uniform(0, 50)
        y = random.uniform(0, 50)
        
        capacity = random.choice([100, 200, 300])
        fill_level = random.uniform(20, 95)
        
        waste_bin = WasteBin(
            bin_id=f"bin-{i}",
            location=(x, y),
            fill_level=fill_level,
            capacity=capacity,
            bin_type=random.choice(["Recyclable", "Non Recyclable", "Mixed"]),
            container_type=random.choice(["Cubic", "Rectangular", "Silvertop-a"])
        )
        waste_bins.append(waste_bin)
    return waste_bins

def assign_bins_to_districts(districts, waste_bins):
    """Assign waste bins to districts based on proximity"""
    # Get district centroids for distance calculation
    district_locations = {}
    try:
        with open('data/districts.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                district_id = int(row['district_id'])
                if district_id <= len(districts):
                    district_locations[district_id] = (float(row['centroid_x']), float(row['centroid_y']))
    except (FileNotFoundError, KeyError):
        # Generate random centroids if file not found
        for i, district in enumerate(districts):
            district_locations[district.district_id] = (
                random.uniform(10, 40),
                random.uniform(10, 40)
            )
    
    # Assign bins to nearest district
    for bin in waste_bins:
        nearest_district = min(
            districts,
            key=lambda d: ((bin.location[0] - district_locations.get(d.district_id, (25, 25))[0])**2 + 
                          (bin.location[1] - district_locations.get(d.district_id, (25, 25))[1])**2)
        )
        nearest_district.add_waste_bin(bin)
    
    return districts

def create_trucks():
    """Create waste collection trucks with different capacities and specializations"""
    trucks = [
        Truck(1, 1200, "Recyclable"),     # Specialized in recyclables, large capacity
        Truck(2, 1000, "Non Recyclable"),  # Specialized in non-recyclables, medium capacity
        Truck(3, 1500),                   # General purpose, largest capacity
        Truck(4, 800, "Recyclable"),      # Another recyclable truck, smaller capacity
        Truck(5, 900)                     # General purpose, medium capacity
    ]
    return trucks

def visualize_routes(assignments, show_plot=True):
    """Visualize truck routes on a map"""
    plt.figure(figsize=(12, 10))
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'teal', 'brown']
    markers = {'Recyclable': 'o', 'Non Recyclable': 's', 'Mixed': '^'}
    
    # Plot each district's routes with a different color
    for i, (district_id, assignment) in enumerate(assignments.items()):
        route = assignment['route']
        color = colors[i % len(colors)]
        
        # Plot waste bins
        for bin in route:
            marker = markers.get(bin.bin_type, 'o')
            plt.scatter(bin.location[0], bin.location[1], color=color, 
                       marker=marker, s=100, alpha=0.7)
        
        # Plot route lines
        for j in range(len(route) - 1):
            plt.plot([route[j].location[0], route[j+1].location[0]],
                     [route[j].location[1], route[j+1].location[1]],
                     color=color, linewidth=2, alpha=0.5)
            
        # Mark bin IDs
        for bin in route:
            plt.annotate(bin.bin_id, bin.location, fontsize=8)
    
    # Add a legend for waste bin types
    for bin_type, marker in markers.items():
        plt.scatter([], [], marker=marker, color='black', 
                   label=f"{bin_type} waste")
    
    plt.title("Waste Collection Routes by District")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.legend()
    plt.grid(True)
    plt.savefig("routes.png")
    
    if show_plot:
        plt.show()
    else:
        plt.close()

def main():
    print("Smart Waste Management System")
    print("-----------------------------")
    
    # Load real data from CSV files
    districts = load_districts_from_csv()
    waste_bins = load_waste_bins_from_csv()
    
    print(f"\nLoaded {len(waste_bins)} waste bins from Smart_Bin.csv")
    
    # Assign bins to districts
    districts = assign_bins_to_districts(districts, waste_bins)
    
    # Apply map coloring to segment districts
    print("\nApplying map coloring algorithm to segment districts...")
    colored_districts = map_coloring(districts)
    
    # Save district visualization without showing it
    visualize_districts(colored_districts, show_plot=False)
    
    # Print district information (simplified)
    print("\nDistrict Information:")
    for district in colored_districts:
        total_waste = sum(bin.current_level for bin in district.waste_bins)
        emptying_needed = sum(1 for bin in district.waste_bins if bin.emptying_needed)
        print(f"District {district.district_id} ({district.name}): Color = {district.color}, " 
              f"Bins = {len(district.waste_bins)}, Total Waste = {total_waste:.1f}")
    
    # Create trucks
    trucks = create_trucks()
    
    # Optimize routes and assign trucks
    print("\nOptimizing routes using backtracking...")
    assignments = assign_trucks_to_districts(trucks, colored_districts)
    
    # Print assignment results (simplified)
    print("\nTruck Assignments:")
    for district_id, assignment in assignments.items():
        district = next(d for d in districts if d.district_id == district_id)
        route = assignment['route']
        distance = assignment['distance']
        truck = assignment['truck']
        
        waste_to_collect = sum(bin.current_level for bin in route)
        print(f"District {district_id} ({district.name}) - Truck {truck.truck_id}: "
              f"Bins = {len(route)}, Waste = {waste_to_collect:.1f}, Distance = {distance:.1f}")
    
    # Save route visualization without showing it
    visualize_routes(assignments, show_plot=False)
    
    print("\nWaste management optimization complete!")
    print("Results saved to district_map.png and routes.png")

if __name__ == "__main__":
    main() 