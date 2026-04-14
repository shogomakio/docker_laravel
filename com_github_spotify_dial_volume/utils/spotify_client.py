"""
Minimal Spotify Web API client for volume control.
Uses OAuth2 Authorization Code flow with PKCE or client credentials.
Requires Spotify Premium.
"""

import base64
import datetime
import threading
import time
from typing import Optional, Dict, Any
from urllib import parse

import requests
from loguru import logger as log

SPOTIFY_ACCOUNTS_URL = "https://accounts.spotify.com"
SPOTIFY_API_URL = "https://api.spotify.com/v1"
REDIRECT_URI = "https://stream-controller/callback"
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

TOKEN_ENDPOINT = f"{SPOTIFY_ACCOUNTS_URL}/api/token"
AUTHORIZE_ENDPOINT = f"{SPOTIFY_ACCOUNTS_URL}/authorize"
PLAYER_ENDPOINT = f"{SPOTIFY_API_URL}/me/player"
VOLUME_ENDPOINT = f"{PLAYER_ENDPOINT}/volume"


class Token:
    def __init__(self, token_string: str, expires_in: int):
        self.token_string = token_string
        buffer_seconds = 60
        self.expires_at = datetime.datetime.now() + datetime.timedelta(
            seconds=max(0, expires_in - buffer_seconds)
        )

    @property
    def is_valid(self) -> bool:
        return datetime.datetime.now() < self.expires_at

    @property
    def value(self) -> str:
        return self.token_string


class SpotifyVolumeClient:
    """Handles Spotify OAuth and volume control API calls."""

    def __init__(self, plugin_base):
        self.plugin_base = plugin_base
        self._access_token: Optional[Token] = None
        self._cached_volume: Optional[int] = None
        self._lock = threading.Lock()

    @property
    def settings(self) -> dict:
        return self.plugin_base.get_settings()

    def _save_settings(self, settings: dict):
        self.plugin_base.set_settings(settings)

    def _encode_basic_auth(self, client_id: str, client_secret: str) -> str:
        credentials = f"{client_id}:{client_secret}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    def _request_token(self, data: dict) -> Optional[dict]:
        settings = self.settings
        client_id = settings.get("client_id", "")
        client_secret = settings.get("client_secret", "")
        if not client_id or not client_secret:
            log.error("Spotify client_id or client_secret not configured")
            return None

        b64_creds = self._encode_basic_auth(client_id, client_secret)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {b64_creds}",
        }
        try:
            resp = requests.post(TOKEN_ENDPOINT, headers=headers, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            log.error(f"Token request failed: {e}")
            return None

    def exchange_code_for_token(self, code: str) -> bool:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        result = self._request_token(data)
        if not result:
            return False
        return self._store_token(result, clear_code=True)

    def refresh_access_token(self) -> bool:
        settings = self.settings
        refresh_token = settings.get("client_refresh_token")
        client_id = settings.get("client_id", "")
        if not refresh_token:
            log.warning("No refresh token available")
            return False

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }
        result = self._request_token(data)
        if not result:
            return False
        return self._store_token(result)

    def _store_token(self, token_data: dict, clear_code: bool = False) -> bool:
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")
        if not access_token or not isinstance(expires_in, int):
            return False

        self._access_token = Token(access_token, expires_in)

        settings = self.settings
        new_refresh = token_data.get("refresh_token")
        if new_refresh:
            settings["client_refresh_token"] = new_refresh
        if clear_code and "client_authorization" in settings:
            del settings["client_authorization"]
        self._save_settings(settings)
        return True

    def get_valid_token(self) -> Optional[str]:
        if self._access_token and self._access_token.is_valid:
            return self._access_token.value

        if self.refresh_access_token():
            if self._access_token and self._access_token.is_valid:
                return self._access_token.value
        return None

    def _api_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        token = self.get_valid_token()
        if not token:
            log.warning(f"No valid token for {url}")
            return None

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        try:
            resp = requests.request(method, url, headers=headers, timeout=10, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            log.error(f"Spotify API error ({method} {url}): {e}")
            return None

    def get_volume(self) -> Optional[int]:
        resp = self._api_request("GET", PLAYER_ENDPOINT)
        if resp and resp.status_code == 200:
            data = resp.json()
            device = data.get("device", {})
            vol = device.get("volume_percent")
            if vol is not None:
                self._cached_volume = vol
            return vol
        return self._cached_volume

    def set_volume(self, volume_percent: int) -> bool:
        volume_percent = max(0, min(100, volume_percent))
        resp = self._api_request(
            "PUT", VOLUME_ENDPOINT, params={"volume_percent": volume_percent}
        )
        if resp is not None:
            self._cached_volume = volume_percent
            return True
        return False

    def get_playback_state(self) -> Optional[Dict[str, Any]]:
        resp = self._api_request("GET", PLAYER_ENDPOINT)
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def toggle_playback(self) -> bool:
        state = self.get_playback_state()
        if state and state.get("is_playing"):
            resp = self._api_request("PUT", f"{PLAYER_ENDPOINT}/pause")
        else:
            resp = self._api_request("PUT", f"{PLAYER_ENDPOINT}/play")
        return resp is not None

    def initiate_login_flow(self):
        settings = self.settings
        client_id = settings.get("client_id", "")
        if not client_id:
            log.error("Client ID not configured")
            return

        try:
            import globals as gl
            from .web_auth_window import WebAuthWindow

            params = {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": SCOPES,
            }
            encoded = parse.urlencode(params)
            url = f"{AUTHORIZE_ENDPOINT}?{encoded}"

            def handle_code(code):
                settings = self.settings
                settings["client_authorization"] = code
                self._save_settings(settings)
                self.exchange_code_for_token(code)

            window = WebAuthWindow(
                application=gl.app,
                initial_url=url,
                modal=True,
                callback=handle_code,
            )
            window.present()
        except ImportError:
            log.error("WebAuthWindow or globals not available. Configure tokens manually.")
