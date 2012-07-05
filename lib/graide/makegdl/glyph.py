#    Copyright 2012, SIL International
#    All rights reserved.
#
#    This library is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation; either version 2.1 of License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should also have received a copy of the GNU Lesser General Public
#    License along with this library in the file named "LICENSE".
#    If not, write to the Free Software Foundation, 51 Franklin Street,
#    suite 500, Boston, MA 02110-1335, USA or visit their web page on the 
#    internet at http://www.fsf.org/licenses/lgpl.html.

import re
from graide.makegdl.psnames import Name
from xml.etree.cElementTree import SubElement

class Glyph(object) :

    def __init__(self, name, gid = 0) :
        self.clear()
        self.setName(name)
        self.gdl = None
        self.gid = gid
        self.uid = ""     # this is a string!
        self.comment = ""

    def clear(self) :
        self.anchors = {}
        self.classes = set()
        self.gdl_properties = {}
        self.properties = {}

    def setName(self, name) :
        self.psname = name
        self.name = next(self.parseNames())

    def addAnchor(self, name, x, y, t = None) :
        self.anchors[name] = (x, y)
        # if not name.startswith("_") and t != 'basemark' :
        #     self.isBase = True

    def parseNames(self) :
        if self.psname :
            for name in self.psname.split("/") :
                res = Name(name)
                yield res
        else :
            yield None

    def GDLName(self) :
        if self.gdl :
            return self.gdl
        elif self.name :
            return self.name.GDL()
        else :
            return None

    def setGDL(self, name) :
        self.gdl = name

    def readAP(self, elem, font) :
        self.uid = elem.get('UID', None)
        for p in elem.iterfind('property') :
            n = p.get('name')
            if n == 'GDLName' :
                self.setGDL(p.get('value'))
            elif n.startswith('GDL_') :
                self.gdl_properties[n[4:]] = p.get('value')
            else :
                self.properties[n] = p.get('value')
        for p in elem.iterfind('point') :
            l = p.find('location')
            self.anchors[p.get('type')] = (int(l.get('x', 0)), int(l.get('y', 0)))
        p = elem.find('note')
        if p is not None and p.text :
            self.comment = p.text
        if 'classes' in self.properties :
            for c in self.properties['classes'].split() :
                if c not in self.classes :
                    self.classes.add(c)
                    font.addGlyphClass(c, self.gid, editable = True)

    def createAP(self, elem, font, apgdlfile) :
        e = SubElement(elem, 'glyph')
        if self.psname : e.set('PSName', self.psname)
        if self.uid : e.set('UID', self.uid)
        if self.gid is not None : e.set('GID', str(self.gid))
        ce = None
        if 'classes' in self.properties and self.properties['classes'].strip() :
            tempClasses = self.properties['classes']
            self.properties['classes'] = " ".join(font.filterAutoClasses(self.properties['classes'].split(), apgdlfile))
        for (k, v) in self.anchors.items() :
            p = SubElement(e, 'point')
            p.set('type', k)
            p.text = "\n        "
            l = SubElement(p, 'location')
            l.set('x', str(v[0]))
            l.set('y', str(v[1]))
            l.tail = "\n    "
            if ce is not None : ce.tail = "\n    "
            ce = p
        for (k, v) in self.gdl_properties.items() :
            if v :
                p = SubElement(e, 'property')
                p.set('name', 'GDL_' + k)
                p.set('value', v)
                if ce is not None : ce.tail = "\n    "
                ce = p
        if self.gdl and (not self.name or self.gdl != self.name.GDL()) :
            p = SubElement(e, 'property')
            p.set('name', 'GDLName')
            p.set('value', self.GDLName())
            if ce is not None : ce.tail = "\n    "
            ce = p
        for (k, v) in self.properties.items() :
            if v :
                p = SubElement(e, 'property')
                p.set('name', k)
                p.set('value', v)
                if ce is not None : ce.tail = "\n    "
                ce = p
        if self.comment :
            p = SubElement(e, 'note')
            p.text = self.comment
            if ce is not None : ce.tail = "\n    "
            ce = p
        if 'classes' in self.properties and self.properties['classes'].strip() :
            self.properties['classes'] = tempClasses
        if ce is not None :
            ce.tail = "\n"
            e.text = "\n    "
        e.tail = "\n"
        return e
      
def isMakeGDLSpecialClass(name) :
#    if re.match(r'^cn?(Takes)?.*?Dia$', name) : return True
#    if name.startswith('clig') : return True
#    if name.startswith('cno_') : return True
    if re.match(r'^\*GC\d+\*$', name) : return True
    return False