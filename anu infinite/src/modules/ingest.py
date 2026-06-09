"""
Feed Ingestion Module for Security Advisory Digest.

Handles fetching and parsing advisories from multiple data sources:
- CISA Known Exploited Vulnerabilities (KEV)
- NVD CVE API
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
import time

from src.core.database import AdvisoryDatabase
from config.settings import CISA_KEV_API_URL, NVD_API_KEY, NVD_API_BASE_URL


class FeedIngester:
    """Handles fetching and parsing security advisory feeds."""

    def __init__(self, db: AdvisoryDatabase):
        """Initialize feed ingester with database connection."""
        self.db = db
        self.session = requests.Session()
        self.session.timeout = 30

    def ingest_cisa_kev(self) -> int:
        """
        Fetch and ingest CISA KEV JSON feed.

        Returns:
            Number of new advisories added
        """
        logger.info("Starting CISA KEV ingestion...")
        added_count = 0

        try:
            response = self.session.get(CISA_KEV_API_URL)
            response.raise_for_status()
            data = response.json()

            if "vulnerabilities" not in data:
                logger.warning("No vulnerabilities in CISA KEV response")
                return 0

            for vuln in data["vulnerabilities"]:
                advisory = self._normalize_cisa_advisory(vuln)

                # Check for duplicates
                if self.db.is_duplicate_cve(advisory["cve_id"]):
                    logger.debug(f"Duplicate CVE {advisory['cve_id']} skipped")
                    continue

                result = self.db.add_advisory(advisory)
                if result > 0:
                    added_count += 1
                    logger.debug(f"Added CISA advisory: {advisory['cve_id']}")

            logger.info(f"CISA KEV ingestion complete. Added {added_count} advisories")
            return added_count

        except requests.RequestException as e:
            logger.error(f"Error fetching CISA KEV feed: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error processing CISA KEV data: {e}")
            return 0

    def ingest_nvd_cves(self, start_index: int = 0, results_per_page: int = 100) -> int:
        """
        Fetch and ingest from NVD CVE API.

        Args:
            start_index: Starting index for pagination
            results_per_page: Number of results per page

        Returns:
            Number of new advisories added
        """
        logger.info("Starting NVD CVE API ingestion...")
        added_count = 0

        if not NVD_API_KEY:
            logger.warning("NVD_API_KEY not configured, skipping NVD ingestion")
            return 0

        try:
            headers = {"apiKey": NVD_API_KEY}
            params = {
                "startIndex": start_index,
                "resultsPerPage": results_per_page
            }

            response = self.session.get(
                NVD_API_BASE_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if "vulnerabilities" not in data:
                logger.warning("No vulnerabilities in NVD response")
                return 0

            for vuln_item in data["vulnerabilities"]:
                advisory = self._normalize_nvd_advisory(vuln_item)

                # Check for duplicates
                if self.db.is_duplicate_cve(advisory["cve_id"]):
                    logger.debug(f"Duplicate CVE {advisory['cve_id']} skipped")
                    continue

                result = self.db.add_advisory(advisory)
                if result > 0:
                    added_count += 1
                    logger.debug(f"Added NVD advisory: {advisory['cve_id']}")

                # Rate limiting
                time.sleep(0.1)

            logger.info(f"NVD CVE API ingestion complete. Added {added_count} advisories")
            return added_count

        except requests.RequestException as e:
            logger.error(f"Error fetching NVD API: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error processing NVD data: {e}")
            return 0

    def ingest_custom_feed(self, feed_url: str, feed_type: str = "json") -> int:
        """
        Ingest advisories from custom feed URL.

        Args:
            feed_url: URL to custom feed
            feed_type: "json" or "rss"

        Returns:
            Number of new advisories added
        """
        logger.info(f"Starting custom feed ingestion from {feed_url}")
        added_count = 0

        try:
            response = self.session.get(feed_url)
            response.raise_for_status()

            if feed_type == "json":
                data = response.json()
                if isinstance(data, list):
                    advisories = data
                elif isinstance(data, dict) and "items" in data:
                    advisories = data["items"]
                else:
                    advisories = []

                for advisory in advisories:
                    normalized = self._normalize_custom_advisory(advisory, feed_url)
                    if self.db.is_duplicate_cve(normalized["cve_id"]):
                        continue
                    result = self.db.add_advisory(normalized)
                    if result > 0:
                        added_count += 1

            logger.info(f"Custom feed ingestion complete. Added {added_count} advisories")
            return added_count

        except requests.RequestException as e:
            logger.error(f"Error fetching custom feed: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error processing custom feed: {e}")
            return 0

    @staticmethod
    def _normalize_cisa_advisory(vuln: Dict) -> Dict:
        """
        Normalize CISA KEV advisory data.

        Args:
            vuln: Raw CISA vulnerability record

        Returns:
            Normalized advisory dictionary
        """
        return {
            "advisory_id": vuln.get("cveID", ""),
            "cve_id": vuln.get("cveID", ""),
            "title": vuln.get("cveID", ""),
            "description": vuln.get("knownRansomwareCampaignUse", "No description"),
            "severity": "High",  # CISA KEV are high severity
            "vendor": "",
            "product": "",
            "version": "",
            "published_date": vuln.get("dateAdded", datetime.now().isoformat()),
            "source_feed": "CISA_KEV",
            "url": f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
        }

    @staticmethod
    def _normalize_nvd_advisory(vuln_item: Dict) -> Dict:
        """
        Normalize NVD API advisory data.

        Args:
            vuln_item: Raw NVD vulnerability item

        Returns:
            Normalized advisory dictionary
        """
        cve = vuln_item.get("cve", {})
        cve_id = cve.get("id", "")
        
        # Extract severity from impact
        severity = "Medium"
        metrics = cve.get("metrics", {})
        if "cvssV3" in metrics:
            base_score = metrics["cvssV3"][0].get("cvssData", {}).get("baseSeverity", "Medium")
            severity = base_score
        elif "cvssV2" in metrics:
            base_score = metrics["cvssV2"][0].get("cvssData", {}).get("severity", "Medium")
            severity = base_score

        # Extract description
        descriptions = cve.get("descriptions", [])
        description = descriptions[0].get("value", "") if descriptions else ""

        # Extract published date
        published_date = cve.get("published", datetime.now().isoformat())

        return {
            "advisory_id": cve_id,
            "cve_id": cve_id,
            "title": cve_id,
            "description": description,
            "severity": severity,
            "vendor": "",
            "product": "",
            "version": "",
            "published_date": published_date,
            "source_feed": "NVD_API",
            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"
        }

    @staticmethod
    def _normalize_custom_advisory(advisory: Dict, source: str) -> Dict:
        """
        Normalize custom advisory data.

        Args:
            advisory: Raw advisory record
            source: Source feed URL

        Returns:
            Normalized advisory dictionary
        """
        return {
            "advisory_id": advisory.get("id", advisory.get("cve_id", "unknown")),
            "cve_id": advisory.get("cve_id", advisory.get("id", "unknown")),
            "title": advisory.get("title", ""),
            "description": advisory.get("description", ""),
            "severity": advisory.get("severity", "Medium"),
            "vendor": advisory.get("vendor", ""),
            "product": advisory.get("product", ""),
            "version": advisory.get("version", ""),
            "published_date": advisory.get("published_date", datetime.now().isoformat()),
            "source_feed": source,
            "url": advisory.get("url", "")
        }

    def ingest_all(self) -> Dict[str, int]:
        """
        Run all ingestion sources.

        Returns:
            Dictionary with counts per source
        """
        logger.info("Starting comprehensive advisory ingestion")

        results = {
            "cisa_kev": self.ingest_cisa_kev(),
            "nvd_api": self.ingest_nvd_cves(),
            "total": 0
        }

        results["total"] = results["cisa_kev"] + results["nvd_api"]
        logger.info(f"Total advisories ingested: {results['total']}")

        return results
