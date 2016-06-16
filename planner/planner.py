from __future__ import absolute_import
import sys
import math
from planner import point
from planner.point import P


def get_point(p, field=0):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x >= d.x or p.y >= d.y:
    raise ValueError("Value out of range: {} {}".format(p, d))
  return data[field][p.x + p.y * d.x]

def set_point(p, v, field=0):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x >= d.x or p.y >= d.y:
    raise ValueError("Value out of range: {} {}".format(p, d))
  data[field][p.x + p.y * d.x] = v

def path(d, data, runs=10, cutter_size=20):
  #cutter radius in 1/1000 of an inch
  radius = cutter_size

  show_path = 1
  show_heading = 0
  show_scan = 0

  max_turn = 1.0/16

  radius_sq = radius ** 2
  yaw_step_angle = math.asin(math.radians(1))
  initial_scan_yaw = P(math.cos(yaw_step_angle/2), math.sin(yaw_step_angle/2))
  yaw_step = P(math.cos(yaw_step_angle), math.sin(yaw_step_angle))
  print format(initial_scan_yaw)
  print format(yaw_step)

  cut_points = []
  for rise in xrange(0, int(radius-1)):
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

  # print len(cut_points)
  # import time
  # direction = P(1.0, 0.0)
  # adir= P(0.0, -0.5)
  # for p in xrange(d.x * d.y):
  #   data[0][p] = 0xffffffff
  #   data[1][p] = 0x00000000
  # direction = P(1.0, 0.0)
  # while True:
  #   # direction <<= yaw_step
  #   # direction <<= math.radians(1)
  #   # direction >>= math.radians(0.1)
  #   for x in range(1):
  #     adir = adir << math.radians(90.0/9)
  #   adir = adir << math.radians(0.1)
  #   origin = P(500.0, 500.0)
  #   set_point(origin + direction * 200, 0)
  #   set_point(origin + adir * 100, 0)
  #   # set_point(origin + direction * 200 - (direction>>10.0) * 100, 0)
  #   time.sleep(0.001)


  for run in xrange(1, runs+1):
    print "Run {}\r".format(run),
    sys.stdout.flush()
    for p in xrange(d.x * d.y):
      data[0][p] = 0xffffffff
      data[1][p] = 0x00000000
    for r in range(500):
      set_point(P(r+200, 200), 0x88888888)
      set_point(P(200, r+200), 0x88888888)
      set_point(P(r+200, 700), 0x88888888)
      set_point(P(700, r+200), 0x88888888)



    try:
      skip = 0
      direction = P(1.0, 0.0)
      current = P(350.0, 500.0)

      feed_step = 1

      working = P(0.0, 0.0)
      scan_point = P(0.0,0.0)
      old_current = P(0,0)
      old_direction = P(0,0)
      tangent = P(0,0)
      while True:
        skip += 1
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
            if show_scan and not skip % 10:
              working |= direction
              for ten in range(9):
                working <<= math.radians(-10)
              working |= current + working*(radius/1.5)
              set_point(working, 0x8844ff44, 1)
            # print '<',
            # set_point(current + scan_point, 0)
            if material != 0xffffffff:
              break
        else:
          if show_scan and not skip % 10:
            working |= direction
            for ten in range(9):
              working <<= math.radians(-10)
            working |= current + working*(radius/1.5)
            set_point(working, 0x88004444, 1)
          # if not skip % 10:
          #   set_point(working, 0x880000ff, 1)
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
            if show_scan and not skip % 10:
              working |= direction
              for ten in range(9):
                working <<= math.radians(-10)
              working |= current + working*(radius/1.5)
              set_point(working, 0x8800ffff, 1)
            # if not skip % 10:
            #   set_point(working, 0x880000ff, 1)
          else:
            assert False;
            direction = old_direction


        # if working//1 != current//1:
          # set_point(working, 0, 1)
        for cut_point in cut_points:
          working |= current
          working += cut_point
          set_point(working, 0, 0)
        if show_path:
          working |= current
          set_point(working, 0x8800ffff, 1)
        if show_heading and not skip % 10:
          for r in range(1, int(radius / 1.5)):
            tangent |= direction
            for ten in range(9):
              tangent <<= math.radians(-10)
            working |= current
            # working += (direction * r)
            working += tangent * r
            # working += (direction*r)
            set_point(working, 0x88888800, 1)

          old_current |= current
          old_direction |= direction
        # print
        current += direction

        if not skip % 10:
          skip = 0
        # current += direction c
        # print '{} {} {:.2f} {} {}'.format(math.hypot(direction.x, direction.y), direction, math.degrees(math.acos(direction.x)), current, current)
        import time
        time.sleep(0.002)
    except ValueError:
      continue

# a90 = P(math.cos(math.radians(90)), math.sin(math.radians(90)))
# aa90 = P(math.cos(math.radians(90)), math.sin(math.radians(90)))
# print a90
# print aa90
# print
# print
# print (a90 >> aa90) // 1
# print (a90 >> aa90>> aa90) // 1
# print (a90 >> aa90>> aa90>> aa90) // 1
# print (a90 >> aa90>> aa90>> aa90>> aa90) // 1
# print a90 >> aa90>> aa90>> aa90>> aa90 == aa90
# print
# print
# print (a90 << aa90) // 1
# print (a90 << aa90<< aa90) // 1
# print (a90 << aa90<< aa90<< aa90) // 1
# print (a90 << aa90<< aa90<< aa90<< aa90) // 1
# print a90 << aa90<< aa90<< aa90<< aa90 == aa90
# ex

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

