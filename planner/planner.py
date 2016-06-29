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

def a(angle):
  return "{} ({})".format(angle * 360 / 65520, angle)

def m(material):
  return "{:08x}".format(material)

def get_point(p, field=0):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x >= d.x or p.y >= d.y:
    return 0
  return data[field][p.x + p.y * d.x]

def set_point(p, v, field=0):
  p //= 1
  if p.x < 0 or p.y < 0 or p.x >= d.x or p.y >= d.y:
    return 0
  was = data[field][p.x + p.y * d.x]
  data[field][p.x + p.y * d.x] = v
  # if was != v:
  #   time.sleep(0.000001)

  return was


def path(d, data, runs=10, cutter_size=20):
  #cutter radius in 1/1000 of an inch
  radius = cutter_size

  show_path = 1
  show_heading = 0
  show_scan = 1
  show_debug = 0

  radius_sq = radius ** 2
  initial_scan_yaw = 1

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
    for c in xrange(d.x * d.y):
      data[0][c] = 0xffffffff
      data[1][c] = 0x00000000
      data[2][c] = 0x00000000

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
        for offset in offset_points:
          if get_point(p+offset) != POINT_NO_GO:
            break
        else:
          continue

        for cut_point in no_go_trace_points:
          no_go_radius = p + cut_point
          if get_point(no_go_radius) & POINT_TYPE_MASK == POINT_NO_GO & POINT_TYPE_MASK:
            continue
          # print '{:08x}'.format(get_point(no_go_radius))
          set_point(no_go_radius, POINT_NO_GO_RADIUS)
          set_point(no_go_radius, POINT_NO_GO_RADIUS, 2)

    print "Tracing edge"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p) != POINT_NO_GO:
          continue
        for offset in offset_points:
          if get_point(p+offset) != POINT_NO_GO:
            break
        else:
          continue

        for cut_point in cut_points:
          no_go_radius = p + cut_point
          if get_point(no_go_radius) in [POINT_NO_GO, POINT_NO_GO_MASK]:
            continue

          set_point(no_go_radius, POINT_NO_GO_MASK)
          set_point(no_go_radius, POINT_NO_GO_MASK, 2)

    # print "Inverting cutter limit path"
    # for y in range(d.y):
    #   for x in range(d.x):
    #     p = P(x, y)
    #     if get_point(p) != POINT_NO_GO_RADIUS:
    #       continue
    #
    #     set_point(p, POINT_MATERIAL)
    #     for cut_point in cut_points:
    #       no_go_radius = p + cut_point
    #
    #       if get_point(no_go_radius) != POINT_NO_GO_MASK:
    #         continue
    #
    #       set_point(no_go_radius, POINT_MATERIAL)

    c = P(200, 800)
    for r in range(1, 50):
      for offset in offset_points_with_center:
        set_point(c + P.angle(0, r) + offset, 0x88ff0000, 0)
      set_point(c + P.angle(65520/4, r), 0x88ff0000, 0)

    try:
      skip = 0
      direction = 0
      current = P(400.0, 500.0)
      last_bound = None
      current_bound = None

      feed_step = 1

      working = P(0.0, 0.0)
      old_current = current
      old_direction = direction

      was_jogging = False
      jogging_distance = 0
      jogging_destination = None
      jogging_direction = direction

      last_on_radius = None
      last_on_direction = None
      last_off_radius = None
      last_off_direction = None
      last_clamped_angle = None

      total_cuts = 0


      while True:
        skip += 1
        scan_angle = direction
        # scan_angle += initial_scan_yaw

        if jogging_distance <= 0:
          for step in xrange(65520/32):
            working = current + P.angle(scan_angle - step, radius + 1)
            material = get_point(working)
            if material in [0xffffffff, POINT_NO_GO_RADIUS]:
              scan_angle -= step
              direction -= step
              break
          else:
            scan_angle = direction
            working = current + P.angle(scan_angle - step, radius + 1)
            material = get_point(working)

          if material in [0xffffffff, POINT_NO_GO_RADIUS, POINT_NO_GO_MASK]:
            for step in xrange(65520):
              scan_angle = direction + step
              material = get_point(current + P.angle(scan_angle, radius+1))

              if show_scan:
                set_point(current + P.angle(scan_angle, radius), 0x8844ff44, 1)
              if show_scan and step > 10:
                set_point(current + P.angle(scan_angle, radius), 0x88ff44ff, 1)
              if material in [0x00000000]:
                if show_debug:
                  print "1", m(material)
                direction = scan_angle
                break
            else:
              if show_debug or True:
                print "Scan fail 1"
          else:
            if show_scan and not skip % 3:
              set_point(current + P.angle(direction, radius), 0x88004444, 1)
            for search_radius in [1]:
              scan_angle = direction
              scan_angle -= 65520/16 * 3
              for step in xrange(65520):
                direction -= 1
                scan_angle -= 1
                try:
                  material = get_point(current + P.angle(scan_angle, radius+1 * (search_radius)))
                except ValueError:
                  continue

                if show_scan:
                  set_point(current + P.angle(direction, radius + 1*search_radius), 0x8800ffff, 1)
                if material not in [0x00000000]:
                  if show_debug:
                    print "2", m(material)
                  break

              else:
                if show_debug or True:
                  print "Scan fail 2"
                continue
              # if search_radius > 1:
              #   jogging_distance = search_radius-1
              #   print "short jog {} {}".format(jogging_distance, direction)
              break
            else:
              if show_debug or True:
                print "Scan fail 3"
              closest_distance = math.hypot(d.x, d.y)
              closest = None
              destination = None
              for y in range(d.y):
                for x in range(d.x):
                  point = P(x, y)
                  material = get_point(point)
                  if material not in [0xffffffff, POINT_NO_GO_RADIUS]:
                    continue

                  point -= current
                  distance = math.hypot(point.x, point.y)
                  if distance <= closest_distance and distance > radius+1:
                    closest = point
                    closest_distance = distance
                    destination = P(x, y)
              if closest is None:
                print "Nothing to do here"
                raise NothingToDo
              direction = int(math.atan2(closest.x, closest.y) * 65520 / (2 * math.pi))
              jogging_distance = int(closest_distance)
              jogging_destination = destination
              jogging_direction = direction
              if show_debug or True:
                print "long jog {} {}".format(jogging_distance, direction)
              if jogging_distance <= 0:
                assert False

        direction %= 65520

        if jogging_distance <= 0:
          if current_bound == POINT_NO_GO_MASK:
            assert False
          elif current_bound == POINT_NO_GO_RADIUS:
            next_bound = get_point(current + P.angle(direction), 2)
            clamped = False
            if next_bound == POINT_NO_GO_MASK:
              clamped = True

              # direction -= 65520 / 16
              # direction /= 65520 / 4
              # direction *= 65520 / 4
              # direction += 65520 / 16
              # print "***on radius, initial direction:", a(direction)
              step = 1000
              trial_direction = direction
              while True:
              # for step in range(0, 65520, 65520/360):
                trial_direction += step
                next_bound = get_point(current + P.angle(trial_direction), 2)
                # print 'trial {:08x}'.format(next_bound), a(step), a(trial_direction)
                if step > 1 and next_bound == POINT_NO_GO_RADIUS:
                  step /= -3
                elif step < 0 and next_bound != POINT_NO_GO_RADIUS:
                  step /= -3
                elif step == 0 or step == 1:
                  step = 1
                  if next_bound == POINT_NO_GO_RADIUS:
                    direction = trial_direction
                    direction %= 65520
                    # print "***", a(step), "direction is now:", a(direction)
                    # last_clamped_angle = direction
                    # last_clamped_position = current
                    break
            # if next_bound == current_bound and (current * 2) // 1.0 / 2 == current // 1.0:
            if clamped:
              next_off_radius = current // 1.0
              next_off_direction = direction

            if clamped and last_bound != POINT_NO_GO_RADIUS:
              last_on_radius = old_current // 1.0
              last_on_direction = direction
              for p in offset_points_with_center:
                for pp in offset_points_with_center:
                  set_point(old_current + p, 0xffffff00, 1)
                  set_point(old_current + p+p+pp, 0xffffff00, 1)
              if show_debug:
                print "******************** On radius", last_on_radius, m(current_bound), a(last_on_direction)
            else:
              current_bound = last_bound
              #we've entered the building

              # print direction
          else:
            assert current_bound in [None, 0x00000000], "{:08x}".format(last_bound)
            if last_bound == POINT_NO_GO_RADIUS:
              last_off_radius = next_off_radius
              last_off_direction = next_off_direction
              for p in offset_points_with_center:
                for pp in offset_points_with_center:
                  set_point(last_off_radius + p, 0xff0000ff, 1)
                  set_point(last_off_radius + p+p+pp, 0xff0000ff, 1)
              if show_debug:
                print "Off radius", last_off_radius, m(current_bound), a(last_off_direction)
              #we've left the building
              pass

          last_bound = current_bound

        else:
          jogging_distance -= 1
          if jogging_distance < 3:
            jogging_distance = 0
            direction = jogging_direction
            current = jogging_destination
            old_current = current
            total_cuts = 1
            was_jogging = 1

        if show_debug:
          print
          print "loc:", current
          print "dir", P.angle(direction), a(direction)
          print "old:", old_current
          print "oldv", P.angle(old_direction), a(old_direction)
        if current // 1 != old_current // 1 and not jogging_distance:
          last_cuts = total_cuts
          total_cuts = 0
          for cut_point in cut_points:
            was = set_point(old_current + cut_point, 0, 0)
            if was != 0:
              total_cuts += 1
              if was_jogging:
                print "**** done jogging"
                was_jogging = 0
          if was_jogging:
            was_jogging += 1
            if was_jogging > radius:
              print "**** timed out jogging" , radius
              was_jogging = 0
              last_off_radius = None
              last_on_radius = None
              # total_cuts += 1
          if show_debug:
            print total_cuts, last_cuts

          if not was_jogging and total_cuts <= 0 and last_cuts <= 0 and jogging_distance <= 0 and current_bound == next_bound:
            if show_debug:
              print "current {}, old {}".format(current//1, old_current//1)
              print "total cuts {}, jogging {}".format(total_cuts, jogging_distance)
            if current_bound == POINT_NO_GO_RADIUS and last_off_radius != None:
              if show_debug:
                print "jogging from {} to last_off {}".format(current, last_off_radius, a(last_off_direction))
              destination = last_off_radius - current
              jogging_destination = last_off_radius
              jogging_direction = last_off_direction
              closest_distance = math.hypot(destination.x, destination.y)
              jogging_distance = max(int(closest_distance)-2,1)
              direction = int(math.atan2(destination.x, destination.y) * 65520 / (2 * math.pi))
            elif current_bound != POINT_NO_GO_RADIUS and last_on_radius != None:
              if show_debug:
                print "*********** jogging from {} to last_on {}".format(current, last_on_radius, a(last_on_direction))
              destination = last_on_radius - current
              jogging_direction = last_on_direction
              jogging_destination = last_on_radius
              closest_distance = math.hypot(destination.x, destination.y)
              jogging_distance = max(int(closest_distance)-2,1)
              direction = int(math.atan2(destination.x, destination.y) * 65520 / (2 * math.pi))
            else:
              return
        if show_path:
          if jogging_distance > 0:
            for p in offset_points_with_center:
              set_point(current, 0x8800ff00, 1)
          elif was_jogging > 0:
              set_point(current, 0x88ff0000, 1)
          else:
            set_point(current, 0x8800ffff, 1)

        direction %= 65520
        if show_heading and not skip % 3 and jogging_distance <= 0:
          for r in range(1, int(radius / 1.5)):
            set_point(current + P.angle(direction -65520/4, r), 0x88888800, 1)

        old_current = current
        old_direction = direction

        current += P.angle(direction)
        current_bound = get_point(current, 2)

        if not skip % 10:
          skip = 0

        # time.sleep(0.01)

    except NothingToDo:
      continue

d = P(1000, 1000)
with open('mmap', 'a'):
  pass
data = point.make_mmapped_data(d, f=open('mmap', 'rb+'))
runs = int((sys.argv[1:] or ["10"])[0])
cutter_size = int((sys.argv[2:] or ["50"])[0])

try:
  path(d, data, runs=runs, cutter_size=cutter_size)
except Exception as e:
  import traceback
  traceback.print_exc(e)

