from .base import Agent
class Reviewer(Agent):
    role='reviewer'
    def execute(self, context): return {'human_approval_required':True,'auto_deploy':False}
