"""
Dial-based Spotify volume control action for StreamController.

Supports Stream Deck+ dials:
  - Turn CW/CCW  -> volume up/down
  - Press (down)  -> mute / unmute
"""

import os
import threading

from loguru import logger as log

from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase


class DialVolumeAction(ActionBase):
    VOLUME_STEP = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pre_mute_volume: int | None = None
        self._muted = False

    @property
    def spotify(self):
        return self.plugin_base.spotify_client

    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "volume_dial.png")
        if os.path.exists(icon_path):
            self.set_media(media_path=icon_path, size=0.75)

        vol = self.spotify.get_volume()
        if vol is not None:
            self._update_label(vol)

    def on_key_down(self) -> None:
        """Dial press -> toggle mute."""
        threading.Thread(target=self._toggle_mute, daemon=True).start()

    def on_key_up(self) -> None:
        pass

    def event_callback(self, event, data=None):
        """Handle dial-specific events (turn CW/CCW, press)."""
        from src.backend.DeckManagement.InputIdentifier import Input

        if event == Input.Dial.Events.TURN_CW:
            threading.Thread(target=self._adjust_volume, args=(self.VOLUME_STEP,), daemon=True).start()
        elif event == Input.Dial.Events.TURN_CCW:
            threading.Thread(target=self._adjust_volume, args=(-self.VOLUME_STEP,), daemon=True).start()
        elif event == Input.Dial.Events.DOWN:
            threading.Thread(target=self._toggle_mute, daemon=True).start()
        elif event == Input.Dial.Events.SHORT_UP:
            pass
        else:
            super().event_callback(event, data)

    def _adjust_volume(self, delta: int):
        try:
            current = self.spotify.get_volume()
            if current is None:
                current = 50
            new_vol = max(0, min(100, current + delta))
            if self.spotify.set_volume(new_vol):
                self._muted = False
                self._update_label(new_vol)
        except Exception as e:
            log.error(f"Volume adjust error: {e}")

    def _toggle_mute(self):
        try:
            if self._muted and self._pre_mute_volume is not None:
                if self.spotify.set_volume(self._pre_mute_volume):
                    self._muted = False
                    self._update_label(self._pre_mute_volume)
            else:
                current = self.spotify.get_volume()
                if current is None:
                    return
                self._pre_mute_volume = current
                if self.spotify.set_volume(0):
                    self._muted = True
                    self._update_label(0)
        except Exception as e:
            log.error(f"Mute toggle error: {e}")

    def _update_label(self, volume: int):
        try:
            prefix = "🔇" if self._muted else "🔊"
            self.set_bottom_label(f"{prefix} {volume}%", font_size=12)
        except Exception:
            pass
