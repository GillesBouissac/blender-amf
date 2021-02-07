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
import fakebpy
import tempfile
import pytest
import xmlschema
import traceback
import bpy
from unittest.mock import Mock
from zipfile import ZipFile

from io_mesh_amf import ExportAMF
from io_mesh_amf.amf_util import AMFExport, Group, flatten


def with_obj_names(groups):
    res = {}
    for key in groups:
        children = []
        for child in groups[key].objects:
            children.append(child["object"].name)
        res[key] = children
    return res


class Test_select_objects():
    """ Verifications of select_objects method """

    def test_selection_only(self, export, context, empty_0, empty_012):
        # Prepare
        objs_selected = flatten(empty_0)
        objs_scene = flatten(empty_012)
        context.selected_objects = objs_selected
        context.scene.objects = objs_scene
        # Test
        export.use_selection = True
        objects = export.select_objects(context)
        # Check
        assert objects == objs_selected

    def test_all(self, export, context, empty_0, empty_012):
        # Prepare
        objs_selected = flatten(empty_0)
        objs_scene = flatten(empty_012)
        context.selected_objects = objs_selected
        context.scene.objects = objs_scene
        # Test
        export.use_selection = False
        objects = export.select_objects(context)
        # Check
        assert objects == objs_scene


class Test_build_amfobjs():
    """ Verifications of build_amfobjs method """

    def test_only_meshs(self, export, empty_012):
        # Test
        blendobjs = flatten(empty_012)
        groups = export.build_amfobjs(map(lambda o:{"object":o},blendobjs))
        # Check
        self._check_groups(groups, {
            'cube_0':['cube_0'],
            'cube_1':['cube_1'],
            'cube_2':['cube_2'],
            'empty_0':['empty_0'],
            'empty_1':['empty_1'],
            'empty_2':['empty_2'],
            'empty_12':['empty_12'],
            'empty_012':['empty_012']
        })

    def test_only_instances(self, export, cube_1, inst_2):
        # Test
        blendobjs = [inst_2]
        groups = export.build_amfobjs(map(lambda o:{"object":o},blendobjs))
        # Check
        self._check_groups(groups, [
            {'collection_1':['cube_1']}
        ])

    def test_all(self, export, cube_0, inst_0, inst_1, inst_2):
        # Test
        blendobjs = [cube_0, inst_0, inst_1, inst_2]
        groups = export.build_amfobjs(map(lambda o:{"object":o},blendobjs))
        # Check
        self._check_groups(groups, [
            {'cube_0':['cube_0']},
            {'collection_0':['cube_0', 'cube_2']},
            {'collection_1':['cube_1']}
        ])

    def _group_equals(self, group, groupref):
        for obj in group:
            found = False
            for objref in groupref:
                if obj == objref:
                    groupref.remove(objref)
                    found = True
                    break
            if not found:
                return False
        if len(groupref) != 0:
            return False
        return True

    def _check_groups(self, groups, groupsref):
        groupscheck = with_obj_names(groups)
        # print(f"Groups generated: {groupscheck}")
        # print(f"Groups expected:  {groupsref}")
        for key in groupscheck:
            found = False
            if key not in groupsref:
                return False
            if not self._group_equals(groupscheck[key], groupsref[key]):
                pytest.fail(f"group to check {groupscheck[key]} not equal to {groupsref[key]}")
            groupsref.pop(key)
        if not len(groupsref) == 0:
            pytest.fail(f"ref groups {groupsref} not found in {groupscheck}")


class Test_execute():
    """ Verifications of full execution """

    def check_archive(self, filepath):
        """ Check filepath is a valid amf archive """
        prefix = "test_export_check"
        with tempfile.TemporaryDirectory(prefix=prefix) as extractDir:
            with ZipFile(filepath, 'r') as amffile:
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

    def _test_execute_exception(self, context_cube):
        # Test, don't define export.filepath
        export = ExportAMF()
        ret = export.execute(context_cube)
        # Check
        assert ret == {'CANCELLED'}

    def _test_execute_no_file(self, export, context_cube):
        # Test
        export.filepath = ""
        ret = export.execute(context_cube)
        # Check
        assert ret == {'CANCELLED'}

    def _test_execute_single_object(self, export, context, empty_012):
        # Prepare
        context.selected_objects = flatten(empty_012)
        export.export_format = 'slic3r'
        export.target_unit = 'inch'
        # Test
        ret = export.execute(context)
        # Check
        assert ret == {'FINISHED'}
        for obj in context.selected_objects:
            if not obj.hide_viewport:
                obj.to_mesh.assert_called_once_with()
        self.check_archive(export.filepath)

    def ______no_test_execute_all_selected_native(self, export, context, empty_012):
        # Prepare
        export.export_format = 'native'
        context.selected_objects = flatten(empty_012)
        # Test
        ret = export.execute(context)
        # Check
        assert ret == {'FINISHED'}
        for obj in context.selected_objects:
            obj.to_mesh.assert_called()
            if "cube" in obj.name:
                obj.mesh_mock.calc_loop_triangles.assert_called()
            else:
                obj.mesh_mock.calc_loop_triangles.assert_not_called()

        self.check_archive(export.filepath)

    def test_execute_all_selected_slicer(self, export, context, empty_012, inst_0, inst_1, inst_2):
        # Prepare
        export.export_format = 'slic3r'
        selected_meshes = flatten(empty_012)
        context.selected_objects = selected_meshes + [inst_0, inst_1, inst_2]
        # Test
        ret = export.execute(context)
        # Check
        assert ret == {'FINISHED'}
        for obj in selected_meshes:
            if not obj.hide_viewport:
                obj.to_mesh.assert_called()
                if "cube" in obj.name:
                    obj.mesh_mock.calc_loop_triangles.assert_called()
                else:
                    obj.mesh_mock.calc_loop_triangles.assert_not_called()
        for obj in [inst_0, inst_1, inst_2]:
                obj.mesh_mock.calc_loop_triangles.assert_not_called()

        # we had to cheat with schema
        self.check_archive(export.filepath)
