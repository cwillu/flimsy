from __future__ import absolute_import
import sys
import math
from planner import point
from planner.point import P


def get_point(p):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x > d.x or p.y > d.y:
    raise ValueError("Value out of range: {} {}".format(p, d))
  return data[p.x + p.y * d.x]

def set_point(p, v, mask=0xfff0f0f0):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x > d.x or p.y > d.y:
    raise ValueError("Value out of range: {} {}".format(p, d))
  data[p.x + p.y * d.x] &= ~v & mask

def path(d, data, runs=10, cutter_size=20):
  #cutter radius in 1/1000 of an inch
  radius = cutter_size

  max_turn = 1.0/16

  radius_sq = radius ** 2
  yaw_step_angle = math.asin(math.radians(1))
  initial_scan_yaw = P(math.cos(yaw_step_angle/2), math.sin(yaw_step_angle/2))
  yaw_step = P(math.cos(yaw_step_angle), math.sin(yaw_step_angle))
  print format(initial_scan_yaw)
  print format(yaw_step)

  cut_points = []
  for rise in xrange(0, int(radius+1)):
    bound = int(round(math.sqrt(radius_sq - rise**2)))
    for stroke in [-bound, -bound + 1, bound-1, bound]: #xrange(-bound, bound + 1):
      cut_points.append(P(rise, stroke))
      cut_points.append(P(-rise, stroke))
      cut_points.append(P(stroke, rise))
      cut_points.append(P(stroke, -rise))

  cut_points = list(set(cut_points))
  cut_points.sort()
  # from pprint import pprint
  # pprint(cut_points)

  print len(cut_points)

  for run in xrange(1, runs+1):
    print "Run {}".format(run)
    try:
      for p in xrange(d.x * d.y):
        data[p] = 0xffffffff

      direction = P(1.0, 0.0)
      current = P(500.0, 500.0)

      feed_step = 1

      working = P(0.0, 0.0)
      scan_point = P(0.0,0.0)
      old_current = P(0,0)
      old_direction = P(0,0)
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
            # print '<',
            # set_point(current + scan_point, 0)
            if material != 0xffffffff:
              break
        else:
          set_point(working, 0x0000ff00, mask=0xffffffff)
          scan_point >>= yaw_step
          working |= current
          working += scan_point
          material = get_point(working)
          for step in xrange(10):
            if material == 0xffffffff:
              break
            # print '>',
            direction >>= yaw_step
            scan_point >>= yaw_step
            working |= current
            working += scan_point
            material = get_point(working)
          else:
            direction = old_direction


        working |= current + direction
        if working//1 != current//1:
          for r in xrange(int(radius-5), int(radius+1)):
            working |= old_current
            working += old_direction*r
            set_point(working, 0)
          for cut_point in cut_points:
            working |= current
            working += cut_point
            set_point(working, 0)
          for r in range(int(radius-5), int(radius+1)):
            working |= current
            working += direction*r
            set_point(working, 0x00ffff00, mask=0xffffffff)
          working |= current
          set_point(working, 0x00ccccff, mask=0xffffffff)

          old_current |= current
          old_direction |= direction
        # print
        current += direction
        # current += direction c
        # print '{} {} {:.2f} {} {}'.format(math.hypot(direction.x, direction.y), direction, math.degrees(math.acos(direction.x)), current, current)
        # import time
        # time.sleep(0.)
    except ValueError:
      continue




# if __name__ == "__main__":

d = P(1000, 1000)
with open('mmap', 'a'):
  pass
data = point.make_mmapped_data(d, f=open('mmap', 'rb+'))
runs = int((sys.argv[1:] or ["10"])[0])
cutter_size = int((sys.argv[2:] or ["50"])[0])
# if point.gc:
#   f, mm, buffer, data = point.gc.pop()
#   mm.close()
#   f.close()
#   print dir(data)
#   data.close()


try:
  path(d, data, runs=runs, cutter_size=cutter_size)
except Exception as e:
  import traceback
  traceback.print_exc(e)

