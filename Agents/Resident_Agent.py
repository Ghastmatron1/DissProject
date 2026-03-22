import langgraph

class ResidentAgent(langgraph.Agent):
    def __init__(self, name):
        super().__init__(name)
        self.knowledge = {}

    def receive_information(self, info):
        self.knowledge.update(info)

    def share_information(self):
        return self.knowledge

    def make_decision(self):
        # Placeholder for decision-making logic based on knowledge
        if 'emergency' in self.knowledge:
            return "Evacuate"
        elif 'event' in self.knowledge:
            return "Attend Event"
        else:
            return "No Action"
