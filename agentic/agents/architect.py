from .base import Agent
class Architect(Agent):
    role='architect'
    def execute(self, context): return {'layers':['API','service','repository','SQLite/PostgreSQL'],'focus':'URL Shortener'}
