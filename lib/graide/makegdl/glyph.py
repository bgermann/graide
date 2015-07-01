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

import re, traceback
from graide.makegdl.psnames import Name
from xml.etree.cElementTree import SubElement

# Convert from Graphite AP name to the standard name, eg upperM -> _upper
def gr_ap(txt) :
    if txt.endswith('M') :
        return "_" + txt[:-1]
    elif txt.endswith('S') :
        return txt[:-1]
    else :
        return txt

# Convert from standard AP name to the Graphite name, eg _upper -> upperM
def ap_gr(txt) :
    if txt.startswith('_') :
        return txt[1:] + 'M'
    else :
        return txt + 'S'


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
        self.gdlProperties = {}
        self.userProperties = {}
        self.properties = {}
        self.collisionProps = {}
        self.sequenceProps = {}
        self.octaboxProps = {}

    def setName(self, name) :
        self.psname = name
        self.name = next(self.parseNames())

    def setAnchor(self, name, x, y, t = None) :
        send = True
        if name in self.anchors :
            if x is None and y is None :
                del self.anchors[name]
                return True
            if x is None : x = self.anchors[name][0]
            if y is None : y = self.anchors[name][1]
            send = self.anchors[name] != (x, y)
        self.anchors[name] = (x, y)
        return send
        # if not name.startswith("_") and t != 'basemark' :
        #     self.isBase = True
        
    def setCollisionProp(self, name, value) :
        self.collisionProps[name] = value
        
    def setSequenceProp(self, name, value) :
        self.sequenceProps[name] = value
        
    def setOctaboxProp(self, name, value) :
        self.octaboxProps[name] = value

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
                self.gdlProperties[n[4:]] = p.get('value')
            else :
                self.properties[n] = p.get('value')
        for p in elem.iterfind('point') :
            l = p.find('location')
            self.setAnchor(ap_gr(p.get('type')), int(l.get('x', 0)), int(l.get('y', 0)))
        p = elem.find('note')
        if p is not None and p.text :
            self.comment = p.text
        if 'classes' in self.properties :
            for c in self.properties['classes'].split() :
                if c not in self.classes :
                    self.classes.add(c)
                    font.addGlyphClass(c, self.gid, editable = True)

    def createAP(self, elem, font, autoGdlFile) :
        e = SubElement(elem, 'glyph')
        if self.psname : e.set('PSName', self.psname)
        if self.uid : e.set('UID', self.uid)
        if self.gid is not None : e.set('GID', str(self.gid))
        ce = None
        if 'classes' in self.properties and self.properties['classes'].strip() :
            tempClasses = self.properties['classes']
            self.properties['classes'] = " ".join(font.filterAutoClasses(self.properties['classes'].split(), autoGdlFile))
            
        for k in sorted(self.anchors.keys()) :
            v = self.anchors[k]
            p = SubElement(e, 'point')
            p.set('type', gr_ap(k))
            p.text = "\n        "
            l = SubElement(p, 'location')
            l.set('x', str(v[0]))
            l.set('y', str(v[1]))
            l.tail = "\n    "
            if ce is not None : ce.tail = "\n    "
            ce = p
            
        for k in sorted(self.gdlProperties.keys()) :
            if k == "*skipPasses*" : continue  # not set in GDL
                
            v = self.gdlProperties[k]
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
            
        for k in sorted(self.properties.keys()) :
            v = self.properties[k]
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
    if re.match(r'^\*GC\d+\*$', name) : return True   # auto-pseudo glyph with name = *GCXXXX*
    return False
