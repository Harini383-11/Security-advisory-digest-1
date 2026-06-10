"""
JSON feed ingestion module for security advisories.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
import json

from models import AdvisoryDB

logger = logging.getLogger(__name__)


class JSONFeedIngester:
    """Handle JSON feed ingestion for security advisories."""

    def ingest_feed(self, feed_url: str, feed_data: Dict[str, Any]) -> List[AdvisoryDB]:
        """
        Ingest security advisories from a JSON feed.
        
        Args:
            feed_url: URL of the JSON feed (for reference)
            feed_data: Parsed JSON feed data
            
        Returns:
            List of AdvisoryDB objects parsed from the feed
        """
        advisories = []
        
        try:
            logger.info(f"Ingesting JSON feed: {feed_url}")
            
            # Handle different JSON feed structures
            items = feed_data.get("items", [])
            if not items and "advisories" in feed_data:
                items = feed_data.get("advisories", [])
            
            for item in items:
                try:
                    advisory = self._parse_item(item, feed_url)
                    if advisory:
                        advisories.append(advisory)
                except Exception as e:
                    logger.error(f"Error parsing JSON item: {e}")
                    continue
            
            logger.info(f"Successfully ingested {len(advisories)} advisories from JSON feed")
            return advisories
            
        except Exception as e:
            logger.error(f"Error ingesting JSON feed {feed_url}: {e}")
            return advisories

    @staticmethod
    def _parse_item(item: Dict[str, Any], feed_url: str) -> AdvisoryDB:
        """
        Parse a single JSON item into an AdvisoryDB object.
        
        Args:
            item: JSON feed item
            feed_url: Source feed URL
            
        Returns:
            AdvisoryDB object or None if parsing fails
        """
        try:
            title = item.get("title", "").strip()
            description = item.get("description", item.get("summary", "")).strip()
            url = item.get("url", item.get("link", ""))
            
            # Parse date
            published_date = JSONFeedIngester._parse_date(item)
            
            # Extract metadata
            advisory_id = item.get("id", f"json_{hash(title + str(published_date)) % 10000000:07d}")
            vendor = item.get("vendor", "Unknown")
            product = item.get("product", "Unknown")
            severity = item.get("severity", "UNKNOWN").upper()
            
            return AdvisoryDB(
                advisory_id=advisory_id,
                title=title,
                description=description,
                severity=severity,
                vendor=vendor,
                product=product,
                published_date=published_date,
                source_feed=feed_url,
                url=url
            )
        except Exception as e:
            logger.error(f"Error parsing JSON item: {e}")
            return None

    @staticmethod
    def _parse_date(item: Dict[str, Any]) -> datetime:
        """Parse publication date from JSON item."""
        try:
            date_str = item.get("published_date", item.get("date", item.get("published")))
            if date_str:
                # Try ISO format
                if isinstance(date_str, str):
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return datetime.now()
        except Exception:
            return datetime.now()
