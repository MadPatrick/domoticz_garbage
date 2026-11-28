"""Minimal stand-in for the Domoticz plugin module, for the unit tests.

Records log lines and notifications, and remembers every device update made
from a thread other than the main thread (OFF_THREAD), so the tests can check
that the fetch thread never touches Devices.
"""
import builtins
import threading

LOG = []
OFF_THREAD = []
NOTIFICATIONS = []
HEARTBEAT = []


def reset():
    LOG.clear()
    OFF_THREAD.clear()
    NOTIFICATIONS.clear()
    HEARTBEAT.clear()
    builtins.Devices = {}
    builtins.Images = {}


def _on_worker():
    return threading.current_thread() is not threading.main_thread()


def Log(msg):
    LOG.append(("Log", msg))


def Error(msg):
    LOG.append(("Error", msg))


def Debug(msg):
    LOG.append(("Debug", msg))


def Debugging(level):
    pass


def Heartbeat(seconds):
    HEARTBEAT.append(seconds)


def SendNotification(**kwargs):
    if _on_worker():
        OFF_THREAD.append(("SendNotification", kwargs))
    NOTIFICATIONS.append(kwargs)


class _Device:
    def __init__(self, Name=None, Unit=None, Image=0, **kwargs):
        self.Name = Name
        self.Unit = Unit
        self.Image = Image
        self.nValue = 0
        self.sValue = ""

    def Create(self):
        builtins.Devices[self.Unit] = self

    def Update(self, nValue, sValue, Image=None, **kwargs):
        if _on_worker():
            OFF_THREAD.append(("Update", self.Unit))
        self.nValue = nValue
        self.sValue = sValue
        if Image is not None:
            self.Image = Image


def Device(**kwargs):
    return _Device(**kwargs)


class _Image:
    def __init__(self, filename):
        self.filename = filename

    def Create(self):
        builtins.Images["GarbageCalendar"] = type("Image", (), {"ID": 7})()


def Image(filename):
    return _Image(filename)
