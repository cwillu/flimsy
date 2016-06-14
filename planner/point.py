import attr
import inspect
import re
import functools
import cffi
import mmap

import math

ffi = cffi.FFI()

gc = []
def make_mmapped_data(d, type=None, f=None):
  if type is None:
    type = "uint32_t"

  f.seek(d.y * d.x * ffi.sizeof(type))
  f.write('\x00')
  f.flush()
  f.seek(0)

  mm = mmap.mmap(f.fileno(), 0)
  buffer = ffi.from_buffer(mm)
  gc.append((f, mm, buffer))

  data = ffi.cast('{} *'.format(type), buffer)
  return data


def etc(func):
  """ decorator """
  name = func.__name__
  if not re.match(r'__.*__$', name):
    raise NameError("{} is not a dunder method".format(name))

  n_name = name
  r_name = name.replace('__', '__r', 1)
  i_name = name.replace('__', '__i', 1)
  c_name = name.replace('__', '__c', 1)

  cls = inspect.currentframe(1).f_locals
  cls[c_name] = classmethod(func)
  def method(name):
    def dec(f):
      cls[name] = f
      return f
    return dec

  @method(n_name)
  @functools.wraps(func)
  def n_func(self, b):
    self = attr.assoc(self)
    func = type(self).__dict__[c_name].__get__(self, type(self))
    return func(self, b)

  @method(r_name)
  @functools.wraps(func)
  def r_func(self, b):
    func = type(self).__dict__[c_name].__get__(self, type(self))
    return func(b, self)

  @method(i_name)
  @functools.wraps(func)
  def i_func(self, b):
    func = type(self).__dict__[c_name].__get__(self, type(self))
    return func(self, b)

  return cls[n_name]

@attr.s
class P(object):
  x = attr.ib()
  y = attr.ib()

  def __neg__(self):
    a.x *= -1
    a.y *= -1

  @etc
  def __add__(cls, a, b):
    if isinstance(b, P):
      a.x += b.x
      a.y += b.y
    elif isinstance(b, tuple):
      a.x += b[0]
      a.y += b[1]
    else:
      a.x += b
      a.y += b
    return a

  @etc
  def __sub__(cls, a, b):
    if isinstance(b, P):
      a.x -= b.x
      a.y -= b.y
    elif isinstance(b, tuple):
      a.x -= b[0]
      a.y -= b[1]
    else:
      return NotImplemented
    return a

  @etc
  def __mul__(cls, a, b):
    if isinstance(b, P):
      a.x *= b.x
      a.y *= b.y
    elif isinstance(b, tuple):
      a.x *= b[0]
      a.y *= b[1]
    else:
      a.x *= b
      a.y *= b
    return a

  @etc
  def __div__(cls, a, b):
    if isinstance(b, P):
      a.x /= b.x
      a.y /= b.y
    elif isinstance(b, tuple):
      a.x /= b[0]
      a.y /= b[1]
    else:
      a.x /= b
      a.y /= b
    return a

  @etc
  def __mod__(cls, a, b):
    if isinstance(b, P):
      a.x %= b.x
      a.y %= b.y
    elif isinstance(b, tuple):
      a.x %= b[0]
      a.y %= b[1]
    else:
      a.x %= b
      a.y %= b
    return a

  @etc
  def __floordiv__(cls, a, b):
    """ Rounded, not floored """

    if isinstance(b, P):
      a.x //= b.x
      a.y //= b.y
    elif isinstance(b, tuple):
      a.x //= b[0]
      a.y //= b[1]
    else:
      a.x //= b
      a.y //= b
    a.x = int(round(a.x))
    a.y = int(round(a.y))
    return a

  def __or__(a, b):
    if isinstance(b, P):
      a.x = b.x
      a.y = b.y
    elif isinstance(b, tuple):
      a.x = b[0]
      a.y = b[1]
    else:
      a.x = b
      a.y = b
    return a
  __ior__ = __or__

  @etc
  def __lshift__(cls, a, b):
    hypot_sq = a.x**2 + a.y**2
    if isinstance(b, P):
      a.x = a.x * b.x - a.y * b.y
      a.y = a.y * b.x + a.x * b.y
    elif isinstance(b, tuple):
      a.x = a.x * b[0] - a.y * b[1]
      a.y = a.y * b[0] + a.x * b[1]
    else:
      a.x = a.x * math.cos(b) - a.y * math.sin(b)
      a.y = a.y * math.cos(b) + a.x * math.sin(b)
    a.y = math.copysign(math.sqrt(hypot_sq - a.x**2), a.y)
    return a

  @etc
  def __rshift__(cls, a, b):
    hypot_sq = a.x**2 + a.y**2
    if isinstance(b, P):
      a.x = a.x * b.x + a.y * b.y
      a.y = a.y * b.x - a.x * b.y
    elif isinstance(b, tuple):
      a.x = a.x * b[0] + a.y * b[1]
      a.y = a.y * b[0] - a.x * b[1]
    else:
      a.x = a.x * math.cos(b) + a.y * math.sin(b)
      a.y = a.y * math.cos(b) - a.x * math.sin(b)
    a.y = math.copysign(math.sqrt(hypot_sq - a.x**2), a.y)
    return a

  def __format__(self, spec=''):
    if not spec:
      spec = '.2f'
    return '{}({}, {})'.format(type(self).__name__, format(self.x, spec), format(self.y, spec))

  # def __invert__(a):
  #   a.x, a.y = a.y, a.x
  #   return a

