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
from zipfile import ZipFile, ZIP_DEFLATED
from tempfile import gettempdir

from . fastxml import XMLWriter
from . amf_util import AMFExport, Group, flatten
from . amf_native import AMFNative
from . amf_slic3r import AMFSlic3r


class ExportAMF(Operator, ExportHelper):
    """ Export meshes in AMF file """
    # Blender mandatory attributes
    bl_idname = "export_mesh.amf"
    bl_label = "Export AMF"
    bl_description = "Export objects to Additive Manufacturing file Format"
    filename_ext = ".amf"
    prepared = {}
    unit = "meter"
    scale = 1
    matrix = Matrix.Identity(4)

    # Conversions from Blender units (meter) to AMF units
    UNIT_CONVERSION = {
        'meter': 1,
        'millimeter': 1e3,
        'micron': 1e6,
        'inch': 39.37008,
        'feet': 3.28084,
    }

    # Blender optional attributes
    filter_glob:   StringProperty(default="*.amf", options={'HIDDEN'})
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
    export_format: EnumProperty(
        name="Export format",
        items=(
            ("native", "AMF Native",
                """ Closest as possible to AMF format """),
            ("slic3r", "AMF Silc3r",
                """ AMF compatible with Silc3r """),
        ),
        default="slic3r",
    )
    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=True,
    )

    def __init__(self):
        super().__init__()

    def execute(self, context):
        """ Do the export when user validates form """
        try:
            # target file has been set in self.filepath by blender before call
            if self.filepath is None or self.filepath == "":
                return {'CANCELLED'}

            # Prepare unit scaling matrix
            self.compute_scaling()

            # prepare objects for export
            objects = map(self.prepare_object, self.select_objects(context))
            objects = list(filter(lambda o: o is not None, objects))
            amfobjs = self.build_amfobjs(objects)

            for k in amfobjs:
                amfobj = amfobjs[k]
                print ( f"amfobjs = {k}")

            # Open the target XML
            basename = os.path.basename(self.filepath)
            noext = os.path.splitext(basename)[0]
            tempName = f"{gettempdir()}/{noext}.xml"

            if self.export_format == "native":
                export_svc = AMFNative()
            elif self.export_format == "slic3r":
                export_svc = AMFSlic3r()
            export_svc.target_unit = self.target_unit
            export_svc.use_mesh_modifiers = self.use_mesh_modifiers
            export_svc.unit = self.unit
            export_svc.scale = self.scale

            with open(tempName, "w") as fd:
                with XMLWriter(fd, 'utf-8') as xml:
                    # Delegate XML writing to specific formaters
                    export_svc.export_document(xml, context, amfobjs, objects)

            # Put result in zip archive for final result
            with ZipFile(self.filepath, 'w', ZIP_DEFLATED) as amffile:
                amffile.write(tempName, arcname=f"{basename}")

            os.remove(tempName)

        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"Error exporting AMF file: {exc_value}")
            traceback.print_tb(exc_traceback, file=sys.stdout)
            return {'CANCELLED'}

        return {'FINISHED'}

    def select_objects(self, context):
        objs = None
        if self.use_selection:
            objs = context.selected_objects
        else:
            objs = context.scene.objects
        return list(objs)

    def build_amfobjs(self, objs):
        """ Computes groups of blender objects """
        amfobjs = {}
        collections = {}
        for obj in objs:
            blendobj = obj["object"]
            if blendobj.is_instancer:
                coll = blendobj.instance_collection
                if not hasattr(collections, coll.name):
                    new_coll = map(self.prepare_object, coll.all_objects.values())
                    new_coll = list(filter(lambda o: o is not None, new_coll))
                    collections[coll.name] = True
                    amfobjs[coll.name] = Group(coll.name, new_coll, coll)
                    print ( f"add {coll.name}")
            else:
                amfobjs[blendobj.name] = Group(blendobj.name, [obj], blendobj)
                print ( f"add {blendobj.name}")
        return amfobjs
 
    def prepare_object(self, obj):
        """ Convert blender object to exportable mesh """

        if hasattr(self.prepared, obj.name):
            return self.prepared[obj.name]

        if obj.hide_viewport:
            return None

        if obj.is_instancer:
            return {"object": obj, "mesh": None}

        # Apply edited changes to the object
        if obj.mode == 'EDIT':
            obj.update_from_editmode()

        # Apply modifiers as specified
        depsgraph = None
        if self.use_mesh_modifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj = obj.evaluated_get(depsgraph)

        # Convert object to mesh
        mesh = None
        try:
            mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        finally:
            if mesh is None:
                return None

        # Mesh tesselation because AMF can only store triangles
        mesh.calc_loop_triangles()
        if len(mesh.loop_triangles) < 4:
            return None

        mat = self.matrix @ obj.matrix_world
        mesh.transform(mat)
        result = {"object": obj, "mesh": mesh}
        self.prepared[obj.name] = result
        return result

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
        self.unit = 'meter'
        self.scale = 1
        if self.target_unit in self.UNIT_CONVERSION:
            self.unit = self.target_unit
            self.scale = self.UNIT_CONVERSION[self.unit]
        self.matrix = Matrix.Scale(self.scale, 4)
