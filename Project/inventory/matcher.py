"""
Inventory matching logic for security advisories.
"""
import logging
from typing import List, Tuple
from difflib import SequenceMatcher

from models import AdvisoryDB, InventoryItemDB, MatchDB

logger = logging.getLogger(__name__)


class InventoryMatcher:
    """Match security advisories against software inventory."""

    def __init__(self):
        """Initialize inventory matcher."""
        self.similarity_threshold = 0.6

    def find_matches(
        self,
        advisory: AdvisoryDB,
        inventory_items: List[InventoryItemDB]
    ) -> List[Tuple[InventoryItemDB, str]]:
        """
        Find inventory items matching an advisory.
        
        Args:
            advisory: Advisory to match
            inventory_items: List of inventory items to search
            
        Returns:
            List of tuples (InventoryItemDB, risk_level)
        """
        matches = []
        
        # Search in advisory title and description
        advisory_text = f"{advisory.title} {advisory.description}".lower()
        
        for item in inventory_items:
            if self._is_match(advisory, item, advisory_text):
                risk_level = self._calculate_risk_level(advisory, item)
                matches.append((item, risk_level))
                logger.debug(
                    f"Match found: {item.software_name} v{item.version} "
                    f"matches {advisory.product} advisory (risk: {risk_level})"
                )
        
        return matches

    def _is_match(
        self,
        advisory: AdvisoryDB,
        item: InventoryItemDB,
        advisory_text: str
    ) -> bool:
        """
        Check if an advisory matches an inventory item.
        
        Args:
            advisory: Advisory to check
            item: Inventory item to check
            advisory_text: Full advisory text (lowercase)
            
        Returns:
            True if match found
        """
        item_name_lower = item.software_name.lower()
        product_lower = advisory.product.lower()
        
        # Exact product name match
        if product_lower == item_name_lower:
            return True
        
        # Partial name match in advisory text
        if item_name_lower in advisory_text:
            return True
        
        # Similarity-based matching
        similarity = SequenceMatcher(None, product_lower, item_name_lower).ratio()
        if similarity >= self.similarity_threshold:
            return True
        
        # Check vendor match + name similarity
        if advisory.vendor.lower() in item_name_lower or item_name_lower in advisory.vendor.lower():
            return True
        
        return False

    @staticmethod
    def _calculate_risk_level(advisory: AdvisoryDB, item: InventoryItemDB) -> str:
        """
        Calculate risk level for a match.
        
        Args:
            advisory: The advisory
            item: The inventory item
            
        Returns:
            Risk level (CRITICAL, HIGH, MEDIUM, LOW)
        """
        # Map advisory severity to risk level
        severity_map = {
            "CRITICAL": "CRITICAL",
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW",
            "UNKNOWN": "MEDIUM"
        }
        
        return severity_map.get(advisory.severity, "MEDIUM")
