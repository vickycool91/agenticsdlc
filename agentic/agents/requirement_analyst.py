from .base import Agent
class RequirementAnalyst(Agent):
    role='requirement_analyst'
    def execute(self, context):
        from agentic.planner import normalize
        return normalize(context['requirement'],context.get('scenario','greenfield'),context.get('repository_context',''))
