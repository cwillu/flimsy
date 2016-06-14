from __future__ import absolute_import
import sys
import math
from planner import point
from planner.point import P



def path():
  d = P(1000, 1000)
  data = point.make_mmapped_data(d, f=open('mmap', 'rb+'))

  for p in xrange(d.x * d.y):
    if data[p] != 0xffffffff:
      # data[p] = 0xffffffff
      data[p] = 0x0

  def get_point(p):
    p //= 1
    if p % d != p:
      raise ValueError("Value out of range: {} {}".format(p, d))
    return data[p.x + p.y * d.x]

  def set_point(p, v):
    p //= 1
    if p % d != p:
      raise ValueError("Value out of range: {} {}".format(p, d))
    data[p.x + p.y * d.x] = v

  current = P(500.0, 500.0)
  radius = 50.0
  radius_sq = radius ** 2
  max_turn = 1.0/16

  yaw_step_angle = math.asin(math.radians(1))
  initial_scan_yaw = P(math.cos(yaw_step_angle/2), math.sin(yaw_step_angle/2))
  yaw_step = P(math.cos(yaw_step_angle), math.sin(yaw_step_angle))
  print format(initial_scan_yaw)
  print format(yaw_step)
  direction = P(1.0, 0.0)

  feed_step = 1

  working = P(0.0, 0.0)
  scan_point = P(0.0,0.0)
  while True:
    scan_point |= direction
    scan_point *= radius + 1
    scan_point <<= initial_scan_yaw

    working |= current
    working += scan_point
    material = get_point(working)
    if material == 0xffffffff:
      for step in xrange(10):
        direction <<= yaw_step
        scan_point <<= yaw_step
        working |= current
        working += scan_point
        material = get_point(working)
        print '<',
        # set_point(current + scan_point, 0)
        if material != 0xffffffff:
          break
    else:
      old_direction = direction / 1
      set_point(working, 0x0000ff00)
      scan_point >>= yaw_step
      working |= current
      working += scan_point
      material = get_point(working)
      for step in xrange(10):
        if material == 0xffffffff:
          break
        print '>',
        direction >>= yaw_step
        scan_point >>= yaw_step
        working |= current
        working += scan_point
        material = get_point(working)
      else:
        direction = old_direction


    working |= current + direction
    if working//1 != current//1:
      working |= current
      for y in xrange(int(radius-5), int(radius+1)):
        bound = int(round(math.sqrt(radius_sq - y**2)))
        for x in xrange(-bound, bound + 1):
          color = 0# if x and y else 0x000000ff
          working |= current
          working += x, y
          set_point(working, color)
          working |= current
          working += x, -y
          set_point(working, color)
        for r in xrange(0, int(radius+1)):
          working |= current
          working += direction*r
          set_point(working, 0x00ffff00)




    print
    current = current + direction
    # current += direction c
    print '{} {} {:.2f} {} {}'.format(math.hypot(direction.x, direction.y), direction, math.degrees(math.acos(direction.x)), current, current)
    # import time
    # time.sleep(0.)

if __name__ == "__main__":
  path(*sys.argv[1:])

