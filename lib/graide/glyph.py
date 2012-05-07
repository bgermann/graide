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


from PySide import QtGui
from graide import freetype
import array, re
from graide.attribview import Attribute, AttribModel
from graide.utils import DataObj
import graide.makegdl.makegdl as gdl

class Glyph(gdl.Glyph, DataObj) :

    def __init__(self, font, name, gid = 0) :
        super(Glyph, self).__init__(name)
        self.gid = gid
        self.properties = {}

    def __str__(self) :
        return self.psname

    def setpixmap(self, face, gid, height = 40) :
        face.set_char_size(height = int(height * 64))
        res = freetype.FT_Load_Glyph(face._FT_Face, gid, freetype.FT_LOAD_RENDER)
        b = face.glyph.bitmap
        self.top = face.glyph.bitmap_top
        self.left = face.glyph.bitmap_left
        if b.rows :
            data = array.array('B', b.buffer)
            mask = QtGui.QImage(data, b.width, b.rows, b.pitch, QtGui.QImage.Format_Indexed8)
            image = QtGui.QImage(b.width, b.rows, QtGui.QImage.Format_Mono)
            image.fill(0)
            image.setAlphaChannel(mask)
            self.pixmap = QtGui.QPixmap(image)
        else :
            self.pixmap = None

    def readAP(self, elem) :
        self.uid = int(elem.get('UID', '0'), 16)
        for p in elem.iterfind('property') :
            n = p.get('name')
            if n.startswith('GDL_') :
                self.gdl_properties[n[4:]] = p.get('value')
            else :
                self.properties[n] = p.get('value')
        for p in elem.iterfind('point') :
            l = p.find('location')
            self.anchors[p.get('type')] = (int(l.get('x', 0)), int(l.get('y', 0)))
        if 'classes' in self.properties :
            self.classes.update(self.properties['classes'].split())
      
    def attribModel(self) :
        res = []
        for a in ['psname', 'gid'] :
            res.append(Attribute(a, self.__getattribute__, None, False, a)) # read-only
        for a in sorted(self.properties.keys()) :
            res.append(Attribute(a, self.getproperty, self.setproperty, False, a))
        for a in sorted(self.gdl_properties.keys()) :
            res.append(Attribute(a, self.getgdlproperty, self.setgdlproperty, False, a))
        pres = []
        for k in self.anchors.keys() :
            pres.append(Attribute(k, self.getpoint, self.setpoint, False, k))
        resAttrib = AttribModel(res)
        pAttrib = AttribModel(pres, resAttrib)
        resAttrib.add(Attribute('points', None, None, True, pAttrib))
        return resAttrib

    def getproperty(self, key) :
        return self.properties[key]

    def setproperty(self, key, value) :
        if value == None :
            del self.properties[key]
        else :
            self.properties[key] = value

    def getgdlproperty(self, key) :
        return self.gdl_properties[key]

    def setgdlproperty(self, key, value) :
        if value == None :
            del self.gdl_properties[key]
        else :
            self.gdl_properties[key] = value

    def getpoint(self, key) :
        return str(self.anchors[key])

    def setpoint(self, key, value) :
        if value == None :
            del self.anchors[key]
        elif value == "" :
            self.anchors[key] = (0, 0)
        else :
            self.anchors[key] = map(int, re.split(r",\s*", value[1:-1]))

