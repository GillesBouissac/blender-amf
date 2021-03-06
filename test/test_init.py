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
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# <pep8 compliant>

import sys
import types
import inspect
import fakebpy
from unittest.mock import Mock, patch

from bpy.types import TOPBAR_MT_file_import
from bpy.types import TOPBAR_MT_file_export
from io_mesh_amf import register, unregister, bl_info


# Every import/export addon should pass this test
class TestInit():

    def test_manifest(self):
        assert bl_info is not None

    @patch('bpy.utils.register_class')
    def test_register_class(self, register_class):
        # Prepare
        TOPBAR_MT_file_import.clear()
        TOPBAR_MT_file_export.clear()

        # Test
        register()

        # Check
        assert register_class.call_count == 2
        class1 = register_class.call_args_list[0][0][0]
        class2 = register_class.call_args_list[1][0][0]
        assert inspect.isclass(type(class1))
        assert inspect.isclass(type(class2))
        assert len(TOPBAR_MT_file_import) == 1
        assert len(TOPBAR_MT_file_export) == 1
        assert inspect.isfunction(TOPBAR_MT_file_import[0])
        assert inspect.isfunction(TOPBAR_MT_file_export[0])

        #   Blender mandatory attributes on registered classes
        assert isinstance(class1.bl_label, str)
        assert isinstance(class1.bl_idname, str)
        assert isinstance(class2.bl_label, str)
        assert isinstance(class2.bl_idname, str)
        assert inspect.isfunction(class2.execute)
        assert inspect.isfunction(class2.execute)

    @patch('bpy.utils.unregister_class')
    def test_unregister_class(self, unregister_class):
        # Prepare
        TOPBAR_MT_file_import.clear()
        TOPBAR_MT_file_export.clear()
        register()
        assert len(TOPBAR_MT_file_import) == 1
        assert len(TOPBAR_MT_file_export) == 1

        # Test
        unregister()

        # Check
        assert unregister_class.call_count == 2
        class1 = unregister_class.call_args_list[0][0][0]
        class2 = unregister_class.call_args_list[1][0][0]
        assert inspect.isclass(type(class1))
        assert inspect.isclass(type(class2))
        assert len(TOPBAR_MT_file_import) == 0
        assert len(TOPBAR_MT_file_export) == 0
