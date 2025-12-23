"""Authentication helper for NotebookLM Consumer.

Uses Chrome DevTools MCP to extract auth tokens from an authenticated browser session.
If the user is not logged in, prompts them to log in via the Chrome window.
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AuthTokens:
    """Authentication tokens for NotebookLM."""
    cookies: dict[str, str]
    csrf_token: str
    session_id: str
    extracted_at: float

    def to_dict(self) -> dict:
        return {
            "cookies": self.cookies,
            "csrf_token": self.csrf_token,
            "session_id": self.session_id,
            "extracted_at": self.extracted_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuthTokens":
        return cls(
            cookies=data["cookies"],
            csrf_token=data["csrf_token"],
            session_id=data["session_id"],
            extracted_at=data.get("extracted_at", 0),
        )

    def is_expired(self, max_age_hours: float = 24) -> bool:
        """Check if tokens are older than max_age_hours."""
        age_seconds = time.time() - self.extracted_at
        return age_seconds > (max_age_hours * 3600)

    @property
    def cookie_header(self) -> str:
        """Get cookies as a header string."""
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())


def get_cache_path() -> Path:
    """Get the path to the auth cache file."""
    cache_dir = Path.home() / ".notebooklm-consumer"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "auth.json"


def load_cached_tokens() -> AuthTokens | None:
    """Load tokens from cache if they exist and are not expired."""
    cache_path = get_cache_path()
    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)
        tokens = AuthTokens.from_dict(data)

        # Check if expired
        if tokens.is_expired():
            print("Cached auth tokens expired, need to refresh...")
            return None

        return tokens
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Failed to load cached tokens: {e}")
        return None


def save_tokens_to_cache(tokens: AuthTokens) -> None:
    """Save tokens to cache."""
    cache_path = get_cache_path()
    with open(cache_path, "w") as f:
        json.dump(tokens.to_dict(), f, indent=2)
    print(f"Auth tokens cached to {cache_path}")


def extract_tokens_via_chrome_devtools() -> AuthTokens | None:
    """
    Extract auth tokens using Chrome DevTools.

    This function assumes Chrome DevTools MCP is available and connected
    to a Chrome browser. It will:
    1. Navigate to notebooklm.google.com
    2. Check if logged in
    3. If not, wait for user to log in
    4. Extract cookies and CSRF token

    Returns:
        AuthTokens if successful, None otherwise
    """
    # This is a placeholder - the actual implementation would use
    # Chrome DevTools MCP tools. Since we're inside an MCP server,
    # we can't directly call another MCP's tools.
    #
    # Instead, we'll provide a CLI command that can be run separately
    # to extract and cache the tokens.

    raise NotImplementedError(
        "Direct Chrome DevTools extraction not implemented. "
        "Use the 'notebooklm-consumer-auth' CLI command instead."
    )


def extract_csrf_from_page_source(html: str) -> str | None:
    """Extract CSRF token from page HTML.

    The token is stored in WIZ_global_data.SNlM0e or similar structures.
    """
    import re

    # Try different patterns for CSRF token
    patterns = [
        r'"SNlM0e":"([^"]+)"',  # WIZ_global_data.SNlM0e
        r'at=([^&"]+)',  # Direct at= value
        r'"FdrFJe":"([^"]+)"',  # Alternative location
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    return None


def extract_session_id_from_page(html: str) -> str | None:
    """Extract session ID from page HTML."""
    import re

    patterns = [
        r'"FdrFJe":"([^"]+)"',
        r'f\.sid=(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    return None


# ============================================================================
# CLI Authentication Flow
# ============================================================================
#
# This is designed to be run as a separate command before starting the MCP.
# It uses Chrome DevTools MCP interactively to extract auth tokens.
#
# Usage:
#   1. Make sure Chrome is open with DevTools MCP connected
#   2. Run: notebooklm-consumer-auth
#   3. If not logged in, log in via the Chrome window
#   4. Tokens are cached to ~/.notebooklm-consumer/auth.json
#   5. Start the MCP server - it will use cached tokens
#
# The auth flow script is separate because:
# - MCP servers can't easily call other MCP tools
# - Interactive login needs user attention
# - Caching allows the MCP to start without browser interaction


def parse_cookies_from_chrome_format(cookies_list: list[dict]) -> dict[str, str]:
    """Parse cookies from Chrome DevTools format to simple dict."""
    result = {}
    for cookie in cookies_list:
        name = cookie.get("name", "")
        value = cookie.get("value", "")
        if name:
            result[name] = value
    return result


# Tokens that need to be present for auth to work
REQUIRED_COOKIES = ["SID", "HSID", "SSID", "APISID", "SAPISID"]


def validate_cookies(cookies: dict[str, str]) -> bool:
    """Check if required cookies are present."""
    for required in REQUIRED_COOKIES:
        if required not in cookies:
            return False
    return True
