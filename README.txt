bloomfilter is a module that includes a bloomfilter data structure along with 
an implmentation of Scalable Bloom Filters as discussed in:

P. Almeida, C.Baquero, N. Preguiça, D. Hutchison, Scalable Bloom Filters, 
(GLOBECOM 2007), IEEE, 2007.

Bloom filters are great if you understand what amount of bits you need to set
aside early to store your entire set. Scalable Bloom Filters allow your bloom
filter bits to grow as a function of false positive probability and size.

A filter is "full" when it's capacity: M * ((ln 2 ^ 2) / abs(ln p)), where M 
is the number of bits and p is the false positive probability, is reached a 
new filter is then created exponentially larger than the last with a tighter 
probability of false positives and a larger k.

The defaults are fairly sane for large sets:
>>> from bloomfilter import ScalableBloomFilter
>>> sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
>>> [sbf.add(i) for i in xrange(0, 100000)]
>>> (sum([f.m for f in sbf.filters]) / 8) / 1024
255 # kilobytes
>>> sbf.capacity()
133095
>>> len(sbf)
99994 # len(sbf) may not equal the entire input length. 0.006% error is well 
below the default 0.1% error threshold 