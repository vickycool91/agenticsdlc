from .base import Agent
class Engineer(Agent):
    role='engineer'
    def execute(self, context): return {'assignment':'URL Shortener','output':'Generated source, API contract and tests'}
