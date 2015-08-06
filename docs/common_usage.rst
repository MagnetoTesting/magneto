Common usages
=============

.. _tagging:

Tag
---

Magneto allows attaching tags to test cases and tests alike, using ``@pytest.mark.TAG_NAME``::

    @pytest.mark.cards
    class CardsTestCase(BaseTestCase):
        """
        Tests example functionality
        """

        @pytest.mark.toggle
        def test_cards_toggle(self):
            ...

Now I can choose to run only ``CardsTestCase`` using ``-k cards``::

    $ magneto run ui_tests/ -k cards

.. _skipping:

Skip
----

Magneto allows conditional skipping for test cases and tests, using ``@pytest.mark.skipif(CONDITION, reason=REASON)``::

    @pytest.mark.skipif(settings.param == False, reason='Skipped cause param is False')
    class ExampleTestCase(BaseTestCase):
        """
        Tests example functionality
        """

        def test_example_1(self):
            ...

Blockers
--------

Some tests can be defined as blockers so that if they fail, all the rest would be skipped.
The boarding test, for instance, is considered a blocker as there's no point in continuing with following tests if the boarding process
failed.
We do this by using a pytest plugin called `pytest-blocker <https://github.com/EverythingMe/pytest-blocker>`_.

Example::

    class ExampleTestCase(BaseTestCase):
        """
        Tests example functionality
        """

        @pytest.mark.blocker
        def test_example_1(self):
            ...

