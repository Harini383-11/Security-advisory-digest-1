"""
SQLite Database Management for Security Advisory Digest.

This module provides database utilities for storing and retrieving security advisories.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

from config.settings import DATABASE_PATH


class AdvisoryDatabase:
    """SQLite database handler for security advisories."""

    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Advisories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                advisory_id TEXT UNIQUE NOT NULL,
                cve_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT,
                vendor TEXT,
                product TEXT,
                version TEXT,
                published_date TEXT,
                source_feed TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cve_id ON advisories(cve_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product ON advisories(product)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vendor ON advisories(vendor)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_severity ON advisories(severity)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_published_date ON advisories(published_date)
        """)

        # Inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                version TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product, version)
            )
        """)

        # Inventory matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_id INTEGER NOT NULL,
                advisory_id INTEGER NOT NULL,
                cve_id TEXT NOT NULL,
                severity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_id) REFERENCES inventory(id),
                FOREIGN KEY (advisory_id) REFERENCES advisories(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database schema initialized")

    def add_advisory(self, advisory: Dict) -> int:
        """
        Add advisory to database.

        Args:
            advisory: Dictionary with advisory data

        Returns:
            Advisory ID if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO advisories (
                    advisory_id, cve_id, title, description, severity,
                    vendor, product, version, published_date, source_feed, url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                advisory.get("advisory_id"),
                advisory.get("cve_id"),
                advisory.get("title"),
                advisory.get("description"),
                advisory.get("severity"),
                advisory.get("vendor"),
                advisory.get("product"),
                advisory.get("version"),
                advisory.get("published_date"),
                advisory.get("source_feed"),
                advisory.get("url")
            ))
            conn.commit()
            advisory_id = cursor.lastrowid
            logger.info(f"Added advisory {advisory.get('cve_id')} with ID {advisory_id}")
            return advisory_id
        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate advisory: {advisory.get('advisory_id')}")
            return -1
        finally:
            conn.close()

    def get_advisory_by_cve(self, cve_id: str) -> Optional[Dict]:
        """Get advisory by CVE ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM advisories WHERE cve_id = ?", (cve_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_advisories(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Get all advisories with pagination."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM advisories ORDER BY published_date DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_advisories_by_severity(self, severity: str, limit: int = 100) -> List[Dict]:
        """Get advisories filtered by severity."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM advisories WHERE severity = ? ORDER BY published_date DESC LIMIT ?",
            (severity, limit)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_advisories_by_product(self, product: str) -> List[Dict]:
        """Get advisories for a specific product."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM advisories WHERE product ILIKE ? ORDER BY published_date DESC",
            (f"%{product}%",)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_critical_advisories(self, limit: int = 50) -> List[Dict]:
        """Get critical and high severity advisories."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM advisories
            WHERE severity IN ('Critical', 'High')
            ORDER BY published_date DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def is_duplicate_cve(self, cve_id: str) -> bool:
        """Check if CVE ID already exists in database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM advisories WHERE cve_id = ? LIMIT 1", (cve_id,))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    def get_duplicate_advisories(self, advisory_id: str) -> List[Dict]:
        """Find duplicate advisories (same CVE)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cve_id FROM advisories WHERE advisory_id = ?
        """, (advisory_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return []

        cve_id = result[0]
        cursor.execute("""
            SELECT * FROM advisories
            WHERE cve_id = ?
            ORDER BY published_date DESC
        """, (cve_id,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_advisory(self, advisory_id: int, updates: Dict) -> bool:
        """Update advisory record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic UPDATE query
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [advisory_id]

        try:
            cursor.execute(
                f"UPDATE advisories SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            conn.commit()
            logger.info(f"Updated advisory {advisory_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating advisory: {e}")
            return False
        finally:
            conn.close()

    def delete_advisory(self, advisory_id: int) -> bool:
        """Delete advisory record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM advisories WHERE id = ?", (advisory_id,))
            conn.commit()
            logger.info(f"Deleted advisory {advisory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting advisory: {e}")
            return False
        finally:
            conn.close()

    def get_statistics(self) -> Dict:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total advisories
        cursor.execute("SELECT COUNT(*) FROM advisories")
        stats["total_advisories"] = cursor.fetchone()[0]

        # Advisories by severity
        cursor.execute("""
            SELECT severity, COUNT(*) FROM advisories
            GROUP BY severity
        """)
        stats["by_severity"] = dict(cursor.fetchall())

        # Total unique CVEs
        cursor.execute("SELECT COUNT(DISTINCT cve_id) FROM advisories")
        stats["unique_cves"] = cursor.fetchone()[0]

        # Total vendors
        cursor.execute("SELECT COUNT(DISTINCT vendor) FROM advisories")
        stats["unique_vendors"] = cursor.fetchone()[0]

        # Latest advisory date
        cursor.execute("SELECT MAX(published_date) FROM advisories")
        result = cursor.fetchone()
        stats["latest_update"] = result[0] if result[0] else None

        conn.close()
        return stats

    def add_inventory_item(self, product: str, version: str) -> int:
        """Add item to inventory."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO inventory (product, version)
                VALUES (?, ?)
            """, (product, version))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Inventory item already exists: {product} {version}")
            cursor.execute(
                "SELECT id FROM inventory WHERE product = ? AND version = ?",
                (product, version)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else -1
        finally:
            conn.close()

    def get_inventory(self) -> List[Dict]:
        """Get all inventory items."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventory")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def add_inventory_match(self, inventory_id: int, advisory_id: int, cve_id: str, severity: str) -> int:
        """Record a match between inventory and advisory."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO inventory_matches (inventory_id, advisory_id, cve_id, severity)
                VALUES (?, ?, ?, ?)
            """, (inventory_id, advisory_id, cve_id, severity))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding inventory match: {e}")
            return -1
        finally:
            conn.close()

    def get_inventory_matches(self, inventory_id: int) -> List[Dict]:
        """Get all matches for an inventory item."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT im.*, a.title, a.url
            FROM inventory_matches im
            JOIN advisories a ON im.advisory_id = a.id
            WHERE im.inventory_id = ?
            ORDER BY im.severity DESC, im.created_at DESC
        """, (inventory_id,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def clear_all_data(self) -> bool:
        """Clear all data from database (use with caution)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM inventory_matches")
            cursor.execute("DELETE FROM inventory")
            cursor.execute("DELETE FROM advisories")
            conn.commit()
            logger.warning("All data cleared from database")
            return True
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
        finally:
            conn.close()
