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


def with_obj_names(objs):
    if type(objs) not in (list, Group):
        return objs.name
    obj_list = objs
    if type(objs) is Group:
        obj_list = objs.objects
    res = []
    for obj in obj_list:
        res.append(with_obj_names(obj))
    return res


class Test_build_groups():
    """ Verifications of build_groups method """

    def test_none(self, export, empty_012):
        # Prepare
        export.group_strategy = 'none'
        bpy.data.objects = flatten(empty_012)
        # Test
        groups = export.build_groups(flatten(empty_012))
        # Check
        self._check_groups(groups, [
            ['cube_0'], ['cube_1'],  ['cube_2'],
            ['empty_0'], ['empty_1'], ['empty_2'],
            ['empty_12'], ['empty_012']
        ])

    def test_all(self, export, empty_012):
        # Prepare
        export.group_strategy = 'all'
        bpy.data.objects = flatten(empty_012)
        # Test
        groups = export.build_groups(flatten(empty_012))
        # Check
        self._check_groups(groups, [[
            'cube_0',  'cube_1',  'cube_2',
            'empty_0', 'empty_1', 'empty_2',
            'empty_12', 'empty_012'
        ]])

    def test_parents_selected(self, export, empty_0, empty_12, empty_012):
        # Prepare
        export.group_strategy = 'parents_selected'
        bpy.data.objects = flatten(empty_012)
        # Test
        objs = flatten(empty_0)
        objs.extend(flatten(empty_12))
        groups = export.build_groups(objs)
        # Check
        self._check_groups(groups, [
            ['cube_0', 'empty_0'],
            ['cube_1',  'cube_2', 'empty_1', 'empty_2', 'empty_12']
        ])

    def test_parents_visible(self, export, empty_0, empty_2, empty_012):
        # Prepare
        export.group_strategy = 'parents_visible'
        bpy.data.objects = flatten(empty_012)
        # Test
        objs = flatten(empty_0)
        objs.extend(flatten(empty_2))
        print(f"objs = {with_obj_names(objs)}")
        groups = export.build_groups(objs)
        # Check
        self._check_groups(groups, [
            # In the tree from empty_012 only those are in the selection
            ['empty_0', 'cube_0', 'empty_2', 'cube_2']
        ])

    def test_parents_viewable(self, export, empty_0, empty_1, empty_012):
        # Prepare
        export.group_strategy = 'parents_viewable'
        bpy.data.objects = flatten(empty_012)
        # Test
        objs = flatten(empty_0)
        objs.extend(flatten(empty_1))
        groups = export.build_groups(objs)
        # Check
        self._check_groups(groups, [
            # The first viewable parent is empty_1 making a group
            ['cube_1', 'empty_1'],
            ['cube_0'],
            ['empty_0']
        ])

    def test_parents_renderable(self, export, empty_0, empty_2, empty_012):
        # Prepare
        export.group_strategy = 'parents_renderable'
        bpy.data.objects = flatten(empty_012)
        # Test
        objs = flatten(empty_0)
        objs.extend(flatten(empty_2))
        groups = export.build_groups(objs)
        # Check
        self._check_groups(groups, [
            ['cube_0', 'empty_0'],
            ['cube_2', 'empty_2']
        ])

    def test_parents_any(self, export, empty_0, empty_2, empty_012):
        # Prepare
        export.group_strategy = 'parents_any'
        bpy.data.objects = flatten(empty_012)
        # Test
        objs = flatten(empty_0)
        objs.extend(flatten(empty_2))
        groups = export.build_groups(objs)
        # Check
        self._check_groups(groups, [
            ['cube_0', 'empty_0', 'cube_2', 'empty_2']
        ])

    def test_no_group_from_parent(self, export, empty_2, empty_012):
        # Prepare
        export.group_strategy = 'parents_viewable'
        bpy.data.objects = flatten(empty_012)
        # Test
        objs = flatten(empty_2)
        groups = export.build_groups(objs)
        # Check
        self._check_groups(groups, [
            ['cube_2'],
            ['empty_2']
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
        return len(groupref) == 0

    def _check_groups(self, groups, groupsref):
        groupscheck = with_obj_names(groups)
        print(f"Groups generated: {groupscheck}")
        print(f"Groups expected:  {groupsref}")
        for group in groupscheck:
            if type(group) is not list:
                group = [group]
            found = False
            for groupref in groupsref:
                if self._group_equals(group, groupref):
                    groupsref.remove(groupref)
                    found = True
                    break
            if not found:
                grpstr = with_obj_names(group)
                pytest.fail(f"group {grpstr} not found in {groupsref}")
        if not len(groupsref) == 0:
            pytest.fail(f"ref groups {groupsref} not found in {grpsstr}")


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

    def test_execute_exception(self, context_cube):
        # Test, don't define export.filepath
        export = ExportAMF()
        ret = export.execute(context_cube)
        # Check
        assert ret == {'CANCELLED'}

    def test_execute_no_file(self, export, context_cube):
        # Test
        export.filepath = ""
        ret = export.execute(context_cube)
        # Check
        assert ret == {'CANCELLED'}

    def test_execute_single_object(self, export, context, empty_012):
        # Prepare
        export.export_strategy = "selection"
        export.group_strategy = 'parents_selected'
        context.selected_objects = flatten(empty_012)
        print(f"selected_objects = {flatten(empty_012)}")
        export.target_unit = 'inch'
        # Test
        ret = export.execute(context)
        # Check
        assert ret == {'FINISHED'}
        context.selected_objects[0].to_mesh.assert_called_once_with()
        self.check_archive(export.filepath)

    def test_execute_all_selected_native(self, export, context, empty_012):
        # Prepare
        export.export_strategy = "selection"
        export.group_strategy = 'all'
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

    def test_execute_all_selected_slicer(self, export, context, empty_012):
        # Prepare
        export.export_strategy = "selection"
        export.group_strategy = 'all'
        export.export_format = 'slic3r'
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

        # we had to cheat with schema
        self.check_archive(export.filepath)
