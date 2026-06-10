"""
Tests for RSS ingestion module.
"""
import pytest
from datetime import datetime
from ingestion.rss import RSSIngester
from models import AdvisoryDB


@pytest.fixture
def rss_ingester():
    """Fixture for RSS ingester."""
    return RSSIngester()


def test_rss_ingester_initialization(rss_ingester):
    """Test RSS ingester initialization."""
    assert rss_ingester is not None
    assert rss_ingester.session is not None


def test_extract_vendor():
    """Test vendor extraction."""
    text = "Apache Web Server Vulnerability"
    vendor = RSSIngester._extract_vendor(text)
    assert vendor == "Apache"


def test_extract_severity_critical():
    """Test severity extraction for critical."""
    title = "Critical Vulnerability"
    description = "This is a critical security issue"
    severity = RSSIngester._extract_severity(title, description)
    assert severity == "CRITICAL"


def test_extract_severity_high():
    """Test severity extraction for high."""
    title = "High Risk Vulnerability"
    description = "High severity security issue"
    severity = RSSIngester._extract_severity(title, description)
    assert severity == "HIGH"


def test_extract_severity_medium():
    """Test severity extraction for medium."""
    title = "Medium Priority Update"
    description = "Medium severity issue found"
    severity = RSSIngester._extract_severity(title, description)
    assert severity == "MEDIUM"


def test_extract_severity_low():
    """Test severity extraction for low."""
    title = "Low Priority Advisory"
    description = "Low severity vulnerability"
    severity = RSSIngester._extract_severity(title, description)
    assert severity == "LOW"


def test_parse_date_from_entry():
    """Test date parsing."""
    entry = {}
    entry["published_parsed"] = (2024, 1, 15, 10, 30, 0, 0, 0, 0)
    
    date = RSSIngester._parse_date(entry)
    assert isinstance(date, datetime)
    assert date.year == 2024
    assert date.month == 1
    assert date.day == 15


def test_parse_date_fallback():
    """Test date parsing fallback."""
    entry = {}
    
    date = RSSIngester._parse_date(entry)
    assert isinstance(date, datetime)
    assert date is not None


def test_rss_ingester_close(rss_ingester):
    """Test closing RSS ingester."""
    rss_ingester.close()
    # Verify no exception
    assert True


def test_parse_entry_basic():
    """Test parsing a basic RSS entry."""
    entry = {
        "title": "Apache HTTP Server Critical Vulnerability",
        "summary": "A critical vulnerability has been found in Apache",
        "link": "https://example.com/advisory/123",
        "published_parsed": (2024, 1, 15, 10, 30, 0, 0, 0, 0)
    }
    
    feed_url = "https://github.blog/security/feed/"
    advisory = RSSIngester._parse_entry(entry, feed_url)
    
    assert advisory is not None
    assert "Apache" in advisory.title
    assert advisory.vendor == "Apache"
    assert advisory.severity == "CRITICAL"
    assert advisory.source_feed == feed_url


def test_parse_entry_missing_fields():
    """Test parsing entry with missing fields."""
    entry = {
        "title": "Security Advisory",
    }
    
    feed_url = "https://example.com/feed"
    advisory = RSSIngester._parse_entry(entry, feed_url)
    
    assert advisory is not None
    assert advisory.title == "Security Advisory"
    assert advisory.description == ""
