"""Tests for the headless rendering stage."""

from src.stages.render import RenderStage, CAREER_TERMS, BLOCKED_RESOURCE_TYPES


def test_render_stage_name():
    """Render stage has the correct name."""
    assert RenderStage().name == "render"


def test_career_terms_multilingual():
    """Career terms include multiple languages."""
    assert "careers" in CAREER_TERMS
    assert "jobs" in CAREER_TERMS
    assert "karriere" in CAREER_TERMS
    assert "carreiras" in CAREER_TERMS
    assert "trabalhe conosco" in CAREER_TERMS


def test_blocked_resource_types():
    """Unnecessary resources are blocked for faster rendering."""
    assert "image" in BLOCKED_RESOURCE_TYPES
    assert "stylesheet" in BLOCKED_RESOURCE_TYPES
    assert "font" in BLOCKED_RESOURCE_TYPES
    assert "media" in BLOCKED_RESOURCE_TYPES
