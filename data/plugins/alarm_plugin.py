import logging
from locale import gettext as _
from os import path
from urllib.parse import urlparse

import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from wiring import Graph
from gi.repository import Gst, Gtk

import tomate.pomodoro.plugin as plugin
from tomate.pomodoro import Bus, Config, Events, on, suppress_errors

logger = logging.getLogger(__name__)

SECTION_NAME = "alarm_plugin"
OPTION_NAME = "file_uri"


class AlarmPlugin(plugin.Plugin):
    has_settings = True

    @suppress_errors
    def __init__(self):
        super().__init__()
        self.config = None
        self.player = self.create_player()

    def configure(self, bus: Bus, graph: Graph) -> None:
        super().configure(bus, graph)
        self.config = graph.get("tomate.config")

    def create_player(self):
        Gst.init(None)
        player = Gst.ElementFactory.make("playbin", "Player")
        player.set_state(Gst.State.NULL)
        player.bus.add_signal_watch()
        player.bus.connect("message", self.on_message)
        return player

    @suppress_errors
    @on(Events.SESSION_END)
    def play(self, *_, **__):
        logger.debug("action=alarm_start uri=%s", self.audio_path)
        self.player.props.uri = self.audio_path
        self.player.set_state(Gst.State.PLAYING)

    @suppress_errors
    def on_message(self, _, message):
        logger.debug("action=onMessage messageType=%s", message.type)
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            logger.debug("action=alarm_eos")

        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            logger.error("action=alarm_failed message='%s-%s'", *message.parse_error())

    @property
    def audio_path(self):
        return self.config.get(
            SECTION_NAME, OPTION_NAME, fallback=self.config.media_uri("alarm.ogg")
        )

    def settings_window(self, toplevel: Gtk.Dialog) -> "SettingsDialog":
        return SettingsDialog(self.config, toplevel)


class SettingsDialog:
    def __init__(self, config: Config, toplevel: Gtk.Dialog):
        self.config = config
        self.widget = self.create_dialog(toplevel)

    def create_dialog(self, toplevel: Gtk.Dialog) -> Gtk.Dialog:
        dialog = Gtk.Dialog(
            border_width=12,
            modal=True,
            resizable=False,
            title=_("Preferences"),
            transient_for=toplevel,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
        )
        dialog.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda widget, _: widget.destroy())
        dialog.set_size_request(350, -1)
        dialog.get_content_area().add(self.create_options())
        return dialog

    def create_options(self):
        custom_audio = self.config.get(SECTION_NAME, OPTION_NAME, fallback="")

        grid = Gtk.Grid(column_spacing=12, row_spacing=12, margin_bottom=12, margin_top=12)
        label = Gtk.Label(label=_("Custom:"), hexpand=True, halign=Gtk.Align.END)
        grid.attach(label, 0, 0, 1, 1)

        entry = self.create_custom_alarm_input(custom_audio)
        grid.attach(entry, 0, 1, 4, 1)

        switch = self.create_custom_alarm_switch(custom_audio, entry)
        grid.attach_next_to(switch, label, Gtk.PositionType.RIGHT, 1, 1)

        return grid

    def create_custom_alarm_input(self, custom_audio):
        entry = Gtk.Entry(
            editable=False,
            hexpand=True,
            name="custom_entry",
            secondary_icon_activatable=True,
            secondary_icon_name=Gtk.STOCK_FILE,
            sensitive=bool(custom_audio),
            text=custom_audio,
        )
        entry.connect("icon-press", self.select_custom_alarm)
        entry.connect("notify::text", self.custom_alarm_changed)
        return entry

    def create_custom_alarm_switch(self, custom_audio, entry):
        switch = Gtk.Switch(
            hexpand=True,
            halign=Gtk.Align.START,
            active=bool(custom_audio),
            name="custom_switch",
        )
        switch.connect("notify::active", self.custom_alarm_toggle, entry)
        return switch

    def select_custom_alarm(self, entry: Gtk.Entry, *_) -> None:
        dialog = self.create_file_chooser(self.dirname(entry.props.text))
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_uri())

        dialog.destroy()

    def dirname(self, audio_path: str):
        return path.dirname(urlparse(audio_path).path) if audio_path else path.expanduser("~")

    def create_file_chooser(self, current_folder: str) -> Gtk.FileChooserDialog:
        dialog = Gtk.FileChooserDialog(
            _("Please choose a file"),
            self.widget,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )
        dialog.add_filter(self.create_filter("audio/mp3", "audio/mpeg"))
        dialog.add_filter(self.create_filter("audio/ogg", "audio/ogg"))
        dialog.set_current_folder(current_folder)
        return dialog

    def create_filter(self, name: str, mime_type: str) -> Gtk.FileFilter:
        mime_type_filter = Gtk.FileFilter()
        mime_type_filter.set_name(name)
        mime_type_filter.add_mime_type(mime_type)
        return mime_type_filter

    def custom_alarm_changed(self, entry: Gtk.Entry, _) -> None:
        custom_alarm = entry.props.text

        if custom_alarm:
            logger.debug("action=set_option section=%s option=%s value", SECTION_NAME, OPTION_NAME)
            self.config.set(SECTION_NAME, OPTION_NAME, custom_alarm)
        else:
            logger.debug("action=remove_option section=%s option=%s", SECTION_NAME, OPTION_NAME)
            self.config.remove(SECTION_NAME, OPTION_NAME)

    def custom_alarm_toggle(self, switch: Gtk.Switch, _, entry: Gtk.Entry) -> None:
        if switch.props.active:
            entry.set_properties(sensitive=True)
        else:
            entry.set_properties(text="", sensitive=False)

    def run(self) -> Gtk.Dialog:
        self.widget.show_all()
        return self.widget
