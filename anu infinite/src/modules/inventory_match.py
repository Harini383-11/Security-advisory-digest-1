"""
Inventory Matching Module for Security Advisory Digest.

Matches organizational inventory against security advisories.
"""

import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

from src.core.database import AdvisoryDatabase


class InventoryMatcher:
    """Handles inventory matching against advisories."""

    def __init__(self, db: AdvisoryDatabase):
        """Initialize inventory matcher."""
        self.db = db

    def load_inventory_from_csv(self, csv_path: str) -> Tuple[int, List[str]]:
        """
        Load inventory from CSV file.

        Expected CSV format:
        Product,Version
        Windows Server,2019
        Apache Tomcat,9

        Args:
            csv_path: Path to CSV file

        Returns:
            Tuple of (count, errors)
        """
        logger.info(f"Loading inventory from {csv_path}")

        count = 0
        errors = []

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames or 'Product' not in reader.fieldnames:
                    errors.append("CSV must have 'Product' column")
                    return 0, errors

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    try:
                        product = row.get('Product', '').strip()
                        version = row.get('Version', '').strip()

                        if not product:
                            errors.append(f"Row {row_num}: Missing product name")
                            continue

                        # Add to database
                        inventory_id = self.db.add_inventory_item(product, version)
                        if inventory_id > 0:
                            count += 1
                            logger.debug(f"Added inventory: {product} {version}")

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")

        except FileNotFoundError:
            errors.append(f"File not found: {csv_path}")
        except Exception as e:
            errors.append(f"Error reading CSV: {str(e)}")

        logger.info(f"Loaded {count} inventory items with {len(errors)} errors")
        return count, errors

    def find_matching_advisories(self, product: str, version: str = None) -> List[Dict]:
        """
        Find advisories matching a product and version.

        Args:
            product: Product name to search
            version: Optional version to search (if None, searches all versions)

        Returns:
            List of matching advisories
        """
        # Get all advisories
        all_advisories = self.db.get_advisories_by_product(product)

        # Filter by version if provided
        if version:
            all_advisories = [
                adv for adv in all_advisories
                if self._version_matches(version, adv.get("version", ""))
            ]

        logger.debug(f"Found {len(all_advisories)} matching advisories for {product} {version}")
        return all_advisories

    @staticmethod
    def _version_matches(target_version: str, advisory_version: str) -> bool:
        """
        Check if versions match (exact match or advisory covers target).

        Args:
            target_version: Version in inventory
            advisory_version: Version in advisory

        Returns:
            True if versions match
        """
        if not advisory_version:
            return True  # If advisory doesn't specify version, assume it applies

        # Exact match
        if target_version == advisory_version:
            return True

        # Simple version range check (e.g., "<=9.0" or ">=1.1")
        if "<" in advisory_version or ">" in advisory_version or "=" in advisory_version:
            try:
                # This is a simplified version check
                # For production, use packaging.version.parse()
                return True  # For now, assume it matches
            except:
                return True

        return False

    def match_inventory_to_advisories(self) -> Dict:
        """
        Match all inventory items to advisories.

        Returns:
            Dictionary with matches and statistics
        """
        logger.info("Matching inventory to advisories")

        inventory = self.db.get_inventory()
        results = {
            "total_inventory_items": len(inventory),
            "items_with_matches": 0,
            "total_matches": 0,
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
            "matches_by_item": []
        }

        for item in inventory:
            matches = self.find_matching_advisories(
                item["product"],
                item["version"]
            )

            if matches:
                results["items_with_matches"] += 1
                results["total_matches"] += len(matches)

                # Count by severity
                for match in matches:
                    severity = match.get("severity", "")
                    if severity == "Critical":
                        results["critical_vulnerabilities"] += 1
                    elif severity == "High":
                        results["high_vulnerabilities"] += 1

                    # Record in database
                    self.db.add_inventory_match(
                        item["id"],
                        match["id"],
                        match["cve_id"],
                        severity
                    )

                results["matches_by_item"].append({
                    "product": item["product"],
                    "version": item["version"],
                    "match_count": len(matches),
                    "critical_count": len([m for m in matches if m.get("severity") == "Critical"]),
                    "high_count": len([m for m in matches if m.get("severity") == "High"])
                })

        logger.info(f"Inventory matching complete. Found {results['total_matches']} matches")
        return results

    def generate_risk_report(self, inventory_id: int = None) -> Dict:
        """
        Generate risk report for inventory.

        Args:
            inventory_id: Optional specific inventory item ID

        Returns:
            Risk report dictionary
        """
        logger.info("Generating risk report")

        report = {
            "generated_at": str(datetime.now()),
            "inventory_items": [],
            "summary": {
                "total_items": 0,
                "at_risk": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0
            }
        }

        inventory = self.db.get_inventory()
        if inventory_id:
            inventory = [item for item in inventory if item["id"] == inventory_id]

        report["summary"]["total_items"] = len(inventory)

        for item in inventory:
            matches = self.db.get_inventory_matches(item["id"])

            if matches:
                report["summary"]["at_risk"] += 1

                item_report = {
                    "product": item["product"],
                    "version": item["version"],
                    "vulnerabilities": len(matches),
                    "by_severity": {},
                    "critical_vulnerabilities": []
                }

                severity_counts = {}
                for match in matches:
                    severity = match.get("severity", "Unknown")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    report["summary"][f"{severity.lower()}_count"] = report["summary"].get(f"{severity.lower()}_count", 0) + 1

                    if severity == "Critical":
                        item_report["critical_vulnerabilities"].append({
                            "cve_id": match["cve_id"],
                            "title": match.get("title", ""),
                            "url": match.get("url", "")
                        })

                item_report["by_severity"] = severity_counts
                report["inventory_items"].append(item_report)

        logger.info(f"Risk report generated for {len(inventory)} items")
        return report

    def export_risk_report(self, report: Dict, output_path: str) -> bool:
        """
        Export risk report to JSON file.

        Args:
            report: Risk report dictionary
            output_path: Path to output JSON file

        Returns:
            Success status
        """
        try:
            import json
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Risk report exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting risk report: {e}")
            return False

    def get_affected_products_list(self) -> List[Dict]:
        """
        Get list of products affected by advisories with counts.

        Returns:
            List of affected products with statistics
        """
        logger.info("Generating affected products list")

        inventory = self.db.get_inventory()
        affected_products = []

        for item in inventory:
            matches = self.db.get_inventory_matches(item["id"])

            if matches:
                affected_products.append({
                    "product": item["product"],
                    "version": item["version"],
                    "total_cves": len(matches),
                    "critical_cves": len([m for m in matches if m.get("severity") == "Critical"]),
                    "high_cves": len([m for m in matches if m.get("severity") == "High"]),
                    "recommendation": self._generate_recommendation(matches)
                })

        return sorted(
            affected_products,
            key=lambda x: x["critical_cves"],
            reverse=True
        )

    @staticmethod
    def _generate_recommendation(matches: List[Dict]) -> str:
        """Generate recommendation based on matches."""
        critical_count = len([m for m in matches if m.get("severity") == "Critical"])
        high_count = len([m for m in matches if m.get("severity") == "High"])

        if critical_count > 0:
            return f"URGENT: {critical_count} critical vulnerabilities found. Patch immediately."
        elif high_count > 3:
            return f"HIGH PRIORITY: {high_count} high-severity vulnerabilities. Plan patching within 7 days."
        elif high_count > 0:
            return f"MEDIUM PRIORITY: {high_count} high-severity vulnerabilities. Patch within 30 days."
        else:
            return "Monitor for updates and patch as part of regular maintenance."


from datetime import datetime
