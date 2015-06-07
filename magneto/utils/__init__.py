from __future__ import absolute_import
from contextlib import contextmanager
from multiprocessing import TimeoutError
import signal
import datetime
import os
import subprocess
import time
import urllib
import zipfile
import shutil

import pytest

from .adb import ADB
from ..logger import Logger


def get_center(bounds):
    """
    Returns given element center coords::

        from magneto.utils import get_center

        element = self.magneto(text='Foo')
        (x, y) = get_center(element.info['bounds'])

    :param dict bounds: Element position coordinates (top, right, bottom, left)
    :return: x and y coordinates of element center
    """

    x = bounds['right'] - ((bounds['right'] - bounds['left']) / 2)
    y = bounds['bottom'] - ((bounds['bottom'] - bounds['top']) / 2)
    return x, y


def get_config(attr, default=None):
    """
    Allows access to config parameters::

        from magneto.utils import get_config

        package = get_config('--app-package')

    :param str attr: Command line argument
    :return: Requested config value
    """

    # must have this check to avoid sphinx-autodoc exception
    if getattr(pytest, 'config', None) != None:
        return pytest.config.getoption(attr) or default
    else:
        return default


@contextmanager
def timewarp(timedelta_):
    now = datetime.datetime.now()
    future = now + timedelta_
    ADB.set_datetime(future)

    try:
        yield
    finally:
        now = datetime.datetime.now()
        ADB.set_datetime(now)


class Timeout():
    """
    Allows polling a function till success or timeout::

        import time
        from magneto.utils import Timeout

        result = False

        with Timeout(seconds=5):
            while not result:
                result = some_function()
                time.sleep(0.5)


    :param integer seconds: Timeout value in seconds. Defaults to 1.
    :param str error_message: Error message to display when timeout occurs. Defaults to 'Timeout'.
    """

    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds or 1
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        Logger.debug('Timeout reached {} seconds limit'.format(self.seconds))
        raise TimeoutError(self.error_message)

    def __enter__(self):
        Logger.debug('Timeout started for {} seconds'.format(self.seconds))
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        Logger.debug('Timeout stopped.')
        signal.alarm(0)


def unlock_device():
    """
    Powers on device and unlocks it.
    """

    # read device screen state
    p = ADB.exec_cmd("shell 'if [ -z $(dumpsys power | grep mScreenOn=true) ]; then echo off; else echo on;fi'",
                     stdout=subprocess.PIPE)
    device_screen = p.stdout.readline().strip('\r\n')

    if device_screen == 'off':
        # power on device
        ADB.exec_cmd('shell input keyevent 26').wait()

    # unlock device
    ADB.exec_cmd('shell input keyevent 82').wait()


def wait_for_device():
    """
    Wait for device to boot. 1 minute timeout.
    """

    wait_for_device_cmd = 'wait-for-device shell getprop sys.boot_completed'
    p = ADB.exec_cmd(wait_for_device_cmd, stdout=subprocess.PIPE)
    boot_completed = p.stdout.readline().strip('\r\n')

    try:
        with Timeout(seconds=60):
            while boot_completed != '1':
                time.sleep(1)
                p = ADB.exec_cmd(wait_for_device_cmd, stdout=subprocess.PIPE)
                boot_completed = p.stdout.readline().strip('\r\n')
                Logger.debug('Waiting for device to finish booting (adb shell getprop sys.boot_completed)')
    except TimeoutError:
        Logger.debug('Timed out while waiting for sys.boot_completed, there might not be a default launcher set, trying to run anyway')
        pass


class Bootstrap(object):
    _map = {
        'calc': 'https://github.com/EverythingMe/magneto-demo-calc/archive/master.zip'
    }

    def __init__(self, name):
        if name not in self._map:
            raise Exception('{} not recognized'.format(name))

        filename, headers = urllib.urlretrieve(self._map[name])

        with zipfile.ZipFile(filename) as zip_file:
            rootdir = zip_file.namelist()[0]
            for member in zip_file.namelist()[1:]:
                if not os.path.basename(member):
                    # create dir from zipfile
                    os.mkdir(os.path.join(os.path.curdir, member.replace(rootdir, '')))
                else:
                    # copy file (taken from zipfile's extract)
                    source = zip_file.open(member)
                    target = file(os.path.join(os.path.curdir, member.replace(rootdir, '')), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
