from __future__ import absolute_import
import sys
import math
import time
from planner import point
from planner.point import P

class NothingToDo(Exception):
  pass


POINT_TYPE_MASK = 0xff000000
POINT_MATERIAL = 0xffffffff
POINT_NO_GO = 0xdddd8888
POINT_NO_GO_RADIUS = 0xdd8888ff
POINT_NO_GO_MASK = 0xdd444499
POINT_PREVIOUSLY_REMOVED = 0x00aaaaaa
POINT_REMOVED = 0x00000000

def get_point(p, field=0):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x >= d.x or p.y >= d.y:
    return 0
    # raise ValueError("Value out of range: {} {}".format(p, d))
  return data[field][p.x + p.y * d.x]

def set_point(p, v, field=0):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x >= d.x or p.y >= d.y:
    return 0
    # raise ValueError("Value out of range: {} {}".format(p, d))
  was = data[field][p.x + p.y * d.x]
  data[field][p.x + p.y * d.x] = v
  # if was != v:
  #   time.sleep(0.000001)

  return was

def circle_test(d, data, *args):
  # P(1.0, 0.0)
  # adir= P(0.0, -0.5)

  for p in xrange(d.x * d.y):
    data[0][p] = 0xffffffff
    data[1][p] = 0x00000000
  direction = P(1.0, 0.0)
  adir = 90.0
  direction = 0.0

  start_time = time.time()
  loops = 0
  periods = []

  while True:
    current_time = time.time()
    if current_time - start_time > 1:
      periods.append(loops)
      # print loops
      if len(periods) >= 10:
        break


      loops = 0
      start_time = current_time

    # direction <<= yaw_step
    # direction <<= math.radians(1)
    # direction >>= math.radians(0.1)
    for x in range(1):
      adir += 65536/4/9
    direction += 65536/360/10
    direction += 65536/360/10
    origin = P(500.0, 500.0)
    set_point(origin + P(math.sin(2*math.pi*direction/65536), math.cos(2*math.pi*direction/65536)) * 100, 0)
    set_point(origin + P(math.sin(2*math.pi*direction/65536), math.cos(2*math.pi*direction/65536)) * 200, 0)
    # set_point(origin + direction * 200 - (direction>>10.0) * 100, 0)
    time.sleep(0.001)
    loops += 1

  periods.sort()
  half_len = len(periods) / 2 - 1


  mean = sum(periods) / float(len(periods))

  median = periods[half_len:-half_len]
  print median, half_len, len(periods)
  median = sum(median) / float(len(median))

  median_below_median = periods[:half_len]
  median_below_median = median_below_median[len(median_below_median)/2-1:-len(median_below_median)/2+1]
  median_below_median = sum(median_below_median) / float(len(median_below_median))

  median_above_median = periods[-half_len:]
  median_above_median = median_above_median[len(median_above_median)/2-1:-len(median_above_median)/2+1]
  median_above_median = sum(median_above_median) / float(len(median_above_median))

  print "{:12s}  {:12.2f}  {:12s}".format('', mean, '')
  print "{:12.2f}  {:12.2f}  {:12.2f}".format(median-median_below_median, median, median_above_median-median)

