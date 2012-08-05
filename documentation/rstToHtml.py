'''This module together with the rstToPdf module converts the .rst files to html

It will automatically install all dependencies.

'''

from rstToPdf import *


def setup():
    url_setuptools = 'http://pypi.python.org/packages/source/s/setuptools/setup'\
                     'tools-0.6c11.tar.gz#md5=7df2a529a074f613b509fb44feefe74e'
    url_docutils = 'downloads.sourceforge.net/project/docutils/docutils/0.9.1/'\
                   'docutils-0.9.1.tar.gz?r=&ts=1343825473&use_mirror=garr'

    urls = []
    try: import setuptools
    except ImportError: urls.append(url_setuptools)
    try: import docutils
    except ImportError: urls.append(url_docutils)
    install_tar_gzs(urls)
    
def rstToHtml(directory):
    from docutils.examples import html_parts
    for filePath, htmlPath in iterFiles(directory, '.html'):
            print filePath
            print 'to html: ', htmlPath
            rst = open(filePath).read().decode('UTF-8')
            html = html_parts(rst, filePath, htmlPath)
            open(htmlPath, 'w').write(html['whole'].encode('UTF-8'))


    
def main():
    setup()
    try:
        rstToHtml(os.getcwd())
    except:
        import sys
        if 'idlelib' in sys.modules:
            raise
        else:
            traceback.print_exc()
            raw_input('Type RETURN to exit >')
        
if __name__ == '__main__':
    main()
