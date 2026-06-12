"""Forge: Multi-Agent Collaboration Engine with SSE streaming."""
import asyncio
import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from skills_manager import discover_skills, format_result

logger = logging.getLogger(__name__)
router = APIRouter()


class ForgeContext:
    def __init__(self, seed: str, output_format: str = "html"):
        self.seed = seed
        self.output_format = output_format
        self.artifact = "" if output_format == "html" else ""
        self.artifacts: list[dict] = []
        self.round = 0
        self.log: list[dict] = []
        self._lock = asyncio.Lock()

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "output_format": self.output_format,
            "artifact": self.artifact,
            "artifacts": self.artifacts,
            "round": self.round,
            "log_count": len(self.log),
        }


def _tpl(s: str, ctx: ForgeContext, agent_name: str = "") -> str:
    s = s.replace("{seed}", ctx.seed)
    s = s.replace("{context}", ctx.artifact)
    s = s.replace("{agent}", agent_name)
    s = s.replace("{round}", str(ctx.round))
    s = s.replace("{ts}", str(time.time()))
    return s


async def _run_forge(
    agents: list[dict],
    iterations: int,
    seed: str,
    output_format: str,
    skills: dict,
):
    ctx = ForgeContext(seed, output_format)
    start_ts = time.time()
    session_id = uuid.uuid4().hex[:12]

    yield f"event: session_start\ndata: {json.dumps({'session_id': session_id, 'agents': len(agents), 'iterations': iterations})}\n\n"

    if output_format == "html":
        ctx.artifact = "<!DOCTYPE html>\n<html lang=\"en\">\n<head><meta charset=\"utf-8\">\n"
        ctx.artifact += f"<title>Forge: {seed[:40]}</title>\n"
        ctx.artifact += "<style>body{font-family:system-ui;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.6}</style>\n"
        ctx.artifact += "</head>\n<body>\n"
        ctx.artifact += f"<h1>Forge: {seed[:60]}</h1>\n<div class=\"forge-content\">\n"

    for iteration in range(1, iterations + 1):
        ctx.round = iteration
        yield f"event: round_start\ndata: {json.dumps({'round': iteration, 'total': iterations})}\n\n"

        for agent in agents:
            agent_name = agent.get("name", "agent")
            agent_role = agent.get("role", "")
            agent_skills = agent.get("skills", [])

            yield f"event: agent_start\ndata: {json.dumps({'agent': agent_name, 'role': agent_role, 'round': iteration})}\n\n"

            if not agent_skills:
                yield f"event: agent_skip\ndata: {json.dumps({'agent': agent_name, 'reason': 'no skills configured'})}\n\n"
                continue

            for skill_binding in agent_skills:
                skill_name = skill_binding.get("skill", "")
                param_tpls = skill_binding.get("params", {})

                skill = skills.get(skill_name)
                if not skill:
                    yield f"event: skill_error\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'error': 'Skill not found'})}\n\n"
                    continue

                resolved = {}
                for k, v in param_tpls.items():
                    if isinstance(v, str):
                        resolved[k] = _tpl(v, ctx, agent_name)
                    else:
                        resolved[k] = v

                yield f"event: skill_call\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'params': resolved})}\n\n"

                try:
                    result = skill.execute(**resolved) if hasattr(skill, "execute") else skill.run(payload=resolved)
                    if asyncio.iscoroutine(result):
                        result = await result
                    formatted = format_result(result)

                    entry = {
                        "agent": agent_name,
                        "skill": skill_name,
                        "params": resolved,
                        "result": formatted,
                        "round": iteration,
                        "timestamp": time.time(),
                    }
                    ctx.log.append(entry)
                    ctx.artifacts.append(entry)

                    result_text = json.dumps(formatted, indent=2)
                    if output_format == "html":
                        ctx.artifact += f"<div class=\"forge-entry\">\n"
                        ctx.artifact += f"  <h3>{agent_name} ({skill_name})</h3>\n"
                        ctx.artifact += f"  <pre>{result_text}</pre>\n"
                        ctx.artifact += f"</div>\n"
                    else:
                        ctx.artifact += f"\n--- {agent_name}/{skill_name} ---\n{result_text}\n"

                    yield f"event: skill_result\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'result': formatted, 'round': iteration})}\n\n"

                except Exception as e:
                    err_msg = f"{type(e).__name__}: {e}"
                    yield f"event: skill_error\ndata: {json.dumps({'agent': agent_name, 'skill': skill_name, 'error': err_msg})}\n\n"

            yield f"event: agent_done\ndata: {json.dumps({'agent': agent_name, 'round': iteration})}\n\n"

        yield f"event: progress\ndata: {json.dumps({'round': iteration, 'total': iterations, 'html': ctx.artifact if output_format == 'html' else '', 'artifact_length': len(ctx.artifact)})}\n\n"

    if output_format == "html":
        ctx.artifact += "</div>\n<footer><p>Generated by SAAS Forge in "
        ctx.artifact += f"{len(ctx.log)} skill calls across {iterations} rounds</p></footer>\n"
        ctx.artifact += "</body>\n</html>"

    elapsed = time.time() - start_ts
    complete_data = json.dumps({
        "session_id": session_id,
        "rounds": iterations,
        "skill_calls": len(ctx.log),
        "elapsed_seconds": round(elapsed, 2),
        "output_format": output_format,
        "artifact": ctx.artifact,
        "artifacts": ctx.artifacts,
    })
    yield f"event: complete\ndata: {complete_data}\n\n"


@router.post("/hooks/forge")
async def forge_endpoint(request: Request):
    try:
        raw = await request.body()
        body = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(422, "Invalid JSON body")

    agents = body.get("agents", [])
    if not agents or not isinstance(agents, list):
        raise HTTPException(422, "'agents' must be a non-empty array")

    iterations = body.get("iterations", 3)
    if not isinstance(iterations, int) or iterations < 1:
        raise HTTPException(422, "'iterations' must be a positive integer")

    seed = body.get("seed", "forge session")
    output_format = body.get("output_format", "html")
    skills = discover_skills()

    for agent in agents:
        for sb in agent.get("skills", []):
            sname = sb.get("skill", "")
            if sname and sname not in skills:
                raise HTTPException(422, f"Skill '{sname}' not found (agent '{agent.get('name', '?')}')")

    return StreamingResponse(
        _run_forge(agents, iterations, seed, output_format, skills),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
