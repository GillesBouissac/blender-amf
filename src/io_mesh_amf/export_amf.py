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
        default="native",
    )
    export_strategy: EnumProperty(
        name="Export strategy",
        items=(
            ("selection", "Selection only",
                """ Only selected object are exported """),
            ("visible", "Visible objects",
                """ Every object visible in the viewport are exported """),
            ("viewable", "Viewable objects",
                """ Every viewable object are exported """),
            ("renderable", "renderable objects",
                """ Every renderable object are exported """),
        ),
        default="selection",
    )
    group_strategy: EnumProperty(
        name="Grouping strategy",
        items=(
            ("parents_any", "Common parent",
                """ Groups are defined from topmost parents
                All parents in file are used """),
            ("parents_visible", "Common visible parent",
                """ Groups from all parents visible in the viewport """),
            ("parents_viewable", "Common viewable parent",
                """ Groups from all parents viewable in viewports """),
            ("parents_renderable", "Common renderable parent",
                """ Groups from all parents renderable in the file """),
            ("parents_selected", "Common exported parent",
                """ Groups from all parent selected for this export """),
            ('all', "One group with all objects",
                "All exported objects are in a single group"),
            ('none', "No group",
                "Exported objects are not gouped"),
        ),
        default="parents_any"
    )

    def __init__(self):
        super().__init__()

    def execute(self, context):
        """ Do the export when user validates form """
        try:
            # target file has been set in self.filepath by blender before call
            if self.filepath is None or self.filepath == "":
                return {'CANCELLED'}

            # prepare objects for export
            objects = self.select_objects(context)
            groups = self.build_groups(objects)

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

            with open(tempName, "w") as fd:
                with XMLWriter(fd, 'utf-8') as xml:
                    # Delegate XML writing to specific formaters
                    export_svc.export_document(xml, context, objects, groups)

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
        if self.export_strategy == "selection":
            objs = context.selected_objects
        else:
            objs = context.scene.objects
            if self.export_strategy == "visible":
                objs = filter(lambda o: o.visible_get(), objs)
            elif self.export_strategy == "viewable":
                objs = filter(lambda o: not o.hide_viewport, objs)
            elif self.export_strategy == "renderable":
                objs = filter(lambda o: not o.hide_render, objs)
        return list(objs)

    def tree_to_group(self, root, selecto, visited):
        """ Build groups from a tree root """
        group = Group(root.name, [])
        for obj in flatten(root):
            if hasattr(obj, "name"):
                visited.append(obj)
                if selecto(obj):
                    group.append(obj)
        return group

    def parents_to_groups(self, selecto, selectp):
        """ Browse parents untill we find those selectable to make group """
        groups = []
        visited = []
        # Each loop take into account a non visited obj with:
        #   no parent or already visited parent
        while len(visited) < len(bpy.data.objects):
            for obj in bpy.data.objects:
                isParentDone = True
                if hasattr(obj, "parent") and obj.parent is not None:
                    if obj.parent not in visited:
                        isParentDone = False
                if obj not in visited and isParentDone:
                    if selectp(obj):
                        subgroup = self.tree_to_group(obj, selecto, visited)
                        if len(subgroup.objects) > 0:
                            groups.append(subgroup)
                    elif selecto(obj):
                        visited.append(obj)
                        groups.append(Group(obj.name, [obj]))
                    else:
                        visited.append(obj)
        return groups

    def build_groups(self, objs):
        """ Computes groups according parent grouping strategy """
        groups = []
        if self.group_strategy == "parents_any":
            return self.parents_to_groups(
                lambda o: o in objs,
                lambda o: True)
        elif self.group_strategy == "parents_visible":
            return self.parents_to_groups(
                lambda o: o in objs,
                lambda o: o.visible_get())
        elif self.group_strategy == "parents_viewable":
            return self.parents_to_groups(
                lambda o: o in objs,
                lambda o: not o.hide_viewport)
        elif self.group_strategy == "parents_renderable":
            return self.parents_to_groups(
                lambda o: o in objs,
                lambda o: not o.hide_render)
        elif self.group_strategy == "parents_selected":
            return self.parents_to_groups(
                lambda o: o in objs,
                lambda o: o in objs)
        elif self.group_strategy == "all":
            return [Group("all", objs)]
        return [Group(o.name, [o]) for o in objs]
