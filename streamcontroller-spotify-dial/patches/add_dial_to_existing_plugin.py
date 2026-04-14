"""
Patch: Add dial volume support to an existing SpotifyForStreamController plugin.

This file can be dropped into the existing plugin's actions/MediaActions/ folder
and registered in main.py.

Usage:
  1. Copy this file to:
     ~/.var/app/com.core447.StreamController/data/StreamController/plugins/SpotifyForStreamController/actions/MediaActions/DialVolumeAction.py

  2. Add to main.py after the other ActionHolder registrations:

     from .actions.MediaActions.DialVolumeAction import DialVolume

     holder = ActionHolder(
         plugin_base=self,
         action_base=DialVolume,
         action_id="de_outsider_Spotify::DialVolume",
         action_name="Dial Volume Control",
     )
     self.add_action_holder(holder)
"""

import os
import threading

from loguru import logger as log

from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase


class DialVolume(ActionBase):
    """
    Assign this action to a Stream Deck+ dial slot.
    - Turn CW: volume up (+5%)
    - Turn CCW: volume down (-5%)
    - Press: mute / unmute
    """

    VOLUME_STEP = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pre_mute_volume = None
        self._muted = False

    @property
    def get_controller(self):
        return self.plugin_base.get_controller

    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "volume_up.png")
        if os.path.exists(icon_path):
            self.set_media(media_path=icon_path, size=0.75)
        vol = self.get_controller.get_volume()
        if vol is not None:
            self._update_label(vol)

    def on_key_down(self) -> None:
        threading.Thread(target=self._toggle_mute, daemon=True).start()

    def on_key_up(self) -> None:
        pass

    def event_callback(self, event, data=None):
        from src.backend.DeckManagement.InputIdentifier import Input

        if event == Input.Dial.Events.TURN_CW:
            threading.Thread(target=self._adjust, args=(self.VOLUME_STEP,), daemon=True).start()
        elif event == Input.Dial.Events.TURN_CCW:
            threading.Thread(target=self._adjust, args=(-self.VOLUME_STEP,), daemon=True).start()
        elif event == Input.Dial.Events.DOWN:
            threading.Thread(target=self._toggle_mute, daemon=True).start()
        else:
            super().event_callback(event, data)

    def _adjust(self, delta: int):
        try:
            current = self.get_controller.get_volume() or 50
            new_vol = max(0, min(100, current + delta))
            self.get_controller.set_volume(new_vol)
            self._muted = False
            self._update_label(new_vol)
        except Exception as e:
            log.error(f"Dial volume adjust error: {e}")

    def _toggle_mute(self):
        try:
            if self._muted and self._pre_mute_volume is not None:
                self.get_controller.set_volume(self._pre_mute_volume)
                self._muted = False
                self._update_label(self._pre_mute_volume)
            else:
                current = self.get_controller.get_volume()
                if current is None:
                    return
                self._pre_mute_volume = current
                self.get_controller.set_volume(0)
                self._muted = True
                self._update_label(0)
        except Exception as e:
            log.error(f"Mute toggle error: {e}")

    def _update_label(self, volume: int):
        try:
            self.set_bottom_label(f"{'MUTE' if self._muted else 'VOL'} {volume}%", font_size=12)
        except Exception:
            pass
