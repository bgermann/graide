
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

from PySide import QtCore, QtGui
from graide.utils import configval, configintval
import os

class FileEntry(QtGui.QWidget) :

    textChanged = QtCore.Signal(str)

    def __init__(self, parent, val, pattern) :
        super(FileEntry, self).__init__(parent)
        self.pattern = pattern
        self.hb = QtGui.QHBoxLayout(self)
        self.hb.setContentsMargins(0, 0, 0, 0)
        self.hb.setSpacing(0)
        self.le = QtGui.QLineEdit(self)
        self.le.textChanged.connect(self.txtChanged)
        if val :
            self.le.setText(val)
        self.hb.addWidget(self.le)
        self.b = QtGui.QToolButton(self)
        self.b.setIcon(QtGui.QIcon.fromTheme("document-open"))
        self.hb.addWidget(self.b)
        self.b.clicked.connect(self.bClicked)

    def bClicked(self) :
        (fname, filt) = QtGui.QFileDialog.getSaveFileName(self,
                dir=os.path.dirname(self.le.text()), filter=self.pattern,
                options=QtGui.QFileDialog.DontConfirmOverwrite)
        self.le.setText(os.path.relpath(fname) if fname else "")

    def text(self) :
        return self.le.text()

    def setText(self, txt) :
        self.le.setText(txt)

    def txtChanged(self, txt) :
        self.textChanged.emit(txt)

class PassSpin(QtGui.QSpinBox) :

    def __init__(self, parent = None) :
        super(PassSpin, self).__init__(parent)
        self.setMinimum(0)
        self.setSpecialValueText('None')
        self.setValue(-1)


class ConfigDialog(QtGui.QDialog) :

    def __init__(self, config, parent = None) :
        super(ConfigDialog, self).__init__(parent)
        self.config = config

        self.vb = QtGui.QVBoxLayout(self)
        self.tb = QtGui.QToolBox(self)
        self.vb.addWidget(self.tb)
        self.ok = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.ok.accepted.connect(self.accept)
        self.ok.rejected.connect(self.reject)
        self.vb.addWidget(self.ok)

        self.main = QtGui.QWidget(self.tb)
        self.main_vb = QtGui.QGridLayout(self.main)
