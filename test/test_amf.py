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

import os
import sys
import types
import inspect
import tempfile
import pytest
import xmlschema
import traceback
import fakebpy
import bpy
from mathutils import Matrix
from unittest.mock import Mock, patch, PropertyMock
from zipfile import ZipFile
from io_mesh_amf.amf_util import AMFExport, flatten


def is_scaling_matrix(matrix):
    """ A scaling only matrix has non zero values on its diagonal """
    scaling = Matrix.Identity(4)
    scaling[0][0] = matrix[0][0]
    scaling[1][1] = matrix[1][1]
    scaling[2][2] = matrix[2][2]
    scaling[3][3] = matrix[3][3]
    return matrix == scaling


class Test_flatten():
    """ Verifications of flatten """

    def test_flatten_list(self):
        # Prepare
        L1 = type('obj', (object,), {'n': 'L1'})
        L2 = type('obj', (object,), {'n': 'L2'})
        L3 = type('obj', (object,), {'n': 'L3'})
        I12 = type('obj', (object,), {'n': 'I12', 'children': [L1, L2]})
        I3 = type('obj', (object,), {'n': 'I3', 'children': [L3]})
        P = type('obj', (object,), {'n': 'P', 'children': [I12, I3]})
        # Test
        res = flatten(None)
        assert len(res) == 0
        res = flatten([None])
        assert len(res) == 0
        res = flatten(L1)
        assert len(res) == 1
        res = flatten([L1])
        assert len(res) == 1
        res = flatten(I12)
        assert len(res) == 3
        res = flatten([I12])
        assert len(res) == 3
        res = flatten(P)
        assert len(res) == 6
        res = flatten([P])
        assert len(res) == 6
        res = flatten(flatten(P))
        assert len(res) == 6


    def test_flatten_tuple(self):
        """ Blender obj.children are tuple """
        # Prepare
        L1 = type('obj', (object,), {'n': 'L1'})
        L2 = type('obj', (object,), {'n': 'L2'})
        L3 = type('obj', (object,), {'n': 'L3'})
        I12 = type('obj', (object,), {'n': 'I12', 'children': (L1, L2)})
        I3 = type('obj', (object,), {'n': 'I3', 'children': (L3)})
        P = type('obj', (object,), {'n': 'P', 'children': (I12, I3)})
        # Test
        res = flatten(None)
        assert len(res) == 0
        res = flatten((None))
        assert len(res) == 0
        res = flatten(L1)
        assert len(res) == 1
        res = flatten((L1))
        assert len(res) == 1
        res = flatten(I12)
        assert len(res) == 3
        res = flatten((I12))
        assert len(res) == 3
        res = flatten(P)
        assert len(res) == 6
        res = flatten((P))
        assert len(res) == 6
        res = flatten(flatten(P))
        assert len(res) == 6


class Test_compute_scaling():
    """ Verifications of compute_scaling """

    def test_compute_scaling_invalid(self):
        # Test
        (target_unit, scale, matrix) = AMFExport.compute_scaling('ua')
        # Check
        assert target_unit == 'meter'
        assert scale == 1
        assert isinstance(matrix, Matrix) is True
        assert matrix == Matrix.Identity(4)

    def test_compute_scaling_meter(self):
        # Test
        (target_unit, scale, matrix) = AMFExport.compute_scaling('meter')
        # Check
        assert target_unit == 'meter'
        assert scale == 1
        assert isinstance(matrix, Matrix) is True
        assert matrix == Matrix.Identity(4)

    def test_compute_scaling_inch(self):
        # Test
        (target_unit, scale, matrix) = AMFExport.compute_scaling('inch')
        # Check
        assert target_unit == 'inch'
        assert scale == 39.37008
        assert isinstance(matrix, Matrix) is True
        assert is_scaling_matrix(matrix) is True


class Test_object2mesh():
    """ Verifications of object2mesh """

    def test_object2mesh_noop(self, context, cube_0):
        # Test
        cube_0.mode = 'OBJECT'
        with patch.object(cube_0, "evaluated_get") as evaluated_get:
            ret = AMFExport.object2mesh(cube_0, Matrix.Identity(4), False)
            # Check
            cube_0.to_mesh.assert_called_once_with()
            cube_0.evaluated_get.assert_not_called()
        assert ret == cube_0.mesh_mock
        cube_0.update_from_editmode.assert_not_called()
        cube_0.mesh_mock.calc_loop_triangles.assert_called_once_with()

    def test_object2mesh_no_mesh(self, context, cube_0):
        # Test
        with patch.object(cube_0, 'to_mesh', return_value=None) as to_mesh:
            ret = AMFExport.object2mesh(cube_0, Matrix.Identity(4), False)
            # Check
            cube_0.to_mesh.assert_called_once_with()
        assert ret is None

    def test_object2mesh_mesh_except(self, context, cube_0):
        # Prepare
        # Test
        cube_0.to_mesh.side_effect = Exception('Mock cant build mesh')
        ret = AMFExport.object2mesh(cube_0, Matrix.Identity(4), False)
        # Check
        cube_0.to_mesh.assert_called_once_with()
        assert ret is None

    def test_object2mesh_editmode(self, context, cube_0):
        # Prepare
        cube_0.mode = 'EDIT'
        # Test
        with patch.object(cube_0, "evaluated_get") as evaluated_get:
            ret = AMFExport.object2mesh(cube_0, Matrix.Identity(4), False)
            # Check
            cube_0.evaluated_get.assert_not_called()
        assert ret == cube_0.mesh_mock
        cube_0.update_from_editmode.assert_called_once_with()
        cube_0.to_mesh.assert_called_once_with()
        cube_0.mesh_mock.calc_loop_triangles.assert_called_once_with()

    def test_object2mesh_modifiers(self, context, cube_0):
        # Prepare
        obj_modified = Mock()
        obj_modified.to_mesh.return_value = cube_0.mesh_mock
        obj_modified.matrix_world = Matrix.Identity(4)
        fake_depsgraph = "fake_depsgraph"
        bpy.context.evaluated_depsgraph_get.return_value = fake_depsgraph
        # Test
        ret = None
        cube_0.mode = 'OBJECT'
        with patch.object(cube_0, "evaluated_get") as evaluated_get:
            evaluated_get.return_value = obj_modified
            ret = AMFExport.object2mesh(cube_0, Matrix.Identity(4), True)
            # Check
            evaluated_get.assert_called_once_with(fake_depsgraph)
        assert ret == cube_0.mesh_mock
        cube_0.update_from_editmode.assert_not_called()
        obj_modified.to_mesh.assert_called_once_with()
        cube_0.mesh_mock.calc_loop_triangles.assert_called_once_with()

    def test_object2mesh_scale(self, context, cube_0):
        # Prepare
        cube_0.mode = 'EDIT'
        # Test
        (unit, scale, matrix) = AMFExport.compute_scaling('millimeter')
        ret = AMFExport.object2mesh(cube_0, matrix, False)
        assert ret == cube_0.mesh_mock
        # Check that the coordinated have been reduced
        assert unit == 'millimeter'
        assert scale == 1000
        ret.transform.assert_called_once_with(matrix)
