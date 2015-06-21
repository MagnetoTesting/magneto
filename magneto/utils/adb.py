import os
import subprocess
import re
import threading
from functools import wraps
from concurrent.futures import Future, wait
import time

from ..logger import Logger


class ADB(object):
    """
    Wrapper for adb commands.

    Import::

        from magneto.utils.adb import ADB

    :required: Android SDK installed and ANDROID_HOME pointing to SDK directory location.
    """

    _lock = threading.Lock()
    device_id = None
    ADB_PATH = os.path.join(os.environ['ANDROID_HOME'], 'platform-tools', 'adb')

    @classmethod
    def exec_cmd(cls, exec_cmd, stdin=None, stdout=None, stderr=None):
        """
        Executes adb commands::

            ADB.exec_cmd('shell uninstall com.android.package')

        In order to retrieve the process output, tap into the stdout::

            import subprocess

            proc = ADB.exec_cmd('shell pm list packages', stdout=subprocess.PIPE)
            list = proc.stdout.readline().strip('\\r\\n')

        :param str exec_cmd: Adb command to execute
        :param stdin:
        :param stdout:
        :param stderr:
        :return: Adb process
        """
        with cls._lock:
            cmd = 'exec {adb_path} {device_id} {command}'.format(
                adb_path=cls.ADB_PATH,
                device_id='-s {0}'.format(cls.device_id) if cls.device_id else '',
                command=exec_cmd
            )

            return subprocess.Popen(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr)

    @classmethod
    def get_log(cls):
        """
        Get log adb logcat.

        :return: Log dump
        """
        dump = []
        p = cls.exec_cmd("logcat -v time -d", stdout=subprocess.PIPE)
        for l in p.stdout:
            dump.append(l.strip())

        return dump

    @classmethod
    def clear_log(cls):
        """
        Clears adb log

        :return: Adb process
        """
        return cls.exec_cmd("logcat -c")

    @classmethod
    def start_activity(cls, package_name, activity_name, extras=None):
        """
        Start app activity.

        Open Gmail app::

            ADB.start_activity('com.google.android.gm', 'com.google.android.gm.ConversationListActivity')

        :param str package_name: Package name
        :param str activity_name: Activity name
        :return:
        """
        Logger.debug('opening activity {}'.format(activity_name))
        cls.exec_cmd("shell am start {0} {1}/{2}".format(extras or '', package_name, activity_name)).wait()

    @classmethod
    def kill_process(cls, package_name):
        """
        Stops given app::

            ADB.kill_process('com.android.chrome')

        :param str package_name: Package name to stop
        :return:
        """
        cls.exec_cmd("shell am force-stop {0}".format(package_name)).wait()

    @classmethod
    def uninstall(cls, package_name):
        Logger.debug('Uninstalling app {}'.format(package_name))
        cls.exec_cmd('uninstall {0}'.format(package_name)).wait()

        # remove app cache
        cls.exec_cmd('shell su -c "rm -rf /data/data/{0}"'.format(package_name)).wait()

    @classmethod
    def install(cls, apk_path, extra_params='', retry=True):
        Logger.debug('Installing app {}'.format(apk_path))
        p = cls.exec_cmd('install {} {}'.format(extra_params, apk_path), stdout=subprocess.PIPE)
        result = p.communicate()[0].strip().split('\r\n')[-1]

        if result == 'Success':
            Logger.debug('App installed')
            return True
        elif result != 'Success' and retry:
            Logger.debug('App install failed: {}'.format(result))
            Logger.debug('Retrying install...')
            return cls.install(apk_path, extra_params=extra_params, retry=False)
        else:
            Logger.debug('App install failed: {}'.format(result))
            return False

    @classmethod
    def getprop(cls, prop):
        p = cls.exec_cmd('shell getprop {}'.format(prop), stdout=subprocess.PIPE)
        return p.stdout.readline().strip('\r\n')

    @classmethod
    def set_datetime(cls, dt):
        adb_date = dt.strftime('%Y%m%d.%H%M%S')
        cls.exec_cmd("shell \"su -c 'date -s {adb_date}'\"".format(adb_date=adb_date)).wait()


class RegexMatcher(object):
    def __init__(self, pattern):
        self._pattern = pattern

    def __call__(self, line):
        return self._pattern.search(line)

    def __str__(self):
        return self._pattern.pattern[:20]+'...'