def path(d, data, runs=10, cutter_size=20):
  #cutter radius in 1/1000 of an inch
  radius = cutter_size

  show_path = 1
  show_heading = 1
  show_scan = 1

  max_turn = 1.0/16

  radius_sq = radius ** 2
  yaw_step = 65520/360 #math.asin(math.radians(1))
  initial_scan_yaw = 1
  # yaw_step = P(math.cos(yaw_step_angle), math.sin(yaw_step_angle))
  # print fomat(initial_scan_yaw)
  # print format(yaw_step)

  offset_points = [P(0, -1), P(-1, 0), P(1, 0), P(0, 1)]
  offset_points_with_center = [P(0, -1), P(-1, 0), P(1, 0), P(0, 1)]

  cut_points = []
  for rise in xrange(0, int(radius-1)):
    bound = int(round(math.sqrt(radius_sq - rise**2)))
    for stroke in [-bound, -bound + 1, bound-1, bound]: #xrange(-bound, bound + 1):
      p = P(rise, stroke)
      cut_points.append(p)
      p = P(-rise, stroke)
      cut_points.append(p)
      p = P(stroke, -rise)
      cut_points.append(p)
      p = P(stroke, rise)
      cut_points.append(p)

  cut_points = list(set(cut_points))
  cut_points.sort(key=lambda p: (p.y, p.x))
  # from pprint import pprint
  # pprint(cut_points)

  # print len(cut_points)

  no_go_trace_points = []
  for cut_point in cut_points:
    for offset in offset_points:
      p = cut_point + offset
      no_go_trace_points.append(p)
  no_go_trace_points = list(set(no_go_trace_points))
  no_go_trace_points.sort(key=lambda p: (p.y, p.x))

  scanner_points = cut_points + no_go_trace_points
  scanner_points = list(set(scanner_points))
  scanner_points.sort(key=lambda p: math.atan2(p.x, p.y))



  for run in xrange(1, runs+1):
    print "Run {}\r".format(run),
    sys.stdout.flush()
    for p in xrange(d.x * d.y):
      data[0][p] = 0xffffffff
      data[1][p] = 0x00000000

    offset = P(200, 250)
    size = (500, 200)
    tl = P(250, 250)
    br = P(800, 650)

    print "Rendering path"
    for y in range(d.y):
      for x in range(d.x):
        if y > tl.y and y < br.y:
          if abs(x-tl.x) < 40 or abs(x-br.x) < 40:
            set_point(P(x, y), POINT_NO_GO)
        if x > tl.x and x < br.x:
          if abs(y-tl.y) < 40 or abs(y-br.y) < 40:
            set_point(P(x, y), POINT_NO_GO)

        circle_center = math.hypot(800-x, 800-y)
        if circle_center > 50 and circle_center < 80:
          set_point(P(x, y), POINT_NO_GO)


    print "Filling path cutter radius"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p) != POINT_NO_GO:
          continue

        for cut_point in no_go_trace_points:
          no_go_radius = p + cut_point
          if get_point(no_go_radius) & POINT_TYPE_MASK == POINT_NO_GO & POINT_TYPE_MASK:
            continue
          # print '{:08x}'.format(get_point(no_go_radius))
          set_point(no_go_radius, POINT_NO_GO_RADIUS)

    print "Tracing edge"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p) != POINT_NO_GO:
          continue

        for cut_point in cut_points:
          no_go_radius = p + cut_point
          if get_point(no_go_radius) == POINT_NO_GO:
            continue

          set_point(no_go_radius, POINT_NO_GO_MASK)

    print "Inverting cutter limit path"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p) != POINT_NO_GO_RADIUS:
          continue

        set_point(p, POINT_MATERIAL)
        for cut_point in cut_points:
          no_go_radius = p + cut_point

          if get_point(no_go_radius) != POINT_NO_GO_MASK:
            continue

          set_point(no_go_radius, POINT_MATERIAL)




    try:
      skip = 0
      direction = 0 #P(1.0, 0.0)
      current = P(350.0, 500.0)

      feed_step = 1

      working = P(0.0, 0.0)
      old_current = current
      old_direction = direction
      jogging_distance = 0
      while True:
        skip += 1
        scan_angle = direction
        scan_angle += initial_scan_yaw

        if jogging_distance <= 0:
          working |= current + P.angle(scan_angle, radius + 1.4)
          material = get_point(working)
          if material == 0xffffffff:
            for step in xrange(16380):
              direction += 1
              scan_angle += 1
              material = get_point(current + P.angle(scan_angle, radius+1.4))

              if show_scan:
                set_point(current + P.angle(direction, radius), 0x8844ff44, 1)
              if material != 0xffffffff:
                break
              if show_scan and step > 10:
                set_point(current + P.angle(direction, radius), 0x880044ff, 1)
          else:
            if show_scan and not skip % 3:
              set_point(current + P.angle(direction, radius), 0x88004444, 1)

            for search_radius in range(1, 2):
              scan_angle = direction
              scan_angle -= initial_scan_yaw
              for step in xrange(65520):
                direction -= 1
                scan_angle -= 1
                try:
                  material = get_point(current + P.angle(scan_angle, radius+1 * (search_radius)))
                except ValueError:
                  continue

                if show_scan:
                  set_point(current + P.angle(direction, radius + 1*search_radius), 0x880044ff, 1)
                if material == 0xffffffff:
                  break

              else:
                continue
              jogging_distance = search_radius-1
              break
            else:
              closest_distance = math.hypot(d.x, d.y)
              closest = None
              for y in range(d.y):
                for x in range(d.x):
                  point = P(x, y)
                  material = get_point(point)
                  if material != 0xffffffff:
                    continue

                  point -= current
                  distance = math.hypot(point.x, point.y)
                  if distance <= closest_distance and distance > radius+1:
                    closest = point
                    closest_distance = distance
              if closest is None:
                raise NothingToDo
              jogging_distance = int(closest_distance - radius)
              if jogging_distance <= 0:
                assert False
              direction = int(math.atan2(closest.x, closest.y) * 65520 / (2 * math.pi))
        else:
          jogging_distance -= 1
        if direction_span != 65520:
          print
          print 360*direction_start/65520, 360*direction_span/65520, 360*direction/65520, 360*old_direction/65520

        print
        print "loc:", current
        print "dir", direction*360/65520
        print "oldv", P.angle(old_direction)*360/65520
        print "v", P.angle(direction)*360/65520
        if current // 1 != old_current // 1:
          total_cuts = 0
          for cut_point in cut_points:
            was = set_point(current + cut_point, 0, 0)
            if was & 0xff000000 == 0xdd000000:
              print
              print current
              print direction
              print P.angle(old_direction)*360/65520
              print P.angle(direction)*360/65520
              assert False, direction*360/65520
            if was != 0:
              total_cuts += 1
          # if total_cuts <= 0 and jogging <= 0:
          #   print "current {}, old {}".format(current//1, old_current//1)
          #   print "total cuts {}, jogging {}".format(total_cuts, jogging)
          #   return
        if show_path:
          set_point(current, 0x8800ffff, 1)

        direction %= 65520
        if show_heading and not skip % 3 and jogging_distance <= 0:
          for r in range(1, int(radius / 1.5)):
            set_point(current + P.angle(direction -65520/4, r), 0x88888800, 1)

        old_current = current
        old_direction = direction

        current += P.angle(direction)
        if not skip % 10:
          skip = 0
        # current += direction c
        # print '{} {} {:.2f} {} {}'.format(math.hypot(direction.x, direction.y), direction, math.degrees(math.acos(direction.x)), current, current)
        # import time

        # time.sleep(0.01)

    except (ValueError, NothingToDo):
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
  # circle_test(d, data, runs, cutter_size)
except Exception as e:
  import traceback
  traceback.print_exc(e)

