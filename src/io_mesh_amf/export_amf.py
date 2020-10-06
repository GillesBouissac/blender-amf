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
import traceback
import bpy
from mathutils import Matrix
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty, FloatProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper
from zipfile import ZipFile
from tempfile import NamedTemporaryFile, gettempdir
from .fastxml import XMLWriter


# Conversions from Blender units (meter) to AMF units
_UNIT_CONVERSION = {
    'meter': 1,
    'millimeter': 1e3,
    'micron': 1e6,
    'inch': 39.37008,
    'feet': 3.28084,
}


class ExportAMF(Operator, ExportHelper):
    """ Export meshes in AMF file """
    # Blender mandatory attributes
    bl_idname = "export_mesh.amf"
    bl_label = "Export AMF"
    bl_description = "Export objects to Additive Manufacturing file Format"
    filename_ext = ".amf"

    # Blender optional attributes
    filter_glob:   StringProperty(default="*.amf", options={'HIDDEN'})
    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=True,
    )
    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply Modifiers to the exported mesh",
        default=True,
    )
    target_unit: EnumProperty(
        name="Unit",
        items=(
            ("meter",      "Meter",      "Export coordinates in meters"),
            ('millimeter', "Millimeter", "Export coordinates in millimeters"),
            ('micron',     "Micron",     "Export coordinates in micrometers"),
            ('inch',       "Inch",       "Export coordinates in inches"),
            ('feet',       "Feet",       "Export coordinates in feets"),
        ),
        default="meter"
    )
    group_strategy: EnumProperty(
        name="Grouping strategy",
        items=(
            ("parents", "Parents",
                "Each exported parent root and its children are grouped"),
            ('all', "All",
                "All exported objects are in a single group"),
            ('none', "None",
                "Exported objects are not gouped"),
        ),
        default="parents"
    )

    def __init__(self):
        super().__init__()

    def execute(self, context):
        """ Do the export when user validates form """
        try:
            # target file has been set in self.filepath by blender before call
            if self.filepath is None or self.filepath == "":
                return {'CANCELLED'}

            basename = os.path.basename(self.filepath)
            noext = os.path.splitext(basename)[0]
            tempName = f"{gettempdir()}/{noext}.xml"

            with open(tempName, "w") as fd:
                self.export_document(fd, context)

            # Put result in zip archive for final result
            with ZipFile(self.filepath, 'w') as amffile:
                amffile.write(tempName, arcname=f"{basename}")

            os.remove(tempName)

        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"Error exporting AMF file: {exc_value}")
            traceback.print_tb(exc_traceback, file=sys.stdout)
            return {'CANCELLED'}

        return {'FINISHED'}

    def export_document(self, fd, context):
        """ Format data in XML file conform to AMF schema """
        if self.use_selection:
            blender_objects = context.selected_objects
        else:
            blender_objects = context.scene.objects

        (target_unit, scale, matrix) = self.compute_scaling()
        with XMLWriter(fd, 'utf-8') as xml:
            attrs = {"unit": target_unit, "version": "1.1"}
            with xml.element("amf", attrs) as root:
                self.export_metadata(root, context.scene, "name")
                self.export_metadata(root, scale, "scale")
                self.export_objects(root, blender_objects, matrix)
                self.export_constellations(root, blender_objects)

    def object2mesh(self, obj, matrix):
        """ Convert blender object to exportable mesh """

        # Apply edited changes to the object
        if obj.mode == 'EDIT':
            obj.update_from_editmode()

        # Apply modifiers as specified
        if self.use_mesh_modifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj = obj.evaluated_get(depsgraph)

        # Convert object to mesh
        mesh = None
        try:
            mesh = obj.to_mesh()
        finally:
            if mesh is None:
                print(f"Object {obj.name} is not exportable as mesh")
                return None

        # Mesh tesselation because AMF can only store triangles
        mesh.calc_loop_triangles()

        mat = matrix @ obj.matrix_world
        mesh.transform(mat)
        return mesh

    def export_metadata(self, xml, obj, attr):
        """ Export a single metadata from an obj attribute """
        value = ""
        if hasattr(obj, attr):
            value = str(getattr(obj, attr, ''))
        else:
            value = str(obj)
        with xml.helement("metadata", {"type": attr}) as xmeta:
            xmeta.text(value)

    def export_objects(self, xml, objs, matrix):
        """ Export objects list """
        for obj in objs:
            self.export_object(xml, obj, matrix)

    def export_object(self, xml, obj, matrix):
        """ Export one object """
        mesh = self.object2mesh(obj, matrix)
        if mesh is not None:
            with xml.element("object", {"id": 0}) as xobj:
                self.export_metadata(xobj, obj, "name")
                self.export_mesh(xobj, mesh)

    def export_mesh(self, xml, mesh):
        """ Export one mesh """
        with xml.element("mesh") as xmesh:
            self.export_vertices(xmesh, mesh.vertices)
            self.export_volume(xmesh, mesh.loop_triangles)

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

    def export_volume(self, xml, triangles):
        """ Export one list of vertices """
        with xml.element("volume") as xvo:
            for triangle in triangles:
                with xvo.helement("triangle") as xt:
                    with xt.helement("v1") as xv:
                        xv.text(triangle.vertices[0])
                    with xt.helement("v2") as xv:
                        xv.text(triangle.vertices[1])
                    with xt.helement("v3") as xv:
                        xv.text(triangle.vertices[2])

    def export_constellations(self, fd, objs):
        """ Export objects groups as specified in self.group_strategy """
        if self.group_strategy == "parents":
            return
        elif self.group_strategy == "all":
            return
        else:
            return
        for obj in objs:
            pass

    def compute_scaling(self):
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
        if self.target_unit in _UNIT_CONVERSION:
            unit = self.target_unit
            scale = _UNIT_CONVERSION[unit]
        return (unit, scale, Matrix.Scale(scale, 4))
