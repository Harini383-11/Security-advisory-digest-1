"""
RSS feed ingestion module for security advisories.
"""
import logging
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import feedparser
import requests

from models import AdvisoryDB
from config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class RSSIngester:
    """Handle RSS feed ingestion for security advisories."""

    def __init__(self):
        """Initialize RSS ingester."""
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT

    def ingest_feed(self, feed_url: str) -> List[AdvisoryDB]:
        """
        Ingest security advisories from an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            
        Returns:
            List of AdvisoryDB objects parsed from the feed
        """
        advisories = []
        
        try:
            logger.info(f"Ingesting RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing error: {feed.bozo_exception}")
            
            for entry in feed.entries:
                try:
                    advisory = self._parse_entry(entry, feed_url)
                    if advisory:
                        advisories.append(advisory)
                except Exception as e:
                    logger.error(f"Error parsing entry: {e}")
                    continue
            
            logger.info(f"Successfully ingested {len(advisories)} advisories from {feed_url}")
            return advisories
            
        except Exception as e:
            logger.error(f"Error ingesting RSS feed {feed_url}: {e}")
            return advisories

    @staticmethod
    def _parse_entry(entry, feed_url: str) -> AdvisoryDB:
        """
        Parse a single RSS entry into an AdvisoryDB object.
        
        Args:
            entry: RSS feed entry
            feed_url: Source feed URL
            
        Returns:
            AdvisoryDB object or None if parsing fails
        """
        try:
            # Extract basic information
            title = entry.get("title", "").strip()
            description = entry.get("summary", entry.get("description", "")).strip()
            published_date = RSSIngester._parse_date(entry)
            url = entry.get("link", "")
            
            # Generate advisory_id from title and date
            advisory_id = f"{urlparse(feed_url).netloc}_{hash(title + str(published_date)) % 10000000:07d}"
            
            # Extract vendor and product information
            # This is a simplified extraction - in production, you'd use NLP
            vendor = RSSIngester._extract_vendor(title)
            product = RSSIngester._extract_product(title)
            severity = RSSIngester._extract_severity(title, description)
            
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
            logger.error(f"Error parsing RSS entry: {e}")
            return None

    @staticmethod
    def _parse_date(entry) -> datetime:
        """Parse publication date from RSS entry."""
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            return datetime.now()
        except Exception:
            return datetime.now()

    @staticmethod
    def _extract_vendor(text: str) -> str:
        """Extract vendor name from text (simplified)."""
        common_vendors = [
            "Apache", "Nginx", "OpenSSL", "MySQL", "PostgreSQL", "Tomcat",
            "Microsoft", "Apple", "Google", "Amazon", "Meta", "Oracle",
            "Linux", "Debian", "Ubuntu", "RedHat", "CentOS", "GitHub"
        ]
        text_upper = text.upper()
        for vendor in common_vendors:
            if vendor.upper() in text_upper:
                return vendor
        return "Unknown"

    @staticmethod
    def _extract_product(text: str) -> str:
        """Extract product name from text (simplified)."""
        # This is a very basic extraction
        # In production, use NLP or ML models
        words = text.split()
        if len(words) > 0:
            return words[0]
        return "Unknown"

    @staticmethod
    def _extract_severity(title: str, description: str) -> str:
        """Extract severity level from text."""
        text = (title + " " + description).lower()
        
        if any(word in text for word in ["critical", "critical severity"]):
            return "CRITICAL"
        elif any(word in text for word in ["high", "high severity"]):
            return "HIGH"
        elif any(word in text for word in ["medium", "medium severity"]):
            return "MEDIUM"
        elif any(word in text for word in ["low", "low severity"]):
            return "LOW"
        else:
            return "UNKNOWN"

    def close(self):
        """Close the session."""
        self.session.close()
