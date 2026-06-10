"""
SQLite database operations for Security Advisory Digest.
"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from contextlib import contextmanager

from config import DB_PATH
from models import AdvisoryDB, InventoryItemDB, MatchDB

logger = logging.getLogger(__name__)


class Database:
    """SQLite database management class."""

    def __init__(self, db_path: Path = DB_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_db(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create advisories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS advisories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    advisory_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    product TEXT NOT NULL,
                    published_date TIMESTAMP NOT NULL,
                    source_feed TEXT NOT NULL,
                    url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create inventory_items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT UNIQUE NOT NULL,
                    software_name TEXT NOT NULL,
                    version TEXT NOT NULL
                )
            """)

            # Create matches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    advisory_id INTEGER NOT NULL,
                    inventory_item_id INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (advisory_id) REFERENCES advisories(id),
                    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
                    UNIQUE(advisory_id, inventory_item_id)
                )
            """)

            # Create indices for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_advisories_advisory_id ON advisories(advisory_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_advisories_product ON advisories(product)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_advisories_severity ON advisories(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_software ON inventory_items(software_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_advisory ON matches(advisory_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_inventory ON matches(inventory_item_id)")

            logger.info("Database initialized successfully")

    # Advisory operations

    def add_advisory(self, advisory: AdvisoryDB) -> int:
        """Add a new advisory to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO advisories 
                    (advisory_id, title, description, severity, vendor, product, published_date, source_feed, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    advisory.advisory_id,
                    advisory.title,
                    advisory.description,
                    advisory.severity,
                    advisory.vendor,
                    advisory.product,
                    advisory.published_date.isoformat(),
                    advisory.source_feed,
                    advisory.url
                ))
                logger.info(f"Added advisory: {advisory.advisory_id}")
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                logger.debug(f"Advisory already exists: {advisory.advisory_id}")
                return self.get_advisory_by_id_string(advisory.advisory_id).id

    def get_advisory_by_id_string(self, advisory_id: str) -> Optional[AdvisoryDB]:
        """Get advisory by advisory_id string."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM advisories WHERE advisory_id = ?", (advisory_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_advisory(row)
            return None

    def get_advisory_by_id(self, advisory_id: int) -> Optional[AdvisoryDB]:
        """Get advisory by database id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM advisories WHERE id = ?", (advisory_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_advisory(row)
            return None

    def get_all_advisories(self) -> List[AdvisoryDB]:
        """Get all advisories."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM advisories ORDER BY published_date DESC")
            rows = cursor.fetchall()
            return [self._row_to_advisory(row) for row in rows]

    def get_recent_advisories(self, limit: int = 50) -> List[AdvisoryDB]:
        """Get recent advisories."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM advisories ORDER BY published_date DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [self._row_to_advisory(row) for row in rows]

    def get_advisories_by_product(self, product: str) -> List[AdvisoryDB]:
        """Get advisories matching a product."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM advisories WHERE LOWER(product) LIKE LOWER(?) ORDER BY published_date DESC",
                (f"%{product}%",)
            )
            rows = cursor.fetchall()
            return [self._row_to_advisory(row) for row in rows]

    # Inventory operations

    def add_inventory_item(self, item: InventoryItemDB) -> int:
        """Add a new inventory item."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO inventory_items (asset_id, software_name, version)
                    VALUES (?, ?, ?)
                """, (item.asset_id, item.software_name, item.version))
                logger.info(f"Added inventory item: {item.asset_id}")
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                logger.debug(f"Inventory item already exists: {item.asset_id}")
                return self.get_inventory_by_asset_id(item.asset_id).id

    def get_inventory_by_asset_id(self, asset_id: str) -> Optional[InventoryItemDB]:
        """Get inventory item by asset_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory_items WHERE asset_id = ?", (asset_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_inventory(row)
            return None

    def get_inventory_by_id(self, item_id: int) -> Optional[InventoryItemDB]:
        """Get inventory item by database id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_inventory(row)
            return None

    def get_all_inventory(self) -> List[InventoryItemDB]:
        """Get all inventory items."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory_items ORDER BY software_name")
            rows = cursor.fetchall()
            return [self._row_to_inventory(row) for row in rows]

    def clear_inventory(self):
        """Clear all inventory items."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventory_items")
            logger.info("Cleared inventory")

    # Match operations

    def add_match(self, match: MatchDB) -> int:
        """Add a new match."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO matches (advisory_id, inventory_item_id, risk_level)
                    VALUES (?, ?, ?)
                """, (match.advisory_id, match.inventory_item_id, match.risk_level))
                logger.info(f"Added match: advisory {match.advisory_id} -> item {match.inventory_item_id}")
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                logger.debug(f"Match already exists")
                return None

    def get_matches_by_advisory(self, advisory_id: int) -> List[MatchDB]:
        """Get all matches for an advisory."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM matches WHERE advisory_id = ?", (advisory_id,))
            rows = cursor.fetchall()
            return [self._row_to_match(row) for row in rows]

    def get_all_matches(self) -> List[MatchDB]:
        """Get all matches."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM matches ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_match(row) for row in rows]

    def get_matches_count(self) -> int:
        """Get total count of matches."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM matches")
            return cursor.fetchone()["count"]

    # Helper methods

    @staticmethod
    def _row_to_advisory(row: sqlite3.Row) -> AdvisoryDB:
        """Convert database row to AdvisoryDB model."""
        return AdvisoryDB(
            id=row["id"],
            advisory_id=row["advisory_id"],
            title=row["title"],
            description=row["description"],
            severity=row["severity"],
            vendor=row["vendor"],
            product=row["product"],
            published_date=datetime.fromisoformat(row["published_date"]),
            source_feed=row["source_feed"],
            url=row["url"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )

    @staticmethod
    def _row_to_inventory(row: sqlite3.Row) -> InventoryItemDB:
        """Convert database row to InventoryItemDB model."""
        return InventoryItemDB(
            id=row["id"],
            asset_id=row["asset_id"],
            software_name=row["software_name"],
            version=row["version"]
        )

    @staticmethod
    def _row_to_match(row: sqlite3.Row) -> MatchDB:
        """Convert database row to MatchDB model."""
        return MatchDB(
            id=row["id"],
            advisory_id=row["advisory_id"],
            inventory_item_id=row["inventory_item_id"],
            risk_level=row["risk_level"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )

    def close(self):
        """Close database connection."""
        logger.info("Database connection closed")
