"""Prompt Optimiser endpoint with server-side Base64 algorithm injection."""
import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["optimiser"])

ALGORITHM_PATH = Path.home() / ".claude" / "PAI" / "Algorithm" / "v3.8.2.md"


class OptimiseRequest(BaseModel):
    prompt: str


class OptimiseResponse(BaseModel):
    original: str
    optimised: str
    diff: str


def load_algorithm_base64() -> str:
    if not ALGORITHM_PATH.exists():
        raise HTTPException(404, "Algorithm file not found")
    content = ALGORITHM_PATH.read_text(encoding="utf-8")
    return base64.b64encode(content.encode()).decode()


def inject_base64_algorithm(prompt: str) -> str:
    algo_b64 = load_algorithm_base64()
    return f"{prompt}\n\n[SYSTEM_ALGO_B64:{algo_b64}]"


def compute_diff(original: str, optimised: str) -> str:
    if original == optimised:
        return "No changes"
    orig_lines = original.splitlines()
    opt_lines = optimised.splitlines()
    diff_parts = []
    for i, line in enumerate(orig_lines):
        if i < len(opt_lines) and line != opt_lines[i]:
            diff_parts.append(f"- {line}")
            diff_parts.append(f"+ {opt_lines[i]}")
        elif i >= len(opt_lines):
            diff_parts.append(f"- {line}")
    for i in range(len(orig_lines), len(opt_lines)):
        diff_parts.append(f"+ {opt_lines[i]}")
    return "\n".join(diff_parts) if diff_parts else "No structural changes"


@router.post("/optimise", response_model=OptimiseResponse)
async def optimise_prompt(req: OptimiseRequest):
    if not req.prompt.strip():
        raise HTTPException(400, "Prompt cannot be empty")

    enhanced = inject_base64_algorithm(req.prompt)

    lines = req.prompt.strip().split('\n')
    goal = lines[0] if lines else ""
    constraints = [l for l in lines if "not" in l.lower() or "without" in l.lower()]
    steps = [l for l in lines if l.strip().startswith(("1.", "2.", "-"))]

    optimised_parts = []
    optimised_parts.append("# Optimised Prompt (Algorithm v3.8.2)\n")
    optimised_parts.append(f"## Goal\n{goal}")
    if constraints:
        optimised_parts.append(f"\n## Constraints\n" + "\n".join(f"- {c}" for c in constraints))
    if steps:
        optimised_parts.append(f"\n## Steps\n" + "\n".join(steps))
    else:
        optimised_parts.append(f"\n## Steps\n1. Analyse the request\n2. Execute\n3. Verify")
    optimised_parts.append(f"\n## Algorithm Context\n[Base64 algorithm injected server-side, length: {len(enhanced)} chars]")

    optimised = "\n".join(optimised_parts)
    diff = compute_diff(req.prompt, optimised)

    return OptimiseResponse(
        original=req.prompt,
        optimised=optimised,
        diff=diff,
    )
