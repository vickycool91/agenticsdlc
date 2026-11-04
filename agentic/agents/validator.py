from .base import Agent
class Validator(Agent):
    role='validator'
    def execute(self, context): return {'checks':['artifact completeness','Python syntax','API contract','reference tests']}
