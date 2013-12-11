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
    w.setWindowIcon(QtGui.QIcon('icons/edit.png'))
    self.gfx = QtGui.QGraphicsScene(w)
    self.gfxview = QtGui.QGraphicsView(self.gfx, w)
    self.buildMenubar(w)
    self.buildToolbar(w)
    self.gfxview.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.gray))
    undoStack = QtGui.QUndoStack()
    w.setCentralWidget(self.gfxview)
    w.showMaximized()
    return self.app.exec_()

  def buildMenubar(self, w):
    menubar = w.menuBar()
    self.buildMenubarFile(w, menubar)
    self.buildMenubarHelp(w, menubar)

  def buildMenubarFile(self, w, menubar):
    fileMenu = menubar.addMenu('&File')
    openFile = QtGui.QAction(QtGui.QIcon('icons/open.png'), '&Open', w)
    openFile.setShortcut('Ctrl+O')
    openFile.setStatusTip('Open a PDF Document')
    openFile.triggered.connect(lambda: self.actionOpen(w))
    saveFile = QtGui.QAction(QtGui.QIcon('icons/save.png'), '&Save', w)
    saveFile.setShortcut('Ctrl+S')
    saveFile.setStatusTip('Save this PDF Document')
    saveFile.triggered.connect(lambda: self.actionSave(w))
    exitProgram = QtGui.QAction(QtGui.QIcon('icons/exit.png'), '&Exit', w)
    exitProgram.setStatusTip('Exit the Program')
    exitProgram.triggered.connect(QtGui.qApp.quit)
    fileMenu.addAction(openFile)
    fileMenu.addAction(saveFile)
    fileMenu.addAction(exitProgram)

  def buildMenubarHelp(self, w, menubar):
    helpMenu = menubar.addMenu('&Help')
    instructions = QtGui.QAction(QtGui.QIcon('icons/help'), '&Instructions', w)
    instructions.setStatusTip('View the Instruction Manual')
    #instructions.triggered.connect(instructionAction)
    about = QtGui.QAction(QtGui.QIcon('icons/info'), '&About', w)
    about.setStatusTip('About this Program')
    #about.triggered.connect(aboutAction)
    helpMenu.addAction(instructions)
    helpMenu.addAction(about)

  def buildToolbar(self, w):
    toolbar = w.addToolBar('Toolbar')
    toolbar.addAction('Add Image', lambda: self.addImage(w))
    toolbar.addAction('Add Text', lambda: self.addText(w))

  def actionOpen(self, w):
    filename = QtGui.QFileDialog.getOpenFileName(w, 'Open PDF', '.', '*.pdf')
    if len(filename) > 0:
      self.gfx.clear()
      self.drawPages(EPDFRead(filename, self.tmp))
      self.gfxview.setSceneRect(self.gfx.itemsBoundingRect())
      self.gfxview.centerOn(0, 0)

  def actionSave(self, w):
    filename = QtGui.QFileDialog.getSaveFileName(w, 'Save PDF', '.', '*.pdf')
    if len(filename) > 0:
      if filename[-4:] != ".PDF" or filename[-4:] != ".pdf":
        filename = filename + ".pdf"
        EPDFWrite(filename, self.document.childItems(), self.gfxview, self.gfx)

  def addImage(self, w):
    filename = QtGui.QFileDialog.getOpenFileName(w, 'Open Image', '.', '*.png')
    if len(filename) > 0:
      image = self.gfx.addPixmap(QtGui.QPixmap(filename))
      image.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
      image.setZValue(2)
      
  def addText(self, w):
    text = self.gfx.addText('Enter Text Here')
    text.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
    text.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
    text.setDefaultTextColor(QtCore.Qt.black)
    text.setZValue(3)

  def drawPages(self, pdf):
    top = 0
    pages = []
    self.fonts = pdf.fonts
    self.document = self.gfx.createItemGroup([])
    b = QtGui.QBrush(QtCore.Qt.white)
    p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), 1)
    p.setCosmetic(True)
    for page in pdf.pages:
      pg = self.gfx.addRect(0, top, page.width, page.height, p, b)
      pg.setZValue(0)
      pg.setHandlesChildEvents(False)
      top += page.height
      self.drawObjects(pdf, pg, page._objs, top)
      pages.append(pg)
    self.document = self.gfx.createItemGroup(pages)
    self.document.setHandlesChildEvents(False)

  def drawObjects(self, pdf, pg, objs, y):
    for obj in objs: 
      if isinstance(obj, LTRect):
        b = QtGui.QBrush()
        p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), obj.linewidth)
        rect = self.gfx.addRect(obj.x0, y - obj.y1, obj.width, obj.height, p, b)
        rect.setParentItem(pg)
        rect.setZValue(1)
      elif isinstance(obj, LTLine):
        p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), obj.linewidth)
        [(x1, y1), (x2, y2)] = obj.pts
        line = self.gfx.addLine(x1, y - y1, x2, y - y2, p)
        line.setParentItem(pg)
        line.setZValue(1)
      #elif isinstance(obj, LTCurve):
      elif isinstance(obj, LTTextBox) or isinstance(obj, LTTextLine):
        if isinstance(obj, LTTextLine):
          texts = pdf.buildText([obj], y, obj.x0)
        else:
          texts = pdf.buildText(obj._objs, y, obj.x0)
        txt = self.gfx.addText('')
        txt.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        txt.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        txt.setHtml(unicode().join(texts))
        txt.setDefaultTextColor(QtCore.Qt.black)
        txt.setPos(obj.x0, y - obj.y1)
        txt.setParentItem(pg)
        txt.setZValue(1)
      elif isinstance(obj, LTImage):
        img = QtGui.QImage()
        img.loadFromData(obj.stream.rawdata)
        pix = QtGui.QPixmap()
        pix.convertFromImage(img)
        pixmap = self.gfx.addPixmap(pix)
        pixmap.setOffset(obj.x0, y - obj.y1)
        pixmap.setParentItem(pg)
        pixmap.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        pixmap.setZValue(1)
      elif isinstance(obj, LTFigure):
        self.drawObjects(pdf, pg, obj._objs, y)
      else: print('Unsupported PDF object: ' + str(type(obj)))
