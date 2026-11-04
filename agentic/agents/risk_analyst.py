from .base import Agent
class RiskAnalyst(Agent):
    role='risk_analyst'
    def execute(self, context): return {'risks':['URL abuse','code collision','analytics write load','SQLite concurrency']}
