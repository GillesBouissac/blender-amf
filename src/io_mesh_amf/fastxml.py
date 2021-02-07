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

# We need a very simple but very fast and low resource xml writer


_DEFAULT_INDENTATION = 4


class _node:

    def __init__(self, fd, doc, name, attrs, indent, level):
        """ Base class for xml elements
        Keyword arguments:
            fd     - output file-like writable object
            doc    - document object
            name   - element name
            attrs  - element attributes {name1:value1, name2:value2 ... }
            indent - if true all children will be output after a CR+level
            level  - current indentation level
        """
        self.fd = fd
        self.doc = doc
        self.name = name
        self.attrs = attrs
        self.indent = indent
        self.level = level
        self.hascontent = False

    def element(self, name, attrs={}):
        """ Element with indentation
            indentation is ignored if doc.pretty==False
        """
        return self._element(name, attrs, True)

    def helement(self, name, attrs={}):
        """ Element with no indentation
            content is never indented even if doc.pretty==True
        """
        return self._element(name, attrs, False)

    def _element(self, name, attrs, indentation):
        if not self.hascontent:
            self.fd.write(">")
        self.hascontent = True
        childlevel = self.level
        if self.doc.pretty and self.indent:
            self.fd.write("\n" + (" " * self.level))
            childlevel += self.doc.indentation
        return _node(self.fd, self.doc, name, attrs, indentation, childlevel)

    def text(self, text):
        """ Element text """
        if not self.hascontent:
            self.fd.write(">")
        self.hascontent = True
        self.fd.write(str(text))

    def __enter__(self):
        self.fd.write(f"<{self.name}")
        for k, v in self.attrs.items():
            self.fd.write(f" {k}=\"{v}\"")
        return self

    def __exit__(self, type, value, traceback):
        if not self.doc.compactempty and not self.hascontent:
            self.fd.write(">")
        if not self.doc.compactempty or self.hascontent:
            if self.doc.pretty and self.indent:
                nspaces = self.level-self.doc.indentation
                self.fd.write("\n" + (" " * nspaces))
            self.fd.write(f"</{self.name}>")
        else:
            self.fd.write("/>")


class _document(_node):
    """ XML document """
    global _DEFAULT_INDENTATION

    def __init__(self, fd, encoding, pretty, compactempty, indentation):
        super().__init__(fd, self, "document", {}, True, 0)
        self.encoding = encoding
        self.pretty = pretty
        self.indentation = indentation
        self.compactempty = compactempty

    def __enter__(self):
        prolog = "<?xml version=\"1.0\" encoding=\"%s\"?>"
        self.fd.write(prolog % self.encoding)
        self.hascontent = True
        return self

    def __exit__(self, type, value, traceback):
        if self.pretty:
            self.fd.write("\n")


def XMLWriter(
    fd,
    encoding="utf-8",
    pretty=True,
    compactempty=True,
    indentation=_DEFAULT_INDENTATION
):
    """ Create a document to write on given file-like fd object
    Keyword arguments:
        fd           - file-like object, only write(text) method is required
        encoding     - xml file encoding, this is the caller responsabily to
                            respect this when creating elements
        pretty       - True for pretty-print output
        compactempty - if True empty elements will be in compact form <name/>
        indentation  - indentation level, default 4
    """
    return _document(fd, encoding, pretty, compactempty, indentation)
