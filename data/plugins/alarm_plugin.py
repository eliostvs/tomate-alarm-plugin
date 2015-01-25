from __future__ import unicode_literals

import logging

import gi
from gi.repository import Gst
from tomate.plugin import TomatePlugin
from tomate.profile import ProfileManagerSingleton
from tomate.utils import suppress_errors

gi.require_version('Gst', '1.0')

logger = logging.getLogger(__name__)


class AlarmPlugin(TomatePlugin):

    signals = (
        ('session_ended', 'alarm'),
    )

    @suppress_errors
    def on_init(self):
        Gst.init(None)

        self.profile = ProfileManagerSingleton.get()

        self.player = Gst.ElementFactory.make('playbin', None)
        self.player.set_property('uri', self.profile.get_media_uri('alarm.ogg'))
        self.player.set_state(Gst.State.NULL)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    @suppress_errors
    def alarm(self, sender=None, **kwargs):
        logger.debug('start alarm')

        self.player.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)

            logger.debug('alarm end')

        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)

            logger.error('alarm error %s - %s', *message.parse_error())
