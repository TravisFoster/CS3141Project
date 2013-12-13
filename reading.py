import re
import string
import StringIO

markerset = {'[':']','<<':'>>','BX':'EX','q':'Q','BI':'ID','BT':'ET','cm':6,
'w':1,'J':1,'j':1,'M':1,'d':2,'ri':1,'i':1,'gs':1,'m':2,'l':2,'c':6,'v':4,
'y':4,'h':0,'re':4,'S':0,'s':0,'f':0,'F':0,'f*':0,'B':0,'B*':0,'b':0,'b*':0,
'n':0,'W':0,'W*':0,'CS':1,'cs':1,'SC':-1,'SCN':-1,'sc':-1,'scn':-1,'G':1,'g':1,
'RG':3,'rg':3,'K':4,'k':4,'Do':1,'sh':1,'Tc':1,'Tw':1,'Tz':1,'TL':1,'Tf':2,
'Tr':1,'Ts':1,'Td':2,'TD':2,'Tm':6,'T*':0,'Tj':1,"'":1,'"':3,'TJ':1,'d0':2,
'd1':6,'MP':1,'DP':2,'BMC':1,'BDC':2}

class PDFStreamRead:
  def __init__(self):
    self.markers = markerset
    self.stops = [[None]]

  def readStream(self, stream):
    self.pdf = StringIO.StringIO(stream)
    return self.getObject()

  def getObject(self):
    objs, obj, eol = [], [], []
    while True:
      char = self.getToken()
      if len(objs) <= 0 and char in self.stops:
        if char == ['stream']: obj[-1]['%stream'] = self.pdf.tell()
        return obj
      assert char != [None], "Incomplete or truncated object."
      if len(eol) > 0 and char == [eol[-1]]:
        eol.pop()
        if obj[0] == ('[',): obj.pop(0)
        if char == ['>>'] or char == ['ID']:
          obj.pop(0)
          assert len(obj)%2 == 0, "Mismatched dictionary pairs."
          tmp = {}
          while len(obj) > 0:
            key = obj.pop(0)
            val = obj.pop(0)
            assert isinstance(key, str) and key[0] == '/', "Key not a name."
            tmp[key[1:]] = val
          obj = tmp
        if char == ['ID']:
          tmps = []
          tmp = self.pdf.read(1)
          if tmp not in string.whitespace: self.pdf.seek(-1, 1)
          while re.match(r'\sEI\s', ''.join(tmps[-4:])) == None:
            tmps.append(self.pdf.read(1))
          obj['%stream'] = ''.join(tmps[:-4])
        tmp = objs.pop()
        tmp.append(obj)
        obj = tmp
      elif isinstance(char, list) and len(char) == 1:
        match = self.markers[char[0]] if char[0] in self.markers else None
        assert isinstance(match, (int, str)), str(char) + "' not an object."
        if isinstance(match, int):
          tmp = [char[0]]
          if match < 0:
            arg = obj.pop()
            while not isinstance(arg, tuple):
              tmp.append(arg)
              if len(obj) <= 0: break
              arg = obj.pop()
            if isinstance(arg, tuple): obj.append(arg)
          else:
            for _ in range(match): tmp.append(obj.pop())
          tmp.reverse()
          obj.append(tuple(tmp))
        else: obj.append((char[0],))
        if isinstance(match, str) or char[0] in ('BMC', 'BDC'):
          eol.append(match if isinstance(match, str) else 'EMC')
          objs.append(obj)
          obj = [obj.pop()]
      else: obj.append(char)

  def getToken(self):
    char = self.pdf.read(1)
    while True:
      while char != '' and char in string.whitespace: char = self.pdf.read(1)
      if char == '': return [None]
      elif char == '%':
        while char not in '\r\n': char = self.pdf.read(1)
        continue
      elif char in '+-.0123456789': return self.getNumber(char)
      elif char == '(': return self.getString()
      elif char == '/': return self.getName()
      elif char in '[]': return [char]
      elif char == '<':
        char = self.pdf.read(1)
        if char in string.hexdigits: return self.getHexString(char)
        assert char == '<', "Invalid dictionary head or hex string."
        return ['<<']
      elif char == '>':
        assert self.pdf.read(1) == '>', "Invalid dictionary tail."
        return ['>>']
      else: return self.getKeyword(char)

  def getKeyword(self, char):
    obj = []
    while char not in string.whitespace and char not in '()<>[]{}/%':
      obj.append(char)
      char = self.pdf.read(1)
    assert len(obj) > 0, "Invalid keyword."
    self.pdf.seek(-1, 1)
    retval = [''.join(obj)]
    if retval == ['null']: return None
    elif retval == ['true']: return True
    elif retval == ['false']: return False
    else: return retval

  def getNumber(self, char):
    obj = [char]
    char = self.pdf.read(1)
    while char in '.0123456789':
      obj.append(char)
      char = self.pdf.read(1)
    self.pdf.seek(-1, 1)
    obj = ''.join(obj)
    cnt = obj.count('.')
    assert cnt in [0, 1], "Too many decimal points."
    if cnt == 0: return int(obj)
    else: return float(obj)

  def getName(self):
    obj = ['/']
    char = self.pdf.read(1)
    while char not in string.whitespace and char not in '()<>[]{}/%':
      obj.append(char)
      char = self.pdf.read(1)
    self.pdf.seek(-1, 1)
    return ''.join(obj)

  def getString(self):
    obj = []
    pcount = 0
    while True:
      char = self.pdf.read(1)
      if char in '\r\n':
        obj.append('\n')
        tmp = char
        char = self.pdf.read(1)
        if char not in '\r\n' or char == tmp: self.pdf.seek(-1, 1)
      elif char == '(':
        pcount += 1
        obj.append(char)
      elif char == ')':
        if pcount <= 0: break
        else:
          pcount -= 1
          obj.append(char)
      elif char == '\\':
        char = self.pdf.read(1)
        if char in 'nrtbf': obj.append(('\\' + char).decode('string_escape'))
        elif char in '\r\n':
          tmp = char
          char = self.pdf.read(1)
          if char not in '\r\n' or char == tmp: self.pdf.seek(-1, 1)
        elif char in string.digits:
          tmp = ['\\', char]
          char = self.pdf.read(1)
          if char in string.digits:
            tmp.append(char)
            char = self.pdf.read(1)
            if char in string.digits: tmp.append(char)
            else: self.pdf.seek(-1, 1)
          else: self.pdf.seek(-1, 1)
          obj.append(''.join(tmp).decode('string_escape'))
        else: obj.append(char)
      else: obj.append(char)
    return ''.join(obj)

  def getHexString(self, char):
    obj = [char]
    while char in string.hexdigits:
      obj.append(char)
      char = self.pdf.read(1)
    assert char == '>', "Invalid hex string."
    if len(obj)%2 != 0: obj.append('0')
    return ''.join(obj).decode('hex')

