from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from ...skills.loader import SkillLoader


class SkillExecute(BaseModel):
    name: str
    params: dict = {}


def get_loader(request: Request) -> SkillLoader:
    return request.app.state.skill_loader


router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/")
def list_skills(loader: SkillLoader = Depends(get_loader)):
    skills = loader.discover_skills()
    return [{"name": s.name, "description": s.description, "category": s.category} for s in skills]


@router.get("/registered")
def list_registered():
    from ...skills.base import get_registered_skills
    return list(get_registered_skills().keys())


@router.post("/execute")
def execute_skill(data: SkillExecute, loader: SkillLoader = Depends(get_loader)):
    skills = loader.discover_skills()
    for s in skills:
        if s.name == data.name:
            result = s.execute(**data.params)
            if isinstance(result, dict):
                return result
            return {"status": "ok", "message": str(result)}
    raise HTTPException(404, f"Skill '{data.name}' not found")
