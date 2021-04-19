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
        file_uri = self.config.get(SECTION_NAME, OPTION_NAME)
        if file_uri is None:
            file_uri = self.config.media_uri("alarm.ogg")
        return file_uri

    def settings_window(self, toplevel):
        return SettingsDialog(self.config, toplevel)


class SettingsDialog:
    def __init__(self, config: Config, toplevel):
        self.config = config
        self.create_widget(toplevel)

    def create_widget(self, toplevel):
        grid = Gtk.Grid(column_spacing=12, row_spacing=12, margin_bottom=12)
        label = Gtk.Label(label=_("Custom alarm:"), hexpand=True, halign=Gtk.Align.END)
        grid.attach(label, 0, 0, 1, 1)
        self.switch = Gtk.Switch(hexpand=True, halign=Gtk.Align.START, name="alarm_switch")
        self.switch.connect("notify::active", self.on_switch_toggle)
        grid.attach_next_to(self.switch, label, Gtk.PositionType.RIGHT, 1, 1)
        self.file_path = Gtk.Entry(
            editable=False,
            hexpand=True,
            secondary_icon_activatable=True,
            secondary_icon_name=Gtk.STOCK_FILE,
            sensitive=False,
            name="alarm_entry",
        )
        self.file_path.connect("icon-press", self.on_icon_press)
        grid.attach(self.file_path, 0, 1, 4, 1)
        self.widget = Gtk.Dialog(
            border_width=12,
            modal=True,
            resizable=False,
            title=_("Preferences"),
            transient_for=toplevel,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
        )
        self.widget.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.widget.connect("response", self.on_close)
        self.widget.set_size_request(350, -1)
        self.widget.get_content_area().add(grid)

    def on_close(self, widget, _):
        if self.file_path.get_text():
            self.config.set(SECTION_NAME, OPTION_NAME, self.file_path.get_text())
        else:
            self.config.remove(SECTION_NAME, OPTION_NAME)

        widget.destroy()

    def run(self):
        self.read_config()
        self.widget.show_all()
        return self.widget

    def read_config(self):
        logger.debug("action=readConfig")

        file_uri = self.config.get(SECTION_NAME, OPTION_NAME)
        if file_uri is not None:
            self.switch.set_active(True)
            self.file_path.set_sensitive(True)
            self.file_path.set_text(file_uri)
        else:
            self.switch.set_active(False)
            self.file_path.set_sensitive(False)

    def on_switch_toggle(self, switch, _):
        if switch.get_active():
            self.file_path.set_sensitive(True)
        else:
            self.file_path.set_text("")
            self.file_path.set_sensitive(False)

    def on_icon_press(self, entry, *_):
        dialog = self.create_file_chooser(self.current_folder(entry))
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.file_path.set_text(dialog.get_uri())

        dialog.destroy()

    def current_folder(self, entry):
        return (
            path.dirname(urlparse(entry.get_text()).path)
            if entry.get_text()
            else path.expanduser("~")
        )

    def create_file_chooser(self, current_folder):
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

    def create_filter(self, name, mime_type):
        mime_type_filter = Gtk.FileFilter()
        mime_type_filter.set_name(name)
        mime_type_filter.add_mime_type(mime_type)
        return mime_type_filter
