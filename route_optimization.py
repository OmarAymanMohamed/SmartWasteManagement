import math
from models import Truck, WasteBin

def distance(bin1, bin2):
    """Calculate Euclidean distance between two waste bins"""
    x1, y1 = bin1.location
    x2, y2 = bin2.location
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def total_route_distance(route):
    """Calculate the total distance of a route"""
    total = 0
    for i in range(len(route) - 1):
        total += distance(route[i], route[i + 1])
    return total

def optimize_route_backtracking(truck, waste_bins, start_point=None):
    """
    Use backtracking to find optimal route for a truck to collect waste.
    Returns the optimized route and its distance.
    
    Args:
        truck: The truck object
        waste_bins: List of waste bins that need collection
        start_point: Starting location coordinates (x,y)
    """
    if not waste_bins:
        return [], 0
    
    # Filter bins that need emptying and those matching truck specialty
    priority_bins = [bin for bin in waste_bins if bin.emptying_needed]
    
    # If truck has specialty, prioritize bins of that type
    if truck.bin_type_specialty:
        matching_bins = [bin for bin in priority_bins 
                        if bin.bin_type == truck.bin_type_specialty or bin.bin_type == "Mixed"]
        if matching_bins:
            priority_bins = matching_bins
    
    # If no priority bins, use regular waste bins
    if not priority_bins:
        priority_bins = waste_bins
    
    # Sort bins by fill level to prioritize fuller bins
    priority_bins = sorted(priority_bins, key=lambda x: x.current_level, reverse=True)
    
    best_route = []
    best_distance = float('inf')
    visited = [False] * len(priority_bins)
    current_route = []
    current_load = 0
    
    def backtrack(position, current_distance):
        nonlocal best_route, best_distance, current_route, current_load
        
        # If all bins that can fit are visited or truck is full
        if all(visited) or current_load >= truck.capacity * 0.9:
            # Complete path found, check if it's better
            if current_distance < best_distance:
                best_distance = current_distance
                best_route = current_route.copy()
            return
        
        for i in range(len(priority_bins)):
            # Skip if already visited or bin would overload truck
            if visited[i] or current_load + priority_bins[i].current_level > truck.capacity:
                continue
                
            # Skip if truck specializes in a waste type and this bin doesn't match (unless mixed)
            if (truck.bin_type_specialty and 
                priority_bins[i].bin_type != truck.bin_type_specialty and 
                priority_bins[i].bin_type != "Mixed"):
                continue
                
            # Calculate distance from current position to this bin
            dist_to_bin = 0
            if position is not None:
                if current_route:
                    dist_to_bin = distance(current_route[-1], priority_bins[i])
                else:
                    # Distance from start point to first bin
                    x, y = position
                    start_bin = WasteBin(-1, position, 0, 0)  # Dummy bin for calculation
                    dist_to_bin = distance(start_bin, priority_bins[i])
            
            # Try this bin
            visited[i] = True
            current_route.append(priority_bins[i])
            current_load += priority_bins[i].current_level
            
            # Recursive call
            backtrack(priority_bins[i].location, current_distance + dist_to_bin)
            
            # Backtrack
            visited[i] = False
            current_route.pop()
            current_load -= priority_bins[i].current_level
    
    # Start the backtracking process
    backtrack(start_point, 0)
    return best_route, best_distance

def assign_trucks_to_districts(trucks, districts):
    """Assign trucks to districts based on waste volume and type"""
    assignments = {}
    
    # Sort districts by total waste volume
    districts_by_volume = sorted(
        districts,
        key=lambda d: sum(bin.current_level for bin in d.waste_bins if bin.emptying_needed),
        reverse=True
    )
    
    # Calculate waste type composition per district for better truck assignment
    district_stats = {}
    for district in districts:
        recyclable = sum(bin.current_level for bin in district.waste_bins 
                         if bin.bin_type == "Recyclable" and bin.emptying_needed)
        non_recyclable = sum(bin.current_level for bin in district.waste_bins 
                            if bin.bin_type == "Non Recyclable" and bin.emptying_needed)
        mixed = sum(bin.current_level for bin in district.waste_bins 
                   if bin.bin_type == "Mixed" and bin.emptying_needed)
        total = recyclable + non_recyclable + mixed
        
        district_stats[district.district_id] = {
            "recyclable": recyclable,
            "non_recyclable": non_recyclable,
            "mixed": mixed,
            "total": total,
            "district": district
        }
    
    # Sort trucks by capacity
    available_trucks = sorted(trucks, key=lambda t: t.capacity, reverse=True)
    
    # First pass - assign specialized trucks to districts with matching waste types
    for district in districts_by_volume:
        if district.district_id in assignments:
            continue
            
        stats = district_stats[district.district_id]
        
        # Find the best specialized truck if the district has significant amounts of one waste type
        if stats["recyclable"] > stats["non_recyclable"] and stats["recyclable"] > stats["mixed"]:
            # Look for recyclable specialized truck
            for i, truck in enumerate(available_trucks):
                if truck.bin_type_specialty == "Recyclable":
                    route, distance = optimize_route_backtracking(truck, district.waste_bins, (0, 0))
                    if route:
                        truck.route = route
                        assignments[district.district_id] = {
                            "truck": truck,
                            "route": route,
                            "distance": distance
                        }
                        available_trucks.pop(i)
                        break
        
        elif stats["non_recyclable"] > stats["recyclable"] and stats["non_recyclable"] > stats["mixed"]:
            # Look for non-recyclable specialized truck
            for i, truck in enumerate(available_trucks):
                if truck.bin_type_specialty == "Non Recyclable":
                    route, distance = optimize_route_backtracking(truck, district.waste_bins, (0, 0))
                    if route:
                        truck.route = route
                        assignments[district.district_id] = {
                            "truck": truck,
                            "route": route,
                            "distance": distance
                        }
                        available_trucks.pop(i)
                        break
    
    # Second pass - assign remaining districts to remaining trucks
    for district in districts_by_volume:
        if district.district_id in assignments:
            continue
            
        if available_trucks:
            truck = available_trucks.pop(0)
            route, distance = optimize_route_backtracking(truck, district.waste_bins, (0, 0))
            
            if route:
                truck.route = route
                assignments[district.district_id] = {
                    "truck": truck,
                    "route": route,
                    "distance": distance
                }
    
    return assignments 