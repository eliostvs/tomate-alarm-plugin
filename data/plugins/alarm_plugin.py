import logging
import os
from locale import gettext as _
from urllib.parse import urlparse

import gi

gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gst, Gtk

import tomate.plugin
from tomate.constant import State
from tomate.event import Events, on
from tomate.graph import graph
from tomate.utils import suppress_errors

logger = logging.getLogger(__name__)

CONFIG_SECTION_NAME = 'alarm_plugin'
CONFIG_OPTION_NAME = 'file_uri'


class AlarmPlugin(tomate.plugin.Plugin):
    has_settings = True

    @suppress_errors
    def __init__(self):
        super(AlarmPlugin, self).__init__()
        self.config = graph.get('tomate.config')

        Gst.init(None)

        self.player = Gst.ElementFactory.make('playbin', None)
        self.player.set_state(Gst.State.NULL)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

        self.preference_window = PreferenceDialog(self.config)

    @suppress_errors
    @on(Events.Session, [State.finished])
    def ring(self, *args, **kwargs):
        self.player.set_property('uri', self.audio_path)
        logger.debug('action=alarmStart uri=%s', self.audio_path)

        self.player.set_state(Gst.State.PLAYING)

    @suppress_errors
    def on_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)

            logger.debug('action=alarmComplete')

        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)

            logger.error("action=alarmFailed message='%s-%s'", *message.parse_error())

    @property
    def audio_path(self):
        file_uri = self.config.get(CONFIG_SECTION_NAME, CONFIG_OPTION_NAME)
        if file_uri is None:
            file_uri = self.config.get_media_uri('alarm.ogg')

        return file_uri

    def settings_window(self):
        return self.preference_window.run()


class PreferenceDialog:
    def __init__(self, config):
        self.config = config

        self.widget = Gtk.Dialog(
            border_width=11,
            modal=True,
            resizable=False,
            title=_('Preferences'),
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
        )
        self.widget.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.widget.connect('response', lambda widget, response: widget.hide())
        self.widget.set_size_request(350, -1)

        self.option_switch = Gtk.Switch(hexpand=True, halign=Gtk.Align.START)
        self.option_switch.connect('notify::active', self.on_option_activate)

        label = Gtk.Label(label=_('Custom alarm:'), hexpand=True, halign=Gtk.Align.END)

        self.path_entry = Gtk.Entry(editable=False,
                                    sensitive=False,
                                    hexpand=True,
                                    secondary_icon_name=Gtk.STOCK_FILE,
                                    secondary_icon_activatable=True)

        self.path_entry.connect('icon-press', self.on_icon_press)

        grid = Gtk.Grid(column_spacing=12, row_spacing=12, margin_bottom=12)

        grid.attach(label, 0, 0, 1, 1)
        grid.attach_next_to(self.option_switch, label, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach(self.path_entry, 0, 1, 4, 1)

        self.widget.get_content_area().add(grid)

    def run(self):
        self.read_config()
        self.widget.show_all()
        return self.widget

    def read_config(self):
        logger.debug('action=readConfig')

        file_uri = self.config.get(CONFIG_SECTION_NAME, CONFIG_OPTION_NAME)
        if file_uri is not None:
            self.option_switch.set_active(True)
            self.path_entry.set_sensitive(True)
            self.path_entry.set_text(file_uri)
        else:
            self.option_switch.set_active(False)
            self.path_entry.set_sensitive(False)

    def on_option_activate(self, switch, param):
        if switch.get_active():
            self.path_entry.set_sensitive(True)
        else:
            self.reset_option()

    def reset_option(self):
        if self.path_entry.get_text():
            logger.debug('action=resetCustomAlarm needed=true')
            self.path_entry.set_text('')
            self.config.remove(CONFIG_SECTION_NAME, CONFIG_OPTION_NAME)
        else:
            logger.debug('action=resetCustomAlarm needed=false')

        self.path_entry.set_sensitive(False)

    def on_icon_press(self, entry, icon_pos, event):
        dialog = Gtk.FileChooserDialog(_('Please choose a file'),
                                       self.widget,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        dialog.add_filter(self.create_filter('audio/mp3', 'audio/mpeg'))
        dialog.add_filter(self.create_filter('audio/ogg', 'audio/ogg'))

        if entry.get_text():
            current_folder = self.get_current_folder(entry)
        else:
            current_folder = os.path.expanduser('~')

        logger.debug('action=setFileChooserFolder folder=%s', current_folder)
        dialog.set_current_folder(current_folder)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.config_option(entry, dialog.get_uri())

        dialog.destroy()

    @staticmethod
    def get_current_folder(entry):
        return os.path.dirname(urlparse(entry.get_text()).path)

    def config_option(self, entry, uri):
        logger.debug('action=setAlarmFile uri=%s', uri)
        self.config.set(CONFIG_SECTION_NAME, CONFIG_OPTION_NAME, uri)
        entry.set_text(uri)

    @staticmethod
    def create_filter(name, mime_type):
        mime_type_filter = Gtk.FileFilter()
        mime_type_filter.set_name(name)
        mime_type_filter.add_mime_type(mime_type)
        return mime_type_filter
