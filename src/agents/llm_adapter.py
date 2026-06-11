from typing import Optional
import requests
import json


class OllamaAdapter:
    """Adapter for Ollama LLM running locally (e.g., Qwen 3.5).

    Ollama API: http://localhost:11434 (default)
    Model: qwen:0.5b or similar available in local Ollama installation
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "qwen:0.5b", base_url: str = "http://localhost:11434"):
        self.api_key = api_key  # For future use if needed
        self.model = model
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/generate"
        self.ollama_available = None  # Cache availability check

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        if self.ollama_available is not None:
            return self.ollama_available
        
        try:
            # Try to reach Ollama health endpoint
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self.ollama_available = response.status_code == 200
            return self.ollama_available
        except requests.exceptions.ConnectionError:
            self.ollama_available = False
            return False
        except Exception:
            self.ollama_available = False
            return False

    def _get_available_models(self) -> list:
        """Get list of models available in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama API and return generated text."""
        # Check if Ollama is available first
        if not self._check_ollama_available():
            return f"[Error: Ollama is not running at {self.base_url}. Start Ollama with: ollama serve]"
        
        try:
            # Check if model exists
            available_models = self._get_available_models()
            if self.model not in available_models:
                models_str = ", ".join(available_models) if available_models else "none"
                return f"[Error: Model '{self.model}' not found. Available models: {models_str}. Pull it with: ollama pull {self.model}]"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.5,
            }
            response = requests.post(self.endpoint, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.exceptions.ConnectionError:
            return f"[Error: Cannot connect to Ollama at {self.base_url}. Start Ollama with: ollama serve]"
        except requests.exceptions.Timeout:
            return f"[Error: Ollama request timed out (180s). Model may be too large or system very slow. Try a smaller model.]"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return f"[Error: Model endpoint not found. Ensure Ollama is running and model is pulled.]"
            return f"[Error: HTTP {e.response.status_code} from Ollama]"
        except Exception as e:
            return f"[Error calling Ollama: {str(e)}]"

    def summarize(self, title: str, text: str, max_chars: int = 500) -> str:
        """Use Ollama to summarize or polish insight text."""
        if not text:
            return "No content to summarize."

        # Craft a prompt for Ollama to polish/summarize the insight
        prompt = f"""You are an executive summary writer. Polish and enhance the following insight for a PowerPoint presentation.
Keep it concise, professional, and impactful (max 3-4 sentences).

Title: {title}
Text: {text}

Polished summary:"""

        response = self._call_ollama(prompt, max_tokens=max_chars)
        
        # If error occurred, return the original text with warning
        if response.startswith("[Error"):
            print(f"⚠️ {response}")
            # Fallback: simple text truncation
            return text.strip()[:max_chars] if len(text.strip()) > max_chars else text.strip()
        
        return response.strip()


# Backward compatibility: alias for existing code
QWEXAdapter = OllamaAdapter

