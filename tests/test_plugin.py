import time
from datetime import datetime as dt, timedelta
from os.path import dirname, join
from typing import Callable

import pytest
from blinker import signal
from gi.repository import Gst, Gtk
from tomate.pomodoro import State
from tomate.pomodoro.config import Config
from tomate.pomodoro.event import Events
from tomate.pomodoro.graph import graph
from tomate.ui.test import run_loop_for, Q

CUSTOM_ALARM = f'file://{join(dirname(__file__), "data", "tomate", "media", "custom.ogg")}'
SECTION_NAME = "alarm_plugin"
OPTION_NAME = "file_uri"


def wait_until(fn: Callable[[], bool], timeout: int = 1, period: int = 0.25):
    limit = dt.utcnow() + timedelta(seconds=timeout)

    while dt.utcnow() < limit:
        if fn():
            return True
        time.sleep(period)
    return False


@pytest.fixture()
def config(tmpdir):
    instance = Config(signal("dispatcher"))
    tmp_path = tmpdir.mkdir("tomate").join("tomate.config")
    instance.config_path = lambda: tmp_path.strpath

    graph.providers.clear()
    graph.register_instance("tomate.config", instance)
    return instance


@pytest.fixture
def subject(config):
    Events.Session.receivers.clear()

    from alarm_plugin import AlarmPlugin
    return AlarmPlugin()


def test_plays_alarm_when_session_finish(subject, config):
    subject.activate()

    Events.Session.send(State.finished)
    assert subject.player.props.current_uri == config.media_uri("alarm.ogg")

    run_loop_for(1)
    assert wait_until(lambda: subject.player.current_state == Gst.State.NULL, timeout=1)
    assert subject.player.props.current_uri is None


def test_plays_custom_alarm(subject, config):
    config.set(SECTION_NAME, OPTION_NAME, CUSTOM_ALARM)
    subject.activate()

    Events.Session.send(State.finished)
    assert subject.player.props.current_uri == CUSTOM_ALARM

    run_loop_for(1)
    assert wait_until(lambda: subject.player.current_state == Gst.State.NULL, timeout=1)
    assert subject.player.props.current_uri is None


class TestSettingsWindow:
    def test_without_custom_alarm(self, subject, config):
        config.remove(SECTION_NAME, OPTION_NAME)
        window = subject.settings_window(Gtk.Window())
        window.run()

        entry = Q.select(window.widget, Q.name("alarm_entry"))
        assert entry.get_text() == ""
        assert entry.get_sensitive() is False

        switch = Q.select(window.widget, Q.name("alarm_switch"))
        assert switch.get_active() is False

    def test_with_custom_alarm(self, subject, config):
        config.set(SECTION_NAME, OPTION_NAME, CUSTOM_ALARM)

        window = subject.settings_window(Gtk.Window())
        window.run()

        entry = Q.select(window.widget, Q.name("alarm_entry"))
        assert entry.get_text() == CUSTOM_ALARM
        assert entry.get_sensitive() is True

        switch = Q.select(window.widget, Q.name("alarm_switch"))
        assert switch.get_active() is True

    def test_enable_custom_alarm(self, subject, config):
        window = subject.settings_window(Gtk.Window())
        window.run()

        switch = Q.select(window.widget, Q.name("alarm_switch"))
        switch.set_active(True)
        switch.notify("activate")

        entry = Q.select(window.widget, Q.name("alarm_entry"))
        assert entry.get_sensitive() is True
        entry.set_text(CUSTOM_ALARM)

        window.widget.emit("response", 0)
        assert config.get(SECTION_NAME, OPTION_NAME) == CUSTOM_ALARM

    def test_disable_custom_alarm(self, subject, config):
        config.set(SECTION_NAME, OPTION_NAME, CUSTOM_ALARM)

        window = subject.settings_window(Gtk.Window())
        window.run()

        switch = Q.select(window.widget, Q.name("alarm_switch"))
        switch.set_active(False)
        switch.notify("activate")

        entry = Q.select(window.widget, Q.name("alarm_entry"))
        assert entry.get_text() == ""
        assert entry.get_sensitive() is False

        window.widget.emit("response", 0)
        assert config.has_option(SECTION_NAME, OPTION_NAME) is False
