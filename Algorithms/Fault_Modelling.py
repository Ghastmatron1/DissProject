# Fault Modelling class
# Class will be for modelling faults in the houses, such as damp, structural damage, etc

class Fault_Modelling:
    def __init__(self, house): # house will be object from housing class
        self.house = house
        self.age = house.age
        self.maintenance_history = house.maintenance_history
        self.location = house.location
        self.materials = house.materials
        self.occupancy = house.occupancy
        #placeholder faults and values for the sake of programming the model, these will be based on real data in the future
        self.faults = {
            "damp": {
                "base_probability": 0.05, #placeholder value
                "factors": ["age", "wall_type", "ventilation", "climate"]
            },
            "boiler_failure": {
                "base_probability": 0.03, #placeholder value
                "factors": ["age", "maintenance_history", "usage"]
            },
            "structural_damage": {
                "base_probability": 0.02, #placeholder value
                "factors": ["age", "materials", "occupancy"]
            },
            "electrical_fault": {
                "base_probability": 0.04, #placeholder value
                "factors": ["age", "maintenance_history", "usage"]
            },
            "plumbing_issue": {
                "base_probability": 0.03, #placeholder value
                "factors": ["age", "maintenance_history", "usage"]
            },
            "roof_leak": {
                "base_probability": 0.02, #placeholder value
                "factors": ["age", "materials", "climate"]
            },
            "foundation_issue": {
                "base_probability": 0.01, #placeholder value
                "factors": ["age", "materials", "occupancy"]
            },
        }

    def calculate_fault_probability(self, fault):
        '''
        Calculates the probability of a specific fault occurring based on the house's attributes and the fault's factors.
        Will be using data from the EHS to determine the weights for each factor
        Need to do research into how variables effect each fault, like age, boiler age, ect
        :param fault:
        :return: probability of the fault occurring
        '''
        if fault not in self.faults:
            raise ValueError(f"Fault '{fault}' not recognized.")

        fault_info = self.faults[fault]
        probability = fault_info["base_probability"]
        for factor in fault_info["factors"]:
            if factor == "age":
                probability += self.age * 0.001 #placeholder weight
            elif factor == "maintenance_history":
                probability -= self.maintenance_history * 0.002 #placeholder weight
            elif factor == "materials":
                if self.materials == "brick":
                    probability -= 0.01 #placeholder value
                elif self.materials == "wood":
                    probability += 0.01 #placeholder value
            elif factor == "occupancy":
                if self.occupancy > 4:
                    probability += 0.01 #placeholder value
            # Add more factors and their effects as needed