class ADBLogWatch(threading.Thread):
    """
    Enables watching adb logcat logs and asserting that they certain ones appeared::

            from magneto.utils.adb import ADBLogWatch

            def test_button_click_log(self, watcher):
                with ADBLogWatch() as watcher:
                    watcher.watch('button clicked')
                    self.magneto(text='Click here').click()
                    watcher.assert_done()
    """
    instance = None

    def __init__(self):
        ADB.clear_log().wait()
        super(ADBLogWatch, self).__init__()
        self._watchers = {}
        self.asked_to_stop = False

        if self.__class__.instance is not None:
            raise RuntimeError('Only one instance of {} is allowed at any time.'.format(self.__class__.__name__))

        self.__class__.instance = self

    @classmethod
    def wrap(cls, fn):
        @wraps(fn)
        def wrapper(instance, *args, **kwargs):
            self = cls()
            with self:
                return fn(instance, self, *args, **kwargs)
        return wrapper

    def __enter__(self, *_):
        self.start()
        return self

    def __exit__(self, *_):
        self.exit()

    def run(self):
        p = ADB.exec_cmd('logcat', stdout=subprocess.PIPE)
        while not self.asked_to_stop:
            line = p.stdout.readline().strip()
            if line == '':
                break
            for matcher, (future, min_times) in self._watchers.items():
                match = matcher(line)
                if match:
                    Logger.debug('Found logcat for "{}"'.format(matcher))
                    if min_times == 1:
                        future.set_result(line)
                        Logger.debug('Removing watch "{}"'.format(matcher))
                        del self._watchers[matcher]
                    else:
                        self._watchers[matcher] = future, min_times - 1

        p.terminate()
        Logger.debug('ADB logcat process terminated')

    def exit(self):
        self.__class__.instance = None
        self.asked_to_stop = True
        self.join()

    def watch(self, pattern, **kwargs):
        """
        Watch for given pattern in logs.

        :param pattern: Regular expression pattern to perform on logcat lines
        :param int min_times: Minimum times a certain pattern should appear in log
        """
        if callable(pattern):
            Logger.debug('watching pattern "{}"'.format(str(pattern)))
            future = Future()
            self._watchers[pattern] = future, kwargs.get('min_times', 1)

            return future
        else:
            return self.watch_compiled(re.compile(pattern), **kwargs)

    def watch_compiled(self, pattern, min_times=1):
        regex_matcher = RegexMatcher(pattern)
        Logger.debug('watching pattern "{}"'.format(str(regex_matcher)))
        future = Future()
        self._watchers[regex_matcher] = future, min_times

        return future

    def assert_done(self, timeout=15, stall=None, futures=None):
        """
        Asserts if all/some watches exist in log.

        :param futures: The futures we want to wait to end
        :param timeout: Amount of time in seconds to wait for watches to appear in log. Defaults to 5 seconds.
        :param stall: Amount of time in seconds to keep waiting before exiting the wait. More info in https://github.com/EverythingMe/magneto/issues/1

        Example::

            from magneto.utils.adb import ADBLogWatch

            def test_incoming_call(self, watcher):
                with ADBLogWatch() as watcher:
                    watcher.watch('call arrived')
                    call_device()
                    watcher.assert_done()

        Example with stall::

            from magneto.utils.adb import ADBLogWatch

            def test_incoming_call(self, watcher):
                with ADBLogWatch() as watcher:
                    watcher.watch('call arrived')
                    call_device()
                    watcher.assert_done(timeout=10, stall=120)
        """

        if futures:
            if not isinstance(futures, list):
                futures = [futures]
        else:
            futures = [future for (future, _) in self._watchers.itervalues()]

        Logger.debug('waiting up to {} seconds for {} watchers'.format(timeout, len(futures)))

        start_time = time.time()
        done, pending = wait(futures, timeout=timeout)
        if not pending:
            Logger.debug('watchers done')
            return

        if stall:
            stall_time = stall-int(time.time() - start_time)
            Logger.debug('Stalling for another %d seconds' % stall_time)
            done, pending = wait(futures, timeout=stall_time)
            if not pending:
                Logger.debug('watchers done')

        patterns_left = '\n'.join('pattern: {}'.format(str(r)) for r in self._watchers)
        raise AssertionError(
            'assert_done failure.\nWaited {} seconds but still have {} watchers:\n{}'
            .format(timeout, len(self._watchers), patterns_left)
        )

    def assert_watch(self, *args, **kwargs):
        """
        Asserts specific watchers if they exists in log

        :param args: <Future> all watchers we want to wait to end
        :param kwargs: extra params to pass to assert_done like timeout..
        :return: self.asset_done
        """
        return self.assert_done(futures=list(args), **kwargs)


class ADBVideoCapture(threading.Thread):
    def __init__(self, video_file_name, timelimit=180, bitrate=1000000, size='1280x720'):
        super(ADBVideoCapture, self).__init__()

        self.video_file_name = video_file_name
        self.recording_process = None
        self.files = []
        self.asked_to_stop = False
        self.timelimit = timelimit
        self.bitrate = bitrate
        self.size = size

        self.daemon = True
        self.start()

    def run(self):
        self.start_recording()
        while not self.asked_to_stop:
            if self.recording_process.poll() is not None:
                self.start_recording()
        self.recording_process.terminate()

    def start_recording(self):
        self.files.append('/sdcard/{0}-{1}.video.mp4'.format(self.video_file_name, len(self.files) + 1))
        self.recording_process = ADB.exec_cmd(
            'shell screenrecord --bit-rate {bitrate} --time-limit {timelimit} --size {size} {file}'.format(
                bitrate=self.bitrate,
                timelimit=self.timelimit,
                size=self.size,
                file=self.files[
                    len(self.files) - 1]))

    def stop_recording(self):
        self.asked_to_stop = True

    def save_files(self, save_file_path):
        for video_file in self.files:
            ADB.exec_cmd('pull {0} {1}'.format(video_file, save_file_path)).wait()

    def delete_files(self):
        for video_file in self.files:
            ADB.exec_cmd('shell rm {0}'.format(video_file)).wait()
