from win import PropTree
from reading import PDFStreamRead
from filters import decodeStream

class QtPDFDocument:
  def __init__(self, fname, docdict):
    self.parent = None
    self.ident = fname[1 + fname.rfind('/'):]
    self.props = PropTree(self.getProps(docdict))
    self.child = []
    for index, child in enumerate(docdict['Root']['Pages']['Kids']):
      if child['Type'] == '/Page':
        self.child.append(QtPDFPage(self, index, child))
      else:
        self.child.append(QtPDFPages(self, index, child))

  def getProps(self, ddict):
    props = {}
    props['Version'] = ddict['Version']
    props['Layout'] = ddict['Root']['PageLayout'] if 'PageLayout' in ddict['Root'] else '/SinglePage'
    props['Mode'] = ddict['Root']['PageMode'] if 'PageMode' in ddict['Root'] else '/UseNone'
    props['Language'] = ddict['Root']['Lang'] if 'Lang' in ddict['Root'] else ''
    return props

class QtPDFPages:
  def __init__(self, parent, idx, pagesdict):
    self.parent = parent
    self.ident = 'Page Set ' + str(idx)
    self.child = []
    for index, child in enumerate(pagesdict['Kids']):
      if child['Type'] == '/Page':
        self.child.append(QtPDFPage(self, index, child))
      else:
        self.child.append(QtPDFPages(self, index, child))

class QtPDFPage:
  def __init__(self, parent, idx, pagedict):
    self.parent = parent
    self.ident = 'Page ' + str(idx)
    conts = pagedict['Contents']
    if not isinstance(conts, list): conts = [conts]
    cstream = []
    for cont in conts:
      if 'F' not in cont and 'Filter' in cont:
        cstream.append(decodeStream(cont['%stream'], cont['Filter']))
      elif 'F' in cont and 'FFilter' in cont:
        cstream.append(decodeStream(cont['%stream'], cont['FFilter']))
      else: cstream.append(cont['%stream'])
    stream = PDFStreamRead().readStream(''.join(cstream))
    self.child = map(lambda x: QtPDFDraw(self, x), stream)

class QtPDFDraw:
  def __init__(self, parent, streamdict):
    self.parent = parent
    if isinstance(streamdict, list):
      self.ident = streamdict.pop(0)[-1]
      self.child = map(lambda x: QtPDFDraw(self, x), streamdict)
    elif isinstance(streamdict, dict): self.ident = 'BI'
    else: self.ident = streamdict[-1]

# /Type (Font)
# /Subype (Type0, Type1, MMType1, Type3, TrueType, CIDFontType0, CIDFontType2)
# /BaseFont (font name) not in Type3
# /FontBBox (bounding box of all characters) in Type3
# /FontMatrix (matrix mapping glyph space to text space) in Type3
# /CharProcs (dictionary of character streams) in Type3
# /FirstChar (first code in Widths) in Type1, MMType1, Type3, TrueType
# /LastChar (last code in Widths) in Type1, MMType1, Type3, TrueType
# /Widths (list of character widths) in Type1, MMType1, Type3, TrueType
# /DW (default glyph width) in CIDFontType0, CIDFontType2
# /W (array of widths for glyphs) in CIDFontType0, CIDFontType2
# /DW2 (vertical metrics) in CIDFontType0, CIDFontType2
# /W2 (array of vertical widths) in CIDFontType0, CIDFontType2
# /CIDToGIDMap (CID to glyph index mapping) in embedded CIDFontType2
# /DescendantFonts (one-element array with CIDFontType_) in Type0
# /FontDescriptor (the font descriptor dictionary) not in Type0
# /Encoding (encoding or cmap dictionary) not in CIDFontType0, CIDFontType2
# /ToUnicode (CMap stream) not in CIDFontType0, CIDFontType2
# /Resources (resource dictionary for use in CharProcs) in Type3
# /CIDSystemInfo (sysinfo dictionary) in CIDFontType0, CIDFontType2
# - /Registry (issuer name)
# - /Ordering (collection name)
# - /Supplement (version number)

