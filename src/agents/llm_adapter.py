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
        self.base_url = base_url.rstrip('/')
        # Ollama-style endpoint
        self.endpoint = f"{self.base_url}/api/generate"
        # Chat-style endpoint (e.g. GPU server exposing /v1/chat/completions)
        self.chat_endpoint = f"{self.base_url}/v1/chat/completions"
        self.ollama_available = None  # Cache availability check

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        if self.ollama_available is not None:
            return self.ollama_available
        
        try:
            # Try to reach Ollama health endpoint first
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.ollama_available = True
                return True
        except Exception:
            # Not necessarily Ollama; try chat endpoint health
            pass

        try:
            # Try chat server health / simple GET to root of chat endpoint
            response = requests.get(self.chat_endpoint, timeout=5)
            # Some chat servers may reject GET; treat any response as available
            self.ollama_available = response.status_code in (200, 405, 400)
            return self.ollama_available
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

    def _use_chat_api(self) -> bool:
        """Determine whether to use chat completions API instead of Ollama API.

        Heuristics: if chat endpoint contains '/v1' or base_url port 8000 is used, prefer chat API.
        """
        if "/v1" in self.chat_endpoint or self.base_url.endswith(":8000") or ":8000" in self.base_url:
            return True
        return False

    def _call_chat_api(self, prompt: str, max_tokens: int = 500) -> str:
        """Call a Chat Completions-style API (e.g. local GPU server) and return text."""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": max_tokens,
            }
            response = requests.post(self.chat_endpoint, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            # Typical response: {"choices":[{"message":{"content":"..."}}]}
            if isinstance(data, dict) and "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                # support both choice.message.content and choice.text
                content = None
                if isinstance(choice.get("message"), dict):
                    content = choice["message"].get("content")
                if not content:
                    content = choice.get("text") or choice.get("message")
                if content:
                    return content.strip()
            return "[Error: Unexpected response from chat server]"
        except requests.exceptions.ConnectionError:
            return f"[Error: Cannot connect to chat server at {self.chat_endpoint}. Start the server and retry]"
        except requests.exceptions.Timeout:
            return f"[Error: Chat server request timed out (180s). Model may be large or server slow.]"
        except requests.exceptions.HTTPError as e:
            return f"[Error: HTTP {e.response.status_code} from chat server]"
        except Exception as e:
            return f"[Error calling chat server: {str(e)}]"

    def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama API and return generated text."""
        # If chat-style endpoint is preferred, use it
        if self._use_chat_api():
            return self._call_chat_api(prompt, max_tokens=max_tokens)

        # Otherwise proceed with Ollama-style API
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

