
|build-status| |coverage-status|

|amf-logo| blender-amf
======================

Blender addon to export objects in Additive Manufacturing Format **AMF**

To ease the transfer of multiple grouped objects from Blender to PrusaSlicer.
This is a very simple implementation only meshes are exported for now.

Features
--------

Don't know if I will implement everything, i don't really need material/textures for 3D Printing

* |checked| Export AMF from blender

  * |checked| Single mesh support
  * |checked| Grouped mesh support
  * |unchecked| Material support
  * |unchecked| Texture support

* |unchecked| Import AMF to blender

  * |unchecked| Single mesh support
  * |unchecked| Grouped mesh support
  * |unchecked| Material support
  * |unchecked| Texture support

Download
------------

Release version
....................

 * download distribution from `latest release <https://github.com/GillesBouissac/blender-amf/releases>`_ 

Latest version
..............

 * use button [Code] then Download ZIP
 * Unzip in temp directory
 * Rezip only the directory io_mesh_amf to io_mesh_amf.zip

Installation
------------

Fast installation
.................

 * In blender:
    + "Edit/Preferences/Add-ons/Install"
    + Select io_mesh_amf.zip
    + Activate the add-on

Multi user installation (Linux)
...............................

 * Execute these commands, don't forget to replace <version> and <path/to/blender>
    + ``unzip io_mesh_amf.zip``
    + ``cp -r io_mesh_amf/ <path/to/blender>/current/<version>/scripts/addons/``

Test
----

.. sourcecode::

  sudo apt-get install python3.8
  sudo apt-get install python3-pip

  pip3 install pytest
  pip3 install pytest-cov
  pip3 install xmlschema
  pip3 install mathutils
  pip3 install coveralls

  pip install -e .
  pytest

PEP 8
-----

.. sourcecode::

  pip3 install pycodestyle
  pycodestyle --show-source --show-pep8 .


.. |build-status| image:: https://travis-ci.com/GillesBouissac/blender-amf.svg?branch=master
   :target: https://travis-ci.com/GillesBouissac/blender-amf
   :alt: Build status

.. |coverage-status| image:: https://img.shields.io/coveralls/GillesBouissac/blender-amf.svg
   :target: https://coveralls.io/r/GillesBouissac/blender-amf
   :alt: Test coverage percentage

.. |amf-logo| image:: images/amf.png
   :width: 50

..  |checked| unicode:: U+2611
..  |unchecked| unicode:: U+2610


