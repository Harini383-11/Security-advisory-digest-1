"""
Tests for SQLite database module.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from db.sqlite import Database
from models import AdvisoryDB, InventoryItemDB, MatchDB


@pytest.fixture
def temp_db():
    """Fixture for temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        yield db
        db.close()


@pytest.fixture
def sample_advisory():
    """Fixture for sample advisory."""
    return AdvisoryDB(
        advisory_id="test_advisory_001",
        title="Test Advisory",
        description="Test advisory description",
        severity="HIGH",
        vendor="TestVendor",
        product="TestProduct",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com/advisory"
    )


@pytest.fixture
def sample_inventory():
    """Fixture for sample inventory item."""
    return InventoryItemDB(
        asset_id="asset_001",
        software_name="TestSoftware",
        version="1.0"
    )


def test_database_initialization(temp_db):
    """Test database initialization."""
    assert temp_db is not None
    assert temp_db.db_path.exists()


def test_add_advisory(temp_db, sample_advisory):
    """Test adding advisory."""
    advisory_id = temp_db.add_advisory(sample_advisory)
    assert advisory_id is not None
    assert advisory_id > 0


def test_get_advisory_by_id_string(temp_db, sample_advisory):
    """Test retrieving advisory by ID string."""
    temp_db.add_advisory(sample_advisory)
    
    retrieved = temp_db.get_advisory_by_id_string(sample_advisory.advisory_id)
    assert retrieved is not None
    assert retrieved.title == sample_advisory.title


def test_get_advisory_by_id(temp_db, sample_advisory):
    """Test retrieving advisory by database ID."""
    advisory_id = temp_db.add_advisory(sample_advisory)
    
    retrieved = temp_db.get_advisory_by_id(advisory_id)
    assert retrieved is not None
    assert retrieved.advisory_id == sample_advisory.advisory_id


def test_get_all_advisories(temp_db, sample_advisory):
    """Test retrieving all advisories."""
    # Add multiple advisories
    for i in range(3):
        advisory = AdvisoryDB(
            advisory_id=f"test_advisory_{i:03d}",
            title=f"Advisory {i}",
            description="Test",
            severity="HIGH",
            vendor="Test",
            product="Test",
            published_date=datetime.now(),
            source_feed="https://example.com/feed",
            url="https://example.com"
        )
        temp_db.add_advisory(advisory)
    
    advisories = temp_db.get_all_advisories()
    assert len(advisories) >= 3


def test_get_advisories_by_product(temp_db):
    """Test retrieving advisories by product."""
    # Add advisory
    advisory = AdvisoryDB(
        advisory_id="test_apache_001",
        title="Apache Vulnerability",
        description="Apache CVE",
        severity="CRITICAL",
        vendor="Apache",
        product="Apache HTTP Server",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com"
    )
    temp_db.add_advisory(advisory)
    
    # Search for Apache advisories
    advisories = temp_db.get_advisories_by_product("Apache")
    assert len(advisories) > 0
    assert any("Apache" in a.product for a in advisories)


def test_add_inventory_item(temp_db, sample_inventory):
    """Test adding inventory item."""
    item_id = temp_db.add_inventory_item(sample_inventory)
    assert item_id is not None
    assert item_id > 0


def test_get_inventory_by_asset_id(temp_db, sample_inventory):
    """Test retrieving inventory by asset ID."""
    temp_db.add_inventory_item(sample_inventory)
    
    retrieved = temp_db.get_inventory_by_asset_id(sample_inventory.asset_id)
    assert retrieved is not None
    assert retrieved.software_name == sample_inventory.software_name


def test_get_inventory_by_id(temp_db, sample_inventory):
    """Test retrieving inventory by database ID."""
    item_id = temp_db.add_inventory_item(sample_inventory)
    
    retrieved = temp_db.get_inventory_by_id(item_id)
    assert retrieved is not None
    assert retrieved.asset_id == sample_inventory.asset_id


def test_get_all_inventory(temp_db):
    """Test retrieving all inventory items."""
    # Add multiple items
    for i in range(3):
        item = InventoryItemDB(
            asset_id=f"asset_{i:03d}",
            software_name=f"Software{i}",
            version=f"1.{i}"
        )
        temp_db.add_inventory_item(item)
    
    inventory = temp_db.get_all_inventory()
    assert len(inventory) >= 3


def test_clear_inventory(temp_db, sample_inventory):
    """Test clearing inventory."""
    temp_db.add_inventory_item(sample_inventory)
    
    before = len(temp_db.get_all_inventory())
    assert before > 0
    
    temp_db.clear_inventory()
    
    after = len(temp_db.get_all_inventory())
    assert after == 0


def test_add_match(temp_db, sample_advisory, sample_inventory):
    """Test adding match."""
    advisory_id = temp_db.add_advisory(sample_advisory)
    inventory_id = temp_db.add_inventory_item(sample_inventory)
    
    match = MatchDB(
        advisory_id=advisory_id,
        inventory_item_id=inventory_id,
        risk_level="CRITICAL"
    )
    
    match_id = temp_db.add_match(match)
    assert match_id is not None


def test_get_matches_by_advisory(temp_db, sample_advisory, sample_inventory):
    """Test retrieving matches by advisory."""
    advisory_id = temp_db.add_advisory(sample_advisory)
    inventory_id = temp_db.add_inventory_item(sample_inventory)
    
    match = MatchDB(
        advisory_id=advisory_id,
        inventory_item_id=inventory_id,
        risk_level="HIGH"
    )
    temp_db.add_match(match)
    
    matches = temp_db.get_matches_by_advisory(advisory_id)
    assert len(matches) > 0


def test_get_all_matches(temp_db, sample_advisory, sample_inventory):
    """Test retrieving all matches."""
    advisory_id = temp_db.add_advisory(sample_advisory)
    inventory_id = temp_db.add_inventory_item(sample_inventory)
    
    match = MatchDB(
        advisory_id=advisory_id,
        inventory_item_id=inventory_id,
        risk_level="MEDIUM"
    )
    temp_db.add_match(match)
    
    matches = temp_db.get_all_matches()
    assert len(matches) > 0


def test_get_matches_count(temp_db, sample_advisory, sample_inventory):
    """Test getting match count."""
    advisory_id = temp_db.add_advisory(sample_advisory)
    inventory_id = temp_db.add_inventory_item(sample_inventory)
    
    match = MatchDB(
        advisory_id=advisory_id,
        inventory_item_id=inventory_id,
        risk_level="LOW"
    )
    temp_db.add_match(match)
    
    count = temp_db.get_matches_count()
    assert count > 0
