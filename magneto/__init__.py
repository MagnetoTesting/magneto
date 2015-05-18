import threading
import time
import itertools
import os

from uiautomator import AutomatorDevice, AutomatorDeviceObject, AutomatorServer, Selector

from .utils import get_center, Timeout, TimeoutError, get_config
from .utils.adb import ADB


class Magneto(threading.local, AutomatorDevice):
    """
    Inherits from ``uiautomator.device``, which has `docs available <https://github.com/xiaocong/uiautomator/blob/master/README.md>`_.
    """
    _instance = None
    _args = ()
    _kwargs = {}
    _device_id = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls(cls._device_id, *cls._args, **cls._kwargs)
        return cls._instance

    @classmethod
    def configure(cls, device_id=None, *args, **kwargs):
        cls._device_id = device_id

        ADB.device_id = cls._device_id
        cls._manufacturer = ADB.getprop('ro.product.manufacturer').lower()
        cls._args = args
        cls._kwargs = kwargs

    def __init__(self, serial=None, local_port=None, adb_server_host=None, adb_server_port=None):
        self.server = MagnetoAutomatorServer(
            serial=serial,
            local_port=local_port,
            adb_server_host=adb_server_host,
            adb_server_port=adb_server_port
        )

    def __call__(self, *args, **kwargs):
        el = MagnetoDeviceObject(self, Selector(**kwargs))
        if not el.exists:
            self.server.stop()
            self.server.start()
            el = MagnetoDeviceObject(self, Selector(**kwargs))
        return el

    @property
    def info(self):
        info = dict(super(Magneto, self).info, manufacturer=self._manufacturer)
        return info

    def drag(self, *args, **kwargs):
        """
        Allows dragging elements on screen by element or coords.

        :param args:
        :param kwargs:

        **Usage**:

        Drag element to element::

            source_el = self.magneto(resourceId=ids.foo)
            target_el = self.magneto(resourceId=ids.bar)

            self.magneto.drag(source_el, target_el)

        Drag element to coordinate::

            source_el = self.magneto(resourceId=ids.foo)
            target_x = 200
            target_y = 100

            self.magneto.drag(source_el, target_x, target_y)

        Drag coordinate to element::

            source_x = 200
            source_y = 100
            target_el = self.magneto(resourceId=ids.foo)

            self.magneto.drag(source_x, source_y, target_el)

        Drag coordinate to coordinate::

            source_x = 200
            source_y = 100
            target_x = 200
            target_y = 100

            self.magneto.drag(source_x, source_y, target_x, target_y)
        """
        if len(args) == 2:
            (start_x, start_y) = args[0].center()
            (end_x, end_y) = args[1].center()
        elif len(args) == 3:
            if args[0].__class__ != 'int':
                (start_x, start_y) = args[0].center()
                (end_x, end_y) = args[1:]
            else:
                (start_x, start_y) = args[:2]
                (end_x, end_y) = args[2].center()
        elif len(args) == 4:
            (start_x, start_y, end_x, end_y) = args

        return super(Magneto, self).drag(start_x, start_y, end_x, end_y, **kwargs)

    def wait_for_element(self, timeout=None, **kwargs):
        """
        Wait for an element to show up::

            self.magneto.wait_for_element(resourceId=ids.foo)

        :param int timeout: Timeout in ms. Defaults to --wait-for-element-timeout which is 5000 by default.
        :param kwargs:
        :return element el:
        """
        if not timeout:
            timeout = get_config('--wait-for-element-timeout')

        el = self(**kwargs)
        el.wait.exists(timeout=timeout)
        return el

    def wait_for_true(self, function, timeout=15000, **kwargs):
        """
        Waits for given function to return True::

            self.magneto.wait_for(lambda: self.magneto.info['displayRotation'] == 90)

        :param function function:
        :param int timeout: Timeout in ms. Default to ``15000``
        :return Boolean result: The result of the last function invocation
        """
        result = False

        try:
            with Timeout(seconds=timeout/1000):
                while not result:
                    result = function(**kwargs)
                    time.sleep(0.5)

        except TimeoutError:
            pass

        return result

    def get_element_children(self, el, **kwargs):
        """
        Yields specific element children
        :param element el:

        :return generator
        """
        for i, _ in enumerate(itertools.repeat(None)):
            selector = el.child(instance=i, **kwargs)
            if not selector.exists:
                break
            yield selector


class MagnetoDeviceObject(AutomatorDeviceObject):
    def __init__(self, device, selector):
        super(MagnetoDeviceObject, self).__init__(device, selector)

    def center(self):
        return get_center(self.info['visibleBounds'])

    def child(self, **kwargs):
        """set childSelector."""
        return MagnetoDeviceObject(
            self.device,
            self.selector.clone().child(**kwargs)
        )

    def sibling(self, **kwargs):
        """set fromParent selector."""
        return MagnetoDeviceObject(
            self.device,
            self.selector.clone().sibling(**kwargs)
        )


class MagnetoAutomatorServer(AutomatorServer):
    __jar_files = {
        "bundle.jar": "libs/bundle.jar",
        "uiautomator-stub.jar": "libs/uiautomator-stub.jar"
    }

    __custom_jar_files = {
        "android.test.runner.jar": "libs/android.test.runner.jar",
        "uiautomator": "libs/uiautomator",
        "uiautomator.jar": "libs/uiautomator.jar"
    }

    def __init__(self, **kwargs):
        super(MagnetoAutomatorServer, self).__init__(**kwargs)

        sdk_int = int(self.adb.cmd("shell", "getprop", "ro.build.version.sdk").communicate()[0].strip())

        if sdk_int > 20:
            base_dir = os.path.dirname(__file__)
            for jar, jar_path in self.__custom_jar_files.items():
                filename = os.path.join(base_dir, jar_path)
                self.adb.cmd("push", filename, "/data/local/tmp/").wait()

            self.adb.cmd("shell", "su", "-c", "chmod", "555", "/data/local/tmp/uiautomator").wait()

    def push(self):
        base_dir = os.path.dirname(__file__)
        for jar, url in self.__jar_files.items():
            filename = os.path.join(base_dir, url)
            self.adb.cmd("push", filename, "/data/local/tmp/").wait()
        return list(self.__jar_files.keys())

    def start(self, timeout=5):
        files = self.push()
        cmd = list(itertools.chain(
            ["shell", "/data/local/tmp/uiautomator", "runtest"],
            files,
            ["-c", "com.github.uiautomatorstub.Stub"]
        ))
        self.uiautomator_process = self.adb.cmd(*cmd)
        self.adb.forward(self.local_port, self.device_port)

        while not self.alive and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        if not self.alive:
            raise IOError("RPC server not started!")

    def stop(self):
        """Stop the rpc server."""
        if self.uiautomator_process and self.uiautomator_process.poll() is None:
            res = None
            try:
                res = urllib2.urlopen(self.stop_uri)
                self.uiautomator_process.wait()
            except:
                self.uiautomator_process.kill()
            finally:
                if res is not None:
                    res.close()
                self.uiautomator_process = None
        try:
            out = self.adb.cmd("shell", "ps", "-C", "/data/local/tmp/uiautomator").communicate()[0].decode("utf-8").strip().splitlines()
            if out:
                index = out[0].split().index("PID")
                for line in out[1:]:
                    if len(line.split()) > index:
                        self.adb.cmd("shell", "kill", "-9", line.split()[index]).wait()
        except:
            pass


class MagnetoException(Exception):
    pass