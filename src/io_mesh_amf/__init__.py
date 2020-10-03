# MIT License
# 
# Copyright (c) 2020 Gilles Bouissac
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# <pep8 compliant>

# Blender plugin manifest
bl_info = {
    "name":        "AMF format",
    "author":      "G.Bouissac",
    "version":     (0, 1, 0),
    "blender":     (2, 82, 0),
    "location":    "File > Import-Export",
    "description": "Import-Export AMF files",
    "support":     'TESTING',
    "category":    "Import-Export"
}

# Auto reload module to be able to update code without blender restart
if "bpy" in locals():
    import importlib
    print ( "Reloading io_mesh_amf modules" )
    if "export_amf" in locals():
        importlib.reload(export_amf)
    if "import_amf" in locals():
        importlib.reload(import_amf)

import bpy.types
import bpy.utils

from .import_amf import ImportAMF
from .export_amf import ExportAMF


def menu_import(self, _):
    """
    Called from blender import the menu item.
    """
    self.layout.operator(ImportAMF.bl_idname, text="Additive Manufacturing Format (.amf)")


def menu_export(self, _):
    """
    Called from blender export the menu item.
    """
    self.layout.operator(ExportAMF.bl_idname, text="Additive Manufacturing Format (.amf)")


classes = (
    ImportAMF,
    ExportAMF
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


