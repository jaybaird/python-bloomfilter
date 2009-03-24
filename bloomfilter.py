"""
This module implements a bloomfilter probabilistic data structure and 
an a Scalable Bloom Filter that grows in size as your add more items to it
without increasing the false positive probability.

Requires the bitarray library: http://pypi.python.org/pypi/bitarray/

    >>> from bloomfilter import BloomFilter
    >>> filter = BloomFilter(bits=8192, hashes=4, probability=0.001)
    >>> [filter.add(x) for x in range(10)]
    [False, False, False, False, False, False, False, False, False, False]
    >>> all([(x in filter) for x in range(10)])
    True
    >>> 10 in filter
    False
    >>> 5 in filter
    True
"""

__version__ = '2.0'
__author__  = "Jay Baird <jay.baird@mochimedia.com>"
__date__    = '2009-March-23'

import math
import array

try:
    import bitarray
except ImportError:
    raise ImportError, 'bloomfilter requires bitarray >= 0.3.4'

def fnv_hash(bytes, rv=0x811c9dc5):
    """
    Implements 32-bit FNV-1a hash
    http://www.isthe.com/chongo/tech/comp/fnv/index.html#FNV-1a
    """
    fnv_prime = 0x1000193
    for c in array.array('B', bytes):
        rv = 0xffffffff & ((rv ^ c) * fnv_prime)
    return rv

def fnv_hashes(key, num_hashes):
    """
    Generates num_hashes indexes based on an FNV-1a hash of the key
    """
    if not isinstance(key, unicode):
        key = key.encode('utf-8')
    else:
        key = str(key)
    rv = fnv_hash(key)
    mask = self.m - 1
    return [fnv_hash(str(i), rv) & mask for i in xrange(num_hashes)]


class BloomFilter(object):
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

        >>> b = BloomFilter(bits=8192, hashes=4, probability=0.001)
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
            hashes = fnv_hashes(key, self.k)
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
        h = fnv_hashes(key, self.k)
        if h in self:
            return True
        for k in h:
            self.filter[k] = True
        self.count += 1

        return False


class ScalableBloomFilter(object):
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