class PDFRead(PDFStreamRead):
  def __init__(self):
    self.markers = {'[':']','<<':'>>','R':2}
    self.stops = [['stream'], ['endobj'], ['startxref']]

  def readPDF(self, fname):
    with open(fname, 'rb') as self.pdf:
      version = self.getVersion()
      self.pdf.seek(self.getXrefOffset())
      trailer = self.getTrailer()
      self.deepDereference(trailer)
      if 'Version' in trailer['Root']:
        trailversion = float(trailer['Root']['Version'][1:])
        if version > trailversion:
          trailer['Root']['Version'] = '/' + str(version)
      else: trailer['Root']['Version'] = '/' + str(version)
    return trailer

  def getVersion(self):
    header = self.pdf.read(8)
    assert header[:5] == '%PDF-', "Invalid header."
    return float(header[5:])

  def getXrefOffset(self):
    pdfpos = -1
    buf = 'startxref0#0%%EOF0'
    bufpos = len(buf) - 1
    xref = []
    while bufpos >= 0:
      self.pdf.seek(pdfpos, 2)
      char = self.pdf.read(1)
      if buf[bufpos] == '0':
        if char in string.whitespace: pdfpos -= 1
        else: bufpos -= 1
      elif buf[bufpos] == '#':
        if char in string.digits:
          xref.append(char)
          pdfpos -= 1
        else: bufpos -= 1
      elif buf[bufpos] == char:
        bufpos -= 1
        pdfpos -= 1
      else: assert False, "Invalid trailer."
    xref.reverse()
    return int(''.join(xref))

  def getTrailer(self):
    maxref = 0
    xrefs = []
    trailer = None
    while True:
      assert self.getToken() == ['xref'], "Invalid xref head."
      xref = []
      idx = self.getToken()
      while idx != ['trailer']:
        dat = []
        cnt = self.getToken()
        if maxref < idx + cnt: maxref = idx + cnt
        for _ in range(cnt):
          val = self.getToken()
          gen = self.getToken()
          typ = self.getToken()
          dat.append((val, gen, typ[0]))
        xref.append((idx, dat))
        idx = self.getToken()
      xrefs.append(xref)
      obj = self.getObject()[0]
      if trailer == None: trailer = obj
      if 'Prev' in obj: self.pdf.seek(obj['Prev'])
      else: break
    self.xref = [(None, None)]*maxref
    while len(xrefs) > 0:
      for idx, group in xrefs.pop():
        for offset, (val, gen, typ) in enumerate(group):
          if self.xref[idx + offset][1] > gen: continue
          if typ == 'n': self.xref[idx + offset] = (val,), gen
          else: self.xref[idx + offset] = None, gen
    return trailer

  def deepDereference(self, obj):
    objs = [obj]
    while len(objs) > 0:
      obj = objs.pop(0)
      if isinstance(obj, dict): iratr = obj
      else: iratr = range(len(obj))
      for idx in iratr:
        if isinstance(obj[idx], tuple):
          i, m, k = obj[idx]
          x, n = self.xref[i]
          assert k == 'R', "Invalid object ref."
          if m != n: obj[idx] = None
          elif isinstance(x, tuple):
            self.pdf.seek(x[0])
            self.xref[i] = self.getIndirectObject(i, m), n
            obj[idx] = self.xref[i][0]
          else:
            obj[idx] = x
            continue
        if isinstance(obj[idx], (list, dict)): objs.append(obj[idx])
      if isinstance(obj, dict) and '%stream' in obj: self.getStream(obj)

  def getIndirectObject(self, eref, egen):
    ref = self.getToken()
    gen = self.getToken()
    obj = self.getToken()
    assert (ref, gen, obj) == (eref, egen, ['obj']), "Invalid object ref."
    return self.getObject()[0]

  def getStream(self, obj):
    self.pdf.seek(obj['%stream'])
    char = self.pdf.read(1)
    if char != '\n': char = self.pdf.read(1)
    stream = self.pdf.read(obj['Length'])
    char = self.pdf.read(1)
    while char in string.whitespace: char = self.pdf.read(1)
    char += self.pdf.read(8)
    assert char == 'endstream', "Invalid stream tail."
    assert self.getToken() == ['endobj'], "Invalid object tail."
    if 'F' in obj:
      with open(obj['F'], 'rb') as fstream: stream = fstream.read()
    obj['%stream'] = stream
