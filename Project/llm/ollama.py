"""
Ollama LLM integration for security advisory summarization.
"""
import logging
import requests
from typing import Optional

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM service."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama service URL
            model: Model name to use
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = OLLAMA_TIMEOUT

    def is_available(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if service is reachable
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=REQUEST_TIMEOUT
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service not available: {e}")
            return False

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system: Optional system prompt
            
        Returns:
            Generated text or None if error
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 1024,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            if system:
                payload["system"] = system
            
            logger.debug(f"Calling Ollama with model {self.model}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None

    def check_model_available(self) -> bool:
        """
        Check if the specified model is available in Ollama.
        
        Returns:
            True if model is available
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"].split(":")[0] for m in models]
                return self.model in model_names
            
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
