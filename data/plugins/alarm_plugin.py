from __future__ import unicode_literals

import logging
import os
from locale import gettext as _

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

        self.preference_dialog = PreferenceDialog(self.config)

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
        return self.preference_dialog.run()


class PreferenceDialog:
    def __init__(self, config):
        self.config = config

        self.widget = Gtk.Dialog(
            _('Preferences'),
            None,
            modal=True,
            resizable=False,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
            buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        )
        self.widget.connect('response', lambda widget, response: widget.hide())
        self.widget.set_size_request(350, 200)

        option_name = Gtk.Label('<b>{0}</b>'.format(_('Alarm file')), use_markup=True)
        option_name.set_halign(Gtk.Align.START)

        self.default_option = Gtk.RadioButton.new_with_label(None, _('Default'))
        self.default_option.connect('toggled', self.on_option_changed)

        self.custom_option = Gtk.RadioButton.new_with_label_from_widget(self.default_option, _('Custom'))

        self.file_entry = Gtk.Entry(editable=False,
                                    sensitive=False,
                                    secondary_icon_name=Gtk.STOCK_FILE,
                                    secondary_icon_activatable=True)

        self.file_entry.connect('icon-press', self.on_icon_press)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                       spacing=5,
                       margin_bottom=5,
                       margin_left=5,
                       margin_right=5)
        vbox.pack_start(option_name, False, True, 0)
        vbox.pack_start(self.default_option, False, True, 0)
        vbox.pack_start(self.custom_option, False, True, 0)
        vbox.pack_start(self.file_entry, True, True, 0)

        self.widget.get_content_area().add(vbox)

    def run(self):
        self.read_config()
        self.widget.show_all()
        return self.widget

    def read_config(self):
        logger.debug('action=readConfig')

        file_uri = self.config.get(CONFIG_SECTION_NAME, CONFIG_OPTION_NAME)
        if file_uri is not None:
            self.custom_option.set_active(True)
            self.file_entry.set_sensitive(True)
            self.file_entry.set_text(file_uri)
        else:
            self.default_option.set_active(True)
            self.file_entry.set_sensitive(False)

    def on_option_changed(self, button):
        if self.default_option.get_active():
            self.reset_option()
        else:
            self.file_entry.set_sensitive(True)

    def reset_option(self):
        if self.file_entry.get_text():
            logger.debug('action=alarmOptionReset needed=true')
            self.file_entry.set_text('')
            self.config.remove(CONFIG_SECTION_NAME, CONFIG_OPTION_NAME)
        else:
            logger.debug('action=alarmOptionReset needed=false')

        self.file_entry.set_sensitive(False)

    def on_icon_press(self, entry, icon_pos, event):
        dialog = Gtk.FileChooserDialog(_("Please choose a file"),
                                       self.widget,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        dialog.add_filter(self.create_filter('audio/ogg', 'audio/ogg'))
        dialog.add_filter(self.create_filter('audio/mp3', 'audio/mpeg'))

        if entry.get_text():
            current_folder = os.path.dirname(entry.get_text())
        else:
            current_folder = os.path.expanduser('~')

        logger.debug('action=setFileChooserFolder folder=%s', current_folder)
        dialog.set_current_folder(current_folder)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.config_option(entry, dialog.get_uri())

        dialog.destroy()

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
