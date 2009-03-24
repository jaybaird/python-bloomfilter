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

bloomfilter is a module that includes a bloomfilter data structure and 
an implmentation of Scalable Bloom Filters as discussed in:

P. Almeida, C.Baquero, N. Preguica, D. Hutchison, Scalable Bloom Filters,
(GLOBECOM 2007), IEEE, 2007.

Bloom filters are great if you understand the amount of bits you need to set
aside early to store your entire set. Scalable Bloom Filters allow your bloom
filters to grow as more elements are stored inside them.

A filter is "full" when it's capacity: M * ((ln 2 ^ 2) / abs(ln p)), where M
is the number of bits and p is the false positive probability, is reached. A
new filter is then created exponentially larger than the last with a tighter
probability of false positives and a larger k.

Requires the bitarray library: http://pypi.python.org/pypi/bitarray/
"""

__version__ = '2.0'
__author__  = "Jay Baird (jay.baird@mochimedia.com)"
__date__    = '2009-March-23'

import math
import array

try:
    import bitarray
except ImportError:
    raise ImportError, 'python-bloomfilter requires bitarray >= 0.3.4'


class bloomfilter(object):
    def __init__(self, bits, hashes, probability=0.001):
        """
        Implements a space-efficient probabilistic data structure

        bits
            the size of the filter, in bits. Must be a power of two.
        hashes
            the number of hashes to get positions in the bitarray.
        probability
            the probability of the filter returning false positives. This
            determines the filters capacity. Going over capacity greatly
            increases the chance of false positives.

        >>> b = bloomfilter(bits=8192, hashes=4, probability=0.001)
        >>> b.add("test")
        False
        >>> "test" in b
        True
        """
        if not bits or not bits % 2 == 0:
            raise ValueError, "Bits must be a power of two."
        if not hashes or hashes <= 0:
            raise ValueError, "Hashes must be greater than or equal to one."
        if probability < 0:
            raise ValueError, "Probability must be a decimal less than 0."
        self.k = hashes
        self.m = bits
        self.p = probability
        self.capacity = int(self.m * (pow(math.log(2), 2) /
                            abs(math.log(self.p))))
        self.count = 0
        self.filter = bitarray.bitarray(self.m)
        self.filter.setall(False)

    def _hashes(self, key):
        """
        Implements FNV-1a hash
        http://en.wikipedia.org/wiki/Fowler_Noll_Vo_hash#FNV-1a_hash
        an integer of the key number is added to the front of the key, so the
        key 'foo' and four hashes will hash ['0foo', '1foo', '2foo', '3foo']

        >>> b = bloomfilter(bits=8192, hashes=4)
        >>> b._hashes([1,2,3])
        [2083, 708, 3552, 1653]
        >>> b._hashes("hello")
        [1621, 4172, 1042, 5745]
        """
        rv = 0x811c9dc5L # FNV Offset Basis

        if not isinstance(key, basestring):
            key = str(key)
        else:
            key = key.encode("utf-8")

        hashes = list()

        for i in range(self.k):
            byte_array = array.array("B")
            byte_array.fromstring(str(i) + key)
            for byte in byte_array:
                rv = (rv ^ (byte & 0xff)) * 16777619 # FNV Prime
            hashes.append(int((rv & 0xffffffffL) & (self.m - 1))) 

        return hashes

    def __contains__(self, key):
        """
        Tests a key's membership in this bloom filter.

        >>> b = bloomfilter(bits=8192, hashes=4)
        >>> b.add("hello")
        False
        >>> "hello" in b
        True
        """

        if not isinstance(key, list):
            hashes = self._hashes(key)
        else:
            hashes = key

        for k in hashes:
            if not self.filter[k]:
                return False
        return True

    def add(self, key):
        """
        Adds a key to this bloom filter. If the key already exists in this
        filter it will return True. Otherwise False.

        >>> b = bloomfilter(bits=8192, hashes=4)
        >>> b.add("hello")
        False
        >>> b.add("hello")
        True
        """
        h = self._hashes(key)
        if h in self:
            return True
        for k in h:
            self.filter[k] = True
        self.count += 1

        return False


class scalablebloomfilter(object):
    SMALL_SET_GROWTH = 2 # slower, but takes up less memory
    LARGE_SET_GROWTH = 4 # faster, but takes up more memory faster

    def __init__(self, bits=8192, hashes=4, probability=0.001, 
                 mode=SMALL_SET_GROWTH):
        if not bits % 2 == 0:
            raise ValueError, "Bits must be a power of two."
        if hashes <= 0:
            raise ValueError, "Hashes must be greater than or equal to one."
        if probability < 0:
            raise ValueError, "Probability must be a decimal less than 0."
        self.s = mode
        self.r = 0.9
        self.k = hashes
        self.m = bits
        self.p = probability
        self.filters = [bloomfilter(bits, hashes, probability)]
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
        if self.active_filter.count == self.active_filter.capacity:
            new_prob = self.active_filter.p * self.r
            new_hashes = int(math.ceil(self.active_filter.k + self.r))
            new_bits = self.m * pow(self.s, len(self.filters))
            new_filter = bloomfilter(bits=new_bits, hashes=new_hashes,
                                     probability=new_prob)
            self.active_filter = new_filter
            self.filters.append(new_filter)
        return dupe

    def capacity(self):
        return sum([f.capacity for f in self.filters])

    def __len__(self):
        return sum([f.count for f in self.filters])


if __name__ == "__main__":
    import doctest
    doctest.testmod()