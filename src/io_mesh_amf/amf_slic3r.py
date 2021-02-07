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
import math
from . amf_util import AMFExport, Group, flatten


class AMFSlic3r(AMFExport):
    """ Export meshes in AMF slic3r format """

    # Map blender unique names to unique id in exported file
    idRegistry = {}
    # Next free id
    nextId = 0
    # Material giving extruder number from material unique name
    materialRegistry = {}
    # Next extruder number
    nextExtruder = 1
    unit = "meter"
    scale = 1

    def export_document(self, xml, context, amfobjs, constellations):
        """ Format data in XML file conform to AMF schema """
        self.idRegistry = {}
        self.nextId = 0

        attrs = {"unit": self.unit, "version": "1.1"}
        with xml.element("amf", attrs) as root:
            self.export_metadata(root, "name", context.scene.name)
            self.export_metadata(root, "scale", self.scale)
            self.export_objects(root, amfobjs)
            self.export_constellations(root, constellations)

    def export_objects(self, xml, amfobjs):
        """ Export objects list, one per group """
        wm = bpy.context.window_manager
        wm.progress_begin(0, len(amfobjs)-1)
        values = list(amfobjs.values())
        for i in range(len(values)):
            amfobj = values[i]
            wm.progress_update(i)
            self.export_object(xml, amfobj)
        wm.progress_end()

    def export_object(self, xml, amfobj):
        """ Export one object """
        for obj in amfobj.objects:
            material = obj['object'].active_material
            if material is not None:
                if material.name not in self.materialRegistry:
                    extruder = 1
                    if "extruder" in material.keys():
                        extruder = math.floor(material.get("extruder"))
                    else:
                        extruder = self.nextExtruder
                        self.nextExtruder += 1
                    self.materialRegistry[material.name] = extruder
        if len(amfobj.objects)>0:
            with xml.element("object", {"id": self.nextId}) as xobj:
                self.idRegistry[amfobj.name] = self.nextId
                self.nextId += 1
                self.export_metadata(xobj, "name", amfobj.name)
                self.export_meshes(xobj, amfobj.objects)

    def export_meshes(self, xml, objects):
        """ Export one group of meshes """
        with xml.element("mesh") as xmesh:
            # Mesh made from multiple volumes
            #   ie one list of vertices for multiple volumes
            # Not allowed by amf schema but most implementations do this
            vertices = []
            next_idx = 0
            for obj in objects:
                mesh = obj["mesh"]
                vertices.extend(mesh.vertices)
            self.export_vertices(xmesh, vertices)
            for obj in objects:
                mesh = obj["mesh"]
                obj = obj["object"]
                metadata = {
                    "name": obj.name,
                    "slic3r.source_offset_x": 100,
                    "slic3r.source_offset_y": 100,
                    "slic3r.source_offset_z": 0
                }
                material = obj.active_material
                if material is not None:
                    metadata["slic3r.extruder"] = self.materialRegistry[material.name]
                self.export_volume(
                    xmesh,
                    mesh.loop_triangles,
                    metadata,
                    next_idx)
                next_idx += len(mesh.vertices)

    def export_constellations(self, xml, constellations):
        """ Export constellations """
        for constellation in constellations:
            blendobj = constellation["object"]
            instances = []
            if blendobj.is_instancer:
                coll = blendobj.instance_collection
                if coll.name in self.idRegistry:
                    instances.append(coll)
            else:
                if blendobj.name in self.idRegistry:
                    instances = [blendobj]
            if len(instances)>0:
                with xml.element("constellation", {"id": self.nextId}) as xco:
                    self.nextId += 1
                    for instance in instances:
                        attrs = {"objectid": self.idRegistry[instance.name]}
                        with xco.element("instance", attrs) as xin:
                            with xin.helement("deltax") as xd:
                                xd.text(str(blendobj.location[0]))
                            with xin.helement("deltay") as xd:
                                xd.text(str(blendobj.location[1]))
                            with xin.helement("deltaz") as xd:
                                xd.text(str(blendobj.location[2]))
                            with xin.helement("rx") as xd:
                                xd.text(str(blendobj.rotation_euler[0]))
                            with xin.helement("ry") as xd:
                                xd.text(str(blendobj.rotation_euler[1]))
                            with xin.helement("rz") as xd:
                                xd.text(str(blendobj.rotation_euler[2]))
