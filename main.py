#!/usr/bin/python2

import sys
import copy
import shutil
import tempfile
import itertools
import fontforge
from pdfminer.layout import *
from pdfminer.pdffont import *
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfdevice import PDFDevice
from PyQt4 import QtCore, QtGui

def main():
  tmp = tempfile.mkdtemp()
  app = QtGui.QApplication(sys.argv)
  w = QtGui.QMainWindow()
  w.resize(800, 600)
  w.setWindowTitle('CS3141 PDF Editor')
  gfx = QtGui.QGraphicsScene(w)
  gfxview = QtGui.QGraphicsView(gfx, w)
  w.addToolBar(buildToolbar(w, gfx, gfxview, tmp))
  gfxview.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.cyan))
  w.setCentralWidget(gfxview)
  w.showMaximized()
  ex = app.exec_()
  shutil.rmtree(tmp, True)
  sys.exit(ex)

def buildToolbar(w, gfx, gfxview, tmp):
  toolbar = QtGui.QToolBar(w)
  openl = lambda: actionOpen(w, gfx, gfxview, tmp)
  toolbar.addAction(QtGui.QIcon.fromTheme('document-open'), 'Open', openl)
  return toolbar

def actionOpen(w, gfx, gfxview, tmp):
  filename = QtGui.QFileDialog.getOpenFileName(w, 'Open PDF', '.')
  if len(filename) > 0:
    gfx.clear()
    drawPages(gfx, initPDFMiner(filename, tmp))
    gfxview.centerOn(0, 0)

def initPDFMiner(fname, tmp):
  fp = open(fname, 'rb')
  par = PDFParser(fp)
  doc = PDFDocument()
  par.set_document(doc)
  doc.set_parser(par)
  doc.initialize()
  if not doc.is_extractable: raise PDFTextExtractionNotAllowed
  rsr = PDFResourceManager()
  lap = LAParams()
  dev = PDFPageAggregator(rsr, laparams=lap)
  inter = PDFPageInterpreter(rsr, dev)
  pages, fonts = [], {}
  for page in doc.get_pages():
    inter.process_page(page)
    pages.append(dev.get_result())
    insertFonts(inter.fontmap, fonts, tmp)
  return pages, fonts

def insertFonts(fmap, fonts, tmp):
  for font in fmap:
    if fmap[font].fontname in fonts: continue
    if hasattr(fmap[font], 'fontfile'):
      fntext = '~'
      if isinstance(fmap[font], PDFTrueTypeFont): fntext = '~.ttf'
      elif isinstance(fmap[font], PDFType1Font): fntext = '~.pfb'
      else: print('Unsupported PDF font: ' + str(type(fmap[font])))
      tmpfnt = tmp + '/' + fmap[font].fontname + fntext
      tmpttf = tmp + '/' + fmap[font].fontname + '.ttf'
      fin = open(tmpfnt, 'wb')
      fin.write(fmap[font].fontfile.data)
      fin.close()
      fout = fontforge.open(tmpfnt)
      fout.familyname = fmap[font].fontname
      fout.generate(tmpttf)
      fout.close()
      idx = QtGui.QFontDatabase.addApplicationFont(tmpttf)
      fams = QtGui.QFontDatabase.applicationFontFamilies(idx)
      tfont = fams[0]
    else:
      tfont = fmap[font].fontname
      if len(tfont) > 7 and tfont[6] == '+': tfont = tfont[7:]
    fonts[fmap[font].fontname] = tfont

def drawPages(gfx, (pages, fonts)):
  top = 0
  b = QtGui.QBrush(QtCore.Qt.white)
  p = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), 1)
  p.setCosmetic(True)
  for page in pages:
    gfx.addRect(0, top, page.width, page.height, p, b)
    drawObjects(gfx, fonts, page._objs, 0, top + page.height)
    top += page.height

