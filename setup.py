from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

setup(
  name = 'bitset',
  ext_modules=[ 
    Extension("bitset", ["bitset.pyx"]),
    ],
  cmdclass = {'build_ext': build_ext}
)