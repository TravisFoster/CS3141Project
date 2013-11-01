#!/usr/bin/python2

import re
import sys
import copy
import shutil
import tempfile
import itertools
import fontforge
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBox, LTChar, LTAnon
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
    except AttributeError:
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
  for page, fonts in pages:
    gfx.addRect(0, top, page.width, page.height, p, b)
    for obj in page._objs:
      if obj.is_empty():
        continue
      if isinstance(obj, LTTextBox):
        for line in obj._objs:
          y = top + page.height
          txt = gfx.addText('')
          txt.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
          txt.setHtml(buildText(fixText(line, y), fonts))
          txt.setDefaultTextColor(QtCore.Qt.black)
          txt.setPos(line._objs[0].x0, y - line._objs[0].y1)
      else:
        y = top + page.height - obj.y1
        gfx.addRect(obj.x0, y, obj.width, obj.height, p, b)
    top += page.height

def fixText(textbox, y):
  text = []
  for index, glyph in enumerate(textbox._objs):
    char = {'text': glyph._text}
    if isinstance(glyph, LTChar):
      char['font'] = glyph.fontname
      char['size'] = glyph.size
      char['xl'] = glyph.x0
      char['xr'] = glyph.x1
      char['y'] = y - glyph.y1
    else:
      char['font'] = text[-1]['font']
      char['size'] = text[-1]['size']
      char['xl'] = text[-1]['xr']
      char['xr'] = text[-1]['xr']
      char['y'] = text[-1]['y']
    text.append(char)
  return text

def buildText(textbox, fonts):
  texts = []
  lines = itertools.groupby(textbox, lambda x: (x['font'], x['size']))
  for (fontname, size), rawline in lines:
    line = list(rawline)
    text = unicode().join(map(lambda x: x['text'], line))
    fnt = QtGui.QFont(fonts[fontname])
    fnt.setPixelSize(size)
    tbox = QtGui.QFontMetrics(fnt).boundingRect(text)
    tsize = size*size/tbox.height()
    fnt.setPixelSize(tsize)
    tbox = QtGui.QFontMetrics(fnt).boundingRect(text)
    width = line[-1]['xr'] - line[0]['xl']
    tspace = (width - tbox.width())/len(text)
    texts.append(u'<span style="font: ' + unicode(int(tsize)) + u'px \''
      + unicode(fonts[fontname]) + u'\'; character-spacing: '
      + unicode(int(tspace*10)) + u'px;">' + unicode(text) + u'</span>')
  return unicode().join(texts)

if __name__ == '__main__':
  main()
