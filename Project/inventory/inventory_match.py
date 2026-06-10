"""
Inventory matching coordination module.
"""
import csv
import logging
from pathlib import Path
from typing import List

from models import InventoryItemDB
from inventory.matcher import InventoryMatcher

logger = logging.getLogger(__name__)


class InventoryMatchService:
    """Service for inventory matching operations."""

    def __init__(self):
        """Initialize inventory match service."""
        self.matcher = InventoryMatcher()

    def load_inventory_from_csv(self, csv_path: Path) -> List[InventoryItemDB]:
        """
        Load inventory items from CSV file.
        
        Expected CSV format:
        software_name,version
        Apache,2.4
        Nginx,1.22
        
        Args:
            csv_path: Path to inventory CSV file
            
        Returns:
            List of InventoryItemDB objects
        """
        inventory = []
        
        if not csv_path.exists():
            logger.warning(f"Inventory file not found: {csv_path}")
            return inventory
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    logger.error("CSV file is empty or has no headers")
                    return inventory
                
                for idx, row in enumerate(reader, start=2):  # Start from 2 (header is 1)
                    try:
                        software_name = row.get("software_name", "").strip()
                        version = row.get("version", "").strip()
                        
                        if not software_name or not version:
                            logger.warning(f"Skipping incomplete row {idx}: {row}")
                            continue
                        
                        # Generate unique asset_id
                        asset_id = f"{software_name}_{version}".replace(" ", "_")
                        
                        item = InventoryItemDB(
                            asset_id=asset_id,
                            software_name=software_name,
                            version=version
                        )
                        inventory.append(item)
                        
                    except Exception as e:
                        logger.error(f"Error parsing inventory row {idx}: {e}")
                        continue
            
            logger.info(f"Loaded {len(inventory)} inventory items from {csv_path}")
            return inventory
            
        except Exception as e:
            logger.error(f"Error loading inventory from CSV: {e}")
            return inventory

    def save_inventory_to_csv(self, inventory: List[InventoryItemDB], csv_path: Path):
        """
        Save inventory items to CSV file.
        
        Args:
            inventory: List of inventory items
            csv_path: Path to save CSV file
        """
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["software_name", "version"])
                writer.writeheader()
                
                for item in inventory:
                    writer.writerow({
                        "software_name": item.software_name,
                        "version": item.version
                    })
            
            logger.info(f"Saved {len(inventory)} inventory items to {csv_path}")
            
        except Exception as e:
            logger.error(f"Error saving inventory to CSV: {e}")
