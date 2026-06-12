from src.skills.base import BaseSkill, register_skill, get_registered_skills, SKILL_REGISTRY
import src.skills.audio_skills
import src.skills.vision_skills
import src.skills.video_skills


class _ConcreteSkill(BaseSkill):
    name = "test_skill"
    description = "A test skill"
    category = "test"
    required_libs = []

    def execute(self, **kwargs):
        return {"status": "ok", **kwargs}


def test_abstract_cannot_instantiate():
    import pytest
    with pytest.raises(TypeError):
        BaseSkill()


def test_concrete_skill():
    skill = _ConcreteSkill()
    assert skill.name == "test_skill"
    assert skill.description == "A test skill"
    assert skill.category == "test"
    assert skill.execute(path="foo") == {"status": "ok", "path": "foo"}


def test_get_metadata():
    skill = _ConcreteSkill()
    meta = skill.get_metadata()
    assert meta["name"] == "test_skill"
    assert meta["category"] == "test"


@register_skill("decorated_test", "test_cat")
class _DecoratedSkill(BaseSkill):
    name = "decorated_test"
    description = "Decorated registration"
    category = "test_cat"
    required_libs = []

    def execute(self, **kwargs):
        return {"ok": True}


def test_empty_registry():
    registered = get_registered_skills()
    assert isinstance(registered, dict)


def test_decorator():
    registered = get_registered_skills()
    assert "decorated_test" in registered
    assert registered["decorated_test"]["category"] == "test_cat"


def test_stub_skills_import():
    from src.skills.audio_skills import AudioTranscribeSkill
    from src.skills.video_skills import VideoSceneDetectSkill
    from src.skills.vision_skills import VisionDetectSkill
    audio = AudioTranscribeSkill()
    assert audio.name == "audio_transcribe"
    assert audio.required_libs == ["librosa"]
    assert VideoSceneDetectSkill().name == "video_scenes"
    assert VisionDetectSkill().name == "vision_detect"


def test_skill_loader_discovers_stubs():
    from src.skills.loader import SkillLoader
    loader = SkillLoader()
    skills = loader.discover_skills()
    names = [s.name for s in skills]
    assert "audio_transcribe" in names
    assert "vision_detect" in names
    assert "video_trim" in names
