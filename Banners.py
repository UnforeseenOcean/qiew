from cemu import *
from PyQt4 import QtGui, QtCore

import os, sys, inspect

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], "pefile")))
yapsy_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], "yapsy")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
    sys.path.insert(0, yapsy_subfolder)    

import pefile
from TextDecorators import *
import yapsy

class Banner(object):
    def getOrientation(self):
        NotImplementedError('method not implemented.')

    def getDesiredGeometry(self):
        NotImplementedError('method not implemented.')


Orientation = enum(Left=0, Bottom=1)

class Banners:
    def __init__(self):
        self._Banners = []
        self.separatorBottom = 5
        self.separatorLeft = 5

    def add(self, banner):
        self._Banners.append(banner)

    def getLeftOffset(self):
        offset = 0
        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Left:
                offset += banner.getDesiredGeometry()
                offset += self.separatorLeft

        return offset

    def getBottomOffset(self):
        offset = 0
        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Bottom:
                offset += banner.getDesiredGeometry()
                offset += self.separatorBottom

        return offset

    def resize(self, width, height):
        limit = self.getBottomOffset()
        for banner in self._Banners:
            # banners are not resizeable actually
            if banner.getOrientation() == Orientation.Left:
                banner.resize(banner.getDesiredGeometry(), height - limit)

            if banner.getOrientation() == Orientation.Bottom:
                banner.resize(width, banner.getDesiredGeometry())

    def setViewMode(self, viewMode):
        for banner in self._Banners:
            banner.setViewMode(viewMode)

    def draw(self, qp, offsetLeft, offsetBottom, maxY):
        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Left:
                banner.draw()
                qp.drawPixmap(offsetLeft, offsetBottom, banner.getPixmap())
                offsetLeft += banner.getDesiredGeometry() + self.separatorLeft

        # initial offset + all offsets from all banners. We are doing this because Y growns down
        offsetBottom = maxY - self.getBottomOffset()

        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Bottom:
                banner.draw()
                qp.drawPixmap(offsetLeft, offsetBottom, banner.getPixmap())
                offsetBottom += banner.getDesiredGeometry() + self.separatorBottom




class FileAddrBanner(Banner):
    def __init__(self, dataModel, viewMode):
        self.width = 0
        self.height = 0
        self.dataModel = dataModel
        self.viewMode = viewMode
        self.qpix = self._getNewPixmap(self.width, self.height)
        self.backgroundBrush = QtGui.QBrush(QtGui.QColor(0, 0, 128))        
        

        # text font
        self.font = QtGui.QFont('Terminus', 11, QtGui.QFont.Light)

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self.fontWidth  = fm.width('a')
        self.fontHeight = fm.height()

        self.textPen = QtGui.QPen(QtGui.QColor(192, 192, 192), 0, QtCore.Qt.SolidLine)

    def getOrientation(self):
        return Orientation.Left

    def getDesiredGeometry(self):
        return 75

    def setViewMode(self, viewMode):
        self.viewMode = viewMode

    def getPixmap(self):
        return self.qpix

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def draw(self):
        qp = QtGui.QPainter()

        offset = self.viewMode.getPageOffset()
        columns, rows = self.viewMode.getGeometry()

        qp.begin(self.qpix)
        qp.fillRect(0, 0, self.width,  self.height, self.backgroundBrush)
        qp.setPen(self.textPen)
        qp.setFont(self.font)
        
        for i in range(rows):
            s = '{0:08x}'.format(offset)
            qp.drawText(0+5, (i+1) * self.fontHeight, s)
            offset += columns
        

        qp.end()

    def resize(self, width, height):
        self.width = width
        self.height = height

        self.qpix = self._getNewPixmap(self.width, self.height)
        


class BottomBanner(Banner):
    def __init__(self, dataModel, viewMode):
        self.width = 0
        self.height = 0
        self.dataModel = dataModel
        self.viewMode = viewMode

        self.qpix = self._getNewPixmap(self.width, self.height)
        self.backgroundBrush = QtGui.QBrush(QtGui.QColor(0, 0, 128))        
        

        # text font
        self.font = QtGui.QFont('Consolas', 11, QtGui.QFont.Light)

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self.fontWidth  = fm.width('a')
        self.fontHeight = fm.height()

        self.textPen = QtGui.QPen(QtGui.QColor(255, 255, 0), 0, QtCore.Qt.SolidLine)

    def getOrientation(self):
        return Orientation.Bottom

    def getDesiredGeometry(self):
        return 50

    def setViewMode(self, viewMode):
        self.viewMode = viewMode

    def draw(self):
        qp = QtGui.QPainter()
        qp.begin(self.qpix)

        qp.fillRect(0, 0, self.width,  self.height, self.backgroundBrush)
        qp.setPen(self.textPen)
        qp.setFont(self.font)

        cemu = ConsoleEmulator(qp, self.height/self.fontHeight, self.width/self.fontWidth)

        dword = self.dataModel.getDWORD(self.viewMode.getCursorAbsolutePosition(), asString=True)
        sd = 'DWORD: {0}'.format(dword)

        pos = 'POS: {0:08x}'.format(self.viewMode.getCursorAbsolutePosition())



        qword = self.dataModel.getQWORD(self.viewMode.getCursorAbsolutePosition(), asString=True)
        sq = 'QWORD: {0}'.format(qword)

        byte = self.dataModel.getBYTE(self.viewMode.getCursorAbsolutePosition(), asString=True)
        sb = 'BYTE: {0}'.format(byte)

        cemu.writeAt(1,  0, pos)
        cemu.writeAt(17, 0, sd)
        cemu.writeAt(35, 0, sq)
        cemu.writeAt(62, 0, sb)

        qp.drawLine(120, 0, 120, 50)
        qp.drawLine(270, 0, 270, 50)
        qp.drawLine(480, 0, 480, 50)
        qp.drawLine(570, 0, 570, 50)
        """
        # position
        qp.drawText(0 + 5, self.fontHeight, pos)
        # separator
        qp.drawLine(120, 0, 120, 50)

        # dword
        qp.drawText(130 + 5, self.fontHeight, sd)
        # separator
        qp.drawLine(270, 0, 270, 50)

        # qword
        qp.drawText(280 + 5, self.fontHeight, sq)
        # separator
        qp.drawLine(480, 0, 480, 50)

        # byte
        qp.drawText(490 + 5, self.fontHeight, sb)
        # separator
        qp.drawLine(570, 0, 570, 50)
        """
        
        qp.end()

        pass
    def getPixmap(self):
        return self.qpix

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.qpix = self._getNewPixmap(self.width, self.height)