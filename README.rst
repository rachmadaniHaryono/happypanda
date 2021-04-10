
   Follow original creator on twitter to keep up to date with HPX:

   .. image:: https://img.shields.io/twitter/follow/pewspew.svg?style=social&label=Follow
     :target: https://twitter.com/twiddly_
   
    Note: Work on this program has been halted in favor of its successor
    `HappyPanda X <https://github.com/happypandax/server>`__ (bugs and such won't be fixed).
    Follow me on twitter to keep up to date with HPX:
    
    .. image:: https://img.shields.io/twitter/follow/twiddly_.svg?style=social&label=Follow
        :target: https://twitter.com/twiddly_

This is a cross platform manga/doujinshi manager with namespace & tag
support.

Features
========

-  Portable, self-contained in folder and cross-platform
-  Low memory footprint
-  Advanced gallery search with regex support (`learn more about it
   here <https://github.com/Pewpews/happypanda/wiki/Gallery-Searching>`__)
-  Gallery tagging: userdefined namespaces and tags
-  Gallery metadata fetching from the web (supports various sources)
-  Gallery downloading from the web (supports various sources) \*
-  Folder monitoring that'll notify you of filesystem changes
-  Multiple ways of adding galleries to make it as convienient as
   possible!
-  Recursive directory/archive scanning
-  Supports ZIP/CBZ, RAR/CBR and directories with loose files
-  Very customizable
-  And lots more...

\* Gallery downloading from E-Hentai costs Credits/GP

Screenshots
===========
<<<<<<< HEAD
.. image:: https://github.com/rabaarabaa/happypanda/raw/master/misc/screenshot1.png
    :width: 100%
    :align: center
.. image:: https://github.com/rabaarabaa/happypanda/raw/master/misc/screenshot2.png
    :width: 100%
    :align: center
.. image:: https://github.com/rabaarabaa/happypanda/raw/master/misc/screenshot3.png
=======
.. image:: https://github.com/Kramoule/happypanda/raw/master/misc/screenshot1.png
    :width: 100%
    :align: center
.. image:: https://github.com/Kramoule/happypanda/raw/master/misc/screenshot2.png
    :width: 100%
    :align: center
.. image:: https://github.com/Kramoule/happypanda/raw/master/misc/screenshot3.png
>>>>>>> Kramoule/develop
    :width: 100%
    :align: center

How to install and run
======================

Windows
^^^^^^^

#. Download the archive from
<<<<<<< HEAD
   `releases <https://github.com/rabaarabaa/happypanda/releases>`__
=======
   `releases <https://github.com/Kramoule/happypanda/releases>`__
>>>>>>> Kramoule/develop
#. Extract the archive to its own folder
#. Find Happypanda.exe and double click on it!

Mac and Linux
^^^^^^^^^^^^^

<<<<<<< HEAD
Install from PYPI or see `INSTALL.md <https://github.com/Pewpews/rabaarabaa/blob/master/INSTALL.md>`__
=======
Install from PYPI or see `INSTALL.md <https://github.com/Kramoule/happypanda/blob/master/INSTALL.md>`__
>>>>>>> Kramoule/develop

PYPI
^^^^^^^^^^^^^
``pip install happypanda`` (thanks `@Evolution0 <https://github.com/Evolution0>`__)
and then run with ``happypanda --home``

Note: use of the ``--home`` flag will make happypanda create required files and directories at:

On windows:
``'C:\Users\YourName\AppData\Local\Pewpew\Happypanda'``

On mac:
``'/Users/YourName/Library/Application Support/Happypanda'``

On linux:
``'/home/YourName/.local/share/Happypanda'``


Updating
========

| Overwrite your previous installation.
| More info in the `wiki <https://github.com/rabaarabaa/happypanda/wiki>`__


PYPI
^^^^^^^^^^^^^
``pip install --upgrade happypanda``


Misc.
=====

For general documentation (how to add galleries and usage of the
search), check the
`wiki <https://github.com/rabaarabaa/happypanda/wiki>`__.

People wanting to import galleries from the Pururin database torrent
should find `this <https://github.com/Exedge/Convertor>`__ useful.

Dependencies
============

-  Qt5 (Install this first) >= 5.4
-  PyQt5 (pip)
-  requests (pip)
-  beautifulsoup4 (pip)
-  watchdog (pip)
-  scandir (pip)
-  rarfile (pip)
-  robobrowser (pip)
-  Send2Trash (pip)
-  Pillow (pip) or PIL
-  python-dateutil (pip)
-  QtAwesome (pip)
-  appdirs (pip)

Contributing
============

You may make a pull request I guess...
