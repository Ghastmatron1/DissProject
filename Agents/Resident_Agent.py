# Python
class ResidentAgent(Agent):
    def __init__(self, unique_id, model, job, salary, location, preferences, current_home):
        super().__init__(unique_id, model)
        self.job = job
        self.salary = salary
        self.location = location
        self.preferences = preferences
        self.current_home = current_home
        self.happiness = 0.5
        self.bank = None
        self.home = None
        self.family = {}
        self.education = None
        self.life_events = []

    def step(self):
        self.evaluate_finances()
        self.search_housing()
        self.interact_with_bank()
        self.update_happiness()

    def evaluate_finances(self):
        # Calculate disposable income and savings
        self.savings = self.salary * 0.2  # Example: Save 20% of salary
        self.disposable_income = self.salary - self.savings

    def search_housing(self):
        # Evaluate housing options based on preferences and finances
        available_houses = self.model.housing_units
        for house in available_houses:
            if house.price <= self.savings and house.location == self.preferences.get('location'):
                self.home = house
                break

    def interact_with_bank(self):
        # Choose a bank and apply for a mortgage
        if self.home:
            for bank in self.model.banks:
                if bank.mortgage_rate < 0.05:  # Example: Choose bank with low mortgage rate
                    self.bank = bank
                    break

    def update_happiness(self):
        # Update happiness based on housing, finances, and life events
        if self.home:
            self.happiness += 0.1
        if self.savings < 1000:
            self.happiness -= 0.1