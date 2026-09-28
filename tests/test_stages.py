"""Tests for discovery stages."""

from src.stages.seed import SeedStage
from src.stages.ats_verify import ATSVerifyStage
from src.stages.website import WebsiteStage
from src.stages.crawl import CrawlStage
from src.stages.slug_probe import SlugProbeStage


def test_stage_names():
    """Each stage has a unique name."""
    assert SeedStage().name == "seed"
    assert ATSVerifyStage().name == "ats_verify"
    assert WebsiteStage().name == "website"
    assert CrawlStage().name == "crawl"
    assert SlugProbeStage().name == "slug_probe"


def test_seed_stage_is_aggregator():
    """Seed stage correctly identifies aggregator URLs."""
    stage = SeedStage()
    assert stage._is_aggregator("https://www.linkedin.com/company/acme/jobs") is True
    assert stage._is_aggregator("https://angel.co/company/acme/jobs") is True
    assert stage._is_aggregator("https://x.com/acme") is True
    assert stage._is_aggregator("https://acme.com/careers") is False


def test_seed_stage_is_careers_page():
    """Seed stage correctly identifies careers pages."""
    stage = SeedStage()
    assert stage._is_careers_page("https://acme.com/careers") is True
    assert stage._is_careers_page("https://acme.com/jobs") is True
    assert stage._is_careers_page("https://acme.com/about/careers") is True
    assert stage._is_careers_page("https://acme.com/about") is False


def test_slug_probe_generates_slugs():
    """Slug probe generates candidate slugs from company name and domain."""
    from src.models import Company

    stage = SlugProbeStage()
    company = Company(
        id="test",
        name="Acme Corp",
        name_normalized="acme corp",
        official_domain="acme.com",
    )
    slugs = stage._generate_slugs(company)
    assert "acmecorp" in slugs
    assert "acme" in slugs
