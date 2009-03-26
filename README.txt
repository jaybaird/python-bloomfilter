pybloom is a module that includes a Bloom Filter data structure along with
an implmentation of Scalable Bloom Filters as discussed in:

P. Almeida, C.Baquero, N. Preguiça, D. Hutchison, Scalable Bloom Filters,
(GLOBECOM 2007), IEEE, 2007.

Bloom filters are great if you understand what amount of bits you need to set
aside early to store your entire set. Scalable Bloom Filters allow your bloom
filter bits to grow as a function of false positive probability and size.

A filter is "full" when at capacity: M * ((ln 2 ^ 2) / abs(ln p)), where M
is the number of bits and p is the false positive probability. When capacity
is reached a new filter is then created exponentially larger than the last
with a tighter probability of false positives and a larger number of hash
functions.

>>> from pybloom import BloomFilter
>>> f = BloomFilter(capacity=1000, error_rate=0.001)
>>> [f.add(x) for x in range(10)]
[False, False, False, False, False, False, False, False, False, False]
>>> all([(x in f) for x in range(10)])
True
>>> 10 in f
False
>>> 5 in f
True
>>> f = BloomFilter(capacity=1000, error_rate=0.001)
>>> for i in xrange(0, f.capacity):
...     _ = f.add(i)
>>> abs((len(f) / float(f.capacity)) - 1.0) <= f.error_rate
True

>>> from pybloom import ScalableBloomFilter
>>> sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
>>> count = 10000
>>> for i in xrange(0, count):
...     _ = sbf.add(i)
...
>>> abs((len(sbf) / float(count)) - 1.0) <= sbf.error_rate
True

# len(sbf) may not equal the entire input length. 0.006% error is well
# below the default 0.1% error threshold
