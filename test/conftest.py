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
from io_mesh_amf.export_amf import ExportAMF

#
# Test model parent/child structure
#   vis: visible in viewport
#   vie: viewable in viewports
#   ren: renderable
#
# Mesh objects:
#
#    empty_012               [vis | --- | ---]
#      |
#      o-- empty_0           [vis | vie | ren]
#      |    |
#      |    o-- cube_0       [vis | vie | ---]
#      |
#      o-- empty_12          [vis | vie | ren]
#          |
#          o-- empty_1       [--- | vie | ---]
#          |    |
#          |    o-- cube_1   [--- | vie | ---]
#          |
#          o-- empty_2       [--- | vie | ---]
#               |
#               o-- cube_2   [--- | vie | ren]
#
# Collections:
#
#    coll_0
#      |
#      o-- cube_0
#      o-- cube_2
#
#    coll_1
#      |
#      o-- cube_1
#
# Collections instances:
#
#    inst_0
#      |
#      o-- coll_0
#
#    inst_1
#      |
#      o-- coll_0
#
#    inst_2
#      |
#      o-- coll_1
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


def cube_triangles():
    return [
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


@pytest.fixture
def cube_0():
    """ Visible cube object """
    mesh = Mock()
    mesh.vertices = cube_vertices(0)
    mesh.loop_triangles = cube_triangles()
    obj = Mock()
    obj.name = 'cube_0'
    obj.mode = 'OBJECT'
    obj.mesh_mock = mesh
    obj.to_mesh.return_value = mesh
    obj.matrix_world = Matrix.Identity(4)
    obj.update_from_editmode = Mock()
    obj.evaluated_get = lambda s: s
    obj.visible_get.return_value = True
    obj.hide_viewport = False
    obj.hide_render = True
    obj.children = None
    obj.active_material = None
    obj.location = [0,0,0]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
    obj.is_instancer = False
    return obj


@pytest.fixture
def cube_1():
    """ Viewable cube object shifted to 3 on x """
    mesh = Mock()
    mesh.vertices = cube_vertices(3)
    mesh.loop_triangles = cube_triangles()
    obj = Mock()
    obj.name = 'cube_1'
    obj.mode = 'OBJECT'
    obj.mesh_mock = mesh
    obj.to_mesh.return_value = mesh
    obj.matrix_world = Matrix.Identity(4)
    obj.mesh_mock.vertices = cube_vertices(3)
    obj.update_from_editmode = Mock()
    obj.evaluated_get = lambda s: s
    obj.visible_get.return_value = False
    obj.hide_viewport = False
    obj.hide_render = True
    obj.children = None
    obj.active_material = None
    obj.location = [3,0,0]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
    obj.is_instancer = False
    return obj


@pytest.fixture
def cube_2():
    """ Renderable cube object shifted to -3 on x """
    mesh = Mock()
    mesh.vertices = cube_vertices(-3)
    mesh.loop_triangles = cube_triangles()
    obj = Mock()
    obj.name = 'cube_2'
    obj.mode = 'OBJECT'
    obj.mesh_mock = mesh
    obj.to_mesh.return_value = mesh
    obj.matrix_world = Matrix.Identity(4)
    obj.mesh_mock.vertices = cube_vertices(-3)
    obj.update_from_editmode = Mock()
    obj.evaluated_get = lambda s: s
    obj.visible_get.return_value = False
    obj.hide_viewport = False
    obj.hide_render = False
    obj.children = None
    obj.active_material = None
    obj.location = [-3,0,0]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
    obj.is_instancer = False
    return obj


@pytest.fixture
def coll_0(cube_0, cube_2):
    obj = Mock()
    obj.name = "collection_0"
    obj.all_objects = {
        f"{cube_0.name}": cube_0,
        f"{cube_2.name}": cube_2
    }
    return obj


@pytest.fixture
def coll_1(cube_1):
    obj = Mock()
    obj.name = "collection_1"
    obj.all_objects = {
        f"{cube_1.name}": cube_1
    }
    return obj


@pytest.fixture
def inst_0(coll_0):
    obj = Mock()
    obj.is_instancer = True
    obj.name = "instance_0"
    obj.instance_collection = coll_0
    obj.location = [0,3,0]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
    obj.hide_viewport = False
    return obj


@pytest.fixture
def inst_1(coll_0):
    obj = Mock()
    obj.is_instancer = True
    obj.name = "instance_1"
    obj.instance_collection = coll_0
    obj.location = [0,0,0]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
    obj.hide_viewport = False
    return obj


@pytest.fixture
def inst_2(coll_1):
    obj = Mock()
    obj.is_instancer = True
    obj.name = "instance_2"
    obj.instance_collection = coll_1
    obj.location = [0,-3,0]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
    obj.hide_viewport = False
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
    obj.hide_viewport = False
    obj.hide_render = False
    obj.is_instancer = False
    obj.location = [0,0,-3]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
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
    obj.is_instancer = False
    obj.location = [0,0,-2]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
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
    obj.hide_viewport = False
    obj.hide_render = True
    obj.is_instancer = False
    obj.location = [0,0,-1]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
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
    obj.hide_viewport = False
    obj.hide_render = False
    obj.is_instancer = False
    obj.location = [0,0,0]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
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
    obj.is_instancer = False
    obj.location = [0,0,3]
    obj.rotation_euler = [0,0,0]
    obj.scale = [1,1,1]
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
    exp.use_selection = True
    exp.export_format = 'native'
    exp.use_mesh_modifiers = False
    exp.target_unit = 'meter'
    return exp
