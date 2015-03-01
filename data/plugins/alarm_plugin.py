from __future__ import unicode_literals

import logging

import gi
from gi.repository import Gst

from tomate.graph import graph
from tomate.plugin import Plugin
from tomate.utils import suppress_errors

gi.require_version('Gst', '1.0')

logger = logging.getLogger(__name__)


class AlarmPlugin(Plugin):

    subscriptions = (
        ('session_ended', 'ring'),
    )

    @suppress_errors
    def __init__(self):
        super(AlarmPlugin, self).__init__()
        Gst.init(None)

        self.config = graph.get('tomate.config')

        self.player = Gst.ElementFactory.make('playbin', None)
        self.player.set_property('uri', self.audiopath)
        self.player.set_state(Gst.State.NULL)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    @suppress_errors
    def ring(self, *args, **kwargs):
        self.player.set_state(Gst.State.PLAYING)

        logger.debug('play ')

    @suppress_errors
    def on_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)

            logger.debug('alarm end')

        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)

            logger.error('alarm error %s - %s', *message.parse_error())

    @property
    def audiopath(self):
        return self.config.get_media_uri('alarm.ogg')
