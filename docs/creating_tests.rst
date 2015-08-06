Writing tests
=============

Tests are defined within a test case file. e.g ``login_test.py``.
It is recommended to store these files under a ``ui_tests`` folder::

    - ui_tests
      - boarding_test.py
      - login_test.py
      - mainpage_test.py
      - feature_test.py
      - other_feature_test.py


Test cases inherit from :ref:`base_test_case.rst` and utilize features such as setup, teardown and assertions.

Defining a test
---------------

Example::

    from magento.base import BaseTestCase

    class ExampleTest(BaseTestCase):
        """
        Tests example functionality
        """

        def test_example_1(self):
            ...

        def test_example_2(self):
            ...

        def test_example_3(self):
            ...

Tests are defined as functions prefixed with `test_` and usually include some kind of assertion.

Example::

     def test_example(self):
        # scroll fast to bottom
        self.magneto(scrollable=True).fling()
        # get element by id
        el = self.magneto(text=ids.foo)
        # assert that the element exists in the current view
        Assert.true(el.exists)

Results
-------

Test results are available via Magneto logs::

    ui_tests/ftu_test.py .s
    ui_tests/cards_test.py F
    ui_tests/discovery_test.py .
    ui_tests/folders_test.py ..s..
    ui_tests/homescreen_test.py .
    ui_tests/magneto_test.py ....
    ui_tests/search_test.py .F....

In the log above, each line represents a test case and its tests results.

* ``.`` = passed
* ``s`` = skipped
* ``F`` = failed

A summary at the end::

    =============== 2 failed, 16 passed, 2 skipped in 348.66 seconds ===============

Failed tests log more information, pointing to where an error or assertion failure occurred::

    self = <magneto.test.cards_test.CardsTestCase testMethod=test_browse_news_cards>

    def test_browse_news_cards(self):
        """
            Test browse through cards in News smart folder
            """
            cards = self.magneto(resourceId=ids.card)

            folder = Folder(folders.news)
            folder.click()
            Assert.true(cards.exists)

            folder.menu.click()
            self.magneto(text=names.hide_cards).click()
            self.magneto.press.home()
            folder.click()
            Assert.false(cards.exists)

            folder.menu.click()
            self.magneto(text=names.show_cards).click()
            self.magneto.press.home()
            folder.click()
    >       Assert.true(cards.exists)
    E       AssertionError: False is not true

    magneto/test/cards_test.py:29: AssertionError

Even more data about failed tests
---------------------------------

Magneto can be instructed to capture adb logcat logs, element hierarchy and screen image at the moment the fail was determined.
When all test runs are over, these files are made available in the dedicated folder (usually ``tmp/magneto_test_data``
unless specified differently with the ``--magneto_failed_data_dir`` parameter) as one bundled file.
This file could be made available in CI systems as a build artifact.

Example::

    - Nexus4-01acd7ef4c3d12d4 4.53.24 PM
      - 7-test_example_1-201503081428-1.video.mp4
      - 7-test_example_1-201503081428.hierarchy.uix
      - 7-test_example_1-201503081428.logcat.log
      - 7-test_example_1-201503081428.screenshot.png

