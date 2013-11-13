from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
import re

class PDFHTMLParser(HTMLParser):
  def __init__(self, txt):
    HTMLParser.__init__(self)
    self.txt = txt
    self.size = None
    self.face = None

  def handle_starttag(self, tag, attrs):
    if tag != 'span': return
    style = ''
    for attr in attrs:
      if attr[0] == 'style': style += attr[1]
    if style == '': return
    css = {}
    regex = r'''\s*([^:\s]+)\s*:\s*(?P<q>['"]?)([^\1;]+)(?P=q)\s*;'''
    for m in re.finditer(regex, style): css[m.group(1)] = m.group(3)
    if 'font-family' in css: self.face = css['font-family']
    if 'font-size' in css:
      self.size = int(re.match(r'([0-9]+)', css['font-size']).group(1))
    try:
      self.txt.setFont(self.face, self.size)
    except:
      print('Error: Font ' + str(self.face) + ' not found.')

  def handle_startendtag(self, tag, attrs):
    if tag == 'br': self.txt.textLine()

  def handle_data(self, data):
    self.txt.textOut(data)

  def handle_entityref(self, name):
    c = unichr(name2codepoint[name])
    self.txt.textOut(c)

  def handle_charref(self, name):
    if name.startswith('x'): c = unichr(int(name[1:], 16))
    else: c = unichr(int(name))
    self.txt.textOut(c)
