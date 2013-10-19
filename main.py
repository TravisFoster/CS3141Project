#!/usr/bin/python2

import sys
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.layout import LTTextBox
from pdfminer.converter import PDFPageAggregator
from PyQt4 import QtCore, QtGui

def main():
  app = QtGui.QApplication(sys.argv)
  w = QtGui.QMainWindow()
  w.resize(800, 600)
  w.setWindowTitle('CS3141 PDF Editor')
  gfx = QtGui.QGraphicsScene(w)
  (fonts, pages) = initPDFMiner('Cminus.pdf')
  drawPages(gfx, fonts, pages)
  gfxview = QtGui.QGraphicsView(gfx, w)
  gfxview.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.cyan))
  gfxview.centerOn(0, 0)
  w.setCentralWidget(gfxview)
  w.showMaximized()
  sys.exit(app.exec_())

def initPDFMiner(fname):
  fp = open(fname, 'rb')
  par = PDFParser(fp)
  doc = PDFDocument()
  par.set_document(doc)
  doc.set_parser(par)
  doc.initialize()
  if not doc.is_extractable:
    raise PDFTextExtractionNotAllowed
  rsr = PDFResourceManager()
  lap = LAParams()
  dev = PDFPageAggregator(rsr, laparams=lap)
  inter = PDFPageInterpreter(rsr, dev)
  pages = []
  for page in doc.get_pages():
    inter.process_page(page)
    pages.append(dev.get_result())
  fonts = insertFonts(inter.fontmap)
  return (fonts, pages)

def insertFonts(fmap):
  fonts = {}
  for font in fmap:
    data = fmap[font].fontfile.data
    idx = QtGui.QFontDatabase.addApplicationFontFromData(data)
    fams = QtGui.QFontDatabase.applicationFontFamilies(idx)
    fonts[fmap[font].fontname] = fams[0]
  return fonts

def drawPages(gfx, fonts, pages):
  top = 0
  b = QtGui.QBrush(QtCore.Qt.white)
  p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), 1)
  p.setCosmetic(True)
  for page in pages:
    gfx.addRect(0, top, page.width, page.height, p, b)
    for obj in page._objs:
      if obj.is_empty():
        continue
      y = top + page.height - obj.y1
      if isinstance(obj, LTTextBox):
        k = obj._objs[0]._objs[0]
        try:
          font = QtGui.QFont(fonts[k.fontname], k.size)
        except KeyError:
          font = QtGui.QFont()
          font.setPointSizeF(k.size)
        txt = gfx.addText(obj.get_text(), font)
        txt.setDefaultTextColor(QtCore.Qt.black)
        txt.setPos(obj.x0, y)
      else:
        gfx.addRect(obj.x0, y, obj.width, obj.height, p, b)
    top += page.height + 20

if __name__ == '__main__':
  main()
