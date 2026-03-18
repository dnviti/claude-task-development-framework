"""Local diffuser image provider via REST API.

Connects to a local diffusion model server (e.g. OllamaDiffuser,
Automatic1111 WebUI, ComfyUI) via its REST API for on-device
image generation.

Zero external dependencies -- stdlib only (urllib, json).
"""

import base64
import json
import urllib.error
import urllib.request
from typing import Optional

from image_providers import ImageProvider


# ── Default Configuration ────────────────────────────────────────────────────

_DEFAULT_BASE_URL = "http://localhost:7860"
_DEFAULT_TIMEOUT = 120  # seconds — image generation can be slow


class LocalDiffuserProvider(ImageProvider):
    """Image provider using a local diffusion model REST API.

    Supports Automatic1111/Stable Diffusion WebUI compatible APIs.
    The server must be running locally before generation is attempted.
    """

    def __init__(self, base_url: str = _DEFAULT_BASE_URL,
                 timeout: int = _DEFAULT_TIMEOUT):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def generate(self, prompt: str, size: str = "1024x1024",
                 style: str = "natural") -> bytes:
        """Generate an image via the local diffusion API.

        Uses the txt2img endpoint (Automatic1111-compatible).
        """
        width, height = self._parse_size(size)

        payload = {
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted",
            "width": width,
            "height": height,
            "steps": 30,
            "cfg_scale": 7.0,
            "sampler_name": "Euler a",
        }

        # Apply style modifiers
        if style == "vivid":
            payload["prompt"] = f"{prompt}, vibrant colors, high contrast"
            payload["cfg_scale"] = 9.0
        elif style == "anime":
            payload["prompt"] = f"{prompt}, anime style, illustration"

        url = f"{self._base_url}/sdapi/v1/txt2img"
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        req = urllib.request.Request(url, data=data, headers=headers,
                                     method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            raise RuntimeError(
                f"Local diffuser API error (HTTP {e.code}): {error_body}"
            )
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Failed to connect to local diffuser at {self._base_url}: {e}. "
                f"Ensure the diffusion server is running."
            )

        # Response contains base64-encoded images
        images = result.get("images", [])
        if not images:
            raise RuntimeError("Local diffuser returned no images.")

        return base64.b64decode(images[0])

    def provider_name(self) -> str:
        return f"local-diffuser ({self._base_url})"

    def is_available(self) -> bool:
        """Check if the local diffuser server is reachable."""
        url = f"{self._base_url}/sdapi/v1/sd-models"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5):
                return True
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            return False

    @staticmethod
    def _parse_size(size: str) -> tuple[int, int]:
        """Parse 'WIDTHxHEIGHT' string into (width, height) tuple."""
        try:
            parts = size.lower().split("x")
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return 1024, 1024
