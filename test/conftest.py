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

import pytest
import tempfile
import fakebpy
import bpy
from mathutils import Matrix
from unittest.mock import Mock
from io_mesh_amf import ExportAMF

#
# Test model parent/child structure
#   vis: visible in viewport
#   vie: viewable in viewports
#   ren: renderable
#
# empty_012                 [vis | --- | ---]
#     |
#     o-- empty_0           [vis | --- | ren]
#     |    |
#     |    o-- cube_0       [vis | --- | ---]
#     |
#     o-- empty_12          [vis | --- | ren]
#         |
#         o-- empty_1       [--- | vie | ---]
#         |    |
#         |    o-- cube_1   [--- | vie | ---]
#         |
#         o-- empty_2       [--- | --- | ---]
#              |
#              o-- cube_2   [--- | --- | ren]
#


class vertex():
    co = []

    def __init__(self, x, y, z):
        self.co = [x, y, z]


class triangle():
    vertices = []

    def __init__(self, v1, v2, v3):
        self.vertices = [v1, v2, v3]


def cube_vertices(x=1):
    return [
        vertex(x+0, 0, 0),
        vertex(x+1, 0, 0),
        vertex(x+1, 1, 0),
        vertex(x+0, 1, 0),
        vertex(x+0, 1, 1),
        vertex(x+1, 1, 1),
        vertex(x+1, 0, 1),
        vertex(x+0, 0, 1)
    ]


@pytest.fixture
def cube_mesh():
    """ cube mesh """
    mesh = Mock()
    mesh.vertices = cube_vertices()
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
def cube_0(cube_mesh):
    """ Visible cube object """
    obj = Mock()
    obj.name = 'cube_0'
    obj.mode = 'OBJECT'
    obj.mesh_mock = cube_mesh
    obj.to_mesh.return_value = cube_mesh
    obj.matrix_world = Matrix.Identity(4)
    obj.update_from_editmode = Mock()
    obj.evaluated_get = lambda s: s
    obj.visible_get.return_value = True
    obj.hide_viewport = True
    obj.hide_render = True
    obj.children = None
    return obj


@pytest.fixture
def cube_1(cube_mesh):
    """ Viewable cube object shifted to 3 on x """
    obj = Mock()
    obj.name = 'cube_1'
    obj.mode = 'OBJECT'
    obj.mesh_mock = cube_mesh
    obj.to_mesh.return_value = cube_mesh
    obj.matrix_world = Matrix.Identity(4)
    obj.mesh_mock.vertices = cube_vertices(3)
    obj.update_from_editmode = Mock()
    obj.evaluated_get = lambda s: s
    obj.visible_get.return_value = False
    obj.hide_viewport = False
    obj.hide_render = True
    obj.children = None
    return obj


@pytest.fixture
def cube_2(cube_mesh):
    """ Renderable cube object shifted to -3 on x """
    obj = Mock()
    obj.name = 'cube_2'
    obj.mode = 'OBJECT'
    obj.mesh_mock = cube_mesh
    obj.to_mesh.return_value = cube_mesh
    obj.matrix_world = Matrix.Identity(4)
    obj.mesh_mock.vertices = cube_vertices(-3)
    obj.update_from_editmode = Mock()
    obj.evaluated_get = lambda s: s
    obj.visible_get.return_value = False
    obj.hide_viewport = True
    obj.hide_render = False
    obj.children = None
    return obj


@pytest.fixture
def __empty_0():
    """ Empty used as parent of cube_0 """
    obj = Mock()
    obj.name = 'empty_0'
    obj.mode = 'OBJECT'
    obj.to_mesh.return_value = None
    obj.matrix_world = Matrix.Identity(4)
    obj.visible_get.return_value = True
    obj.hide_viewport = True
    obj.hide_render = False
    return obj


@pytest.fixture
def __empty_1():
    """ Empty used as parent of cube_1 """
    obj = Mock()
    obj.name = 'empty_1'
    obj.mode = 'OBJECT'
    obj.to_mesh.return_value = None
    obj.matrix_world = Matrix.Identity(4)
    obj.visible_get.return_value = False
    obj.hide_viewport = False
    obj.hide_render = True
    return obj


@pytest.fixture
def __empty_2():
    """ Empty used as parent of cube_2 """
    obj = Mock()
    obj.name = 'empty_2'
    obj.mode = 'OBJECT'
    obj.to_mesh.return_value = None
    obj.matrix_world = Matrix.Identity(4)
    obj.visible_get.return_value = False
    obj.hide_viewport = True
    obj.hide_render = True
    return obj


@pytest.fixture
def __empty_12():
    """ Empty used as parent of __empty_1 and __empty_2 """
    obj = Mock()
    obj.name = 'empty_12'
    obj.mode = 'OBJECT'
    obj.to_mesh.return_value = None
    obj.matrix_world = Matrix.Identity(4)
    obj.visible_get.return_value = True
    obj.hide_viewport = True
    obj.hide_render = False
    return obj


@pytest.fixture
def __empty_012():
    """ Empty used as parent of __empty_0, __empty_1 and __empty_2 """
    obj = Mock()
    obj.name = 'empty_012'
    obj.mode = 'OBJECT'
    obj.to_mesh.return_value = None
    obj.matrix_world = Matrix.Identity(4)
    obj.visible_get.return_value = True
    obj.hide_viewport = True
    obj.hide_render = True
    return obj


@pytest.fixture
def empty_0(cube_0, __empty_0):
    __empty_0.children = (cube_0)  # Blender children are tuples
    cube_0.parent = __empty_0
    return __empty_0


@pytest.fixture
def empty_1(cube_1, __empty_1):
    __empty_1.children = (cube_1)  # Blender children are tuples
    cube_1.parent = __empty_1
    return __empty_1


@pytest.fixture
def empty_2(cube_2, __empty_2):
    __empty_2.children = (cube_2)  # Blender children are tuples
    cube_2.parent = __empty_2
    return __empty_2


@pytest.fixture
def empty_12(__empty_12, empty_1, empty_2):
    __empty_12.children = (empty_1, empty_2)  # Blender children are tuples
    empty_1.parent = __empty_12
    empty_2.parent = __empty_12
    return __empty_12


@pytest.fixture
def empty_012(__empty_012, empty_0, empty_12):
    __empty_012.parent = None
    __empty_012.children = (empty_0, empty_12)  # Blender children are tuples
    empty_0.parent = __empty_012
    empty_12.parent = __empty_012
    return __empty_012


@pytest.fixture
def context():
    """ empty context """
    context = Mock()
    context.scene.name = "Nom de scene pour test"
    return context


@pytest.fixture
def context_cube(context, cube_0):
    """ context with cube object """
    context.selected_objects = [cube_0]
    return context


@pytest.fixture
def export():
    """ Export object to test with all default properties """
    tempName = f"{tempfile.gettempdir()}/test_export.amf"
    exp = ExportAMF()
    exp.filepath = tempName
    exp.export_strategy = "selection"
    exp.export_format = 'native'
    exp.group_strategy = 'parents_selected'
    exp.use_mesh_modifiers = False
    exp.target_unit = 'meter'
    return exp
