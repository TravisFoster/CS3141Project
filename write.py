from html import PDFHTMLParser
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyQt4 import QtGui, QtCore
from pdfminer.layout import *
from PIL import Image
import cStringIO

class EPDFWrite:
  def __init__(self, filename, pages, tmp, fonts):
    for font in fonts:
      try:
        ttf = TTFont(fonts[font], tmp + '/' + fonts[font] + '.ttf')
        pdfmetrics.registerFont(ttf)
      except: pass
    size = pages[0].rect()
    pdf = canvas.Canvas(filename, pagesize=(size.width(), size.height()))
    for page in pages:
      size = page.rect()
      top = size.y() + size.height()
      for item in page.childItems(): self.drawItem(pdf, top, item)
      pdf.showPage()
    pdf.save()

  def drawItem(self, pdf, pageheight, item):
    if isinstance(item, QtGui.QGraphicsRectItem):
      box = item.rect()
      y = pageheight - box.y() - box.height()
      stroke = item.pen().widthF()
      fill = 0 if item.brush().style() == QtCore.Qt.NoBrush else 1
      pdf.rect(box.x(), y, box.width(), box.height(), stroke, fill)
    if isinstance(item, QtGui.QGraphicsLineItem):
      line = item.line()
      x1, x2 = line.x1(), line.x2()
      y1, y2 = pageheight - line.y1(), pageheight - line.y2()
      pdf.line(x1, y1, x2, y2)
    #if isinstance(item, QtGui.QGraphicsPathItem):
    if isinstance(item, QtGui.QGraphicsTextItem):
      box = item.boundingRect()
      txt = pdf.beginText()
      txt.setTextOrigin(box.x(), pageheight - box.y())
      parser = PDFHTMLParser(txt)
      parser.feed(item.toHtml().toUtf8().data())
      pdf.drawText(txt)
    if isinstance(item, QtGui.QGraphicsPixmapItem):
      box = item.boundingRect()
      buf = QtCore.QBuffer()
      buf.open(QtCore.QIODevice.ReadWrite)
      item.pixmap().toImage().save(buf, 'PNG')
      strio = cStringIO.StringIO()
      strio.write(buf.data())
      buf.close()
      strio.seek(0)
      img = Image.open(strio)
      pdf.drawInlineImage(img, box.x(), pageheight - box.y() - box.height())
