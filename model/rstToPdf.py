#!/usr/bin/env python2
'''
this program started as main program will make all rst files, found in the
folder it is run in, to pdf files.
'''

import sys
import os
import urllib
import gzip
import tarfile
import atexit
import traceback
import subprocess


def iterateRstFiles(folder, ending = ('.rst',)):
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() in ending:
                filepath = os.path.join(dirpath, filename)
                yield filepath

def download(url, filename):
    handle = urllib.urlopen(url)
    if handle.code != 200:
        raise IOError('code should be 200, not %s' % handle.code)
    with open(filename, 'wb') as out:
        copyTo(handle, out)

def extract_gz(filename):
    f = gzip.GzipFile(filename)
    t = tmpnam()
    with open(t, 'wb') as out:
        copyTo(f, out)
    return t

def copyTo(source, destination):
    while True:
        data = source.read(1024)
        if len(data) == 0: break
        destination.write(data)

def extact_tar(filename):
     tar = tarfile.open(filename, 'r')
     for item in tar:
         tar.extract(item, extract_path)

def extract_tar(filename):
    tar = tarfile.open(filename)
    tmpname = tmpnam()
    tar.extractall(tmpname)
    return tmpname

_tmp_names = []
def tmpnam():
    name = os.tempnam()
    _tmp_names.append(name)
    return name

def _del_tmps():
    for tmpname in _tmp_names:
        try:
            if os.path.isfile(tmpname):
                os.remove(tmpname)
            elif os.path.isdir(tmpname):
                for dirpath, dirnames, filenames in os.walk(tmpname):
                    for fileName in filenames:
                        os.remove(os.path.join(dirpath, fileName))
                for dirpath, dirnames, filenames in os.walk(tmpname, \
                                                            topdown = False):
                    for dirName in dirnames:
                        dirPath = os.path.join(dirpath, dirName)
                        if os.path.exists(dirPath):
                            os.removedirs(dirPath)
        except:
            traceback.print_exc()
        
atexit.register(_del_tmps)

def find(dirname, filename):
    for dirpath, dirnames, filenames in os.walk(dirname):
        if filename in filenames:
            yield os.path.join(dirpath, filename)


def install(filename):
    p = subprocess.Popen([sys.executable, filename, 'install'], \
                     stdout = subprocess.PIPE, \
                     stdin = subprocess.PIPE, \
                     stderr = subprocess.PIPE, \
                     cwd = os.path.dirname(filename), \
                     )
    stdout, stderr = p.communicate()
    return stdout, stderr, p.returncode

def download_install_tar_gz(url, debug = 0):
    tmpname = tmpnam()
    if debug: print 'downloading from', url
    download(url, tmpname)
    if debug: print 'extract gz from', tmpname
    gzname = extract_gz(tmpname)
    if debug: print 'extract tar from', gzname
    tarname = extract_tar(gzname)
    if debug: print 'find setup from', tarname
    for setup in find(tarname, 'setup.py'):
        if debug: print 'exec setup', setup
        return install(setup)


def setup():
    url_setuptools = 'http://pypi.python.org/packages/source/s/setuptools/setup'\
                     'tools-0.6c11.tar.gz#md5=7df2a529a074f613b509fb44feefe74e'
    url_rst2pdf = 'http://rst2pdf.googlecode.com/files/rst2pdf-0.91.tar.gz'
    url_roman = 'http://pypi.python.org/packages/source/r/roman/'\
                'roman-1.4.0.tar.gz#md5=4f8832ed4108174b159c2afb4bd1d1dd'
    urls = []
    try: import setuptools
    except ImportError: urls.append(url_setuptools)
    try: import rst2pdf
    except ImportError: urls.append(url_rst2pdf)
    try: import roman
    except ImportError: urls.append(url_roman)
    install_tar_gzs(urls)

def install_tar_gzs(urls, debug = 1):
    for url in urls:
        print '-' * 80
        stdout, stderr, code= download_install_tar_gz(url, debug = 1)
        print stdout
        print stderr
        if code != 0:
            print 'Program exited with error code %s' % code


def iterFiles(directory, ext):
    for filePath in iterateRstFiles(directory):
        dirPath, fileName = os.path.split(filePath)
        outName = os.path.splitext(fileName)[0] + ext
        outputPath = os.path.join(dirPath, outName)
        if not os.path.exists(outputPath) or \
           os.path.getmtime(outputPath) + 10 < os.path.getmtime(filePath):
            yield filePath, outputPath

def rstToPdf(directory):
    import rst2pdf.createpdf as createpdf
    for filePath, pdfPath in iterFiles(directory, '.pdf'):
            print filePath
            print 'to pdf: ', pdfPath
            createpdf.main([filePath, '-o', pdfPath])




def main():
    setup()
    try:
        rstToPdf(os.getcwd())
    except:
        traceback.print_exc()
        raw_input('Type RETURN to exit >')
        
if __name__ == '__main__':
    main()
