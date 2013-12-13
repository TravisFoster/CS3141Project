class PDFStreamWrite:
  def writeStream(self, stream):
    pass

  def writeVal(self, pdf, val, vals):
    try:
      idx = vals.index(val)
      pdf.write(str(idx + 1) + ' 0 R')
    except ValueError:
      if val == None:
        pdf.write('null')
      elif isinstance(val, bool):
        pdf.write(str(val).lower())
      elif isinstance(val, (int, long, float)):
        pdf.write(str(val))
      elif isinstance(val, str):
        if val[0] == '/': pdf.write(val)
        else: pdf.write('(' + val + ')')
      elif isinstance(val, list):
        pdf.write('[ ')
        for item in val:
          self.writeVal(pdf, item)
          pdf.write(' ')
        pdf.write(']')
      elif isinstance(val, dict):
        stream = None
        pdf.write('<<\n')
        for item in val:
          if item == '%stream': stream = val[item]
          else:
            pdf.write('/' + item + ' ')
            self.writeVal(pdf, val[item])
            pdf.write('\n')
        pdf.write(' >>')
        if stream != None:
          pdf.write(' stream\n')
          pdf.write(stream)
          pdf.write('\nendstream')

class PDFWrite(PDFStreamWrite):
  def writePDF(self, fname, vals, trailer):
    with open(fname, 'wb') as pdf:
      xref = []
      pdf.write('%PDF-' + trailer['Root']['Version'][1:] + '\n')
      pdf.write('%\xE2\xE3\xCF\xD3\n')
      for idx, val in enumerate(vals):
        xref.append(pdf.tell())
        pdf.write(str(idx + 1) + ' 0 obj ')
        self.writeVal(pdf, val, vals)
        pdf.write(' endobj\n')
      sxref = pdf.tell()
      pdf.write('xref\n0 ' + str(len(xref) + 1) + '\n')
      pdf.write('0000000000 65535 f \n')
      for offset in xref: pdf.write(str(offset).zfill(10) + ' 00000 n \n')
      pdf.write('trailer\n')
      self.writeVal(pdf, trailer, vals)
      pdf.write('\nstartxref\n' + str(sxref) + '\n%%EOF')
