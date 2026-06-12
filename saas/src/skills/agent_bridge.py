try:
    from ...agent.skill import AgentSkill
except ImportError:
    AgentSkill = None

try:
    from ...agent import __version__ as _agent_ver_str
    _agent_ver_parts = [int(p) for p in str(_agent_ver_str).split('.')[:2]]
except (ImportError, AttributeError, ValueError, TypeError):
    _agent_ver_parts = []

if _agent_ver_parts and _agent_ver_parts[0] < 1:
    import warnings
    warnings.warn(
        f"Agent module version {'.'.join(map(str, _agent_ver_parts))} may be incompatible"
    )

from ..base import register_skill

register_skill("Agent", "agent")(AgentSkill)
