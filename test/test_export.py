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
import fakebpy
import tempfile
import pytest
import xmlschema
import traceback
import bpy
from mathutils import Matrix
from unittest.mock import Mock, patch, PropertyMock
from zipfile import ZipFile
from io_mesh_amf import ExportAMF


def is_scaling_matrix(matrix):
    """ A scaling only matrix has non zero values on its diagonal """
    scaling = Matrix.Identity(4)
    scaling[0][0] = matrix[0][0]
    scaling[1][1] = matrix[1][1]
    scaling[2][2] = matrix[2][2]
    scaling[3][3] = matrix[3][3]
    return matrix == scaling


class TestExportBeforeExecute():
    """ Verifications before execute can be called """

    def test_compute_scaling_invalid(self):
        # Prepare
        export = ExportAMF()
        export.target_unit = 'ua'
        # Test
        (target_unit, scale, matrix) = export.compute_scaling()
        # Check
        assert target_unit == 'meter'
        assert scale == 1
        assert isinstance(matrix, Matrix) is True
        assert matrix == Matrix.Identity(4)

    def test_compute_scaling_meter(self):
        # Prepare
        export = ExportAMF()
        export.target_unit = 'meter'
        # Test
        (target_unit, scale, matrix) = export.compute_scaling()
        # Check
        assert target_unit == 'meter'
        assert scale == 1
        assert isinstance(matrix, Matrix) is True
        assert matrix == Matrix.Identity(4)

    def test_compute_scaling_inch(self):
        # Prepare
        export = ExportAMF()
        export.target_unit = 'inch'
        # Test
        (target_unit, scale, matrix) = export.compute_scaling()
        # Check
        assert target_unit == 'inch'
        assert scale == 39.37008
        assert isinstance(matrix, Matrix) is True
        assert is_scaling_matrix(matrix) is True


class vertex():
    co = []

    def __init__(self, x, y, z):
        self.co = [x, y, z]


class triangle():
    vertices = []

    def __init__(self, v1, v2, v3):
        self.vertices = [v1, v2, v3]


@pytest.fixture
def cube_mesh():
    """ cube mesh """
    mesh = Mock()
    mesh.vertices = [
        vertex(0, 0, 0),
        vertex(1, 0, 0),
        vertex(1, 1, 0),
        vertex(0, 1, 0),
        vertex(0, 1, 1),
        vertex(1, 1, 1),
        vertex(1, 0, 1),
        vertex(0, 0, 1)
    ]
    mesh.loop_triangles = [
        triangle(0, 2, 1),
        triangle(0, 3, 2),
        triangle(2, 3, 4),
        triangle(2, 4, 5),
        triangle(1, 2, 5),
        triangle(1, 5, 6),
        triangle(0, 7, 4),
        triangle(0, 4, 3),
        triangle(5, 4, 7),
        triangle(5, 7, 6),
        triangle(0, 6, 7),
        triangle(0, 1, 6),
    ]
    return mesh


@pytest.fixture
def cube(cube_mesh):
    """ cube object """
    obj = Mock()
    obj.mode = 'OBJECT'
    obj.name = 'cube'
    obj.mesh_mock = cube_mesh
    obj.to_mesh.return_value = cube_mesh
    obj.matrix_world = Matrix.Identity(4)
    obj.update_from_editmode = Mock()
    obj.evaluated_get = lambda s: s
    return obj


@pytest.fixture
def context():
    """ empty context """
    context = Mock()
    context.scene.name = "Nom de scene pour test"
    return context


@pytest.fixture
def context_cube(context, cube):
    """ context with cube object """
    context.selected_objects = [cube]
    return context


@pytest.fixture
def export():
    """ Export object to test with all default properties """
    tempName = f"{tempfile.gettempdir()}/test_export.amf"
    exp = ExportAMF()
    exp.filepath = tempName
    exp.use_selection = True
    exp.use_mesh_modifiers = False
    exp.target_unit = 'meter'
    exp.group_strategy = 'parent'
    return exp