# /Type (Encoding)
# /BaseEncoding (MacRomanEncoding, MacExpertEncoding, WinAnsiEncoding)
# /Differences (array of differences from the base encoding)

# /Type (CMap)
# /CMapName (cmap name)
# /CIDSystemInfo (the CIDSystemInfo dictionary)
# /WMode (0 if horizontal, 1 if vertical)
# /UseCMap (parent cmap)

# /Type (FontDescriptor)
# /FontName (same as BaseFont)
# /FontFamily (font family name)
# /FontStretch (font stretching value)
# /FontWeight (font boldness value)
# /Flags (flags that specify the kind of font)
# /FontBBox (bounding box of all characters)
# /ItalicAngle (the angle of the italics in the font)
# /Ascent (maximum height above baseline)
# /Descent (maximum drop below baseline)
# /Leading (distance between baselines)
# /CapHeight (height of flat capital characters)
# /XHeight (height of the 'x' character)
# /StemV (vertical stem thickness)
# /StemH (horizontal stem thickness)
# /AvgWidth (average width of glyphs)
# /MaxWidth (width of biggest glyph)
# /MissingWidth (width to use for missing characters)
# /Style (glyph style dictionary) in CIDFontType0, CIDFontType2
# /Lang (font language) in CIDFontType0, CIDFontType2
# /FD (dictionary of overrides for glyphs) in CIDFontType0, CIDFontType2
# /CIDSet (stream defining a font subset) in CIDFontType0, CIDFontType2
# /FontFile (embedded type1 font file stream)
# /FontFile2 (embedded truetype font file stream)
# /FontFile3 (embedded font file stream with type specified in the stream)
# /CharSet (a list of the characters defined in this subset)

# FontDescriptor Flags:
# 01 - Fixed Width
# 02 - Serif'd
# 03 - Symbolic
# 04 - Script
# 07 - Italic
# 17 - All Caps
# 18 - Small Caps
# 19 - Force Bold

# Font Streams also contain:
# /Length1 (unfiltered truetype length or unfiltered type1 cleartext length)
# /Length2 (unfiltered type1 encrypted length)
# /Length3 (unfiltered type1 fixed content length)
# /Subtype (the FontFile3 type specifier)
# /Metadata (metadata for the font program)

class QtPDFFont:
  def __init__(self, fdict):
    assert fdict['Type'] == '/Font', "Not a font dictionary."
    

  def buildDict(self):
    fdict = {'Type': '/Font'}
    

  def paintText(self, painter, text):
    pass

  def getGlyph(self, glyph):
    if glyph in self.glyphs: return self.glyphs[glyph]
    self.fontdata.load_char(glyph, FT_LOAD_NO_BITMAP)
    outline = self.fontdata.glyph.outline
    path = QtGui.QPainterPath()
    start = 0
    for end in outline.contours:
      points = outline.points[start:end + 1]
      tags = outline.tags[start:end + 1]
      points.append(points[0])
      tags.append(tags[0])
      segments = [[points[0]]]
      for j in range(1, len(points)):
        segments[-1].append(points[j])
        if tags[j] & 1 and j < len(points) - 1: segments.append([points[j]])
      path.moveTo(*points[0])
      for segment in segments:
        if len(segment) == 2: path.lineTo(*segment[1])
        elif len(segment) == 3:
          [(cx, cy), (px, py)] = segment[1:]
          path.quadTo(cx, cy, px, py)
        else:
          for i in range(1, len(segment) - 2):
            cx, cy = segment[i]
            px, py = segment[i + 1]
            path.quadTo(cx, cy, (cx + px)/2.0, (cy + py)/2.0)
          [(cx, cy), (px, py)] = segment[-2:]
          path.quadTo(cx, cy, px, py)
      start = end + 1
    self.glyphs[glyph] = path
    return path

  def getRenderMode(mode):
    return mode&1 == 0, mode + 1&2 > 0, mode&4 > 0

  def setRenderMode((f, s, c)):
    return ((1 if f else 0) + (2 if s else 0) - 1&3) + (4 if c else 0)
