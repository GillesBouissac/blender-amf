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

# Faking Blender Python API

import sys
import types
import inspect
from unittest.mock import Mock, patch
from fakemodule import fakeType, fakePackage


# Fake blender classes that will allow us to mock every API
class _Operator:
    pass


class _ImportHelper:
    pass


class _ExportHelper:
    pass


TOPBAR_MT_file_import = []
TOPBAR_MT_file_export = []


# Register fake classes and packages
fakePackage([
    'bpy',
    'bpy.types',
    'bpy_extras',
    'bpy_extras.io_utils',
])
fakeType({
    # These 3 types are the reason for fakemodule existence
    # We can't mock them or we get a bad metaclass error on these lines:
    #   class ExportAMF(Operator, ExportHelper):
    #   class ImportAMF(Operator, ImportHelper):
    # We define them with empty classes with 'type' metaclass
    #   Their attributes can be mocked if needed
    'bpy.types.Operator':                   _Operator,
    'bpy_extras.io_utils.ImportHelper':     _ImportHelper,
    'bpy_extras.io_utils.ExportHelper':     _ExportHelper,

    'bpy.types.TOPBAR_MT_file_import':      TOPBAR_MT_file_import,
    'bpy.types.TOPBAR_MT_file_export':      TOPBAR_MT_file_export,
    'bpy.utils.register_class':             Mock,
    'bpy.utils.unregister_class':           Mock,
    'bpy.props.BoolProperty':               Mock,
    'bpy.props.StringProperty':             Mock,
    'bpy.props.FloatProperty':              Mock,
    'bpy.props.EnumProperty':               Mock,
    'bpy.context':                          Mock(),
})
