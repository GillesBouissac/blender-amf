# blender-amf

Blender addon for exporting/importing objects to/from AMF file

Just because i'm tired to export every parts of my designs individually (STL)
    and then reconstruct the aggregation in my Slicer
    
Thus, this is a very simple implementation only meshes are exported with no material/textures

# Features

Don't know if I will implement everything, i don't really need material/textures for 3D Printing

[x] Export AMF from blender
   [x] Mesh support
   [ ] Material support
   [ ] Texture support
[ ] Import AMF to blender
   [ ] Mesh support
   [ ] Material support
   [ ] Texture support

# Installation

1. Download the repository (zip with menu or git clone)
2. Unzip in temp directory
3. Install src/io_mesh_amf into blender in either way:
    * Local user installation all platform:
        * Zip src/io_mesh_amf and import that zip in Blender with:
        * "Edit/Preferences/Add-ons/Install"
    * Multi user installation all platform: <blender root dir>/current/<version>/scripts/addons
        * # Don't forget to replace <version> and <blender root dir> !
        * `cp -r src/io_mesh_amf <blender root dir>/current/<version>/scripts/addons/`
    * Other way for local user installation for Linux:
        * # Don't forget to replace <version> !
        * `cp -r src/io_mesh_amf ~/.config/blender/<version>/scripts/addons/`

# Test

```
sudo apt-get install python3.8
sudo apt-get install python3-pip

pip3 install pytest
pip3 install coverage
pip3 install pytest-cov
pip3 install xmlschema
pip3 install mathutils

pytest-3 --cov=io_mesh_amf --cov-report html
```

# PEP 8

```
pip3 install pycodestyle

pycodestyle --show-source --show-pep8 .
```


