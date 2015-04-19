import threading
import time
import itertools

from uiautomator import AutomatorDevice, AutomatorDeviceObject, Selector

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


class MagnetoException(Exception):
    pass