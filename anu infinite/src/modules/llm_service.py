"""
Ollama LLM Integration for Security Advisory Digest.

Provides functions for summarization and analysis using Ollama.
"""

import requests
import json
from typing import Dict, List, Optional
from loguru import logger

from config.settings import OLLAMA_HOST, OLLAMA_MODEL


class OllamaService:
    """Integration with Ollama LLM."""

    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        """Initialize Ollama service."""
        self.host = host
        self.model = model
        self.api_url = f"{host}/api"
        self._verify_connection()

    def _verify_connection(self) -> bool:
        """Verify Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Connected to Ollama at {self.host}")
                return True
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            return False

    def generate_text(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None if error
        """
        try:
            logger.debug(f"Generating text with {self.model}")

            response = requests.post(
                f"{self.api_url}/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return None

        except requests.Timeout:
            logger.error("Ollama request timeout")
            return None
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None

    def summarize_advisory(self, advisory: Dict) -> Optional[str]:
        """
        Summarize a single advisory.

        Args:
            advisory: Advisory data dictionary

        Returns:
            Summary text or None
        """
        logger.info(f"Summarizing advisory {advisory.get('cve_id')}")

        prompt = f"""Summarize the following security advisory in 2-3 sentences:

CVE ID: {advisory.get('cve_id')}
Title: {advisory.get('title')}
Description: {advisory.get('description')}
Severity: {advisory.get('severity')}
Vendor: {advisory.get('vendor')}
Product: {advisory.get('product')}

Provide a concise, technical summary focusing on the impact and required action."""

        return self.generate_text(prompt, max_tokens=150)

    def summarize_advisories(self, advisories: List[Dict]) -> Optional[str]:
        """
        Generate summary of multiple advisories.

        Args:
            advisories: List of advisory dictionaries

        Returns:
            Summary text or None
        """
        logger.info(f"Summarizing {len(advisories)} advisories")

        critical_count = len([a for a in advisories if a.get("severity") == "Critical"])
        high_count = len([a for a in advisories if a.get("severity") == "High"])

        cves_list = ", ".join([a.get("cve_id") for a in advisories[:10]])

        prompt = f"""Generate an executive summary of the following security advisories:

Total Advisories: {len(advisories)}
Critical: {critical_count}
High: {high_count}
Sample CVEs: {cves_list}

Most Common Vendors: {', '.join(set([a.get('vendor') for a in advisories if a.get('vendor')])[:5])}

Provide a high-level summary for executives with key risks and recommendations."""

        return self.generate_text(prompt, max_tokens=300)

    def answer_user_query(self, query: str, context: str) -> Optional[str]:
        """
        Answer user question about advisories using context.

        Args:
            query: User question
            context: Relevant advisory context

        Returns:
            Answer text or None
        """
        logger.info(f"Answering query: {query}")

        prompt = f"""You are a security expert. Answer the following question based on the provided security advisory information.

Question: {query}

Context:
{context}

Provide a clear, technical answer. If the answer cannot be determined from the context, say so clearly."""

        return self.generate_text(prompt, max_tokens=400)

    def generate_risk_report(self, inventory_matches: List[Dict], inventory_item: Dict) -> Optional[str]:
        """
        Generate detailed risk report for an inventory item.

        Args:
            inventory_matches: List of vulnerability matches
            inventory_item: Inventory item information

        Returns:
            Risk report text or None
        """
        logger.info(f"Generating risk report for {inventory_item.get('product')}")

        critical_vulns = [m for m in inventory_matches if m.get("severity") == "Critical"]
        high_vulns = [m for m in inventory_matches if m.get("severity") == "High"]

        cve_list = ", ".join([m.get("cve_id") for m in inventory_matches[:5]])

        prompt = f"""Generate a security risk report for the following asset:

Product: {inventory_item.get('product')}
Version: {inventory_item.get('version')}

Vulnerabilities Found:
- Critical: {len(critical_vulns)}
- High: {len(high_vulns)}
- Total: {len(inventory_matches)}

Sample CVEs: {cve_list}

Provide:
1. Risk Assessment (1-3 sentences)
2. Required Actions (2-3 action items)
3. Urgency Level (Immediate/High/Medium/Low)"""

        return self.generate_text(prompt, max_tokens=300)

    def categorize_advisory(self, advisory: Dict) -> Optional[str]:
        """
        Categorize an advisory by attack type and impact.

        Args:
            advisory: Advisory data dictionary

        Returns:
            Categorization text or None
        """
        logger.info(f"Categorizing advisory {advisory.get('cve_id')}")

        prompt = f"""Categorize this security vulnerability:

CVE ID: {advisory.get('cve_id')}
Title: {advisory.get('title')}
Description: {advisory.get('description')}

Provide:
1. Attack Type (e.g., Remote Code Execution, SQL Injection, etc.)
2. CVSS Vector Category
3. Affected Component (Application, OS, Middleware, etc.)
4. Likelihood of Exploitation (High/Medium/Low)"""

        return self.generate_text(prompt, max_tokens=200)

    def generate_patch_recommendations(self, advisory: Dict) -> Optional[str]:
        """
        Generate patching recommendations for an advisory.

        Args:
            advisory: Advisory data dictionary

        Returns:
            Recommendations text or None
        """
        logger.info(f"Generating patch recommendations for {advisory.get('cve_id')}")

        prompt = f"""Generate patching recommendations for this vulnerability:

CVE ID: {advisory.get('cve_id')}
Product: {advisory.get('product')}
Version: {advisory.get('version')}
Severity: {advisory.get('severity')}
Description: {advisory.get('description')}

Provide:
1. Immediate Actions (if any temporary workarounds)
2. Patching Priority
3. Testing Recommendations
4. Deployment Timeline"""

        return self.generate_text(prompt, max_tokens=250)

    def health_check(self) -> Dict:
        """Check Ollama service health."""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_exists = any(m.get("name", "").startswith(self.model) for m in models)
                return {
                    "status": "healthy",
                    "host": self.host,
                    "model_available": model_exists,
                    "available_models": [m.get("name") for m in models]
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "offline",
                "error": str(e)
            }
