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
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# <pep8 compliant>

import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType

_MOCK_PACKAGES = {}
_PACKAGE_TYPES = {}

class EmptyClass:
    """
        Empty class that can be used as a replacement
        Its attributes can be mocked afterwards
    """
    pass
def fakePackage(packages_list):
    """
        Declare a package or a list of packages even if it doesn't really exist
        Every package in the hierarchy will be replaced unless they are already loaded for real
    """
    if type(packages_list) is list: 
        _fakeHierarchy ( packages_list )
    else:
        _fakeHierarchy ( [ packages_list ] )

def fakeType ( types ):
    """
        Declare a type and its parent packages even if they don't really exist
        Each type name is associated with a type replacement (ex: {"a.b.c.MyClass", EmptyClass} )
    """
    global _PACKAGE_TYPES
    for k,v in types.items():
        packages = k.split('.')
        name = packages.pop()
        package = '.'.join(packages)
        if not package in _PACKAGE_TYPES:
            _PACKAGE_TYPES[package] = {}
        fakePackage (package)
        _PACKAGE_TYPES[package][name] = v


class _FakeModuleLoader(MetaPathFinder):
    """
        The module loader that will make ppl think modules declared with fakeType or fakePackage really exists
    """
    def find_spec(self, fullname, path=None, target=None):
        # print ( "find_spec: %s" % (fullname) )
        global _MOCK_PACKAGES
        if fullname in _MOCK_PACKAGES.keys():
            spec = ModuleSpec(name=fullname, loader=self, origin="mock package")
            spec.submodule_search_locations = ""
            return spec
        return None

    def create_module(self, spec):
        # print ( "create_module: %s" % (spec.name) )
        mod = ModuleType(spec.name)
        mod.__package__ = mod.__name__
        mod.__loader__ = self
        mod.__spec__ = spec
        return mod

    def exec_module(self, module):
        global _PACKAGE_TYPES
        fullname = module.__name__
        package = fullname
        # print ( "exec_module: %s" % (package) )
        # Record child types
        if package in _PACKAGE_TYPES:
            names = _PACKAGE_TYPES[package]
            for k,v in names.items():
                module.__dict__[k] = v
        # for k,v in module.__dict__.items():
        #     print ( "    - %s: %s" % (k,v) )

def _fakeHierarchy ( packages_list ):
    """
        Utility function to record a fake package hierarchy
    """
    global _MOCK_PACKAGES
    for package_elem in packages_list:
        packages = package_elem.split('.')
        path = ""
        for package in packages:
            parent = path
            if parent in _MOCK_PACKAGES:
                _MOCK_PACKAGES[parent].append(package)
            path = path + ("" if path=="" else ".") + package
            if not path in _MOCK_PACKAGES:
                _MOCK_PACKAGES[path] = []

# Record our fake loader
sys.meta_path.append(_FakeModuleLoader())


