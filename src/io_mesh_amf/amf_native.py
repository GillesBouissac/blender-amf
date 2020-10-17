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
from . amf_util import AMFExport, Group, flatten


class AMFNative(AMFExport):
    """ Export meshes in AMF native format """

    # Map blender unique names to unique id in exported file
    idRegistry = {}
    # Next free id
    idNext = 0

    def export_document(self, xml, context, objects, groups):
        """ Format data in XML file conform to AMF schema """
        self.idRegistry = {}
        self.idNext = 0

        (unit, scale, matrix) = AMFExport.compute_scaling(self.target_unit)
        attrs = {"unit": unit, "version": "1.1"}
        with xml.element("amf", attrs) as root:
            self.export_metadata(root, "name", context.scene.name)
            self.export_metadata(root, "scale", scale)
            self.export_objects(root, objects, matrix)
            self.export_constellations(root, groups)

    def export_objects(self, xml, objs, matrix):
        """ Export objects list """
        wm = bpy.context.window_manager
        wm.progress_begin(0, len(objs)-1)
        for i in range(len(objs)):
            obj = objs[i]
            wm.progress_update(i)
            self.export_object(xml, obj, matrix)
        wm.progress_end()

    def export_object(self, xml, obj, matrix):
        """ Export one object """
        mesh = AMFExport.object2mesh(obj, matrix, self.use_mesh_modifiers)
        if mesh is not None:
            if len(mesh.loop_triangles) > 4:
                with xml.element("object", {"id": self.idNext}) as xobj:
                    self.idRegistry[obj.name] = self.idNext
                    self.idNext += 1
                    self.export_metadata(xobj, "name", obj.name)
                    self.export_mesh(xobj, obj.name, mesh)

    def export_mesh(self, xml, name, mesh):
        """ Export one mesh """
        with xml.element("mesh") as xmesh:
            self.export_vertices(xmesh, mesh.vertices)
            self.export_volume(xmesh, mesh.loop_triangles)

    def export_constellations(self, xml, groups):
        """ Export objects groups """
        for group in groups:
            group = Group(
                group.name,
                [obj for obj in group.objects if obj.name in self.idRegistry])
            if len(group.objects) > 0:
                with xml.element("constellation", {"id": self.idNext}) as xco:
                    self.idNext += 1
                    for obj in group.objects:
                        attrs = {"objectid": self.idRegistry[obj.name]}
                        with xco.element("instance", attrs) as xin:
                            with xin.helement("deltax") as xd:
                                xd.text("0.0")
                            with xin.helement("deltay") as xd:
                                xd.text("0.0")
                            with xin.helement("deltaz") as xd:
                                xd.text("0.0")
                            with xin.helement("rx") as xd:
                                xd.text("0.0")
                            with xin.helement("ry") as xd:
                                xd.text("0.0")
                            with xin.helement("rz") as xd:
                                xd.text("0.0")
