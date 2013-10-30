#!/usr/bin/python2

import re
import sys
import shutil
import tempfile
import fontforge
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
  pages, tmps = initPDFMiner('Cminus.pdf')
  drawPages(gfx, pages)
  gfxview = QtGui.QGraphicsView(gfx, w)
  gfxview.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.cyan))
  gfxview.centerOn(0, 0)
  w.setCentralWidget(gfxview)
  w.showMaximized()
  ex = app.exec_()
  for tmp in tmps:
    shutil.rmtree(tmp, True)
  sys.exit(ex)

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
  tmps = []
  for page in doc.get_pages():
    inter.process_page(page)
    fpage = dev.get_result()
    ffont, ftmp = insertFonts(inter.fontmap)
    pages.append((fpage, ffont))
    tmps.extend(ftmp)
  return pages, tmps

def insertFonts(fmap):
  fonts = {}
  tmps = []
  for font in fmap:
    try:
      newfont = re.sub(r'(?<=/FamilyName \()[^\)]*(?=\))',
        fmap[font].fontname, fmap[font].fontfile.data, 1)
      tmp = tempfile.mkdtemp()
      tmps.append(tmp)
      tmppfb = tmp + '/' + fmap[font].fontname + '.pfb'
      tmpttf = tmp + '/' + fmap[font].fontname + '.ttf'
      fin = open(tmppfb, 'wb')
      fin.write(newfont)
      fin.close()
      fout = fontforge.open(tmppfb)
      fout.generate(tmpttf)
      fout.close()
      idx = QtGui.QFontDatabase.addApplicationFont(tmpttf)
      fams = QtGui.QFontDatabase.applicationFontFamilies(idx)
      tfont = fams[0]
    except None:
      print('Font load from data failed.')
      tfont = fmap[font].fontname
      if len(tfont) > 7 and tfont[6] == '+':
        tfont = tfont[7:]
    fonts[fmap[font].fontname] = tfont
  return fonts, tmps

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
          boxes = buildText(line, fonts)
          for box, left in boxes:
            txt = gfx.addText('')
            txt.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            txt.setHtml(box)
            txt.setDefaultTextColor(QtCore.Qt.black)
            txt.setPos(left, y)
      else:
        y = top + page.height - obj.y1
        gfx.addRect(obj.x0, y, obj.width, obj.height, p, b)
    top += page.height

def buildText(textbox, fonts):
  boxes = []
  text = []
  left = None
  font = None
  size = None
  for glyph in textbox._objs:
    if len(glyph._text) <= 0:
      continue
    elif left == None:
      left = glyph.x0
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
      elif glyph._text == u'\t':
        while len(text) != 0 and text[-1] == u'<br />':
          text.pop()
        if len(text) != 0:
          text.append(u'</span>')
          boxes.append((unicode().join(text), left))
        text = []
        left = None
        font = None
        size = None
      else:
        text.append(unicode(glyph._text))
  while len(text) != 0 and text[-1] == u'<br />':
    text.pop()
  if len(text) != 0:
    text.append(u'</span>')
    boxes.append((unicode().join(text), left))
  return boxes

if __name__ == '__main__':
  main()
