from .base import Agent
class TechnicalWriter(Agent):
    role='technical_writer'
    def execute(self, context): return {'deliverables':['README','architecture','OpenAPI','engineering summary']}
