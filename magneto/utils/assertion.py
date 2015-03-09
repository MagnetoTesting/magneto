import re
from ..magneto import Magneto


class Assert(object):
    @classmethod
    def current_package(cls, *expected_packages, **kwargs):
        """
        Checks current package equals the expected.
        Raises exception if timed out

        :param expected_packages: package names
        :param str msg: Overrides default exception message

        Example::

            # single package
            Assert.current_package('com.android.chrome')

            # any package
            Assert.current_package('com.google.android.gm', 'com.android.email')
        """
        magneto = Magneto.instance()

        found = magneto.wait_for_true(lambda: magneto.info['currentPackageName'] in expected_packages, **kwargs)

        if not found:
            msg = kwargs.get('msg', None)
            current_package = magneto.info['currentPackageName']
            default_msg = "{0} is the current package, not {1} ".format(current_package, ' nor '.join(expected_packages))

            raise AssertionError(cls._format_message(msg, default_msg))

    @classmethod
    def true(cls, expr, msg=None):
        """
        Checks that the expression is true

        Assert that the device is a tablet::

            Assert.true(device.type == 'tablet')
        """
        if not expr:
            msg = cls._format_message(msg, "{} is not true".format(expr))
            raise AssertionError(msg)

    @classmethod
    def false(cls, expr, msg=None):

        """
        Checks that the expression is false

        Assert that the device is not a tablet::

            Assert.false(device.type == 'tablet')
        """
        if expr:
            msg = cls._format_message(msg, "{} is not false".format(expr))
            raise AssertionError(msg)

    @classmethod
    def regexp_matches(cls, text, expected_regexp, msg=None):
        """
        Fail the test unless the text matches the regular expression.

        Assert that the user agent string matches a OS 4.1.2::

            Assert.regexp_matches(user_agent, '.*\s4.1.2;')

        """
        # compile if not already
        if isinstance(expected_regexp, basestring):
            expected_regexp = re.compile(expected_regexp)

        # test regex
        if not expected_regexp.search(text):
            msg = msg or "Regexp mismatch"
            msg = '{0}: {1} not found in {2}'.format(msg, expected_regexp.pattern, text)
            raise AssertionError(msg)

    @classmethod
    def _format_message(cls, msg, default_msg):
        return msg or default_msg
