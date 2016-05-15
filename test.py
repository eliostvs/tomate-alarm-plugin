from __future__ import unicode_literals

import pytest
from gi.repository import Gst
from mock import Mock, patch
from tomate.graph import graph


def setup_module():
    graph.register_instance(
        'tomate.config',
        Mock(**{'get_media_uri.return_value': '/usr/share/tomate/media/alarm.ogg'})
    )


@pytest.fixture()
@patch('alarm_plugin.Gst.ElementFactory.make')
def plugin(factory):
    from alarm_plugin import AlarmPlugin

    return AlarmPlugin()


@pytest.fixture()
def message():
    mock = Mock()
    mock.type = Gst.MessageType.EOS

    return mock


@patch('alarm_plugin.Gst.ElementFactory.make')
def test_create_playbin(make):
    from alarm_plugin import AlarmPlugin

    plugin = AlarmPlugin()

    make.assert_called_once_with('playbin', None)

    plugin.player.set_property.assert_called_once_with('uri', '/usr/share/tomate/media/alarm.ogg')
    plugin.player.set_state.assert_called_once_with(Gst.State.NULL)


def test_ring(plugin):
    plugin.player.reset_mock()

    plugin.ring()

    plugin.player.set_state.assert_called_once_with(Gst.State.PLAYING)


def test_player_should_change_state_to_null(plugin, message):
    plugin.player.reset_mock()
    plugin.on_message(None, message)

    plugin.player.set_state.assert_called_once_with(Gst.State.NULL)


def test_player_should_change_state_to_null_when_error(plugin, message):
    message.type = Gst.MessageType.ERROR
    message.parse_error.return_value = ('', '')

    plugin.player.reset_mock()

    plugin.on_message(None, message)

    plugin.player.set_state.called_once_with(Gst.State.NULL)
