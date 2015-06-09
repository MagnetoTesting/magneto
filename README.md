Magneto
=======

![image]

Magneto was built by Automation Engineers for Automation Engineers out of necessity for a mobile centric test automation
framework that's easy to setup, run and utilize. At [EverythingMe], we went through many open source solutions but none
felt fast, easy and hassle free.

Magneto is written in **Python** for **Android** devices. It utilizes the [uiautomator] tool via
a [Python wrapper] and [pytest] as a test framework.

Magneto can be triggered from CLI, IDE and CI.

Quick start
-----------
```bash
$ pip install magneto
$ magneto init calc
$ magneto run tests/
```


Required params:

| Option | Description |
| --- | --- |
| ``<TEST_DIR>`` | Test file directory path. Usually ``ui_tests`` (Required) |
| ``--app-package <APK_PACKAGE_NAME>``| Tested app package name. e.g. ``--app-package com.facebook.katana`` |
| ``--app-activity <APK_ACTIVITY>`` | Tested app activity string. e.g. ``--app-activity com.facebook.katana.LoginActivity`` |

Documentation
-------------
Full documentation at [magneto.readthedocs.org]


Contribute
----------

We invite you to use Magneto to test your Android products, to [open issues][magneto_issues], to request features, to ask questions
and submit your own Pull Requests.

Leading contributors:

* [ranbena]
* [maticrivo]
* [amirnissim]
* [bergundy]


[uiautomator]: http://developer.android.com/tools/help/uiautomator/index.html
[Python wrapper]: https://github.com/xiaocong/uiautomator
[EverythingMe]: http://everything.me
[pytest]: http://pytest.org/
[magneto_issues]: https://github.com/EverythingMe/Magneto/issues

[ranbena]: https://github.com/ranbena
[maticrivo]: https://github.com/maticrivo
[amirnissim]: https://github.com/amirnissim
[bergundy]: https://github.com/bergundy

[magneto.readthedocs.org]: http://magneto.readthedocs.org

[image]: https://s3.amazonaws.com/evme-static-assets/magneto/Magneto.jpg
