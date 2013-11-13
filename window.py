import shutil
import tempfile
import itertools
from pdfminer.layout import *
from PyQt4 import QtCore, QtGui
from write import EPDFWrite
from read import EPDFRead

class EPDFWindow:
  def __init__(self, args):
    self.app = QtGui.QApplication(args)

  def __enter__(self):
    self.tmp = tempfile.mkdtemp()
    return self

  def __exit__(self, type, value, traceback):
    shutil.rmtree(self.tmp, True)

  def show(self):
    w = QtGui.QMainWindow()
    w.resize(800, 600)
    w.setWindowTitle('CS3141 PDF Editor')
    self.gfx = QtGui.QGraphicsScene(w)
    self.gfxview = QtGui.QGraphicsView(self.gfx, w)
    w.addToolBar(self.buildToolbar(w))
    self.gfxview.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.cyan))
    w.setCentralWidget(self.gfxview)
    w.showMaximized()
    return self.app.exec_()

  def buildToolbar(self, w):
    toolbar = QtGui.QToolBar(w)
    toolbar.addAction('Open', lambda: self.actionOpen(w))
    toolbar.addAction('Save', lambda: self.actionSave(w))
    return toolbar

  def actionOpen(self, w):
    filename = QtGui.QFileDialog.getOpenFileName(w, 'Open PDF', '.', '*.pdf')
    if len(filename) > 0:
      self.gfx.clear()
      self.drawPages(EPDFRead(filename, self.tmp))
      self.gfxview.centerOn(0, 0)

  def actionSave(self, w):
    filename = QtGui.QFileDialog.getSaveFileName(w, 'Save PDF', '.', '*.pdf')
    if len(filename) > 0:
      EPDFWrite(filename, self.document.childItems(), self.tmp, self.fonts)

  def drawPages(self, pdf):
    top = 0
    self.fonts = pdf.fonts
    self.document = self.gfx.createItemGroup([])
    b = QtGui.QBrush(QtCore.Qt.white)
    p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), 1)
    p.setCosmetic(True)
    for page in pdf.pages:
      pg = self.gfx.addRect(0, top, page.width, page.height, p, b)
      pg.setParentItem(self.document)
      top += page.height
      self.drawObjects(pdf, pg, page._objs, top)

  def drawObjects(self, pdf, pg, objs, y):
    for obj in objs: 
      if isinstance(obj, LTRect):
        b = QtGui.QBrush()
        p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), obj.linewidth)
        rect = self.gfx.addRect(obj.x0, y - obj.y1, obj.width, obj.height, p, b)
        rect.setParentItem(pg)
      elif isinstance(obj, LTLine):
        p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), obj.linewidth)
        [(x1, y1), (x2, y2)] = obj.pts
        line = self.gfx.addLine(x1, y - y1, x2, y - y2, p)
        line.setParentItem(pg)
      #elif isinstance(obj, LTCurve):
      elif isinstance(obj, LTTextBox) or isinstance(obj, LTTextLine):
        if isinstance(obj, LTTextLine):
          texts = pdf.buildText([obj], y, obj.x0)
        else:
          texts = pdf.buildText(obj._objs, y, obj.x0)
        txt = self.gfx.addText('')
        txt.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        txt.setHtml(unicode().join(texts))
        txt.setDefaultTextColor(QtCore.Qt.black)
        txt.setPos(obj.x0, y - obj.y1)
        txt.setParentItem(pg)
      elif isinstance(obj, LTImage):
        img = QtGui.QImage()
        img.loadFromData(obj.stream.rawdata)
        pix = QtGui.QPixmap()
        pix.convertFromImage(img)
        pixmap = self.gfx.addPixmap(pix)
        pixmap.setOffset(obj.x0, y - obj.y1)
        pixmap.setParentItem(pg)
      elif isinstance(obj, LTFigure):
        self.drawObjects(pdf, pg, obj._objs, y)
      else: print('Unsupported PDF object: ' + str(type(obj)))
