#!/usr/bin/env python
from setuptools import setup

VERSION = '2.1.0'
DESCRIPTION = "Bloom filter: A Probabilistic data structure"
LONG_DESCRIPTION = """
This bloom filter is forked from pybloom_live, and it is a Python implementation of the bloom filter probabilistic data
structure. The module also provides a Scalable Bloom Filter that allows a
bloom filter to grow without knowing the original set size.
"""

CLASSIFIERS = filter(None, map(str.strip,
"""
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: Python :: 3
Operating System :: OS Independent
Topic :: Utilities
Topic :: Database :: Database Engines/Servers
Topic :: Software Development :: Libraries :: Python Modules
""".splitlines()))

setup(
    name="pybloom_live",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    keywords=('data structures', 'bloom filter', 'bloom', 'filter',
              'probabilistic', 'set'),
    author="Jay Baird",
    author_email="jay.baird@me.com",
    url="https://github.com/joseph-fox/python-bloomfilter",
    license="MIT License",
    platforms=['any'],
    test_suite="pybloom_live.tests",
    zip_safe=True,
    install_requires=['bitarray>=0.3.4'],
    packages=['pybloom_live']
)
