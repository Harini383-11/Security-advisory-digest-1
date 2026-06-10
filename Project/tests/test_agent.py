"""
Tests for agent workflow module.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from agent import SecurityAdvisoryAgent
from models import AdvisoryDB, InventoryItemDB


@pytest.fixture
def temp_dir():
    """Fixture for temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_advisories():
    """Fixture for sample advisories."""
    return [
        AdvisoryDB(
            advisory_id="test_001",
            title="Apache Vulnerability",
            description="Critical Apache vulnerability",
            severity="CRITICAL",
            vendor="Apache",
            product="Apache",
            published_date=datetime.now(),
            source_feed="https://example.com/feed1",
            url="https://example.com/1"
        ),
        AdvisoryDB(
            advisory_id="test_002",
            title="Nginx Security Issue",
            description="Nginx security update",
            severity="HIGH",
            vendor="Nginx",
            product="Nginx",
            published_date=datetime.now(),
            source_feed="https://example.com/feed1",
            url="https://example.com/2"
        ),
    ]


@pytest.fixture
def sample_inventory():
    """Fixture for sample inventory."""
    return [
        InventoryItemDB(
            id=1,
            asset_id="app_001",
            software_name="Apache",
            version="2.4"
        ),
        InventoryItemDB(
            id=2,
            asset_id="app_002",
            software_name="Nginx",
            version="1.22"
        ),
    ]


@patch("agent.Database")
@patch("agent.RSSIngester")
@patch("agent.InventoryMatchService")
@patch("agent.LLMService")
def test_agent_initialization(mock_llm, mock_inventory_service, mock_rss, mock_db):
    """Test agent initialization."""
    agent = SecurityAdvisoryAgent()
    
    assert agent is not None
    assert agent.database is not None
    assert agent.rss_ingester is not None
    assert agent.inventory_service is not None
    assert agent.llm_service is not None


@patch("agent.Database")
@patch("agent.RSSIngester")
@patch("agent.InventoryMatchService")
@patch("agent.LLMService")
def test_step_1_read_feeds(mock_llm, mock_inventory_service, mock_rss, mock_db, sample_advisories):
    """Test step 1: read feeds."""
    mock_rss_instance = MagicMock()
    mock_rss.return_value = mock_rss_instance
    mock_rss_instance.ingest_feed.return_value = sample_advisories
    
    agent = SecurityAdvisoryAgent()
    
    with patch("agent.RSS_FEEDS", ["https://example.com/feed1"]):
        advisories = agent._step_1_read_feeds()
    
    assert len(advisories) > 0
    assert advisories[0].advisory_id == "test_001"


@patch("agent.Database")
@patch("agent.RSSIngester")
@patch("agent.InventoryMatchService")
@patch("agent.LLMService")
def test_step_2_store_advisories(mock_llm, mock_inventory_service, mock_rss, mock_db, sample_advisories):
    """Test step 2: store advisories."""
    mock_db_instance = MagicMock()
    mock_db.return_value = mock_db_instance
    mock_db_instance.add_advisory.return_value = 1
    
    agent = SecurityAdvisoryAgent()
    agent.database = mock_db_instance
    
    count = agent._step_2_store_advisories(sample_advisories)
    
    assert count == len(sample_advisories)


@patch("agent.Database")
@patch("agent.RSSIngester")
@patch("agent.InventoryMatchService")
@patch("agent.LLMService")
def test_step_3_load_inventory(mock_llm, mock_inventory_service, mock_rss, mock_db, sample_inventory):
    """Test step 3: load inventory."""
    mock_inventory_instance = MagicMock()
    mock_inventory_service.return_value = mock_inventory_instance
    mock_inventory_instance.load_inventory_from_csv.return_value = sample_inventory
    
    mock_db_instance = MagicMock()
    mock_db.return_value = mock_db_instance
    
    agent = SecurityAdvisoryAgent()
    agent.database = mock_db_instance
    agent.inventory_service = mock_inventory_instance
    
    with patch("agent.INVENTORY_FILE", Path("dummy.csv")):
        inventory = agent._step_3_load_inventory()
    
    assert len(inventory) > 0


@patch("agent.Database")
@patch("agent.RSSIngester")
@patch("agent.InventoryMatchService")
@patch("agent.LLMService")
def test_step_4_match_advisories(mock_llm, mock_inventory_service, mock_rss, mock_db, sample_advisories, sample_inventory):
    """Test step 4: match advisories."""
    mock_db_instance = MagicMock()
    mock_db.return_value = mock_db_instance
    
    # Mock the matcher
    mock_inventory_instance = MagicMock()
    mock_matcher = MagicMock()
    mock_matcher.find_matches.return_value = [(sample_inventory[0], "CRITICAL")]
    mock_inventory_instance.matcher = mock_matcher
    
    mock_inventory_service.return_value = mock_inventory_instance
    
    agent = SecurityAdvisoryAgent()
    agent.database = mock_db_instance
    agent.inventory_service = mock_inventory_instance
    
    # Mock get_advisory_by_id_string
    mock_db_instance.get_advisory_by_id_string.return_value = sample_advisories[0]
    mock_db_instance.get_advisory_by_id_string.id = 1
    mock_db_instance.add_match.return_value = 1
    
    matches = agent._step_4_match_advisories(sample_advisories, sample_inventory)
    
    assert isinstance(matches, dict)


@patch("agent.Database")
@patch("agent.RSSIngester")
@patch("agent.InventoryMatchService")
@patch("agent.LLMService")
def test_create_response(mock_llm, mock_inventory_service, mock_rss, mock_db):
    """Test response creation."""
    response = SecurityAdvisoryAgent._create_response(
        "success",
        "Test message",
        report=None,
        error=None
    )
    
    assert response["status"] == "success"
    assert response["message"] == "Test message"
    assert response["error"] is None


@patch("agent.Database")
@patch("agent.RSSIngester")
@patch("agent.InventoryMatchService")
@patch("agent.LLMService")
def test_create_response_error(mock_llm, mock_inventory_service, mock_rss, mock_db):
    """Test error response creation."""
    response = SecurityAdvisoryAgent._create_response(
        "error",
        "Operation failed",
        report=None,
        error="Test error"
    )
    
    assert response["status"] == "error"
    assert response["error"] == "Test error"
