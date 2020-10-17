
blender-amf |build-status| |coverage-status|
============================================

Blender addon to export objects from Additive Manufacturing Format **AMF**

To ease the transfer of multiple grouped objects from Blender to PrusaSlicer.
This is a very simple implementation only meshes are exported for now.

Features
--------

Don't know if I will implement everything, i don't really need material/textures for 3D Printing

* ``[X]`` Export AMF from blender

  * ``[X]`` Single mesh support
  * ``[X]`` Grouped mesh support
  * ``[.]`` Material support
  * ``[.]`` Texture support

* ``[.]`` Import AMF to blender

  * ``[.]`` Single mesh support
  * ``[.]`` Grouped mesh support
  * ``[.]`` Material support
  * ``[.]`` Texture support

Installation
------------

#. Download the repository (zip with menu or git clone)
#. Unzip in temp directory
#. Install src/io_mesh_amf into blender in either way:

   * Local user installation all platform:
      + Zip src/io_mesh_amf and import that zip in Blender with:
      + "Edit/Preferences/Add-ons/Install"
   * Multi user installation all platform:
      + ``# Don't forget to replace <version> and <path/to/blender>``
      + ``cp -r src/io_mesh_amf <path/to/blender>/current/<version>/scripts/addons/``
   * Other way for local user installation for Linux:
      + ``# Don't forget to replace <version>``
      + ``cp -r src/io_mesh_amf ~/.config/blender/<version>/scripts/addons/``



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
