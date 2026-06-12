"""
Optional Gemini Bridge - Disabled by default.
Requires API key and internet connection.
"""

import sys
import io
import os
from typing import Optional, Dict, Any

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer and not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class GeminiBridge:
    """Optional bridge to Gemini API. Disabled by default."""

    def __init__(self, api_key: Optional[str] = None):
        self.enabled = False
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._check_availability()

    def _check_availability(self):
        """Check if bridge can be enabled"""
        if not self.api_key:
            print("[GeminiBridge] No API key provided. Bridge disabled.")
            return

        try:
            # Lazy import to avoid dependency if not used
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.enabled = True
            print("[GeminiBridge] Enabled. Ready for requests.")
        except ImportError:
            print("[GeminiBridge] google-generativeai not installed. Install with: pip install google-generativeai")
        except Exception as e:
            print(f"[GeminiBridge] Error initializing: {e}")

    async def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate response using Gemini"""
        if not self.enabled:
            return None

        try:
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"[GeminiBridge] Generation error: {e}")
            return None


# Singleton instance
_gemini_bridge = None


def get_gemini_bridge() -> GeminiBridge:
    global _gemini_bridge
    if _gemini_bridge is None:
        _gemini_bridge = GeminiBridge()
    return _gemini_bridge
