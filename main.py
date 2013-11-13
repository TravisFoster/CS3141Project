#!/usr/bin/python2

import sys
from window import EPDFWindow

if __name__ == '__main__':
  with EPDFWindow(sys.argv) as win:
    exitcode = win.show()
  sys.exit(exitcode)
