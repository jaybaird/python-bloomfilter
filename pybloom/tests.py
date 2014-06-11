from __future__ import absolute_import
from pybloom.pybloom import BloomFilter, ScalableBloomFilter
from pybloom.utils import running_python_3, range_fn

try:
    from StringIO import StringIO
    import cStringIO
except ImportError:
    from io import BytesIO as StringIO
import os
import doctest
import unittest
import random
import tempfile
from unittest import TestSuite

def additional_tests():
    proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_fn = os.path.join(proj_dir, 'README.txt')
    suite = TestSuite([doctest.DocTestSuite('pybloom.pybloom')])
    if os.path.exists(readme_fn):
        suite.addTest(doctest.DocFileSuite(readme_fn, module_relative=False))
    return suite

class TestUnionIntersection(unittest.TestCase):
    def test_union(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        chars = [chr(i) for i in range_fn(97, 123)]
        for char in chars[int(len(chars)/2):]:
            bloom_one.add(char)
        for char in chars[:int(len(chars)/2)]:
            bloom_two.add(char)
        new_bloom = bloom_one.union(bloom_two)
        for char in chars:
            self.assertTrue(char in new_bloom)

    def test_intersection(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        chars = [chr(i) for i in range_fn(97, 123)]
        for char in chars:
            bloom_one.add(char)
        for char in chars[:int(len(chars)/2)]:
            bloom_two.add(char)
        new_bloom = bloom_one.intersection(bloom_two)
        for char in chars[:int(len(chars)/2)]:
            self.assertTrue(char in new_bloom)
        for char in chars[int(len(chars)/2):]:
            self.assertTrue(char not in new_bloom)

    def test_intersection_capacity_fail(self):
        bloom_one = BloomFilter(1000, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        def _run():
            new_bloom = bloom_one.intersection(bloom_two)
        self.assertRaises(ValueError, _run)

    def test_union_capacity_fail(self):
        bloom_one = BloomFilter(1000, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        def _run():
            new_bloom = bloom_one.union(bloom_two)
        self.assertRaises(ValueError, _run)

    def test_intersection_k_fail(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.01)
        def _run():
            new_bloom = bloom_one.intersection(bloom_two)
        self.assertRaises(ValueError, _run)

    def test_union_k_fail(self):
        bloom_one = BloomFilter(100, 0.01)
        bloom_two = BloomFilter(100, 0.001)
        def _run():
            new_bloom = bloom_one.union(bloom_two)
        self.assertRaises(ValueError, _run)

class Serialization(unittest.TestCase):
    SIZE = 12345
    EXPECTED = set([random.randint(0, 10000100) for _ in range_fn(SIZE)])

    def test_serialization(self):
        for klass, args in [(BloomFilter, (self.SIZE,)),
                            (ScalableBloomFilter, ())]:
            filter = klass(*args)
            for item in self.EXPECTED:
                filter.add(item)

            f = tempfile.TemporaryFile()
            filter.tofile(f)
            stringio = StringIO()
            filter.tofile(stringio)
            streams_to_test = [f, stringio]
            if not running_python_3:
                cstringio = cStringIO.StringIO()
                filter.tofile(cstringio)
                streams_to_test.append(cstringio)

            del filter

            for stream in streams_to_test:
                stream.seek(0)
                filter = klass.fromfile(stream)
                for item in self.EXPECTED:
                    self.assertTrue(item in filter)
                del(filter)
                stream.close()

if __name__ == '__main__':
    unittest.main()
