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

import bpy
from mathutils import Matrix


def flatten(parent):
    return __flatten(parent, [])


class AMFExport():
    """ AMF export service base class """

    # Conversions from Blender units (meter) to AMF units
    UNIT_CONVERSION = {
        'meter': 1,
        'millimeter': 1e3,
        'micron': 1e6,
        'inch': 39.37008,
        'feet': 3.28084,
    }

    def export_document(self, xml, context, objects, groups):
        """ Format data in XML file conform to target format """
        # This service method is supposed to be overloaded

    def export_metadata(self, xml, name, value):
        """ Export a single metadata from an obj attribute """
        value = str(value)
        with xml.helement("metadata", {"type": name}) as xmeta:
            xmeta.text(value)

    def export_vertices(self, xml, vertices):
        """ Export one list of vertices """
        with xml.element("vertices") as xvs:
            for vertex in vertices:
                with xvs.helement("vertex") as xv:
                    with xv.helement("coordinates") as xc:
                        with xc.helement("x") as xx:
                            xx.text(str(vertex.co[0]))
                        with xc.helement("y") as xy:
                            xy.text(str(vertex.co[1]))
                        with xc.helement("z") as xz:
                            xz.text(str(vertex.co[2]))

    def export_volume(self, xml, triangles, metadata=[], vertex_id_offset=0):
        """ Export one list of vertices """
        with xml.element("volume") as xvo:
            for meta in metadata:
                self.export_metadata(xvo, meta["name"], meta["value"])
            with xvo.helement("color") as xcol:
                with xcol.helement("r") as xr:
                    xr.text("1")
                with xcol.helement("g") as xr:
                    xr.text("0")
                with xcol.helement("b") as xr:
                    xr.text("0")
            for triangle in triangles:
                with xvo.helement("triangle") as xt:
                    with xt.helement("v1") as xv:
                        xv.text(triangle.vertices[0]+vertex_id_offset)
                    with xt.helement("v2") as xv:
                        xv.text(triangle.vertices[1]+vertex_id_offset)
                    with xt.helement("v3") as xv:
                        xv.text(triangle.vertices[2]+vertex_id_offset)

    @staticmethod
    def object2mesh(obj, matrix, use_mesh_modifiers=True):
        """ Convert blender object to exportable mesh """

        # Apply edited changes to the object
        if obj.mode == 'EDIT':
            obj.update_from_editmode()

        # Apply modifiers as specified
        if use_mesh_modifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj = obj.evaluated_get(depsgraph)

        # Convert object to mesh
        mesh = None
        try:
            mesh = obj.to_mesh()
        finally:
            if mesh is None:
                return None

        # Mesh tesselation because AMF can only store triangles
        mesh.calc_loop_triangles()

        mat = matrix @ obj.matrix_world
        mesh.transform(mat)
        return mesh

    @classmethod
    def compute_scaling(cls, target_unit):
        """ Select the better unit from blender to AMF
        Blender internal locations are stored in meters but
            we want the result to be close to what the user sees
        Then compute the scale from blender coordinates to this unit
        Returns the tuple (target_unit, scale_needed, matrix)
            target_unit:  The recomputed target unit
            scale_needed: False if the scaling matrix is identity
            matrix:       Transformation Matrix to be applied to objects
        """
        unit = 'meter'
        scale = 1
        if target_unit in cls.UNIT_CONVERSION:
            unit = target_unit
            scale = cls.UNIT_CONVERSION[unit]
        return (unit, scale, Matrix.Scale(scale, 4))


class Group:
    name = ""
    objects = []

    def __init__(self, name, objects=[]):
        self.name = name
        self.objects = objects

    def append(self, obj):
        self.objects.append(obj)

    def extend(self, obj):
        self.objects.extend(obj)


def __flatten(parent, visited):
    """ Return a flat list of all tree objects """
    objs = []
    if type(parent) in (list, tuple):
        for obj in parent:
            objs.extend(__flatten(obj, visited))
    elif parent is not None:
        if parent not in visited:
            visited.append(parent)
            objs.append(parent)
            if hasattr(parent, 'children') and parent.children is not None:
                objs.extend(__flatten(parent.children, visited))
    return objs
