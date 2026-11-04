from .base import Agent
class TestEngineer(Agent):
    role='test_engineer'
    def execute(self, context): return {'checks':['validation','short-code uniqueness','redirects','analytics','unknown codes']}
