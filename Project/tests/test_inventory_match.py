"""
Tests for inventory matching module.
"""
import pytest
from datetime import datetime
from inventory.matcher import InventoryMatcher
from models import AdvisoryDB, InventoryItemDB


@pytest.fixture
def matcher():
    """Fixture for inventory matcher."""
    return InventoryMatcher()


@pytest.fixture
def sample_advisory():
    """Fixture for sample advisory."""
    return AdvisoryDB(
        advisory_id="test_001",
        title="Apache HTTP Server Remote Code Execution",
        description="A critical vulnerability in Apache that allows remote code execution",
        severity="CRITICAL",
        vendor="Apache",
        product="Apache",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com/advisory/123"
    )


@pytest.fixture
def sample_inventory():
    """Fixture for sample inventory."""
    return [
        InventoryItemDB(id=1, asset_id="app_001", software_name="Apache", version="2.4"),
        InventoryItemDB(id=2, asset_id="app_002", software_name="Nginx", version="1.22"),
        InventoryItemDB(id=3, asset_id="app_003", software_name="OpenSSL", version="3.0"),
    ]


def test_matcher_initialization(matcher):
    """Test matcher initialization."""
    assert matcher is not None
    assert matcher.similarity_threshold == 0.6


def test_find_matches_exact(matcher, sample_advisory, sample_inventory):
    """Test finding exact matches."""
    matches = matcher.find_matches(sample_advisory, sample_inventory)
    
    assert len(matches) > 0
    assert matches[0][0].software_name == "Apache"


def test_find_matches_no_match(matcher, sample_inventory):
    """Test when no matches found."""
    advisory = AdvisoryDB(
        advisory_id="test_002",
        title="Windows Server Vulnerability",
        description="Vulnerability in Windows Server",
        severity="HIGH",
        vendor="Microsoft",
        product="Windows",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com/advisory/456"
    )
    
    matches = matcher.find_matches(advisory, sample_inventory)
    
    # Should not match since Windows is not in inventory
    assert len(matches) == 0


def test_calculate_risk_level_critical(matcher, sample_advisory):
    """Test risk level calculation for critical severity."""
    inventory_item = InventoryItemDB(
        id=1,
        asset_id="app_001",
        software_name="Apache",
        version="2.4"
    )
    
    risk_level = matcher._calculate_risk_level(sample_advisory, inventory_item)
    assert risk_level == "CRITICAL"


def test_calculate_risk_level_high():
    """Test risk level calculation for high severity."""
    advisory = AdvisoryDB(
        advisory_id="test_003",
        title="High Severity Advisory",
        description="Advisory",
        severity="HIGH",
        vendor="Test",
        product="Test",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com/advisory"
    )
    
    inventory_item = InventoryItemDB(
        id=1,
        asset_id="app_001",
        software_name="Test",
        version="1.0"
    )
    
    matcher = InventoryMatcher()
    risk_level = matcher._calculate_risk_level(advisory, inventory_item)
    assert risk_level == "HIGH"


def test_calculate_risk_level_low():
    """Test risk level calculation for low severity."""
    advisory = AdvisoryDB(
        advisory_id="test_004",
        title="Low Severity Advisory",
        description="Advisory",
        severity="LOW",
        vendor="Test",
        product="Test",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com/advisory"
    )
    
    inventory_item = InventoryItemDB(
        id=1,
        asset_id="app_001",
        software_name="Test",
        version="1.0"
    )
    
    matcher = InventoryMatcher()
    risk_level = matcher._calculate_risk_level(advisory, inventory_item)
    assert risk_level == "LOW"


def test_is_match_exact_product(matcher, sample_advisory, sample_inventory):
    """Test exact product name matching."""
    advisory_text = sample_advisory.title.lower() + " " + sample_advisory.description.lower()
    
    result = matcher._is_match(sample_advisory, sample_inventory[0], advisory_text)
    assert result is True


def test_is_match_partial_name(matcher, sample_inventory):
    """Test partial name matching."""
    advisory = AdvisoryDB(
        advisory_id="test_005",
        title="Nginx Web Server Vulnerability",
        description="Advisory about nginx",
        severity="MEDIUM",
        vendor="Nginx",
        product="Nginx",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com/advisory"
    )
    
    advisory_text = advisory.title.lower() + " " + advisory.description.lower()
    result = matcher._is_match(advisory, sample_inventory[1], advisory_text)
    assert result is True
