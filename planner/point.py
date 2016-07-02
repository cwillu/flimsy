import attr
import inspect
import re
import functools
import cffi
import mmap

import math

ffi = cffi.FFI()

gc = []
def make_mmapped_data(d, type=None, f=None, frames=3):
  if type is None:
    type = "uint32_t"

  frame_len = d.y * d.x
  f.seek(frames * frame_len * ffi.sizeof(type))
  f.write('\x00')
  f.flush()
  f.seek(0)

  mm = mmap.mmap(f.fileno(), 0)
  buffer = ffi.from_buffer(mm)

  data = ffi.cast('{} *'.format(type), buffer)
  gc.append((f, mm, buffer, data))
  _frames = []
  for i in range(frames):
    _frames.append(data[frame_len*i:frame_len*(i+1)])
  return _frames

def iter_row_wise(d):
  for y in range(d.y):
    for x in range(d.x):
      yield P(d.x, d.y)

def iter_col_wise(d):
  for x in range(d.x):
    for y in range(d.y):
      yield P(d.x, d.y)


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
    self = self.__class__(self.x, self.y)
    return func(self, b)

  @method(r_name)
  @functools.wraps(func)
  def r_func(self, b):
    self = self.__class__(self.x, self.y)
    return func(b, self)


  # method(i_name)(func)
  # @method(i_name)
  # @functools.wraps(func)
  # def i_func(self, b):
  #   func = getattr(self, c_name)
  #   func = type(self).__dict__[c_name].__get__(self, type(self))
  #   return func(self, b)

  return cls[n_name]

ANGLE_FACTOR = math.pi * 2 / 65520
SIN = []
COS = []
for angle in range(65520 * 2):
  radians = angle * ANGLE_FACTOR #* math.pi*2 / 65520
  SIN.append(math.sin(radians))
  COS.append(math.cos(radians))

@attr.s(slots=True)
class P(object):
  x = attr.ib()
  y = attr.ib()

  @classmethod
  def angle(cls, angle, radius=1.0):
    return cls(radius * SIN[angle], radius * COS[angle])

  def __neg__(self):
    a.x *= -1
    a.y *= -1

  @etc
  def __add__(a, b):
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
  def __sub__(a, b):
    if isinstance(b, P):
      a.x -= b.x
      a.y -= b.y
    elif isinstance(b, tuple):
      a.x -= b[0]
      a.y -= b[1]
    else:
      a.x -= b
      a.y -= b
    return a

  @etc
  def __mul__(a, b):
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
  def __div__(a, b):
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
  def __mod__(a, b):
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

  # def __mod__(a, b):
  #   a.x

  @etc
  def __floordiv__(a, b):
    """ Rounded, not floored """

    # if b == 1:
    #   pass
    if isinstance(b, P):
      a.x /= b.x
      a.y /= b.y
    elif isinstance(b, tuple):
      a.x /= b[0]
      a.y /= b[1]
    else:
      a.x /= b
      a.y /= b
    a.x = int(a.x)
    a.y = int(a.y)
    return a

  def __or__(a, b):
    # a = a.__class__(0,0)
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
  def __lshift__(a, b):
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
      # return a
    a.y = math.copysign(math.sqrt(max(0, hypot_sq - a.x**2)), a.y)
    return a

  @etc
  def __rshift__(a, b):
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
      # return a
    a.y = math.copysign(math.sqrt(max(0, hypot_sq - a.x**2)), a.y)
    return a

  def __format__(self, spec=''):
    if not spec:
      spec = '.2f'
    return '{}({}, {})'.format(type(self).__name__, format(self.x, spec), format(self.y, spec))

  # def __invert__(a):
  #   return a.__class__(a.y, a.x)

