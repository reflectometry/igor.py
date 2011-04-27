#!/usr/bin/env python
import sys
from distutils.core import setup
import igor

if len(sys.argv) == 1:
    sys.argv.append('install')

# README.rst is only needed to upload the package;
# it isn't needed for download and install.
try:
    long_description = open('README.rst').read()
except:
    long_description = None
dist = setup(
        name = 'igor.py',
        version = igor.__version__,
        author='Paul Kienzle',
        author_email='paul.kienzle@nist.gov',
        url='https://github.com/reflectometry/igor.py',
        description='Read Igor Pro files from python',
        long_description=long_description,
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Science/Research',
            'License :: Public Domain',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            ],
        py_modules = ['igor'],
        #data_files = ['README.rst'],
)

# End of file

