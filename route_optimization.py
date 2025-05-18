import math
import time
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

def optimize_route_backtracking(truck, waste_bins, start_point=None, max_bins=15, time_limit=5.0):
    """
    Use backtracking with optimizations to find optimal route for a truck to collect waste.
    Returns the optimized route and its distance.
    
    Args:
        truck: The truck object
        waste_bins: List of waste bins that need collection
        start_point: Starting location coordinates (x,y)
        max_bins: Maximum number of bins to consider for optimization (limits complexity)
        time_limit: Maximum time in seconds to spend on optimization
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
    
    # Limit the number of bins to process to avoid exponential complexity
    priority_bins = priority_bins[:max_bins]
    
    best_route = []
    best_distance = float('inf')
    visited = [False] * len(priority_bins)
    current_route = []
    current_load = 0
    start_time = time.time()
    
    def backtrack(position, current_distance):
        nonlocal best_route, best_distance, current_route, current_load
        
        # Check if time limit is reached
        if time.time() - start_time > time_limit:
            return
        
        # If all bins that can fit are visited or truck is full
        if all(visited) or current_load >= truck.capacity * 0.9:
            # Complete path found, check if it's better
            if current_distance < best_distance:
                best_distance = current_distance
                best_route = current_route.copy()
            return
        
        # Sort remaining bins by distance to current position for better pruning
        remaining_indices = []
        for i in range(len(priority_bins)):
            if not visited[i] and current_load + priority_bins[i].current_level <= truck.capacity:
                if not truck.bin_type_specialty or priority_bins[i].bin_type == truck.bin_type_specialty or priority_bins[i].bin_type == "Mixed":
                    dist_to_bin = 0
                    if position is not None:
                        if current_route:
                            dist_to_bin = distance(current_route[-1], priority_bins[i])
                        else:
                            # Distance from start point to first bin
                            x, y = position
                            start_bin = WasteBin(bin_id="-1", location=position, fill_level=0)  # Dummy bin for calculation
                            dist_to_bin = distance(start_bin, priority_bins[i])
                    remaining_indices.append((i, dist_to_bin))
        
        # Sort by distance (nearest first) for better pruning
        remaining_indices.sort(key=lambda x: x[1])
        
        for i, dist_to_bin in remaining_indices:
            # Skip if truck specializes in a waste type and this bin doesn't match (unless mixed)
            if (truck.bin_type_specialty and 
                priority_bins[i].bin_type != truck.bin_type_specialty and 
                priority_bins[i].bin_type != "Mixed"):
                continue
                
            # Try this bin
            visited[i] = True
            current_route.append(priority_bins[i])
            current_load += priority_bins[i].current_level
            
            # Recursive call
            backtrack(priority_bins[i].location, current_distance + dist_to_bin)
            
            # If we've found a good enough solution or reached time limit, stop searching
            if best_distance < float('inf') and time.time() - start_time > time_limit:
                return
            
            # Backtrack
            visited[i] = False
            current_route.pop()
            current_load -= priority_bins[i].current_level
    
    # Start the backtracking process
    backtrack(start_point, 0)
    
    # If we couldn't find a route with backtracking (due to time constraints),
    # fall back to a greedy approach
    if not best_route and priority_bins:
        print(f"Fallback to greedy algorithm for truck {truck.truck_id}")
        return greedy_route_optimization(truck, priority_bins, start_point)
        
    return best_route, best_distance

def greedy_route_optimization(truck, waste_bins, start_point=None):
    """
    A faster greedy algorithm for route optimization when backtracking is too slow.
    Always picks the nearest bin that fits in the truck.
    """
    route = []
    remaining_bins = waste_bins.copy()
    current_load = 0
    total_distance = 0
    current_position = start_point
    
    while remaining_bins and current_load < truck.capacity * 0.9:
        # Find nearest bin that fits
        nearest_bin = None
        nearest_distance = float('inf')
        nearest_idx = -1
        
        for i, bin in enumerate(remaining_bins):
            # Skip if bin would overload truck
            if current_load + bin.current_level > truck.capacity:
                continue
                
            # Skip if truck specializes in a waste type and this bin doesn't match
            if (truck.bin_type_specialty and 
                bin.bin_type != truck.bin_type_specialty and 
                bin.bin_type != "Mixed"):
                continue
            
            # Calculate distance to this bin
            if current_position:
                if route:
                    dist = distance(route[-1], bin)
                else:
                    # Distance from start point to first bin
                    start_bin = WasteBin(bin_id="-1", location=current_position, fill_level=0)
                    dist = distance(start_bin, bin)
            else:
                dist = 0
                
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_bin = bin
                nearest_idx = i
        
        # If found a bin that fits, add it to the route
        if nearest_bin:
            route.append(nearest_bin)
            current_load += nearest_bin.current_level
            total_distance += nearest_distance
            current_position = nearest_bin.location
            del remaining_bins[nearest_idx]
        else:
            # No more bins fit in the truck
            break
    
    return route, total_distance

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
                    print(f"Optimizing routes for District {district.district_id} with Truck {truck.truck_id} (Recyclable specialist)...")
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
                    print(f"Optimizing routes for District {district.district_id} with Truck {truck.truck_id} (Non-Recyclable specialist)...")
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
            print(f"Optimizing routes for District {district.district_id} with Truck {truck.truck_id} (General purpose)...")
            route, distance = optimize_route_backtracking(truck, district.waste_bins, (0, 0))
            
            if route:
                truck.route = route
                assignments[district.district_id] = {
                    "truck": truck,
                    "route": route,
                    "distance": distance
                }
    
    return assignments 