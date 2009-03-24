"""This module implements a bloom filter probabilistic data structure and 
an a Scalable Bloom Filter that grows in size as your add more items to it
without increasing the false positive probability.

Requires the bitarray library: http://pypi.python.org/pypi/bitarray/

    >>> from pybloom import BloomFilter
    >>> f = BloomFilter(bits=8192, probability=0.001)
    >>> for i in xrange(0, f.capacity):
    ...     _ = f.add(i)
    ...
    >>> 500 in f
    True
    >>> f.capacity in f
    False
    >>> abs((len(sbf) / 100000.0) - 1.0) <= f.probability
    True

    >>> from pybloom import ScalableBloomFilter
    >>> sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
    >>> for i in xrange(0, 100000):
    ...     _ = sbf.add(i)
    ...
    >>> (sum([f.bits for f in sbf.filters]) / 8) / 1024.0
    255.0
    >>> sbf.capacity
    133100
    >>> len(sbf)
    94609
    >>> abs((len(sbf) / 100000.0) - 1.0) <= sbf.probability
    True
    # len(sbf) may not equal the entire input length. 0.006% error is well
    # below the default 0.1% error threshold

"""

import math
import array

try:
    import bitarray
except ImportError:
    raise ImportError('pybloom requires bitarray >= 0.3.4')

def fnv_hash(bytes, rv=0x811c9dc5):
    """Implements 32-bit FNV-1a hash
    http://www.isthe.com/chongo/tech/comp/fnv/index.html#FNV-1a

    """
    fnv_prime = 0x1000193
    for c in array.array('B', bytes):
        rv = 0xffffffff & ((rv ^ c) * fnv_prime)
    return rv

def fnv_hashes(key, num_hashes, num_bits):
    """Generates num_hashes indexes based on an FNV-1a hash of the key"""
    if isinstance(key, basestring) and not isinstance(key, unicode):
        key = key.encode('utf-8')
    else:
        key = str(key)
    mask = num_bits - 1
    rv = fnv_hash(key)
    return [fnv_hash(str(i), rv) & mask for i in xrange(num_hashes)]


class BloomFilter(object):
    def __init__(self, bits, probability=0.001):
        """Implements a space-efficient probabilistic data structure

        bits
            the size of the filter, in bits. Must be a power of two.
        probability
            the probability of the filter returning false positives. This
            determines the filters capacity. Going over capacity greatly
            increases the chance of false positives.

        >>> b = BloomFilter(bits=8192, probability=0.001)
        >>> b.add("test")
        False
        >>> "test" in b
        True

        """
        if not bits or bits != 1 << int(math.log(bits) / math.log(2)):
            raise ValueError("Bits must be a power of two.")
        if not probability or probability < 0:
            raise ValueError("Probability must be a decimal less than 0.")
        self.bits = bits
        self.probability = probability
        self.hashes = int(round(math.log(1/self.probability, 2)))
        self.capacity = int(round(self.bits * pow(math.log(2), 2) /
                                           abs(math.log(self.probability))))
        self.count = 0
        self.filter = bitarray.bitarray(self.bits)
        self.filter.setall(False)

    def __contains__(self, key):
        """Tests a key's membership in this bloom filter.

        >>> b = BloomFilter(bits=8192)
        >>> b.add("hello")
        False
        >>> "hello" in b
        True

        """
        if not isinstance(key, list):
            hashes = fnv_hashes(key, self.hashes, self.bits)
        else:
            hashes = key

        for k in hashes:
            if not self.filter[k]:
                return False
        return True

    def __len__(self):
        """Return the number of keys stored by this bloom filter."""
        return self.count

    def add(self, key):
        """ Adds a key to this bloom filter. If the key already exists in this
        filter it will return True. Otherwise False.

        >>> b = BloomFilter(bits=8192)
        >>> b.add("hello")
        False
        >>> b.add("hello")
        True

        """
        h = fnv_hashes(key, self.hashes, self.bits)
        if h in self:
            return True
        for k in h:
            self.filter[k] = True
        self.count += 1
        return False


class ScalableBloomFilter(object):
    SMALL_SET_GROWTH = 2 # slower, but takes up less memory
    LARGE_SET_GROWTH = 4 # faster, but takes up more memory faster

    def __init__(self, bits=8192, probability=0.001, mode=SMALL_SET_GROWTH):
        """ Implements a space-efficient probabilistic data structure that
        grows as more items are added while maintaining a steady false
        positive rate

        bits
            the size of the filter, in bits. Must be a power of two.
        probability
            the probability of the filter returning false positives. This
            determines the filters capacity. Going over capacity greatly
            increases the chance of false positives.
        mode
            can be either ScalableBloomFilter.SMALL_SET_GROWTH or
            ScalableBloomFilter.LARGE_SET_GROWTH. SMALL_SET_GROWTH is slower
            but uses less memory. LARGE_SET_GROWTH is faster but consumes
            memory faster.

        >>> b = ScalableBloomFilter(bits=8192, probability=0.001, \
                                    mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        >>> b.add("test")
        False
        >>> "test" in b
        True
        
        """
        if not bits or bits != 1 << int(math.log(bits) / math.log(2)):
            raise ValueError("Bits must be a power of two.")
        if not probability or probability < 0:
            raise ValueError("Probability must be a decimal less than 0.")
        self.scale = mode
        self.ratio = 0.9
        self.bits = bits
        self.probability = probability
        self.filters = [BloomFilter(bits=bits, probability=probability)]
        self.filter = self.filters[0]

    def __contains__(self, key):
        """Tests a key's membership in this bloom filter.

        >>> b = ScalableBloomFilter(bits=8192, probability=0.001, \
                                    mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        >>> b.add("hello")
        False
        >>> "hello" in b
        True

        """
        for f in self.filters:
            if key in f:
                return True
        return False

    def add(self, key):
        """Adds a key to this bloom filter. 
        If the key already exists in this filter it will return True. 
        Otherwise False.

        >>> b = ScalableBloomFilter(bits=8192, probability=0.001, \
                                    mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        >>> b.add("hello")
        False
        >>> b.add("hello")
        True

        """
        dupe = self.filter.add(key)
        if dupe:
            return dupe
        if self.filter.count == self.filter.capacity:
            prob = self.filter.probability * self.ratio
            bits = self.bits * pow(self.scale, len(self.filters))
            new_filter = BloomFilter(bits=bits, probability=prob)
            self.filter = new_filter
            self.filters = [new_filter] + self.filters
        return dupe

    @property
    def capacity(self):
        """Returns the total capacity for all filters in this SBF"""
        return sum([f.capacity for f in self.filters])

    @property
    def count(self):
        return len(self)

    def __len__(self):
        """Returns the total number of elements stored in this SBF"""
        return sum([f.count for f in self.filters])

    def size(self):
        return sum([len(f.filter) for f in self.filters])

if __name__ == "__main__":
    import doctest
    doctest.testmod()