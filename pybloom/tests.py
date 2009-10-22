import os
import doctest
import unittest
import random
import tempfile
from pybloom import BloomFilter, ScalableBloomFilter
from unittest import TestSuite
 
def additional_tests():
    proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_fn = os.path.join(proj_dir, 'README.txt')
    suite = TestSuite([doctest.DocTestSuite('pybloom.pybloom')])
    if os.path.exists(readme_fn):
        suite.addTest(doctest.DocFileSuite(readme_fn, module_relative=False))
    return suite

class Serialization(unittest.TestCase):
    SIZE = 12345
    EXPECTED = set([random.randint(0, 10000100) for _ in xrange(SIZE)])

    def test_serialization(self):
        for klass, args in [(BloomFilter, (self.SIZE,)),
                            (ScalableBloomFilter, ())]:
            filter = klass(*args)
            for item in self.EXPECTED:
                filter.add(item)

            # It seems bitarray is finicky about the object being an
            # actual file, so we can't just use StringIO. Grr.
            f = tempfile.TemporaryFile()
            filter.tofile(f)
            del filter

            f.seek(0)
            filter = klass.fromfile(f)

            for item in self.EXPECTED:
                self.assert_(item in filter)

if __name__ == '__main__':
    unittest.main()
