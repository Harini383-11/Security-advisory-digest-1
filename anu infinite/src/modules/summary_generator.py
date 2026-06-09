"""
Security Summary Generator for daily digests.

Generates executive summaries of latest security advisories.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.core.database import AdvisoryDatabase
from src.modules.llm_service import OllamaService


class SummaryGenerator:
    """Generates security digests and summaries."""

    def __init__(self, db: AdvisoryDatabase, llm: OllamaService):
        """Initialize summary generator."""
        self.db = db
        self.llm = llm

    def generate_daily_digest(self, days_back: int = 1) -> Optional[str]:
        """
        Generate daily security digest.

        Args:
            days_back: Number of days to look back (default 1 for previous day)

        Returns:
            Digest text or None
        """
        logger.info(f"Generating daily digest for last {days_back} days")

        # Get stats
        stats = self.db.get_statistics()
        critical_advs = self.db.get_critical_advisories(limit=100)

        # Filter by date if needed
        recent_advs = [a for a in critical_advs if self._is_recent(a.get("published_date"), days_back)]

        if not recent_advs:
            return "No critical advisories in the selected time period."

        # Build summary components
        critical_count = len([a for a in recent_advs if a.get("severity") == "Critical"])
        high_count = len([a for a in recent_advs if a.get("severity") == "High"])
        vendors_affected = set([a.get("vendor") for a in recent_advs if a.get("vendor")])

        summary_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_critical": critical_count,
            "total_high": high_count,
            "vendors_affected": list(vendors_affected)[:10],
            "top_cves": [a.get("cve_id") for a in recent_advs[:5]],
            "recommendations": self._generate_recommendations(recent_advs)
        }

        # Generate digest using LLM
        prompt = self._build_digest_prompt(summary_data, recent_advs)
        digest = self.llm.generate_text(prompt, max_tokens=800)

        return digest

    def generate_executive_summary(self) -> Dict:
        """
        Generate executive summary with all key metrics.

        Returns:
            Summary dictionary
        """
        logger.info("Generating executive summary")

        stats = self.db.get_statistics()
        critical_advs = self.db.get_critical_advisories(limit=50)
        inventory_stats = self._get_inventory_stats()

        summary = {
            "generated_at": datetime.now().isoformat(),
            "database_statistics": stats,
            "top_vulnerabilities": [
                {
                    "cve_id": a.get("cve_id"),
                    "severity": a.get("severity"),
                    "product": a.get("product"),
                    "description": a.get("description", "")[:200]
                }
                for a in critical_advs[:10]
            ],
            "inventory_at_risk": inventory_stats,
            "recommendations": self._generate_recommendations(critical_advs)
        }

        return summary

    def _get_inventory_stats(self) -> Dict:
        """Get inventory risk statistics."""
        try:
            inventory = self.db.get_inventory()
            at_risk = 0
            total_vulns = 0

            for item in inventory:
                matches = self.db.get_inventory_matches(item["id"])
                if matches:
                    at_risk += 1
                    total_vulns += len(matches)

            return {
                "total_items": len(inventory),
                "items_at_risk": at_risk,
                "total_vulnerabilities": total_vulns
            }
        except Exception as e:
            logger.error(f"Error getting inventory stats: {e}")
            return {}

    def _build_digest_prompt(self, summary_data: Dict, advisories: List[Dict]) -> str:
        """Build prompt for LLM digest generation."""
        prompt = f"""Generate a professional security digest for {summary_data.get('date')}:

STATISTICS:
- Critical Advisories: {summary_data.get('total_critical')}
- High Severity Advisories: {summary_data.get('total_high')}
- Affected Vendors: {', '.join(summary_data.get('vendors_affected', [])[:5])}
- Top CVEs: {', '.join(summary_data.get('top_cves', [])[:5])}

RECOMMENDATIONS:
{summary_data.get('recommendations')}

Generate an executive summary including:
1. Overall Security Posture Assessment
2. Key Vulnerabilities Requiring Action
3. Affected Products and Vendors
4. Recommended Actions with Timeline
5. Risk Score (High/Medium/Low)

Format as a professional security briefing."""

        return prompt

    @staticmethod
    def _is_recent(date_str: str, days_back: int) -> bool:
        """Check if date is within the specified days back."""
        try:
            if not date_str:
                return False
            advisory_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            threshold = datetime.now() - timedelta(days=days_back)
            return advisory_date >= threshold
        except:
            return False

    def _generate_recommendations(self, advisories: List[Dict]) -> str:
        """Generate recommendations based on advisories."""
        try:
            critical_count = len([a for a in advisories if a.get("severity") == "Critical"])
            high_count = len([a for a in advisories if a.get("severity") == "High"])

            recommendations = []

            if critical_count > 0:
                recommendations.append(f"• IMMEDIATE: {critical_count} critical vulnerabilities require immediate patching")

            if high_count > 5:
                recommendations.append(f"• URGENT: {high_count} high-severity vulnerabilities should be patched within 7 days")
            elif high_count > 0:
                recommendations.append(f"• HIGH: {high_count} high-severity vulnerabilities should be prioritized")

            recommendations.append("• Implement comprehensive vulnerability management program")
            recommendations.append("• Regular security assessments and monitoring")
            recommendations.append("• Incident response planning for critical vulnerabilities")

            return "\n".join(recommendations)

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return "See above vulnerabilities for details"

    def export_summary(self, summary: Dict, output_format: str = "json") -> bool:
        """
        Export summary to file.

        Args:
            summary: Summary dictionary
            output_format: "json" or "markdown"

        Returns:
            Success status
        """
        try:
            import json
            from pathlib import Path

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if output_format == "json":
                filepath = f"data/summaries/summary_{timestamp}.json"
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)

                with open(filepath, 'w') as f:
                    json.dump(summary, f, indent=2)

            elif output_format == "markdown":
                filepath = f"data/summaries/summary_{timestamp}.md"
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)

                with open(filepath, 'w') as f:
                    f.write("# Security Advisory Digest\n\n")
                    f.write(f"Generated: {summary.get('generated_at')}\n\n")
                    f.write("## Database Statistics\n\n")
                    stats = summary.get("database_statistics", {})
                    for key, value in stats.items():
                        f.write(f"- {key}: {value}\n")

            logger.info(f"Summary exported to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting summary: {e}")
            return False
