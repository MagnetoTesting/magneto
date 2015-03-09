from __future__ import absolute_import

import os
from datetime import datetime

import pytest

from .magneto import Magneto
from .logger import Logger
from .utils import get_config
from .utils.adb import ADB, ADBVideoCapture


class BaseTestCase(object):
    """
    Used as the test case base class.

    Example::

        class FooTestCase(BaseTestCase):
            '''
            Test Foo
            '''

            def test_bar(self):
                '''
                Test bar
                '''
                self.assertTrue(True)
    """

    magneto = None
    blocker_failed = False
    video_thread = None
    current_test = None
    test_suite_timestamp = None
    test_number = 0

    @classmethod
    def setup_class(cls):
        if BaseTestCase.magneto is None:
            BaseTestCase.magneto = Magneto.instance()
            BaseTestCase.test_suite_timestamp = datetime.now().strftime("%Y%m%d%H%M")

    @classmethod
    def teardown_class(cls):
        pass

    @classmethod
    def unconfigure(cls, *_):
        if BaseTestCase.magneto:
            if not BaseTestCase.blocker_failed:
                BaseTestCase.magneto.press.home()
            BaseTestCase.magneto.server.stop()
            BaseTestCase.magneto = None
            BaseTestCase.video_thread = None
            BaseTestCase.current_test = None
            BaseTestCase.test_number = 0
            BaseTestCase.test_suite_timestamp = None

    @classmethod
    def pytest_runtest_setup(cls, item, report):
        cls.test_number += 1
        cls.current_test = '{number}-{name}'.format(number=cls.test_number, name=item.name)
        if not report.skipped and get_config('--save-data-on-failure') and get_config('--include-video-on-failure'):
            cls.video_thread = ADBVideoCapture(cls.current_test)

    @classmethod
    def pytest_runtest_call(cls, item, report):
        if cls.video_thread:
            cls.video_thread.stop_recording()
        if report.failed:
            if 'blocker' in item.keywords:
                cls.blocker_failed = True
                for test in item.session.items:
                    if test.name != item.name and test._request:
                        test._request.applymarker(
                            pytest.mark.skipif(True,
                                               reason="{0} blocker failed, skipping remaining tests.".format(
                                                   item.name)))

            if get_config('--save-data-on-failure'):
                data_path_suffix = get_config('--device-id', 'device') + '-' + cls.test_suite_timestamp
                data_path = os.path.join(get_config('--magneto-failed-data-dir'), data_path_suffix)
                Logger.debug('Saving failed test data into {}'.format(data_path))
                if not os.path.isdir(data_path):
                    Logger.debug('Creating directory {}'.format(data_path))
                    os.makedirs(data_path)

                Logger.debug('Saving test logcat')
                logcat_file_path = os.path.join(data_path, '{0}.logcat.log'.format(cls.current_test))
                logcat_buffer = ADB.get_log()
                logcat_file = open(logcat_file_path, 'w')
                logcat_file.write('\n'.join(logcat_buffer))
                logcat_file.close()

                Logger.debug('Saving test hierarchy xml')
                cls.magneto.dump(os.path.join(data_path, '{0}.hierarchy.uix'.format(cls.current_test)))
                Logger.debug('Saving test screenshot')
                cls.magneto.screenshot(os.path.join(data_path, '{0}.screenshot.png'.format(cls.current_test)))
                if cls.video_thread:
                    Logger.debug('Saving test video')
                    cls.video_thread.save_files(data_path)

    @classmethod
    def pytest_runtest_teardown(cls, *_):
        ADB.clear_log()
        if cls.video_thread:
            cls.video_thread.delete_files()
            cls.video_thread = None

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass
