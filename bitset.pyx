ctypedef int size_t
cdef extern from "stdlib.h":
  void *malloc(size_t size)
  void *calloc(size_t nmemb, size_t size)
  void *realloc(void *ptr, size_t size)
  void *memcpy(void *dest, void *src, size_t n)
  int free(void*)
  int sizeof()

cdef extern from "strings.h":
  void bzero(void *s, size_t n)
  
cdef class BitSet:

  # The actual data buffer
  cdef unsigned char *data

  # The allocated size of the data buffer
  cdef size_t dlen

  # The retained number of bits - this might be smaller
  # than dlen*8 since we can pre-allocated a large buffer
  # to make things faster
  cdef size_t bitlen
  
  def __new__(self, bit_capacity=0, initial_bit_len=0):
    cdef size_t initial_dlen

    initial_dlen = bit_capacity / 8
    if bit_capacity % 8 > 0:
      initial_dlen = initial_dlen + 1
      
    if initial_dlen > 0:
      self.data = <unsigned char *>calloc(initial_dlen, 1)
    else:
      self.data = NULL
    self.dlen = initial_dlen
    self.bitlen = initial_bit_len
    
  def __dealloc__(self):
    if self.data != NULL:
      free(self.data)


  def check(self):
    """Check correctness of lengths"""
    cdef int required_bits
    required_bytes = self.bitlen / 8
    if self.bitlen % 8 > 0:
      required_bytes = required_bytes + 1

    assert(self.dlen >= required_bytes)

  def __str__(self):
    cdef char *out
    out = <char *>malloc(self.bitlen + 1)

    cdef i
    for 0 <= i < self.bitlen:
      if self.__getitem__(i):
        out[i] = c'1'
      else:
        out[i] = c'0'

    out[self.bitlen] = c'\0'
    return out

  def __len__(self):
    return self.bitlen

  def __setitem__(self, int bit, int val):
    cdef size_t byte, bit_in_byte, need_len

    byte = bit / 8
    bit_in_byte = bit % 8

    need_len = byte + 1
    if self.dlen < need_len:
      #print "realloc (have %d need %d)" % (self.dlen, need_len)
      self.data = <unsigned char *>realloc(self.data, need_len)
      if self.data == NULL:
        raise "out of memory"
      bzero(self.data + self.dlen,
            need_len - self.dlen)
      self.dlen = need_len

    if bit >= self.bitlen:
      self.bitlen = bit + 1

    cdef unsigned char bitmask
    bitmask = (val << bit_in_byte)
    self.data[byte] = self.data[byte] & (~bitmask) | bitmask


  def __iadd__(self, int val):
    cdef int bit
    bit = self.bitlen
    self.__setitem__(bit, val)
    return self

  def __getitem__(self, int bit):
    cdef size_t byte, bit_in_byte
    byte = bit / 8
    bit_in_byte = bit % 8
    
    if self.dlen <= byte:
      return 0

    return self.data[byte] & (1 << bit_in_byte)

  def get_bits(self):
    cdef size_t cur_bit, cur_byte, num_bytes, i, j

    num_bytes = self.bitlen / 8

    cdef list res
    res = []

    cur_bit = 0
    for 0 <= i < num_bytes:
      cur_byte = self.data[i]
      
      for 0 <= j < 8:
        if cur_byte & 0x01:
          res.append(cur_bit)
        cur_bit = cur_bit + 1
        cur_byte = cur_byte >> 1

    cdef size_t extra_bits
    extra_bits = self.bitlen - cur_bit
    if extra_bits:
      cur_byte = self.data[num_bytes]
      for 0 <= i < extra_bits:
        if cur_byte & 0x01:
          res.append(cur_bit)
        cur_bit = cur_bit + 1
        cur_byte = cur_byte >> 1

    return res
    
  def __invert__(BitSet self):
    cdef BitSet res
    res = BitSet(self.bitlen, self.bitlen)

    cdef int len_words, i
    cdef unsigned int *self_int, *res_int

    len_words = self.bitlen / 8 / sizeof(int)
    self_int = <unsigned int *>self.data
    res_int  = <unsigned int *>res.data

    for 0 <= i < len_words:
      res_int[i] = ~self_int[i]

    i = i * sizeof(int)

    # Copy over the rest of the full bytes
    cdef len_bytes
    len_bytes = self.bitlen / 8
    
    while i < len_bytes:
      res.data[i] = ~self.data[i]
      i = i + 1

    cdef extra_bits
    extra_bits = self.bitlen % 8

    # we may have now some extra bits in the last byte
    # so we need to copy just those bits

    cdef unsigned char mask

    if extra_bits > 0:
      mask = (1 << (extra_bits)) - 1
      res.data[i] = (~self.data[i]) & mask
      
    return res
    

  def __or__(BitSet self, BitSet other):
    self.check()
    other.check()
    
    cdef size_t minlen, maxlen
    cdef BitSet bigger

    if self.bitlen < other.bitlen:
      minlen = self.dlen
      maxlen = other.dlen
      bigger = other
    else:
      minlen = other.dlen
      maxlen = self.dlen
      bigger = self
      
    cdef BitSet result
    result = BitSet(bigger.bitlen, bigger.bitlen)

    cdef size_t i

    # First copy as much as possible using
    # machine word size
    cdef unsigned int *a_int, *b_int, *r_int
    a_int = <unsigned int *>self.data
    b_int = <unsigned int *>other.data
    r_int = <unsigned int *>result.data

    cdef int minlen_words
    minlen_words = minlen / sizeof(int)

    i = 0
    while i < minlen_words:
      r_int[i] = a_int[i] | b_int[i]
      i = i + 1

    # now we're going to use i in terms of bytes, so
    # the counter needs to be turned into a byte counter
    i = i * sizeof(int)

    while i < minlen:
      result.data[i] = self.data[i] | other.data[i]
      i = i + 1

    # now we can just use memcpy to copy the rest
    # since we're orring with 0s on the smaller side
    cdef unsigned char *src, *dst
    dst = result.data + i
    src = bigger.data + i
    memcpy(<void *>dst, <void *>src, maxlen - minlen)
    
    return result


  def __and__(BitSet self, BitSet other):    
    self.check()
    other.check()

    cdef size_t minlen, maxlen, maxbitlen

    if self.bitlen < other.bitlen:
      minlen = self.dlen
      maxlen = other.dlen
      maxbitlen = other.bitlen
    else:
      minlen = other.dlen
      maxlen = self.dlen
      maxbitlen = self.bitlen
      
    cdef BitSet result
    result = BitSet(maxbitlen, maxbitlen)

    cdef size_t i

    # First copy as much as possible using
    # machine word size
    cdef unsigned int *a_int, *b_int, *r_int
    a_int = <unsigned int *>self.data
    b_int = <unsigned int *>other.data
    r_int = <unsigned int *>result.data

    cdef int minlen_words
    minlen_words = minlen / sizeof(int)

    i = 0
    while i < minlen_words:
      r_int[i] = a_int[i] & b_int[i]
      i = i + 1

    # now we're going to use i in terms of bytes, so
    # the counter needs to be turned into a byte counter
    i = i * sizeof(int)

    while i < minlen:
      result.data[i] = self.data[i] & other.data[i]
      i = i + 1

    # the rest of the bitset is just zeros
    return result
