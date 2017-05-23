pybloom2
=======


``pybloom2`` is a fork of https://github.com/jaybaird/python-bloomfilter.
It includes a Bloom Filter data structure along with
an implementation of Scalable Bloom Filter[1].


.. code-block:: python

    >>> from pybloom2 import BloomFilter
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
    >>> (1.0 - (len(f) / float(f.capacity))) <= f.error_rate + 2e-18
    True

    >>> from pybloom2 import ScalableBloomFilter
    >>> sbf = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
    >>> count = 10000
    >>> for i in xrange(0, count):
    ...     _ = sbf.add(i)
    ...
    >>> (1.0 - (len(sbf) / float(count))) <= sbf.error_rate + 2e-18
    True

    # len(sbf) may not equal the entire input length. 0.01% error is well
    # below the default 0.1% error threshold. As the capacity goes up, the
    # error will approach 0.1%.


..
references
==========
[1] P. Almeida, C.Baquero, N. Preguiça, D. Hutchison, Scalable Bloom Filters, (GLOBECOM 2007), IEEE, 2007. http://www.sciencedirect.com/science/article/pii/S0020019006003127