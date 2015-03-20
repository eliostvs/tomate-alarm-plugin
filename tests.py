from __future__ import unicode_literals

import unittest

from gi.repository import Gst
from mock import Mock, patch
from tomate.graph import graph
from tomate.tests import SubscriptionMixin


class TestAlarmPlugin(SubscriptionMixin, unittest.TestCase):

    def create_instance(self):
        return self.plugin

    @patch('gi.repository.Gst.ElementFactory.make')
    def setUp(self, factory):
        graph.register_instance(
            'tomate.config',
            Mock(**{'get_media_uri.return_value': '/usr/share/tomate/media/alarm.ogg'})
        )

        from alarm_plugin import AlarmPlugin

        self.plugin = AlarmPlugin()
        self.factory = factory

    def test_create_playbin(self):
        self.factory.assert_called_once_with('playbin', None)
        self.plugin.player.set_property.assert_called_once_with('uri', '/usr/share/tomate/media/alarm.ogg')
        self.plugin.player.set_state.assert_called_once_with(Gst.State.NULL)

    def test_ring(self):
        self.plugin.player.reset_mock()
        self.plugin.ring()

        self.plugin.player.set_state.assert_called_once_with(Gst.State.PLAYING)

    def test_player_should_change_state_to_null(self):
        message = Mock()
        message.type = Gst.MessageType.EOS

        self.plugin.player.reset_mock()
        self.plugin.on_message(None, message)

        self.plugin.player.set_state.assert_called_once_with(Gst.State.NULL)

    def test_player_should_change_state_to_null_when_error(self, *args):
        message = Mock()
        message.type = Gst.MessageType.ERROR
        message.parse_error.return_value = ('', '')

        self.plugin.player.reset_mock()

        self.plugin.on_message(None, message)

        self.plugin.player.set_state.called_once_with(Gst.State.NULL)
