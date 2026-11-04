from .base import Agent
class Planner(Agent):
    role='planner'
    def execute(self, context):
        from agentic.planner import build_tasks
        return [t.view() for t in build_tasks(context.get('scenario','greenfield'))]
