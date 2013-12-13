import zlib

def decodeStream(data, filts):
  if not isinstance(filts, list): filts = [filts]
  for filt in filts:
    if filt == '/FlateDecode': data = zlib.decompress(data)
    elif filt == '/DCTDecode': pass
    else: raise Exception('Error: unsupported stream filter: ' + filt)
  return data
