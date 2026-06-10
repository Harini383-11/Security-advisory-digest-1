"""
Main agent for orchestrating the Security Advisory Digest workflow.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from config import RSS_FEEDS, INVENTORY_FILE, DB_PATH
from db.sqlite import Database
from ingestion.rss import RSSIngester
from inventory.inventory_match import InventoryMatchService
from llm.ollama import OllamaClient
from llm.llm_service import LLMService
from models import AISummary
from reports.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class SecurityAdvisoryAgent:
    """Agent for orchestrating security advisory digest workflow."""

    def __init__(self):
        """Initialize the agent."""
        logger.info("Initializing Security Advisory Agent")
        self.database = Database(DB_PATH)
        self.rss_ingester = RSSIngester()
        self.inventory_service = InventoryMatchService()
        self.llm_service = LLMService()

    def run(self, force_refresh: bool = False, advisories_override: Optional[List] = None, inventory_override: Optional[List] = None) -> Optional[Dict]:
        """
        Execute the complete agent workflow.
        
        Workflow:
        Step 1: Read RSS feeds
        Step 2: Store advisories
        Step 3: Load inventory
        Step 4: Match advisories
        Step 5: Generate AI summary
        Step 6: Generate report
        Step 7: Return JSON response
        
        Args:
            force_refresh: Force refresh of advisories
            
        Returns:
            Report data as dictionary or None if error
        """
        try:
            logger.info("=" * 80)
            logger.info("Starting Security Advisory Digest Workflow")
            logger.info("=" * 80)
            
            # Step 1: Read RSS feeds (or use override)
            logger.info("STEP 1: Reading RSS feeds or using override...")
            if advisories_override is not None:
                advisories = advisories_override
                logger.info(f"Using {len(advisories)} advisories from override input")
            else:
                advisories = self._step_1_read_feeds()
            if not advisories:
                logger.warning("No advisories found in feeds")
            else:
                logger.info(f"✓ Found {len(advisories)} advisories from feeds")
            
            # Step 2: Store advisories
            logger.info("STEP 2: Storing advisories in database...")
            stored_count = self._step_2_store_advisories(advisories, force_refresh)
            logger.info(f"✓ Stored {stored_count} new advisories")
            
            # Step 3: Load inventory (or use override)
            logger.info("STEP 3: Loading inventory or using override...")
            if inventory_override is not None:
                inventory_items = inventory_override
                logger.info(f"Using {len(inventory_items)} inventory items from override input")
                # Persist override inventory items to DB so they have stable IDs for matching
                for item in inventory_items:
                    try:
                        # Accept either model instances or plain dicts
                        if hasattr(item, 'id') and item.id:
                            continue
                        # If it's a dict, create minimal object for DB insertion
                        from models import InventoryItemDB
                        inv = item if isinstance(item, InventoryItemDB) else InventoryItemDB(**item)
                        new_id = self.database.add_inventory_item(inv)
                        inv.id = new_id
                        # If original was a dict, replace its contents
                        if not isinstance(item, InventoryItemDB):
                            item.update({'id': new_id})
                    except Exception as e:
                        logger.warning(f"Error persisting override inventory item: {getattr(item, 'asset_id', str(item))}: {e}")
                        continue
            else:
                inventory_items = self._step_3_load_inventory()
            logger.info(f"✓ Loaded {len(inventory_items)} inventory items")
            
            if not inventory_items:
                logger.warning("No inventory items found")
                return self._create_response("success", "No inventory to match")
            
            # Step 4: Match advisories
            logger.info("STEP 4: Matching advisories against inventory...")
            matches = self._step_4_match_advisories(advisories, inventory_items)
            matched_count = sum(len(v) for v in matches.values())
            logger.info(f"✓ Found {matched_count} matches")
            
            # Step 5: Generate AI summaries
            logger.info("STEP 5: Generating AI summaries...")
            summaries = self._step_5_generate_summaries(advisories)
            logger.info(f"✓ Generated {len(summaries)} summaries")
            
            # Step 6: Generate report
            logger.info("STEP 6: Generating report...")
            report = self._step_6_generate_report(advisories, inventory_items, matches, summaries)
            logger.info("✓ Report generated successfully")
            
            # Step 7: Return JSON response
            logger.info("STEP 7: Preparing JSON response...")
            response = self._step_7_create_response(report)
            logger.info("✓ JSON response prepared")
            
            logger.info("=" * 80)
            logger.info("Workflow completed successfully")
            logger.info("=" * 80)
            
            return response
            
        except Exception as e:
            logger.error(f"Agent workflow failed: {e}", exc_info=True)
            return self._create_response(
                "error",
                f"Workflow failed: {str(e)}",
                error=str(e)
            )

    def _step_1_read_feeds(self) -> List:
        """Step 1: Read RSS feeds."""
        advisories = []
        
        for feed_url in RSS_FEEDS:
            try:
                logger.debug(f"Ingesting feed: {feed_url}")
                feed_advisories = self.rss_ingester.ingest_feed(feed_url)
                advisories.extend(feed_advisories)
            except Exception as e:
                logger.error(f"Error reading feed {feed_url}: {e}")
                continue
        
        logger.info(f"Total advisories read from all feeds: {len(advisories)}")
        return advisories

    def _step_2_store_advisories(self, advisories: List, force_refresh: bool = False) -> int:
        """Step 2: Store advisories in database."""
        stored_count = 0
        
        for advisory in advisories:
            try:
                self.database.add_advisory(advisory)
                stored_count += 1
            except Exception as e:
                logger.warning(f"Error storing advisory {advisory.advisory_id}: {e}")
                continue
        
        logger.info(f"Stored advisories: {stored_count}")
        return stored_count

    def _step_3_load_inventory(self) -> List:
        """Step 3: Load inventory from CSV."""
        inventory = self.inventory_service.load_inventory_from_csv(INVENTORY_FILE)
        
        # Store inventory in database
        for item in inventory:
            try:
                self.database.add_inventory_item(item)
            except Exception as e:
                logger.warning(f"Error storing inventory item {item.asset_id}: {e}")
                continue
        
        return inventory

    def _step_4_match_advisories(self, advisories: List, inventory_items: List) -> Dict:
        """Step 4: Match advisories against inventory."""
        matches = {}
        
        for advisory in advisories:
            try:
                advisory_matches = self.inventory_service.matcher.find_matches(
                    advisory,
                    inventory_items
                )
                
                if advisory_matches:
                    matches[advisory.advisory_id] = advisory_matches
                    
                    # Store matches in database
                    advisory_db = self.database.get_advisory_by_id_string(advisory.advisory_id)
                    if advisory_db:
                        for matched_item, risk_level in advisory_matches:
                            try:
                                from models import MatchDB
                                match = MatchDB(
                                    advisory_id=advisory_db.id,
                                    inventory_item_id=matched_item.id,
                                    risk_level=risk_level
                                )
                                self.database.add_match(match)
                            except Exception as e:
                                logger.debug(f"Error storing match: {e}")
                                continue
                
            except Exception as e:
                logger.error(f"Error matching advisory {advisory.advisory_id}: {e}")
                continue
        
        logger.info(f"Matched advisories: {len(matches)}")
        return matches

    def _step_5_generate_summaries(self, advisories: List) -> Dict[str, AISummary]:
        """Step 5: Generate AI summaries."""
        summaries = {}
        
        if not self.llm_service.is_available():
            logger.warning("LLM service not available, skipping summaries")
            return summaries
        
        for advisory in advisories[:5]:  # Limit to first 5 for demo
            try:
                logger.debug(f"Generating summary for {advisory.advisory_id}")
                summary = self.llm_service.generate_summary(advisory)
                
                if summary:
                    summaries[advisory.advisory_id] = summary
                    logger.debug(f"✓ Summary generated for {advisory.advisory_id}")
                
            except Exception as e:
                logger.warning(f"Error generating summary for {advisory.advisory_id}: {e}")
                continue
        
        logger.info(f"Generated {len(summaries)} summaries")
        return summaries

    def _step_6_generate_report(
        self,
        advisories: List,
        inventory_items: List,
        matches: Dict,
        summaries: Dict
    ):
        """Step 6: Generate report."""
        report = ReportGenerator.generate_report(
            advisories,
            inventory_items,
            matches,
            summaries,
            output_path=Path("data/report.json")
        )
        
        return report

    def _step_7_create_response(self, report) -> Dict:
        """Step 7: Create JSON response."""
        return self._create_response(
            "success",
            "Scan completed successfully",
            report=report
        )

    @staticmethod
    def _create_response(
        status: str,
        message: str,
        report=None,
        error: Optional[str] = None
    ) -> Dict:
        """Create standard response object."""
        response = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "report": None,
            "error": error
        }
        
        if report:
            response["report"] = {
                "scan_time": report.scan_time,
                "total_advisories": report.total_advisories,
                "matched_count": len(report.matches),
                "matches": [
                    {
                        "advisory_id": m.advisory.advisory_id,
                        "title": m.advisory.title,
                        "severity": m.advisory.severity,
                        "risk_level": m.risk_level,
                        "affected_items": [
                            {
                                "software_name": item.software_name,
                                "version": item.version
                            }
                            for item in m.matches
                        ]
                    }
                    for m in report.matches
                ],
                "executive_summary": report.executive_summary
            }
        
        return response

    def close(self):
        """Clean up resources."""
        logger.info("Closing agent resources")
        self.rss_ingester.close()
        self.database.close()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    agent = SecurityAdvisoryAgent()
    result = agent.run()
    
    if result:
        import json
        print(json.dumps(result, indent=2, default=str))
    
    agent.close()
