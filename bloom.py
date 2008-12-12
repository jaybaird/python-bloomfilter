"""
The MIT License

Copyright (c) <2008> <Jay Baird>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Requires the BitVector library: http://RVL4.ecn.purdue.edu/~kak/dist/BitVector-1.5.1.html
"""

__version__ = '1.0'
__author__  = "Jay Baird (jay.baird@mochimedia.com)"
__date__    = '2008-December-10'

import zlib
import math
import hashlib
import base64

from cStringIO import StringIO

try:
    from bit_vector import BitVector
except ImportError:
    raise ImportError, 'python-sbf requires BitVector >= 1.5.1'

class BloomFilter(object):
    def __init__(self, m=None, k=None, p=0.001):
        self.k = k
        self.m = m
        self.p = p
        self.stripe_size = int(math.ceil(self.m/self.k))
        self.n = int(self.m * (pow(math.log(2), 2) / abs(math.log(self.p))))
        self.count = 0

        self.slices = [BitVector(size=self.stripe_size) for i in xrange(int(math.ceil(self.m/(self.m/self.k))))]

    def _hashes(self, key):
        if not isinstance(key, basestring):
            key = str(key)
        d = hashlib.sha512(key).hexdigest()
        # doesn't support k > 25. yet.
        return [int(d[i*5:i*5+5], 16) % self.stripe_size for i in range(self.k)]
        #return hashes

    def __contains__(self, key):
        for j,k in enumerate(self._hashes(key)):
            if not self.slices[j][k]:
                return False    
        return True 

    def add(self, key):
        if key in self:
            return True
        for j,k in enumerate(self._hashes(key)):
            self.slices[j][k] = 1
        self.count += 1
        return False
        
    def serialize(self):
        compressed_slices = []
        for s in self.slices:
            f = StringIO()
            s.write_bits_to_fileobject(f)
            compressed_slices.append(base64.encodestring(zlib.compress(f.getvalue())))
        data = dict(
            k=self.k,
            m=self.m,
            p=self.p,
            n=self.n,
            count=self.count,
            strip_size=self.stripe_size,
            slices=compressed_slices
        )
        return data

class ScalableBloomFilter(object):
    SMALL_SET_GROWTH = 2 # slower, but takes up less memory
    LARGE_SET_GROWTH = 4 # faster, but takes up more memory faster
    
    def __init__(self, m=8192, k=4, p=0.001, mode=SMALL_SET_GROWTH):
        self.s = mode
        self.r = 0.9
        self.k = k
        self.m = m
        self.p = p
        self.filters = [BloomFilter(m=m, k=k, p=p)]
        self.active_filter = self.filters[0]
        
    def __contains__(self, key):
        for f in self.filters:
            if key in f:
                return True
        return False
        
    def add(self, key):
        dupe = self.active_filter.add(key)
        if dupe:
            return dupe
        if self.active_filter.count == self.active_filter.n:
            new_filter = BloomFilter(m=(self.m * pow(self.s, len(self.filters))), 
                                     k=int(math.ceil(self.active_filter.k + self.r)), 
                                     p=self.active_filter.p * self.r)
            ## print "Filter is full, creating new filter, size: %d, k: %d" % (new_filter.m, new_filter.k)
            self.active_filter = new_filter
            self.filters.append(new_filter)
        return dupe
        
    def capacity(self):
        capacity = 0
        for f in self.filters:
            capacity += f.n
        return capacity
        
    def __len__(self):
        counts = 0
        for f in self.filters:
            counts += f.count
        return counts
        
    def serialize(self):
        filters = []
        for f in self.filters:
            filters.append(f.serialize())
        dct = dict(
            s=self.s,
            r=self.r,
            k=self.k,
            m=self.m,
            p=self.p,
            filters=filters
        )
        return dct
        
def test_bloom_filter():
    e = BloomFilter(m=100, k=4)
    vals = ['one', 'two', 'three', 'four', 'five']
    for val in vals:
        e.add(val)
    assert 'one' in e
    assert 'two' in e
    assert 'three' in e
    assert 'four' in e
    assert 'five' in e
    assert 'six' not in e
    
def test_sbf_false_positive():
    sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
    false_pos = 0
    for i in xrange(0, 100000):
        if sbf.add(i):
            false_pos += 1
    print '%.3f%%' % (100 * (false_pos / float(100000)))
    assert (false_pos/100000) <= sbf.p
    
if __name__ == '__main__':
    test_bloom_filter()
    test_sbf_false_positive()