class TestExportObject2mesh():
    """ Verifications of object2mesh """

    def test_object2mesh_noop(self, export, context, cube):
        # Test
        cube.mode = 'OBJECT'
        with patch.object(cube, "evaluated_get") as evaluated_get:
            ret = export.object2mesh(cube, Matrix.Identity(4))
            # Check
            cube.to_mesh.assert_called_once_with()
            cube.evaluated_get.assert_not_called()
        assert ret == cube.mesh_mock
        cube.update_from_editmode.assert_not_called()
        cube.mesh_mock.calc_loop_triangles.assert_called_once_with()

    def test_object2mesh_no_mesh(self, export, context, cube):
        # Test
        with patch.object(cube, 'to_mesh', return_value=None) as to_mesh:
            ret = export.object2mesh(cube, Matrix.Identity(4))
            # Check
            cube.to_mesh.assert_called_once_with()
        assert ret is None

    def test_object2mesh_mesh_except(self, export, context, cube):
        # Prepare
        # Test
        cube.to_mesh.side_effect = Exception('Mock cant build mesh')
        ret = export.object2mesh(cube, Matrix.Identity(4))
        # Check
        cube.to_mesh.assert_called_once_with()
        assert ret is None

    def test_object2mesh_editmode(self, export, context, cube):
        # Prepare
        cube.mode = 'EDIT'
        # Test
        with patch.object(cube, "evaluated_get") as evaluated_get:
            ret = export.object2mesh(cube, Matrix.Identity(4))
            # Check
            cube.evaluated_get.assert_not_called()
        assert ret == cube.mesh_mock
        cube.update_from_editmode.assert_called_once_with()
        cube.to_mesh.assert_called_once_with()
        cube.mesh_mock.calc_loop_triangles.assert_called_once_with()

    def test_object2mesh_modifiers(self, export, context, cube):
        # Prepare
        obj_modified = Mock()
        obj_modified.to_mesh.return_value = cube.mesh_mock
        obj_modified.matrix_world = Matrix.Identity(4)
        fake_depsgraph = "fake_depsgraph"
        bpy.context.evaluated_depsgraph_get.return_value = fake_depsgraph
        # Test
        ret = None
        cube.mode = 'OBJECT'
        export.use_mesh_modifiers = True
        with patch.object(cube, "evaluated_get") as evaluated_get:
            evaluated_get.return_value = obj_modified
            ret = export.object2mesh(cube, Matrix.Identity(4))
            # Check
            evaluated_get.assert_called_once_with(fake_depsgraph)
        assert ret == cube.mesh_mock
        cube.update_from_editmode.assert_not_called()
        obj_modified.to_mesh.assert_called_once_with()
        cube.mesh_mock.calc_loop_triangles.assert_called_once_with()

    def test_object2mesh_scale(self, export, context, cube):
        # Prepare
        cube.mode = 'EDIT'
        export.target_unit = 'millimeter'
        # Test
        (unit, scale, matrix) = export.compute_scaling()
        ret = export.object2mesh(cube, matrix)
        assert ret == cube.mesh_mock
        # Check that the coordinated have been reduced
        assert unit == 'millimeter'
        assert scale == 1000
        ret.transform.assert_called_once_with(matrix)


class TestExportExecute():
    """ Verifications of full execution """

    def test_execute_exception(self, context_cube):
        # Test, don't define export.filepath
        export = ExportAMF()
        ret = export.execute(context_cube)
        # Check
        assert ret == {'CANCELLED'}

    def test_execute_no_file(self, export):
        # Test
        export.filepath = ""
        ret = export.execute(context_cube)
        # Check
        assert ret == {'CANCELLED'}

    def test_execute(self, export, context_cube):
        # Test
        export.target_unit = 'inch'
        ret = export.execute(context_cube)
        # Check
        assert ret == {'FINISHED'}
        # Check this is a zip archive
        prefix = "test_export_check"
        with tempfile.TemporaryDirectory(prefix=prefix) as extractDir:
            with ZipFile(export.filepath, 'r') as amffile:
                ziplist = amffile.infolist()
                assert len(ziplist) == 1
                zipxml = ziplist[0]
                assert zipxml.is_dir() is False
                xmlFile = amffile.extract(zipxml.filename, extractDir)
                assert os.path.isfile(xmlFile) is True
                try:
                    amf_schema = xmlschema.XMLSchema("test/amf.xsd")
                    amf_schema.validate(xmlFile)
                except Exception:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    print(f"Error exporting AMF file: {exc_value}")
                    traceback.print_tb(exc_traceback, file=sys.stdout)
                    pytest.fail(str(exc_value))
        pass
