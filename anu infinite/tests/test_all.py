"""
Pytest test cases for Security Advisory Digest.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import AdvisoryDatabase
from src.modules.ingest import FeedIngester
from src.modules.dedup import DeduplicationEngine
from src.modules.inventory_match import InventoryMatcher
from src.modules.rag import RAGEngine


@pytest.fixture
def test_db():
    """Create test database."""
    db = AdvisoryDatabase(":memory:")
    yield db


@pytest.fixture
def sample_advisory():
    """Sample advisory for testing."""
    return {
        "advisory_id": "CVE-2024-0001",
        "cve_id": "CVE-2024-0001",
        "title": "Test Vulnerability",
        "description": "This is a test vulnerability",
        "severity": "High",
        "vendor": "TestVendor",
        "product": "TestProduct",
        "version": "1.0",
        "published_date": "2024-01-01T00:00:00",
        "source_feed": "TEST",
        "url": "https://example.com"
    }


class TestDatabase:
    """Test database operations."""

    def test_add_advisory(self, test_db, sample_advisory):
        """Test adding advisory to database."""
        result = test_db.add_advisory(sample_advisory)
        assert result > 0

    def test_get_advisory_by_cve(self, test_db, sample_advisory):
        """Test retrieving advisory by CVE ID."""
        test_db.add_advisory(sample_advisory)
        retrieved = test_db.get_advisory_by_cve("CVE-2024-0001")
        assert retrieved is not None
        assert retrieved["cve_id"] == "CVE-2024-0001"

    def test_duplicate_cve_detection(self, test_db, sample_advisory):
        """Test duplicate CVE detection."""
        test_db.add_advisory(sample_advisory)
        assert test_db.is_duplicate_cve("CVE-2024-0001") is True
        assert test_db.is_duplicate_cve("CVE-2024-0002") is False

    def test_get_critical_advisories(self, test_db):
        """Test retrieving critical advisories."""
        # Add test advisories
        for i in range(3):
            advisory = {
                "advisory_id": f"CVE-2024-{i:04d}",
                "cve_id": f"CVE-2024-{i:04d}",
                "title": f"Test {i}",
                "description": "Test",
                "severity": "Critical" if i < 2 else "High",
                "vendor": "Test",
                "product": "Test",
                "published_date": "2024-01-01T00:00:00",
                "source_feed": "TEST",
                "url": "https://example.com"
            }
            test_db.add_advisory(advisory)

        critical = test_db.get_critical_advisories()
        assert len(critical) >= 2

    def test_database_statistics(self, test_db, sample_advisory):
        """Test database statistics."""
        test_db.add_advisory(sample_advisory)
        stats = test_db.get_statistics()

        assert stats["total_advisories"] > 0
        assert stats["unique_cves"] > 0
        assert "by_severity" in stats

    def test_inventory_operations(self, test_db):
        """Test inventory operations."""
        item_id = test_db.add_inventory_item("TestProduct", "1.0")
        assert item_id > 0

        inventory = test_db.get_inventory()
        assert len(inventory) > 0
        assert inventory[0]["product"] == "TestProduct"


class TestDeduplication:
    """Test deduplication engine."""

    def test_find_duplicates(self, test_db):
        """Test finding duplicate CVEs."""
        # Add duplicate advisories
        adv1 = {
            "advisory_id": "ADV-001",
            "cve_id": "CVE-2024-0001",
            "title": "Test",
            "description": "Test 1",
            "severity": "High",
            "vendor": "Vendor",
            "product": "Product",
            "published_date": "2024-01-01T00:00:00",
            "source_feed": "TEST",
            "url": "https://example.com"
        }
        adv2 = {
            "advisory_id": "ADV-002",
            "cve_id": "CVE-2024-0001",
            "title": "Test",
            "description": "Test 2",
            "severity": "High",
            "vendor": "Vendor",
            "product": "Product",
            "published_date": "2024-01-02T00:00:00",
            "source_feed": "TEST",
            "url": "https://example.com"
        }

        test_db.add_advisory(adv1)
        test_db.add_advisory(adv2)

        dedup = DeduplicationEngine(test_db)
        duplicates = dedup.find_duplicates_by_cve()

        assert "CVE-2024-0001" in duplicates
        assert len(duplicates["CVE-2024-0001"]) == 2

    def test_deduplication_report(self, test_db):
        """Test deduplication report."""
        dedup = DeduplicationEngine(test_db)
        report = dedup.get_deduplication_report()

        assert "total_cves" in report
        assert "cves_with_duplicates" in report
        assert "duplicate_advisories_count" in report


class TestInventoryMatching:
    """Test inventory matching."""

    def test_find_matching_advisories(self, test_db):
        """Test finding advisories for inventory product."""
        # Add advisory
        advisory = {
            "advisory_id": "CVE-2024-0001",
            "cve_id": "CVE-2024-0001",
            "title": "Apache Vulnerability",
            "description": "Test",
            "severity": "High",
            "vendor": "Apache",
            "product": "Apache Tomcat",
            "version": "9.0",
            "published_date": "2024-01-01T00:00:00",
            "source_feed": "TEST",
            "url": "https://example.com"
        }
        test_db.add_advisory(advisory)

        matcher = InventoryMatcher(test_db)
        matches = matcher.find_matching_advisories("Apache Tomcat", "9.0")

        assert len(matches) > 0

    def test_risk_report_generation(self, test_db):
        """Test risk report generation."""
        # Add inventory
        item_id = test_db.add_inventory_item("TestProduct", "1.0")

        matcher = InventoryMatcher(test_db)
        report = matcher.generate_risk_report()

        assert "generated_at" in report
        assert "summary" in report
        assert "inventory_items" in report

    def test_affected_products_list(self, test_db):
        """Test getting affected products list."""
        matcher = InventoryMatcher(test_db)
        affected = matcher.get_affected_products_list()

        assert isinstance(affected, list)


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_workflow(self, test_db):
        """Test complete workflow."""
        # Add advisories
        advisory = {
            "advisory_id": "CVE-2024-0001",
            "cve_id": "CVE-2024-0001",
            "title": "Test",
            "description": "Test vulnerability",
            "severity": "Critical",
            "vendor": "TestVendor",
            "product": "TestProduct",
            "version": "1.0",
            "published_date": "2024-01-01T00:00:00",
            "source_feed": "TEST",
            "url": "https://example.com"
        }
        test_db.add_advisory(advisory)

        # Add inventory
        inv_id = test_db.add_inventory_item("TestProduct", "1.0")

        # Record match
        adv_id = test_db.get_advisory_by_cve("CVE-2024-0001")["id"]
        match_id = test_db.add_inventory_match(inv_id, adv_id, "CVE-2024-0001", "Critical")

        assert match_id > 0

        # Verify match retrieval
        matches = test_db.get_inventory_matches(inv_id)
        assert len(matches) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_description(self, test_db):
        """Test advisory with empty description."""
        advisory = {
            "advisory_id": "CVE-2024-0001",
            "cve_id": "CVE-2024-0001",
            "title": "Test",
            "description": "",
            "severity": "High",
            "vendor": "Test",
            "product": "Test",
            "published_date": "2024-01-01T00:00:00",
            "source_feed": "TEST",
            "url": "https://example.com"
        }
        result = test_db.add_advisory(advisory)
        assert result > 0

    def test_missing_fields(self, test_db):
        """Test advisory with missing optional fields."""
        advisory = {
            "advisory_id": "CVE-2024-0002",
            "cve_id": "CVE-2024-0002",
            "title": "Test",
            "description": "Test"
        }
        result = test_db.add_advisory(advisory)
        assert result > 0

    def test_duplicate_inventory_item(self, test_db):
        """Test adding duplicate inventory items."""
        id1 = test_db.add_inventory_item("Product", "1.0")
        id2 = test_db.add_inventory_item("Product", "1.0")

        # Should return same ID on duplicate
        assert id1 == id2

    def test_invalid_advisory_query(self, test_db):
        """Test querying non-existent advisory."""
        result = test_db.get_advisory_by_cve("CVE-9999-9999")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
