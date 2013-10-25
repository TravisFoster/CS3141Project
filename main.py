#!/usr/bin/python2

import re
import sys
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBox, LTChar
from pdfminer.converter import PDFPageAggregator
from PyQt4 import QtCore, QtGui

def main():
  app = QtGui.QApplication(sys.argv)
  w = QtGui.QMainWindow()
  w.resize(800, 600)
  w.setWindowTitle('CS3141 PDF Editor')
  gfx = QtGui.QGraphicsScene(w)
  pages = initPDFMiner('Cminus.pdf')
  drawPages(gfx, pages)
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
    pages.append((dev.get_result(), insertFonts(inter.fontmap)))
  return pages

def insertFonts(fmap):
  fonts = {}
  for font in fmap:
    try:
      data = fmap[font].fontfile.data
      data = QByteArray(len(data), data)
      idx = QtGui.QFontDatabase.addApplicationFontFromData(data)
      if idx < 0:
        print('Error: Font "' + fmap[font].fontname + '" invalid.')
      fams = QtGui.QFontDatabase.applicationFontFamilies(idx)
    except:
      fams = [fmap[font].fontname]
    fonts[fmap[font].fontname] = fams[0]
  return fonts

def drawPages(gfx, pages):
  top = 0
  b = QtGui.QBrush(QtCore.Qt.white)
  p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), 1)
  p.setCosmetic(True)
  for (page, fonts) in pages:
    gfx.addRect(0, top, page.width, page.height, p, b)
    for obj in page._objs:
      if obj.is_empty():
        continue
      if isinstance(obj, LTTextBox):
        for line in obj._objs:
          y = top + page.height - line.y1
          txt = gfx.addText('')
          txt.setHtml(buildText(line, fonts))
          txt.setDefaultTextColor(QtCore.Qt.black)
          txt.setPos(line.x0, y)
      else:
        y = top + page.height - obj.y1
        gfx.addRect(obj.x0, y, obj.width, obj.height, p, b)
    top += page.height

def buildText(textbox, fonts):
  text = []
  font = None
  size = None
  cidex = re.compile(r'\(cid:(.*)\)')
  for glyph in textbox._objs:
    rex = cidex.match(glyph._text)
    if rex != None:
      glyph._text = u':&lt;' + unicode(int(rex.group(1))) + u'&gt;:'
    if len(glyph._text) <= 0:
      continue
    if isinstance(glyph, LTChar):
      if glyph.fontname != font or glyph.size != size:
        if len(text) != 0:
          text.append(u'</span>')
        text.append(u'<span style="font:')
        text.append(u' ' + unicode(int(glyph.size)) + u'px')
        text.append(u" '" + unicode(fonts[glyph.fontname]) + u"'")
        text.append(u';">')
        font = glyph.fontname
        size = glyph.size
      text.append(unicode(glyph._text))
    else:
      if glyph._text == u'\n':
        text.append(u'<br />')
      elif glyph._text == u' ':
        text.append(u'&nbsp;')
      else:
        text.append(unicode(glyph._text))
  if len(text) != 0:
    text.append(u'</span>')
  return unicode().join(text)

if __name__ == '__main__':
  main()