def drawObjects(gfx, fonts, objs, x, y):
  for obj in objs: 
    if isinstance(obj, LTRect):
      brush = QtGui.QBrush()
      pen = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), obj.linewidth)
      gfx.addRect(x + obj.x0, y - obj.y1, obj.width, obj.height, pen, brush)
    elif isinstance(obj, LTLine):
      pen = QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), obj.linewidth)
      [(x1, y1), (x2, y2)] = obj.pts
      gfx.addLine(x + x1, y - y1, x + x2, y - y2, pen)
    #elif isinstance(obj, LTCurve):
    elif isinstance(obj, LTTextBox):
      texts = buildText(fixText(fixLineOrder(obj), y, fonts, obj.x0), fonts)
      txt = gfx.addText('')
      txt.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
      txt.setHtml(unicode().join(texts))
      txt.setDefaultTextColor(QtCore.Qt.black)
      txt.setPos(x + obj.x0, y - obj.y1)
    elif isinstance(obj, LTImage):
      img = QtGui.QImage()
      img.loadFromData(obj.stream.rawdata)
      pix = QtGui.QPixmap()
      pix.convertFromImage(img)
      pixmap = gfx.addPixmap(pix)
      pixmap.setOffset(x + obj.x0, y - obj.y1)
    elif isinstance(obj, LTFigure):
      drawObjects(gfx, fonts, obj._objs, x, y)
    else: print('Unsupported PDF object: ' + str(type(obj)))

def fixLineOrder(textbox):
  linesets = []
  for line in sorted(textbox._objs, key=lambda x: -x.y1):
    isset = False
    for lineset in linesets:
      if line.y1 - lineset[0][0] > line.height/2:
        if lineset[0][0] > line.y0: lineset[0][0] = line.y0
        lineset[1].append(line)
        isset = True
        break
    if not isset: linesets.append(([line.y0, line.y1], [line]))
  box = []
  for lineset in linesets:
    for line in sorted(lineset[1], key=lambda x: (x.x0 + x.x1)/2):
      box.extend(line._objs)
  return box

def fixText(textbox, y, fonts, boxleft):
  text = []
  for index, glyph in enumerate(textbox):
    char = {}
    if isinstance(glyph, LTChar):
      char['font'] = glyph.fontname
      char['size'] = glyph.size
      char['xl'] = glyph.x0
      char['xr'] = glyph.x1
      char['y'] = y - glyph.y1
      if glyph._text == '<': char['text'] = '&lt;'
      elif glyph._text == '>': char['text'] = '&gt;'
      elif glyph._text == '&': char['text'] = '&amp;'
      else: char['text'] = glyph._text
    else:
      try:
        while not isinstance(textbox[index + 1], LTChar):
          textbox.pop(index + 1)
        prevc = textbox[index - 1]
        nextc = textbox[index + 1]
        if nextc.y1 - prevc.y0 > nextc.height/2:
          char['font'] = prevc.fontname
          char['size'] = prevc.size
          char['xl'] = prevc.x1
          char['xr'] = nextc.x0
          char['y'] = y - prevc.y1
          char['text'] = ''
        else:
          char['font'] = nextc.fontname
          char['size'] = nextc.size
          char['xl'] = boxleft
          char['xr'] = nextc.x0
          char['y'] = y - nextc.y1
          char['text'] = '<br />'
        font = QtGui.QFont(fonts[char['font']])
        font.setPixelSize(char['size'])
        space = QtGui.QFontMetrics(font).boundingRect(' ').width()
        if space > 0:
          char['text'] += '&nbsp;'*int((char['xr'] - char['xl'])/space)
      except IndexError: continue
    text.append(char)
  return text

def buildText(textbox, fonts):
  texts = []
  lines = itertools.groupby(textbox, lambda x: (x['font'], x['size']))
  for (fontname, size), rawline in lines:
    line = list(rawline)
    text = unicode().join(map(lambda x: x['text'], line))
    font = QtGui.QFont(fonts[fontname])
    font.setPixelSize(size)
    tsize = (size*size)/(QtGui.QFontMetrics(font).boundingRect(text).height())
    texts.append(u'<span style="font: ' + unicode(int(tsize)) + u'px \''
      + unicode(fonts[fontname]) + u'\';">' + unicode(text) + u'</span>')
  return unicode().join(texts)

if __name__ == '__main__':
  main()
