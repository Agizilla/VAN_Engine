from src.ui.console import ConsoleUI
from src.ui.menu import Menu, MenuItem
from src.ui.app import ClawDiaApp
from src.skills.loader import SkillLoader
from src.skills.registry import detect_capabilities, CapabilityReport
from src.skills.base import SKILL_REGISTRY


def test_console_ui_creates():
    ui = ConsoleUI()
    assert ui is not None
    assert ui.width > 0


def test_menu_add_items():
    menu = Menu("Test")
    calls = []
    menu.add("Alpha", lambda _: calls.append("a"), "A")
    menu.add("Beta", lambda _: calls.append("b"), "B")
    assert len(menu.items) == 2
    assert menu.items[0].label == "Alpha"
    assert menu.items[0].key == "A"


def test_capability_report():
    report = CapabilityReport({"librosa": True, "opencv": False})
    assert report.audio is True
    assert report.vision is False
    assert report.summary() == "Audio"
    assert report.to_dict() == {"librosa": True, "opencv": False}


def test_detect_capabilities_runs():
    report = detect_capabilities()
    assert isinstance(report, CapabilityReport)
    assert isinstance(report.audio, bool)
    assert isinstance(report.vision, bool)
    assert isinstance(report.video, bool)


def test_skill_loader_empty_registry():
    SKILL_REGISTRY.clear()
    loader = SkillLoader()
    skills = loader.discover_skills()
    assert isinstance(skills, list)


def test_clawdia_app_creates():
    app = ClawDiaApp()
    assert app.ui is not None
    assert app.skill_loader is not None
