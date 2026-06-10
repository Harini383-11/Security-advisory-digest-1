"""
Report generation for security advisories scan results.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models import AdvisoryDB, InventoryItemDB, AISummary, ReportData, AdvisoryMatch

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate reports from scan results."""

    @staticmethod
    def generate_report(
        advisories: List[AdvisoryDB],
        inventory_items: List[InventoryItemDB],
        matches: dict,
        summaries: dict,
        output_path: Optional[Path] = None
    ) -> ReportData:
        """
        Generate comprehensive report.
        
        Args:
            advisories: List of advisories found
            inventory_items: List of inventory items
            matches: Dict mapping advisory_id to matched inventory items
            summaries: Dict mapping advisory_id to AI summaries
            output_path: Optional path to save JSON report
            
        Returns:
            ReportData object
        """
        scan_time = datetime.now().isoformat()
        
        # Build matched advisories with inventory items
        advisory_matches = []
        for advisory in advisories:
            if advisory.advisory_id in matches:
                matched_items = matches[advisory.advisory_id]
                
                if matched_items:
                    # Determine max risk level
                    risk_levels = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
                    max_risk = max(
                        [risk_levels.get(item[1], 0) for item in matched_items],
                        default=0
                    )
                    
                    # Reverse mapping
                    risk_level_map = {4: "CRITICAL", 3: "HIGH", 2: "MEDIUM", 1: "LOW"}
                    risk_level = risk_level_map.get(max_risk, "UNKNOWN")
                    
                    # Create inventory item models
                    inventory_models = [item[0] for item in matched_items]
                    
                    advisory_match = AdvisoryMatch(
                        advisory=advisory,
                        matches=inventory_models,
                        risk_level=risk_level
                    )
                    advisory_matches.append(advisory_match)
        
        # Get executive summary from first summary if available
        executive_summary = ""
        if summaries:
            first_summary = next(iter(summaries.values()), None)
            if first_summary:
                executive_summary = first_summary.executive_summary
        
        report = ReportData(
            scan_time=scan_time,
            total_advisories=len(advisories),
            matches=advisory_matches,
            executive_summary=executive_summary,
            all_advisories=advisories
        )
        
        if output_path:
            ReportGenerator.save_report(report, output_path)
        
        return report

    @staticmethod
    def save_report(report: ReportData, output_path: Path):
        """
        Save report to JSON file.
        
        Args:
            report: Report data
            output_path: Path to save file
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict for JSON serialization
            report_dict = {
                "scan_time": report.scan_time,
                "total_advisories": report.total_advisories,
                "matched_advisories": len(report.matches),
                "matches": [
                    {
                        "advisory": {
                            "id": m.advisory.id,
                            "advisory_id": m.advisory.advisory_id,
                            "title": m.advisory.title,
                            "severity": m.advisory.severity,
                            "vendor": m.advisory.vendor,
                            "product": m.advisory.product,
                            "url": m.advisory.url
                        },
                        "affected_items": [
                            {
                                "asset_id": item.asset_id,
                                "software_name": item.software_name,
                                "version": item.version
                            }
                            for item in m.matches
                        ],
                        "risk_level": m.risk_level
                    }
                    for m in report.matches
                ],
                "executive_summary": report.executive_summary
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            logger.info(f"Report saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    @staticmethod
    def generate_console_report(report: ReportData) -> str:
        """
        Generate human-readable console report.
        
        Args:
            report: Report data
            
        Returns:
            Formatted report string
        """
        lines = [
            "=" * 80,
            "SECURITY ADVISORY DIGEST REPORT",
            "=" * 80,
            f"Scan Time: {report.scan_time}",
            f"Total Advisories Found: {report.total_advisories}",
            f"Matched Advisories: {len(report.matches)}",
            "",
            "EXECUTIVE SUMMARY:",
            "-" * 80,
            report.executive_summary if report.executive_summary else "No summary available",
            "",
            "MATCHED ADVISORIES:",
            "-" * 80,
        ]
        
        if report.matches:
            for i, match in enumerate(report.matches, 1):
                lines.extend([
                    f"\n{i}. {match.advisory.title}",
                    f"   Advisory ID: {match.advisory.advisory_id}",
                    f"   Severity: {match.advisory.severity}",
                    f"   Risk Level: {match.risk_level}",
                    f"   Vendor/Product: {match.advisory.vendor} / {match.advisory.product}",
                    f"   Affected Items:",
                ])
                
                for item in match.matches:
                    lines.append(f"      - {item.software_name} v{item.version}")
                
                lines.append(f"   URL: {match.advisory.url}")
        else:
            lines.append("No matched advisories found.")
        
        lines.extend([
            "",
            "=" * 80,
        ])
        
        return "\n".join(lines)
