markerset = {
  # block markers
  '[' :']' , # list
  '<<':'>>', # dictionary
  'BX':'EX', # compatibility (ignore unrecognized markers)
  'q' :'Q' , # localize the graphics state
  'BI':'ID', # denote an inline image, along with 'EI'
  'BT':'ET', # denote a text object
  # operator markers
  'cm' : 6 , # concat a new transformation matrix to the CTM
  'w'  : 1 , # set the line width
  'J'  : 1 , # set the line cap style
  'j'  : 1 , # set the line join style
  'M'  : 1 , # set the miter limit
  'd'  : 2 , # set the line dash pattern
  'ri' : 1 , # set the color rendering intent
  'i'  : 1 , # set the flatness tolerance (0-100)
  'gs' : 1 , # set the graphics state to reflect the argument
  'm'  : 2 , # move the drawing cursor and start a new subpath
  'l'  : 2 , # line to a new point
  'c'  : 6 , # cubic bezier curve
  'v'  : 4 , # simplified cubic bezier curve (from)
  'y'  : 4 , # simplified cubic bezier curve (to)
  'h'  : 0 , # line to the beginning of the current subpath
  're' : 4 , # draw a rectangle
  'S'  : 0 , # stroke the path
  's'  : 0 , # close and then stroke the path (h S)
  'f'  : 0 , # fill the path using nonzero-winding
  'F'  : 0 , # fill the path (same as above)
  'f*' : 0 , # fill the path using even-odd
  'B'  : 0 , # fill and stroke the path using nonzero-winding
  'B*' : 0 , # fill and stroke the path using even-odd
  'b'  : 0 , # close, fill, and stroke using nonzero-winding (h B)
  'b*' : 0 , # close, fill, and stroke using even-odd (h B*)
  'n'  : 0 , # end the path without drawing anything (used for clipping path)
  'W'  : 0 , # intersect the clipping path with the current path using nonzero
  'W*' : 0 , # intersect the clipping path with the current path using even-odd
  'CS' : 1 , # set the current foreground color space
  'cs' : 1 , # set the current background color space
  'SC' : -1, # set the current foreground color (limited color spaces)
  'SCN': -1, # set the current foreground color (all color spaces)
  'sc' : -1, # set the current background color (limited color spaces)
  'scn': -1, # set the current background color (all color spaces)
  'G'  : 1 , # set the foreground color to a grayscale color
  'g'  : 1 , # set the background color to a grayscale color
  'RG' : 3 , # set the foreground color to an rgb color
  'rg' : 3 , # set the background color to an rgb color
  'K'  : 4 , # set the foreground color to a cmyk color
  'k'  : 4 , # set the background color to a cmyk color
  'Do' : 1 , # paint the referenced XObject
  'sh' : 1 , # paint the given shading dictionary
  'Tc' : 1 , # set the text character spacing
  'Tw' : 1 , # set the text word spacing
  'Tz' : 1 , # set the text horizontal scaling
  'TL' : 1 , # set the text leading
  'Tf' : 2 , # set the font and size for future texts
  'Tr' : 1 , # set the text rendering mode
  'Ts' : 1 , # set the text rise
  'Td' : 2 , # start a new line with offset from current line start
  'TD' : 2 , # start a new line with offset, and set leading
  'Tm' : 6 , # set a new text matrix and start a new line there
  'T*' : 0 , # start a new line using the current leading (0 l Td)
  'Tj' : 1 , # show the given string of text
  "'"  : 1 , # start a new line and show the given text (T* s Tj)
  '"'  : 3 , # start a new line and show, given word and char spacings
  'TJ' : 1 , # for each in the array, show if string, offset if number
  'd0' : 2 , # declare a type3 glyph description, and set its width
  'd1' : 6 , # declare a type3 glyph description, and set its width and bbox
  'MP' : 1 , # mark a point using a tag
  'DP' : 2 , # mark a point using a tag and a properties list
  'BMC': 1 , # mark a content set terminated by 'EMC' using a tag
  'BDC': 2 , # mark a content set terminated by 'EMC' using a tag and props
}

