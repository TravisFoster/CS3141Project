#!/usr/bin/python2

import sys
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from PyQt4 import QtCore, QtGui

def main():
  app = QtGui.QApplication(sys.argv)
  w = QtGui.QMainWindow()
  w.resize(800, 600)
  w.setWindowTitle('CS3141 PDF Editor')
  gfx = QtGui.QGraphicsScene(w)
  doc = initPDFMiner('/home/tucker/Downloads/Cminus.pdf')
  drawPages(gfx, doc)
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
  return pages

def drawPages(gfx, doc):
  top = 0
  b = QtGui.QBrush(QtCore.Qt.white)
  p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), 1)
  p.setCosmetic(True)
  for page in doc:
    gfx.addRect(0, top, page.width, page.height, p, b)
    top += page.height + 20

if __name__ == '__main__':
  main()
