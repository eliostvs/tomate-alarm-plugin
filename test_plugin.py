import gi
import pytest

from unittest.mock import patch, Mock

gi.require_version("Gst", "1.0")

from gi.repository import Gst

from tomate.core.graph import graph


def setup_module():
    graph.register_instance(
        "tomate.config",
        Mock(**{"get_media_uri.return_value": "/usr/share/tomate/media/alarm.ogg"}),
    )


@pytest.fixture(autouse=True)
def config(mocker):
    mock = mocker.Mock()
    graph.register_instance("tomate.config", mock)
    return mock


@pytest.fixture
@patch("alarm_plugin.Gst.ElementFactory.make")
def plugin(factory_make):
    from alarm_plugin import AlarmPlugin

    return AlarmPlugin()


@pytest.fixture()
def message(mocker):
    mock = mocker.Mock()
    mock.type = Gst.MessageType.EOS

    return mock


@patch("alarm_plugin.Gst.ElementFactory.make")
def test_create_playbin(make):
    from alarm_plugin import AlarmPlugin

    plugin = AlarmPlugin()

    make.assert_called_once_with("playbin", None)

    plugin.player.set_state.assert_called_once_with(Gst.State.NULL)


file_path = "/usr/share/tomate/media/alarm.ogg"


def test_ring_with_default_alarm_file(plugin, config):
    from alarm_plugin import CONFIG_SECTION_NAME, CONFIG_OPTION_NAME

    def side_effect(section, option):
        if section == CONFIG_SECTION_NAME and option == CONFIG_OPTION_NAME:
            return None

        return "Error"

    config.get.side_effect = side_effect
    config.get_media_uri.side_effect = (
        lambda file: file_path if file == "alarm.ogg" else None
    )

    plugin.player.reset_mock()

    plugin.ring()

    plugin.player.set_property.assert_called_once_with("uri", file_path)
    plugin.player.set_state.assert_called_once_with(Gst.State.PLAYING)


def test_ring_with_custom_alarm_file(plugin, config):
    from alarm_plugin import CONFIG_SECTION_NAME, CONFIG_OPTION_NAME

    def side_effect(section, option):
        if section == CONFIG_SECTION_NAME and option == CONFIG_OPTION_NAME:
            return file_path

    config.get.side_effect = side_effect

    plugin.player.reset_mock()

    plugin.ring()

    plugin.player.set_property.assert_called_once_with("uri", file_path)
    plugin.player.set_state.assert_called_once_with(Gst.State.PLAYING)


def test_player_should_change_state_to_null(plugin, message):
    plugin.player.reset_mock()
    plugin.on_message(None, message)

    plugin.player.set_state.assert_called_once_with(Gst.State.NULL)


def test_player_should_change_state_to_null_when_error(plugin, message):
    message.type = Gst.MessageType.ERROR
    message.parse_error.return_value = ("", "")

    plugin.player.reset_mock()

    plugin.on_message(None, message)

    plugin.player.set_state.called_once_with(Gst.State.NULL)


def test_plugin_has_settings(plugin):
    assert plugin.has_settings is True
