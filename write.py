from html import PDFHTMLParser
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyQt4 import QtGui, QtCore
from pdfminer.layout import *
from PIL import Image
import cStringIO

class EPDFWrite:
  def __init__(self, filename, pages, gfxview, gfx):
    pageWidth = pages[0].rect().right()
    pageHeight = pages[0].rect().bottom()
    pdf = canvas.Canvas(filename, pagesize=(pageWidth, pageHeight))
    for page in pages:
      pageImage = QtGui.QImage(pageWidth, pageHeight, QtGui.QImage.Format_RGB32)
      gfx.render(QtGui.QPainter(pageImage), QtCore.QRectF(), QtCore.QRectF(0, page.rect().y(), pageWidth, pageHeight))
      self.drawPage(pdf, pageImage)
      pdf.showPage()
    pdf.save()

  def drawPage(self, pdf, pageImage):
      buf = QtCore.QBuffer()
      buf.open(QtCore.QIODevice.ReadWrite)
      pageImage.save(buf, 'PNG')
      strio = cStringIO.StringIO()
      strio.write(buf.data())
      buf.close()
      strio.seek(0)
      img = Image.open(strio)
      pdf.drawInlineImage(img, 0, 0)