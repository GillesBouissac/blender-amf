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


class AMFSlic3r(AMFExport):
    """ Export meshes in AMF slic3r format """

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
            self.export_groups_as_object(root, groups, matrix)
            self.export_constellations(root, groups)

    def export_groups_as_object(self, xml, groups, matrix):
        """ Export objects list, one per group """
        wm = bpy.context.window_manager
        wm.progress_begin(0, len(groups)-1)
        for i in range(len(groups)):
            group = groups[i]
            wm.progress_update(i)
            self.export_group_as_object(xml, group, matrix)
        wm.progress_end()

    def export_group_as_object(self, xml, group, matrix):
        """ Export one object """
        meshedobj = []
        meshes = []
        for obj in group.objects:
            mesh = AMFExport.object2mesh(obj, matrix, self.use_mesh_modifiers)
            if mesh is not None and len(mesh.loop_triangles) > 4:
                meshes.append(mesh)
                meshedobj.append(obj)

        with xml.element("object", {"id": self.idNext}) as xobj:
            self.idRegistry[group.name] = self.idNext
            self.idNext += 1
            self.export_metadata(xobj, "name", group.name)
            self.export_meshes(xobj, meshes, meshedobj)

    def export_meshes(self, xml, meshes, objs):
        """ Export one group of meshes """
        with xml.element("mesh") as xmesh:
            # Here is the cheating: Slicer uses multiple
            #   Volume elements in object element
            # The AMF Schema does not allow this
            # They merge multiple objects in one
            group_vertices = []
            meshes_idx = []
            next_idx = 0
            for mesh in meshes:
                group_vertices.extend(mesh.vertices)
                meshes_idx.append(next_idx)
                next_idx += len(mesh.vertices)
            self.export_vertices(xmesh, group_vertices)
            for i in range(len(meshes)):
                mesh = meshes[i]
                obj = objs[i]
                self.export_volume(
                    xmesh,
                    mesh.loop_triangles,
                    [{"name": "name", "value": obj.name}],
                    meshes_idx[i])

    def export_constellations(self, xml, groups):
        """ Export objects groups """
        for group in groups:
            with xml.element("constellation", {"id": self.idNext}) as xco:
                self.idNext += 1
                attrs = {"objectid": self.idRegistry[group.name]}
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
