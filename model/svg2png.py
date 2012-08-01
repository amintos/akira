#!/usr/bin/env python

import os
import sys
import subprocess

win64Path = 'C:\\Program Files (x86)\\Inkscape\\inkscape.exe'
win32Path = 'C:\\Program Files\\Inkscape\\inkscape.exe'
win64Command = win64Path

# hier beginnen pfade und kommandos
win64 = (win64Path, win64Command)
win32 = (win32Path, win32Path)

nicco = (win64Path, 'C:\\bin\\inkscape.bat')

macs = ('/Applications/Inkscape.app/Contents/Resources/bin/inkscape', \
         '/Applications/Inkscape.app/Contents/Resources/bin/inkscape')

ubuntu = ('/usr/bin/inkscape', 'inkscape')

# eigene hier einfuegen
inkscapePath = [\
    win64, \
    win32, \
    macs, \
    ubuntu, \
    nicco, \
    ]

inkCommand = None

for path, command in inkscapePath:
    if os.path.exists(path) and os.path.isfile(path):
        inkCommand = command
        break

def iterateSVG(folder):
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() == '.svg':
                filepath = os.path.join(dirpath, filename)
                yield filepath
 
if inkCommand is None:
    print ('inkscape wurde nicht gefunden.\n')
    exit(1)

def pngName(svg):
    base, ext = os.path.splitext(svg)
    return base + '.png'

def doConvert(svg, png):
    removeText(svg)
    print ('converting\t%s \n    to   \t%s' % (svg, png))
    pipe = subprocess.Popen([inkCommand, '-A', '%s' % png, '%s' % svg ])
    pipe.wait()

def convertIfNewer(svg):
    png = pngName(svg)
    if not os.path.exists(png) or \
       os.path.getmtime(png) + 10 < os.path.getmtime(svg):
        # 10 sekunden Zeitunterschied
        print ('converting\t%s \n    to   \t%s' % (svg, png))
        pipe = subprocess.Popen([inkCommand, '-f', str(svg), '-e', str(png), ])
        pipe.wait()

def svg2png(folder = '.'):
    for filename in iterateSVG(folder):
        convertIfNewer(filename)

if __name__ == '__main__':
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        doConvert(sys.argv[1], pngName(sys.argv[1]))
    else:
        svg2png()

