"""
Tests for LLM module.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from llm.ollama import OllamaClient
from llm.llm_service import LLMService
from models import AdvisoryDB


@pytest.fixture
def mock_ollama_client():
    """Fixture for mocked Ollama client."""
    return Mock(spec=OllamaClient)


@pytest.fixture
def sample_advisory():
    """Fixture for sample advisory."""
    return AdvisoryDB(
        advisory_id="test_001",
        title="Critical Security Vulnerability",
        description="A critical vulnerability has been discovered",
        severity="CRITICAL",
        vendor="TestVendor",
        product="TestProduct",
        published_date=datetime.now(),
        source_feed="https://example.com/feed",
        url="https://example.com/advisory"
    )


def test_ollama_client_initialization():
    """Test Ollama client initialization."""
    client = OllamaClient()
    assert client is not None
    assert client.base_url == "http://localhost:11434"
    assert client.model == "llama3"


def test_ollama_client_custom_url():
    """Test Ollama client with custom URL."""
    client = OllamaClient(base_url="http://example.com:8000", model="custom")
    assert client.base_url == "http://example.com:8000"
    assert client.model == "custom"


def test_llm_service_initialization():
    """Test LLM service initialization."""
    llm_service = LLMService()
    assert llm_service is not None


def test_llm_service_with_client(mock_ollama_client):
    """Test LLM service with custom client."""
    llm_service = LLMService(mock_ollama_client)
    assert llm_service.client == mock_ollama_client


def test_generate_executive_summary(sample_advisory):
    """Test executive summary generation."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.generate.return_value = "This is a test summary."
    
    llm_service = LLMService(mock_client)
    
    summary = llm_service._generate_executive_summary(sample_advisory)
    
    assert summary is not None
    assert mock_client.generate.called


def test_generate_business_impact(sample_advisory):
    """Test business impact generation."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.generate.return_value = "Business impact analysis here."
    
    llm_service = LLMService(mock_client)
    
    impact = llm_service._generate_business_impact(sample_advisory)
    
    assert impact is not None
    assert mock_client.generate.called


def test_generate_remediation_advice(sample_advisory):
    """Test remediation advice generation."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.generate.return_value = "Remediation steps here."
    
    llm_service = LLMService(mock_client)
    
    advice = llm_service._generate_remediation_advice(sample_advisory)
    
    assert advice is not None
    assert mock_client.generate.called


def test_generate_summary_complete(sample_advisory):
    """Test complete summary generation."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.generate.side_effect = [
        "Executive summary.",
        "Business impact.",
        "Remediation advice."
    ]
    
    llm_service = LLMService(mock_client)
    
    summary = llm_service.generate_summary(sample_advisory)
    
    assert summary is not None
    assert summary.executive_summary == "Executive summary."
    assert summary.business_impact == "Business impact."
    assert summary.remediation_advice == "Remediation advice."


def test_generate_summary_with_failure(sample_advisory):
    """Test summary generation with failure."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.generate.return_value = None
    
    llm_service = LLMService(mock_client)
    
    summary = llm_service.generate_summary(sample_advisory)
    
    # Should return None if generation fails
    assert summary is None


def test_is_available_true():
    """Test checking if LLM service is available (true case)."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.is_available.return_value = True
    
    llm_service = LLMService(mock_client)
    
    assert llm_service.is_available() is True


def test_is_available_false():
    """Test checking if LLM service is available (false case)."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.is_available.return_value = False
    
    llm_service = LLMService(mock_client)
    
    assert llm_service.is_available() is False
