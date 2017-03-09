This is a cross platform manga/doujinshi manager with namespace & tag
support.

Features
========

-  Portable, self-contained in folder and cross-platform
-  Advanced gallery search with regex support
-  Low memory footprint
-  Gallery tagging: userdefined namespaces and tags
-  Gallery metadata fetching from the web (supports various sources)
-  Gallery downloading from the web (supports various sources) \*
-  Folder monitoring that'll notify you of filesystem changes
-  Multiple ways of adding galleries to make it as convienient as possible!
-  Recursive directory/archive scanning
-  Supports ZIP/CBZ, RAR/CBR and directories with loose files
-  Very customizable
-  And lots more...

\* Gallery downloading from E-Hentai costs Credits/GP


Screenshots
===========
.. image:: ../misc/screenshot1.png
    :width: 100%
    :align: center
.. image:: ../misc/screenshot2.png
    :width: 100%
    :align: center
.. image:: ../misc/screenshot3.png
    :width: 100%
    :align: center

Installation and Update
=======================

This program require Qt5 with minimum version 5.4.
User from window/64bit linux/osx can use pip to install this.
User with 32bit linux should install `python3-pyqt5`, 
before install with pip.

Use pip to install

.. code-block:: bash

        git clone https://github.com/rachmadaniHaryono/happypanda
        cd happypanda
        pip install .

Use pip install from github link

.. code-block:: bash

        pip install https://github.com/rachmadaniHaryono/happypanda

if pip require sudo to install, use `--user` flag.

Contribute
==========

- Issue Tracker: https://github.com/rachmadaniHaryono/happypanda/issues
- Source Code: https://github.com/rachmadaniHaryono/happypanda

Support
=======

If you need help you can contact developer at `Happypanda room at gitter`_
or `file a bug in the issue tracker`_.

.. _Happypanda room at gitter: https://gitter.im/Pewpews/happypanda
.. _file a bug in the issue tracker: https://github.com/rachmadaniHaryono/happypanda/issues


Fork's goals
============

After reaching 1.1, Happypanda development is halted for Happypandax project.
This fork is created to continue the happypanda project with better code base
and more feature.

Main goals
----------

- Testing coverage for non pyqt stuff over 50 %.
- Using peewee for database module.
- More supported gallery downloader.

Optional goals
--------------

- Metadata from other website such as myanimelist, mangaupdates, etc

Misc.
=====

People wanting to import galleries from the Pururin database torrent
should find `Exedge/Convertor`_ useful.

.. _Exedge/Convertor: https://github.com/Exedge/Convertor

License
=======

The project is licensed under the GNU GPL
