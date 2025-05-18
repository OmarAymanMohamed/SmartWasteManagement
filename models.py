class District:
    def __init__(self, district_id, name, adjacent_districts=None):
        self.district_id = district_id
        self.name = name
        self.adjacent_districts = adjacent_districts or []
        self.color = None
        self.waste_bins = []
    
    def add_adjacent_district(self, district):
        if district not in self.adjacent_districts:
            self.adjacent_districts.append(district)
            district.adjacent_districts.append(self)
    
    def add_waste_bin(self, waste_bin):
        self.waste_bins.append(waste_bin)


class WasteBin:
    def __init__(self, bin_id, location, fill_level, capacity=100, bin_type="Mixed", container_type="Standard"):
        self.bin_id = bin_id
        self.location = location  # (x, y) coordinates
        self.capacity = capacity  # maximum capacity in kg or percentage
        self.current_level = fill_level  # current fill level (FL_B in dataset)
        self.emptying_needed = self.current_level > 65  # Based on fill level threshold
        self.container_type = container_type  # From Container Type in dataset
        self.bin_type = bin_type  # From Recyclable fraction in dataset
    
    @property
    def fill_percentage(self):
        return (self.current_level / self.capacity) * 100


class Truck:
    def __init__(self, truck_id, capacity, bin_type_specialty=None):
        self.truck_id = truck_id
        self.capacity = capacity  # maximum capacity in kg
        self.current_load = 0
        self.route = []  # list of WasteBin objects to visit
        self.bin_type_specialty = bin_type_specialty  # Trucks can specialize in certain waste types
    
    def add_bin_to_route(self, waste_bin):
        if self.can_handle(waste_bin):
            self.route.append(waste_bin)
            return True
        return False
    
    def can_handle(self, waste_bin):
        # Check if truck has capacity and handles this bin type (if specialization exists)
        if self.bin_type_specialty and waste_bin.bin_type != self.bin_type_specialty and waste_bin.bin_type != "Mixed":
            return False
        return self.current_load + waste_bin.current_level <= self.capacity
    
    def collect_waste(self, waste_bin):
        if self.can_handle(waste_bin):
            self.current_load += waste_bin.current_level
            waste_bin.current_level = 0
            return True
        return False 