#        self.main_vb.setVerticalSpacing(0)
        self.main_font = FileEntry(self.main, configval(config, 'main', 'font'), 'Font Files (*.ttf)')
        self.main_vb.addWidget(QtGui.QLabel('Font File:'), 0, 0)
        self.main_vb.addWidget(self.main_font, 0, 1, 1, 2)
        self.main_gdl = FileEntry(self.main, configval(config, 'build', 'gdlfile'), 'GDL Files (*.gdl)')
        self.main_vb.addWidget(QtGui.QLabel('GDL File:'), 1, 0)
        self.main_vb.addWidget(self.main_gdl, 1, 1, 1, 2)
        self.main_tests = FileEntry(self.main, configval(config, 'main', 'testsfile'), 'Tests Lists (*.xml)')
        self.main_vb.addWidget(QtGui.QLabel('Tests File:'), 2, 0)
        self.main_vb.addWidget(self.main_tests, 2, 1, 1, 2)
        self.main_rtl = QtGui.QCheckBox()
        self.main_rtl.setChecked(configintval(config, 'main', 'defaultrtl'))
        self.main_vb.addWidget(QtGui.QLabel('Default RTL'), 3, 0)
        self.main_vb.addWidget(self.main_rtl, 3, 1)
        self.main_vb.setRowStretch(4, 1)
        self.tb.addItem(self.main, "General")

        self.build = QtGui.QWidget(self.tb)
        self.build_vb = QtGui.QGridLayout(self.build)
        self.build_ap = FileEntry(self.main, configval(config, 'main', 'ap'), 'AP Files (*.xml)')
        self.build_ap.textChanged.connect(self.apChanged)
        self.build_vb.addWidget(QtGui.QLabel('Attachment Point Database:'), 0, 0, 1, 2)
        self.build_vb.addWidget(self.build_ap, 0, 2)
        self.build_inmake = QtGui.QWidget(self.build)
        self.build_vb.addWidget(self.build_inmake, 1, 0, 1, 3)
        self.build_invb = QtGui.QGridLayout(self.build_inmake)
        self.build_cmd = QtGui.QLineEdit(self.build_inmake)
        self.build_cmd.setText(configval(config, 'build', 'makegdlcmd'))
        self.build_cmd.setToolTip('External make gdl command: %a=AP Database, %f=Font File, %g=Generated GDL File,\n    %i=included GDL file %p=positioning pass number')
        self.build_invb.addWidget(QtGui.QLabel('Make GDL Command:'), 0, 0)
        self.build_invb.addWidget(self.build_cmd, 0, 1, 1, 2)
        self.build_inc = FileEntry(self.build_inmake, configval(config, 'build', 'makegdlfile'), 'GDL Files (*.gdl)')
        self.build_invb.addWidget(QtGui.QLabel('Autogenerated GDL file:'), 1, 0)
        self.build_invb.addWidget(self.build_inc, 1, 1, 1, 2)
        self.build_pos = PassSpin(self.build_inmake)
        self.build_invb.addWidget(QtGui.QLabel('Automatic positioning pass:'), 2, 0, 1, 2)
        self.build_invb.addWidget(self.build_pos, 2, 2)
        self.build_vb.setRowStretch(3, 1)
        if not self.build_ap.text() :
            self.build_inmake.setEnabled(False)
        self.tb.addItem(self.build, 'Build')

        self.ui = QtGui.QWidget(self.tb)
        self.ui_vb = QtGui.QGridLayout(self.ui)
        self.ui_size = QtGui.QSpinBox(self.ui)
        self.ui_size.setRange(1, 36)
        if config.has_option('ui', 'textsize') :
            self.ui_size.setValue(configintval(config, 'ui', 'textsize'))
        else :
            self.ui_size.setValue(10)
        self.ui_vb.addWidget(QtGui.QLabel('Editor text point size'), 0, 0)
        self.ui_vb.addWidget(self.ui_size, 0, 1)
        self.ui_gsize = QtGui.QSpinBox(self.ui)
        self.ui_gsize.setRange(1, 288)
        if config.has_option('main', 'size') :
            self.ui_gsize.setValue(configintval(config, 'main', 'size'))
        else :
            self.ui_gsize.setValue(40)
        self.ui_vb.addWidget(QtGui.QLabel('Font Glyph pixel size'), 1, 0)
        self.ui_vb.addWidget(self.ui_gsize, 1, 1)
        self.ui_vb.setRowStretch(2, 1)
        self.tb.addItem(self.ui, 'User Interface')

        self.resize(500, 500)

    def apChanged(self, txt) :
        self.build_inmake.setEnabled(True if txt else False)
        if txt and not self.build_inc.text() :
            fname = (self.main_font.text() or configval(self.config, 'main', 'font'))[0:-3] + "gdl"
            count = 0
            nname = fname
            while os.path.exists(nname) :
                nname = fname[:-4] + "_makegdl"
                if count : nname += "_" + str(count)
                nname += ".gdl"
            self.build_inc.setText(nname)

    def updateConfig(self, app, config) :
        self.updateChanged(self.main_font, config, 'main', 'font', app.loadFont)
        self.updateChanged(self.main_gdl, config, 'build', 'gdlfile', app.selectLine)
        self.updateChanged(self.main_tests, config, 'main', 'testsfile', app.loadTests)
        if self.main_rtl.isChecked != configval(config, 'main', 'defaultrtl') :
            config.set('main', 'defaultrtl', "1" if self.main_rtl.isChecked() else "0")
        self.updateChanged(self.build_ap, config, 'main', 'ap', app.loadAP)
        if self.build_ap.text() :
            config.set('build', 'usemakegdl', "1")
            self.updateChanged(self.build_inc, config, 'build', 'makegdlfile')
            config.set('build', 'pospass', str(self.build_pos.value()))
            txt = self.build_cmd.text()
            if txt :
                config.set('build', 'makegdlcmd', txt)
            elif config.has_option('build', 'makegdlcmd') :
                config.remove_option('build', 'makegdlcmd')
        else :
            config.set('build', 'usemakegdl', '0')
        if self.ui_size.value() != configintval(config, 'ui', 'textsize') :
            config.set('ui', 'textsize', str(self.ui_size.value()))
            app.tabEdit.setSize(self.ui_size.value())
        if self.ui_gsize.value() != configintval(config, 'main', 'size') :
            config.set('main', 'size', str(self.ui_gsize.value()))
            app.loadFont(configval(config, 'main', 'font'))

    def updateChanged(self, widget, config, section, option, fn = None) :
        t = widget.text()
        if t != configval(config, section, option) and (t or configval(config, section, option)) :
            if not t :
                config.remove_option(section, option)
            else :
                config.set(section, option, t)
            if fn :
                fn(t)

