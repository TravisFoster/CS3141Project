import itertools
import fontforge
from pdfminer.layout import *
from pdfminer.pdffont import *
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfdevice import PDFDevice
from PyQt4 import QtGui

class EPDFRead:
  def __init__(self, fname, tmp):
    self.pages = []
    self.fonts = {}
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
    for page in doc.get_pages():
      inter.process_page(page)
      self.pages.append(dev.get_result())
      self.insertFonts(inter.fontmap, tmp)

  def insertFonts(self, fmap, tmp):
    for font in fmap:
      if fmap[font].fontname in self.fonts: continue
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
        tfont = fams[0].toUtf8().data()
      else:
        tfont = fmap[font].fontname
        if len(tfont) > 7 and tfont[6] == '+': tfont = tfont[7:]
      self.fonts[fmap[font].fontname] = tfont

  def buildText(self, objs, y, x0):
    texts = []
    textbox = self.fixText(self.fixLineOrder(objs), y, x0)
    lines = itertools.groupby(textbox, lambda x: (x['font'], x['size']))
    for (fontname, size), rawline in lines:
      line = list(rawline)
      text = unicode().join(map(lambda x: x['text'], line))
      font = QtGui.QFont(self.fonts[fontname])
      font.setPixelSize(size)
      tsize = size*size/QtGui.QFontMetrics(font).boundingRect(text).height()
      texts.append(u'<span style="font: ' + unicode(int(tsize))
        + u'px \'' + unicode(self.fonts[fontname]) + u'\';">'
        + unicode(text) + u'</span>')
    return unicode().join(texts)

  def fixLineOrder(self, textbox):
    linesets = []
    for line in sorted(textbox, key=lambda x: -x.y1):
      isset = False
      for lineset in linesets:
        if line.y1 - lineset[0][0] > line.height/2:
          if lineset[0][0] > line.y0: lineset[0][0] = line.y0
          lineset[1].append(line)
          isset = True
          break
      if not isset: linesets.append(([line.y0, line.y1], [line]))
    box = [LTAnon(' ')]
    for lineset in linesets:
      for line in sorted(lineset[1], key=lambda x: (x.x0 + x.x1)/2):
        box.extend(line._objs)
    return box

  def fixText(self, textbox, y, boxleft):
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
          if not isinstance(prevc, LTChar):
            char['font'] = nextc.fontname
            char['size'] = nextc.size
            char['xl'] = boxleft
            char['xr'] = nextc.x0
            char['y'] = y - nextc.y1
            char['text'] = ''
          elif nextc.y1 - prevc.y0 > nextc.height/2:
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
          font = QtGui.QFont(self.fonts[char['font']])
          font.setPixelSize(char['size'])
          space = QtGui.QFontMetrics(font).boundingRect(' ').width()
          if space > 0:
            char['text'] += '&nbsp;'*int((char['xr'] - char['xl'])/space)
        except IndexError: continue
      text.append(char)
    return text
