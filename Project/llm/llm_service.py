"""
LLM service for security advisory summarization and analysis.
"""
import logging
from typing import Optional

from models import AdvisoryDB, AISummary
from llm.ollama import OllamaClient

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based advisory analysis."""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        Initialize LLM service.
        
        Args:
            ollama_client: OllamaClient instance, creates new one if None
        """
        self.client = ollama_client or OllamaClient()

    def generate_summary(self, advisory: AdvisoryDB) -> Optional[AISummary]:
        """
        Generate AI summary for an advisory.
        
        Args:
            advisory: Advisory to summarize
            
        Returns:
            AISummary object or None if generation fails
        """
        try:
            # Generate executive summary
            executive_summary = self._generate_executive_summary(advisory)
            if not executive_summary:
                return None
            
            # Generate business impact
            business_impact = self._generate_business_impact(advisory)
            if not business_impact:
                business_impact = "Unable to generate business impact analysis."
            
            # Generate remediation advice
            remediation_advice = self._generate_remediation_advice(advisory)
            if not remediation_advice:
                remediation_advice = "Refer to official vendor documentation for remediation steps."
            
            return AISummary(
                executive_summary=executive_summary,
                business_impact=business_impact,
                remediation_advice=remediation_advice
            )
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def _generate_executive_summary(self, advisory: AdvisoryDB) -> Optional[str]:
        """Generate executive summary for advisory."""
        prompt = f"""You are a cybersecurity analyst. Provide a concise executive summary (2-3 sentences) of this security advisory:

Title: {advisory.title}
Severity: {advisory.severity}
Vendor: {advisory.vendor}
Product: {advisory.product}

Description:
{advisory.description}

Provide only the summary, no additional text."""

        system = "You are a cybersecurity expert. Provide clear, actionable security analysis."
        
        summary = self.client.generate(prompt, system)
        if summary:
            logger.debug("Executive summary generated successfully")
        return summary

    def _generate_business_impact(self, advisory: AdvisoryDB) -> Optional[str]:
        """Generate business impact analysis for advisory."""
        prompt = f"""As a security consultant, analyze the business impact of this advisory:

Title: {advisory.title}
Severity: {advisory.severity}
Vendor: {advisory.vendor}
Product: {advisory.product}

Description:
{advisory.description}

Explain in 3-4 sentences:
1. What systems/services could be affected
2. Potential business consequences
3. Urgency level

Provide only the analysis, no additional text."""

        system = "You are a security business consultant. Focus on business impact and risk."
        
        impact = self.client.generate(prompt, system)
        if impact:
            logger.debug("Business impact analysis generated successfully")
        return impact

    def _generate_remediation_advice(self, advisory: AdvisoryDB) -> Optional[str]:
        """Generate remediation advice for advisory."""
        prompt = f"""As a security operations expert, provide remediation steps for this advisory:

Title: {advisory.title}
Vendor: {advisory.vendor}
Product: {advisory.product}

Description:
{advisory.description}

Provide 3-5 specific remediation steps:
1. Immediate actions
2. Short-term fixes
3. Long-term solutions

Provide only the steps, no additional text."""

        system = "You are a security operations expert. Provide specific, actionable remediation steps."
        
        remediation = self.client.generate(prompt, system)
        if remediation:
            logger.debug("Remediation advice generated successfully")
        return remediation

    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.client.is_available()
