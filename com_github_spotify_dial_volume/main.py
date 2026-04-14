"""
Spotify Dial Volume - StreamController Plugin

Adds a dial action to control Spotify volume on Stream Deck+ devices.
Turn the dial to adjust volume, press to mute/unmute.

Requires a Spotify Premium account and a registered Spotify Developer App.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

from .actions.DialVolumeAction.DialVolumeAction import DialVolumeAction
from .utils.spotify_client import SpotifyVolumeClient


class SpotifyDialVolume(PluginBase):
    def __init__(self):
        super().__init__()

        self.spotify_client = SpotifyVolumeClient(self)

        dial_holder = ActionHolder(
            plugin_base=self,
            action_base=DialVolumeAction,
            action_id="com_github_spotify_dial_volume::DialVolume",
            action_name="Spotify Dial Volume",
        )
        self.add_action_holder(dial_holder)

        self.register(
            plugin_name="Spotify Dial Volume",
            github_repo="https://github.com/StreamController/PluginTemplate",
            plugin_version="1.0.0",
            app_version="1.5.0-beta",
        )

    def get_settings_area(self):
        group = Adw.PreferencesGroup()
        for row in self.get_config_rows():
            group.add(row)
        return group

    def get_config_rows(self) -> list:
        rows = []
        settings = self.get_settings()

        client_id_row = Adw.EntryRow(title="Spotify Client ID")
        cid = settings.get("client_id")
        if cid:
            client_id_row.set_text(cid)
        client_id_row.set_show_apply_button(True)
        client_id_row.connect("apply", self._on_setting_changed, "client_id")
        rows.append(client_id_row)

        client_secret_row = Adw.PasswordEntryRow(title="Spotify Client Secret")
        secret = settings.get("client_secret")
        if secret:
            client_secret_row.set_text(secret)
        client_secret_row.set_show_apply_button(True)
        client_secret_row.connect("apply", self._on_setting_changed, "client_secret")
        rows.append(client_secret_row)

        login_row = Adw.ButtonRow(title="Login with Spotify")
        login_row.connect("activated", self._on_login)
        rows.append(login_row)

        refresh_row = Adw.PasswordEntryRow(title="Refresh Token")
        rt = settings.get("client_refresh_token")
        if rt:
            refresh_row.set_text(rt)
        refresh_row.set_show_apply_button(True)
        refresh_row.connect("apply", self._on_setting_changed, "client_refresh_token")
        rows.append(refresh_row)

        return rows

    def _on_setting_changed(self, entry_row, key: str):
        settings = self.get_settings()
        settings[key] = entry_row.get_text()
        self.set_settings(settings)

    def _on_login(self, _):
        self.spotify_client.initiate_login_flow()
