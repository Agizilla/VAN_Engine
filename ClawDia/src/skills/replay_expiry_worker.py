from .base import BaseSkill, register_skill, SkillContext
from .replay_audit import ReplayAuditSkill


@register_skill("replay_expiry_worker", "system")
class ReplayExpiryWorker(BaseSkill):
    name = "replay_expiry_worker"
    description = "Periodic worker that expires old replay_audit events"
    author = "DeepSeek / ARC / ClawDia"
    version = "1.0.0"
    category = "system"
    tags = ["maintenance", "expiry", "audit"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["run", "status"], "default": "run"},
        },
    }
    INTERVAL_HOURS = 24

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "run")
        if action == "status":
            return {"error": None, "result": {"interval_hours": self.INTERVAL_HOURS, "skill": "replay_expiry_worker"}}
        return self._run()

    def _run(self) -> dict:
        audit = ReplayAuditSkill()
        result = audit.execute(action="expire")
        if result.get("error"):
            self.publish("replay_expiry:failed", {"error": result["error"]})
            return result
        self.publish("replay_expiry:completed", result.get("result", {}))
        return {"error": None, "result": {"expired": result.get("result", {}).get("deleted", 0)}}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, dict):
            result = self.execute(**payload)
        else:
            result = self.execute(action="run")
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]
