"""
AI Agent Loop for Security Advisory Digest.

Multi-step reasoning agent that retrieves advisories, checks inventory,
and generates answers with confidence scoring.
"""

from typing import Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum

from src.core.database import AdvisoryDatabase
from src.modules.rag import RAGEngine
from src.modules.llm_service import OllamaService
from src.modules.inventory_match import InventoryMatcher


class ConfidenceLevel(Enum):
    """Confidence levels for agent responses."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SecurityAgent:
    """AI agent for security advisory queries."""

    def __init__(self, db: AdvisoryDatabase, rag: RAGEngine, llm: OllamaService, matcher: InventoryMatcher):
        """Initialize security agent with dependencies."""
        self.db = db
        self.rag = rag
        self.llm = llm
        self.matcher = matcher
        self.max_retrieval_iterations = 3

    def process_query(self, query: str, inventory_context: bool = True) -> Dict:
        """
        Process user query through multi-step reasoning.

        Args:
            query: User question
            inventory_context: Whether to include inventory context

        Returns:
            Response dictionary with answer and confidence
        """
        logger.info(f"Processing query: {query}")

        response = {
            "query": query,
            "answer": None,
            "confidence": ConfidenceLevel.LOW.value,
            "sources": [],
            "reasoning_steps": [],
            "retrieved_advisories": 0
        }

        try:
            # Step 1: Retrieve relevant advisories from vector DB
            response["reasoning_steps"].append("Retrieving relevant advisories...")
            advisories = self._retrieve_advisories(query)
            response["retrieved_advisories"] = len(advisories)
            response["sources"] = [a.get("metadata", {}).get("cve_id") for a in advisories[:5]]

            if not advisories:
                response["reasoning_steps"].append("No advisories found, checking inventory...")
                # If no advisories, check if query mentions an inventory item
                if inventory_context:
                    advisories = self._check_inventory_relevance(query)

            # Step 2: Check inventory if applicable
            if inventory_context:
                response["reasoning_steps"].append("Checking inventory matches...")
                inventory_matches = self._check_inventory_matches(query, advisories)
            else:
                inventory_matches = []

            # Step 3: Generate initial answer
            response["reasoning_steps"].append("Generating answer...")
            answer = self._generate_answer(query, advisories, inventory_matches)

            if not answer:
                response["reasoning_steps"].append("Answer quality low, retrieving more context...")
                # Step 4: If confidence is low, retrieve more context
                advisories = self._retrieve_more_context(query, advisories)
                answer = self._generate_answer(query, advisories, inventory_matches)

            response["answer"] = answer

            # Step 5: Score confidence
            response["reasoning_steps"].append("Scoring confidence...")
            confidence = self._score_confidence(query, advisories, answer)
            response["confidence"] = confidence.value

            logger.info(f"Query processed with {confidence.value} confidence")

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            response["answer"] = f"Error processing query: {str(e)}"
            response["confidence"] = ConfidenceLevel.LOW.value

        return response

    def _retrieve_advisories(self, query: str, top_k: int = 10) -> List[Dict]:
        """Retrieve relevant advisories using RAG."""
        try:
            results = self.rag.search_vectors(query, top_k=top_k)
            logger.info(f"Retrieved {len(results)} advisories")
            return results
        except Exception as e:
            logger.error(f"Error retrieving advisories: {e}")
            return []

    def _retrieve_more_context(self, query: str, initial_advisories: List[Dict], top_k: int = 20) -> List[Dict]:
        """Retrieve more context with expanded search."""
        try:
            logger.info("Expanding retrieval...")
            # Try different search approaches
            results = self.rag.search_vectors(query, top_k=top_k)

            # Combine with initial results, removing duplicates
            seen_ids = {a.get("id") for a in initial_advisories}
            expanded = initial_advisories.copy()

            for result in results:
                if result.get("id") not in seen_ids:
                    expanded.append(result)
                    seen_ids.add(result.get("id"))

            return expanded
        except Exception as e:
            logger.error(f"Error expanding retrieval: {e}")
            return initial_advisories

    def _check_inventory_matches(self, query: str, advisories: List[Dict]) -> List[Dict]:
        """Check if query mentions inventory items and find matches."""
        try:
            matches = []
            inventory = self.db.get_inventory()

            for item in inventory:
                # Simple check if product mentioned in query
                if item["product"].lower() in query.lower():
                    item_matches = self.db.get_inventory_matches(item["id"])
                    matches.extend(item_matches)

            logger.debug(f"Found {len(matches)} inventory matches")
            return matches
        except Exception as e:
            logger.error(f"Error checking inventory matches: {e}")
            return []

    def _check_inventory_relevance(self, query: str) -> List[Dict]:
        """Check if query is inventory-related and retrieve relevant advisories."""
        try:
            inventory = self.db.get_inventory()
            advisories = []

            for item in inventory:
                if item["product"].lower() in query.lower():
                    item_advisories = self.matcher.find_matching_advisories(
                        item["product"],
                        item["version"]
                    )
                    advisories.extend(item_advisories)

            return advisories
        except Exception as e:
            logger.error(f"Error checking inventory relevance: {e}")
            return []

    def _generate_answer(self, query: str, advisories: List[Dict], inventory_matches: List[Dict]) -> Optional[str]:
        """Generate answer using LLM."""
        try:
            if not advisories and not inventory_matches:
                return "No relevant security advisories found for your query."

            # Build context from advisories
            context = "RETRIEVED ADVISORIES:\n"
            for i, adv in enumerate(advisories[:5], 1):
                context += f"\n{i}. {adv.get('document', '')[:500]}"

            if inventory_matches:
                context += "\n\nINVENTORY MATCHES:\n"
                for i, match in enumerate(inventory_matches[:5], 1):
                    context += f"\n{i}. CVE: {match.get('cve_id')} - Severity: {match.get('severity')}"

            # Generate answer
            answer = self.llm.answer_user_query(query, context)
            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return None

    def _score_confidence(self, query: str, advisories: List[Dict], answer: Optional[str]) -> ConfidenceLevel:
        """Score confidence in the answer."""
        try:
            if not answer:
                return ConfidenceLevel.LOW

            # Calculate confidence based on factors
            factors = {
                "has_answer": answer and len(answer) > 20,
                "has_advisories": len(advisories) > 0,
                "advisories_count": len(advisories) >= 5,
                "answer_length": len(answer) > 100
            }

            confidence_score = sum(factors.values())

            if confidence_score >= 4:
                return ConfidenceLevel.HIGH
            elif confidence_score >= 2:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW

        except Exception as e:
            logger.error(f"Error scoring confidence: {e}")
            return ConfidenceLevel.LOW

    def search_cve(self, cve_id: str) -> Dict:
        """Search for specific CVE."""
        logger.info(f"Searching for CVE {cve_id}")

        advisory = self.db.get_advisory_by_cve(cve_id)

        if not advisory:
            return {"error": f"CVE {cve_id} not found"}

        return {
            "cve_id": advisory.get("cve_id"),
            "title": advisory.get("title"),
            "description": advisory.get("description"),
            "severity": advisory.get("severity"),
            "vendor": advisory.get("vendor"),
            "product": advisory.get("product"),
            "url": advisory.get("url"),
            "published_date": advisory.get("published_date")
        }

    def get_critical_advisories(self, limit: int = 10) -> List[Dict]:
        """Get list of critical advisories."""
        logger.info("Fetching critical advisories")

        advisories = self.db.get_critical_advisories(limit=limit)

        return [
            {
                "cve_id": a.get("cve_id"),
                "title": a.get("title"),
                "severity": a.get("severity"),
                "product": a.get("product"),
                "url": a.get("url")
            }
            for a in advisories
        ]

    def get_inventory_risk_summary(self) -> Dict:
        """Get summary of inventory risks."""
        logger.info("Generating inventory risk summary")

        inventory = self.db.get_inventory()
        total_matches = 0
        critical_count = 0
        high_count = 0

        at_risk_items = []

        for item in inventory:
            matches = self.db.get_inventory_matches(item["id"])
            if matches:
                total_matches += len(matches)
                critical_count += len([m for m in matches if m.get("severity") == "Critical"])
                high_count += len([m for m in matches if m.get("severity") == "High"])

                at_risk_items.append({
                    "product": item["product"],
                    "version": item["version"],
                    "vulnerabilities": len(matches)
                })

        return {
            "total_inventory_items": len(inventory),
            "items_at_risk": len(at_risk_items),
            "total_vulnerabilities": total_matches,
            "critical_vulnerabilities": critical_count,
            "high_vulnerabilities": high_count,
            "top_at_risk": sorted(at_risk_items, key=lambda x: x["vulnerabilities"], reverse=True)[:5]
        }
