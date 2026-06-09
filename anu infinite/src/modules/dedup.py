"""
Deduplication Engine for Security Advisory Digest.

Detects and handles duplicate CVEs and advisories.
"""

from typing import List, Dict, Optional
from loguru import logger
from collections import defaultdict

from src.core.database import AdvisoryDatabase


class DeduplicationEngine:
    """Handles detection and merging of duplicate advisories."""

    def __init__(self, db: AdvisoryDatabase):
        """Initialize deduplication engine."""
        self.db = db

    def find_duplicates_by_cve(self) -> Dict[str, List[Dict]]:
        """
        Find all advisories with duplicate CVE IDs.

        Returns:
            Dictionary mapping CVE ID to list of advisories
        """
        logger.info("Scanning for duplicate CVEs...")
        all_advisories = self.db.get_all_advisories(limit=10000)

        duplicates = defaultdict(list)
        for advisory in all_advisories:
            duplicates[advisory["cve_id"]].append(advisory)

        # Filter to only actual duplicates
        actual_duplicates = {
            cve_id: advs for cve_id, advs in duplicates.items()
            if len(advs) > 1
        }

        logger.info(f"Found {len(actual_duplicates)} CVEs with duplicates")
        return actual_duplicates

    def find_duplicate_descriptions(self, threshold: float = 0.9) -> List[List[Dict]]:
        """
        Find advisories with similar descriptions (potential duplicates).

        Args:
            threshold: Similarity threshold (0-1)

        Returns:
            List of groups of similar advisories
        """
        logger.info(f"Finding advisories with similar descriptions (threshold: {threshold})")
        all_advisories = self.db.get_all_advisories(limit=10000)

        groups = []
        processed = set()

        for i, adv1 in enumerate(all_advisories):
            if i in processed:
                continue

            group = [adv1]
            processed.add(i)

            for j, adv2 in enumerate(all_advisories[i + 1:], start=i + 1):
                if j in processed:
                    continue

                # Simple similarity check based on description length and common words
                if self._calculate_similarity(adv1.get("description", ""), adv2.get("description", "")) >= threshold:
                    group.append(adv2)
                    processed.add(j)

            if len(group) > 1:
                groups.append(group)

        logger.info(f"Found {len(groups)} groups of similar advisories")
        return groups

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using Jaccard index.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def keep_latest_advisory(self, cve_id: str) -> Optional[int]:
        """
        For a given CVE ID, keep the latest advisory and delete others.

        Args:
            cve_id: CVE ID to deduplicate

        Returns:
            ID of the kept advisory
        """
        logger.info(f"Deduplicating CVE {cve_id}")

        duplicates = self.db.get_duplicate_advisories("")

        # Get advisories for this CVE
        advisories = [adv for adv in duplicates if adv.get("cve_id") == cve_id]

        if len(advisories) <= 1:
            logger.debug(f"No duplicates to remove for {cve_id}")
            return advisories[0]["id"] if advisories else None

        # Sort by published date (latest first)
        advisories.sort(key=lambda x: x["published_date"], reverse=True)

        # Keep the latest
        kept_advisory = advisories[0]
        logger.info(f"Keeping advisory {kept_advisory['id']} (published: {kept_advisory['published_date']})")

        # Delete others
        deleted_count = 0
        for advisory in advisories[1:]:
            if self.db.delete_advisory(advisory["id"]):
                deleted_count += 1

        logger.info(f"Deleted {deleted_count} duplicate advisories for {cve_id}")
        return kept_advisory["id"]

    def deduplicate_all_cves(self) -> Dict[str, int]:
        """
        Deduplicate all CVEs in the database.

        Returns:
            Statistics dictionary with counts
        """
        logger.info("Starting comprehensive CVE deduplication")

        duplicates = self.find_duplicates_by_cve()
        stats = {
            "cves_with_duplicates": len(duplicates),
            "advisories_deleted": 0,
            "errors": 0
        }

        for cve_id, advisories in duplicates.items():
            if len(advisories) > 1:
                initial_count = len(advisories)
                try:
                    self.keep_latest_advisory(cve_id)
                    stats["advisories_deleted"] += initial_count - 1
                except Exception as e:
                    logger.error(f"Error deduplicating {cve_id}: {e}")
                    stats["errors"] += 1

        logger.info(f"Deduplication complete. Deleted {stats['advisories_deleted']} advisories")
        return stats

    def merge_advisory_descriptions(self, cve_id: str) -> bool:
        """
        Merge descriptions of duplicate advisories for a CVE.

        Args:
            cve_id: CVE ID to process

        Returns:
            Success status
        """
        logger.info(f"Merging descriptions for {cve_id}")

        advisories = self.db.get_all_advisories(limit=10000)
        matching = [adv for adv in advisories if adv["cve_id"] == cve_id]

        if len(matching) <= 1:
            logger.debug(f"Only one advisory for {cve_id}, no merge needed")
            return True

        # Collect unique descriptions
        descriptions = []
        for advisory in matching:
            if advisory.get("description"):
                descriptions.append(advisory["description"])

        # Merge descriptions
        merged_description = " | ".join(descriptions)

        # Update the latest advisory
        matching.sort(key=lambda x: x["published_date"], reverse=True)
        latest = matching[0]

        return self.db.update_advisory(latest["id"], {
            "description": merged_description
        })

    def get_deduplication_report(self) -> Dict:
        """
        Generate a deduplication report.

        Returns:
            Report dictionary
        """
        logger.info("Generating deduplication report")

        duplicates = self.find_duplicates_by_cve()
        similar_groups = self.find_duplicate_descriptions()

        report = {
            "total_cves": len(duplicates),
            "cves_with_duplicates": len([d for d in duplicates.values() if len(d) > 1]),
            "duplicate_advisories_count": sum(len(d) - 1 for d in duplicates.values() if len(d) > 1),
            "similar_advisory_groups": len(similar_groups),
            "summary": f"{len([d for d in duplicates.values() if len(d) > 1])} CVEs with duplicates, "
                       f"{sum(len(d) - 1 for d in duplicates.values() if len(d) > 1)} total duplicate advisories"
        }

        return report
