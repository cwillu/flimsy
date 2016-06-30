from __future__ import absolute_import
import sys
import math
import time
from planner import point
from planner.point import P

class NothingToDo(Exception):
  pass

POINT_MATERIAL = 0xffeeeeee
POINT_NO_GO = 0xdddd8888
POINT_NO_GO_RADIUS = 0x00880000
POINT_NO_GO_MASK = 0xdd444499
POINT_PREVIOUSLY_REMOVED = 0x00aaaaaa
POINT_REMOVED = 0x88000000
POINT_CANT_REACH = 0xaaffff00
POINT_NO_BOUND = 0x88000000

def a(angle):
  if angle is None:
    import traceback
    traceback.print_stack()
    return "a(NONE)!?"

  return "{} ({})".format(angle * 360 / 65520, angle)

def m(material):
  return "{:08x}".format(material)

def t(tick):
  return "{:8d}".format(tick)

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
  offset_points_solid = [P(0, -1), P(-1, 0), P(1, 0), P(0, 1), P(-1, -1), P(-1, 1), P(1, -1), P(1, 1)]
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
    for offset in offset_points_solid:
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
      data[0][c] = POINT_MATERIAL
      data[1][c] = 0x88000000
      data[2][c] = POINT_NO_BOUND

    offset = P(200, 250)
    size = (500, 200)


    tl = P(250, 250)
    br = P(800, 650)

    lines = [
      (P(600-radius, 250), P(600, 500)),
      (P(700-radius, 250), P(700, 500)),
    ]

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

        for p1, p2 in lines:
          if y >= p1.y and y <= p2.y:
            if x >= p1.x and x <= p2.x:
              set_point(P(x, y), POINT_NO_GO)

        if x == 0 or x == d.x - 1 or y == 0 or y == d.y - 1:
          set_point(P(x, y), POINT_NO_GO)


    c = P(200, 800)
    for r in range(1, 50):
      for offset in offset_points_with_center:
        set_point(c + P.angle(0, r) + offset, POINT_NO_GO, 0)
      set_point(c + P.angle(65520/4, r), POINT_NO_GO, 0)


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
          if get_point(no_go_radius, 2) != POINT_NO_BOUND:
            continue
          if get_point(no_go_radius) == POINT_NO_GO:
            continue
          # print '{:08x}'.format(get_point(no_go_radius))
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
          if get_point(no_go_radius) in [POINT_NO_GO, POINT_CANT_REACH]:
            continue

          set_point(no_go_radius, POINT_CANT_REACH, 0)
          set_point(no_go_radius, POINT_NO_GO_MASK, 2)

    print "Inverting cutter limit path"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p, 2) != POINT_NO_GO_RADIUS:
          continue

        set_point(p, POINT_MATERIAL)
        for cut_point in cut_points:
          no_go_radius = p + cut_point

          if get_point(no_go_radius) != POINT_CANT_REACH:
            continue

          set_point(no_go_radius, POINT_MATERIAL, 0)

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

      prior_last_on = None

      total_cuts = 0
      no_cuts_for = 0
      last_offs = []
      last_ons = set()

      tick = 0
      timer = 0.0000
      while True:
        if show_debug:
          print
        tick += 1
        skip += 1

        scan_angle = direction
        # scan_angle += initial_scan_yaw

        if jogging_distance <= 0:
          for step in xrange(65520/4):
            working = current + P.angle(scan_angle - step, radius + 1)
            material = get_point(working)
            if material in [POINT_MATERIAL]:
              scan_angle -= step
              direction -= step
              break
          else:
            scan_angle = direction
            working = current + P.angle(scan_angle - step, radius + 1)
            material = get_point(working)


          if material not in [POINT_REMOVED]:
            for step in xrange(65520):
              scan_angle = direction + step
              material = get_point(current + P.angle(scan_angle, radius+1))

              if show_scan:
                set_point(current + P.angle(scan_angle, radius), 0x88444444, 1)
              if material in [POINT_REMOVED]:
                if show_debug:
                  print t(tick), "scan 1", m(material)
                direction = scan_angle
                break
            else:
              if show_debug or True:
                print t(tick), "Scan fail 1"
          else:
            if show_scan and not skip % 3:
              set_point(current + P.angle(direction, radius), 0x88444444, 1)
            for search_radius in [1]:
              scan_angle = direction
              scan_angle -= 65520/16 * 3
              for step in xrange(65520):
                # TODO most of these loops can be massively improved by seeking the angle by bisection instead of stepping like this
                scan_angle -= 1
                try:
                  material = get_point(current + P.angle(scan_angle, radius+1 * (search_radius)))
                except ValueError:
                  continue

                if show_scan:
                  set_point(current + P.angle(scan_angle, radius + 1*search_radius), 0x88444444, 1)
                if material not in [POINT_REMOVED]:
                  direction -= 65520/16 * 3
                  direction -= step
                  direction %= 65520
                  if show_debug:
                    print t(tick), "scan 2", m(material)
                  break

              else:
                if show_debug or True:
                  print t(tick), "Scan fail 2", total_cuts, was_jogging, last_cuts, no_cuts_for, len(last_ons), len(last_offs)
                if no_cuts_for > 1:
                  no_cuts_for = radius * 8
                  was_jogging = 0
                  print "No cut fail 2"
                  # TODO We shouldn't get here nearly as often, we're dropping the last cut at intersections with existing material cuts (not at a bound)

        direction %= 65520

        if jogging_distance > 0:
          jogging_distance -= 1
          if jogging_distance < 1:
            jogging_distance = 0
            direction = jogging_direction
            current = jogging_destination
            old_current = current
            total_cuts = 1
            was_jogging = 1
            current_bound = get_point(current, 2)

        if jogging_distance <= 0:
          if current_bound in [POINT_NO_GO_RADIUS]:
            next_bound = get_point(current + P.angle(direction), 2)
            clamped = False
            if next_bound == POINT_NO_GO_MASK:
              clamped = True
              if show_debug:
                print t(tick), "clamping"

              # direction -= 65520 / 16
              # direction /= 65520 / 4
              # direction *= 65520 / 4
              # direction += 65520 / 16
              # print t(tick), "***on radius, initial direction:", a(direction)
              step = 1000
              trial_direction = direction
              while True:
              # for step in range(0, 65520, 65520/360):
                trial_direction += step
                next_bound = get_point((current) + P.angle(trial_direction), 2)
                # print t(tick), 'trial {:08x}'.format(next_bound), a(step), a(trial_direction)
                if step > 1 and next_bound == POINT_NO_GO_RADIUS:
                  step /= -3
                elif step < 0 and next_bound != POINT_NO_GO_RADIUS:
                  step /= -3
                elif step == 0 or step == 1:
                  step = 1
                  if next_bound == POINT_NO_GO_RADIUS:
                    direction = trial_direction
                    direction %= 65520
                    if show_debug:
                      print t(tick), "***", a(step), "direction is now:", a(direction)
                    # last_clamped_angle = direction
                    # last_clamped_position = current
                    break
            # if next_bound == current_bound and (current * 2) // 1.0 / 2 == current // 1.0:
            if show_debug:
              print t(tick), "post clamping direction", a(direction), "clamped?", clamped, "current bound", m(current_bound)
            if clamped:
              next_off_radius = current + P.angle(direction)
              next_off_direction = direction
              next_bound = get_point((current) + P.angle(trial_direction), 2)
              assert next_bound not in [POINT_NO_GO_MASK, POINT_NO_GO], m(next_bound)


            if clamped and last_bound != POINT_NO_GO_RADIUS:
              last_on_radius = current // 1.0
              # last_on_radius = old_current // 1.0
              last_on_direction = direction
              last_ons.add(last_on_radius)
              for p in offset_points_with_center:
                for pp in offset_points_with_center:
                  set_point(old_current + p, 0xffffff88, 1)
                  set_point(old_current + p+p+pp, 0xffffff99, 1)
              if show_debug:
                print t(tick), "On radius", last_on_radius, m(current_bound), a(last_on_direction)

              # if last_offs:
              #   ### XXX copied
              #   last_offs.sort(key=lambda (p, _): math.hypot(p.x - current.x, p.y - current.y))
              #   last_off_radius, last_off_direction = last_offs.pop(0)
              #   print t(tick), "to off", last_off_radius, a(last_off_direction)
              #
              #   # last_offs.extend(last_ons)
              #   last_ons = []
              #   destination = last_off_radius - current
              #   jogging_destination = last_off_radius
              #   jogging_direction = last_off_direction
              #   closest_distance = math.hypot(destination.x, destination.y)
              #   jogging_distance = max(int(closest_distance)-2,1)
              #   direction = int(math.atan2(destination.x, destination.y) * 65520 / (2 * math.pi))
              #   was_jogging = 0
              #   if show_debug:
              #     print t(tick), "jogging from {} to last_off {} dir: {}".format(current, last_off_radius, a(last_off_direction))
              #     print t(tick), "distance", jogging_distance

              # else:
              #
              #   # last_ons.append((last_on_radius, last_on_direction))
              #   for p in offset_points_with_center:
              #     for pp in offset_points_with_center:
              #       set_point(old_current + p, 0xffffff00, 1)
              #       set_point(old_current + p+p+pp, 0xffffff00, 1)
              #   if show_debug:
              #     print t(tick), "******************** On radius", last_on_radius, m(current_bound), a(last_on_direction)
            else:
              current_bound = last_bound
              #we've entered the building

              # print t(tick), direction
          else:
            if current_bound not in [None, POINT_NO_BOUND]:
              print t(tick), current
              print t(tick), m(current_bound), m(last_bound)
              assert False

            if last_bound == POINT_NO_GO_RADIUS:
              last_off_radius = next_off_radius - P.angle(next_off_direction, 1)
              last_off_direction = next_off_direction
              bnd = get_point(last_off_radius, 2)
              if show_debug:
                print t(tick), "*"*10, m(bnd), m(current_bound), m(next_bound)
                print t(tick), "last_bound==nogorad", last_off_radius, a(last_off_direction)
              last_offs.append((last_off_radius, last_off_direction))
              for p in offset_points_with_center:
                for pp in offset_points_with_center:
                  set_point(last_off_radius + p, 0xff0000ff, 1)
                  set_point(last_off_radius + p+p+pp, 0xff0000ff, 1)
                  set_point(last_off_radius + p+p+p+pp, 0xff0000ff, 1)
              if show_debug:
                print t(tick), "Off radius", last_off_radius, m(current_bound), a(next_off_direction), m(last_bound), a(last_off_direction)
              #we've left the building
              pass

          last_bound = current_bound


        if show_debug:
          print
          print t(tick), "loc:", current
          print t(tick), "dir", P.angle(direction), a(direction)
          print t(tick), "old:", old_current
          print t(tick), "oldv", P.angle(old_direction), a(old_direction)
          print t(tick), "mat", m(current_bound)
        if current // 1 != old_current // 1 and not jogging_distance:
          next_bound = get_point((current) + P.angle(direction), 2)
          last_cuts = total_cuts
          total_cuts = 0
          for cut_point in cut_points:
            was = set_point(old_current + cut_point, POINT_REMOVED, 0)
            if was == POINT_REMOVED:
              continue
            total_cuts += 1

          if total_cuts:
            if was_jogging and show_debug:
              print t(tick), "**** done jogging"
            no_cuts_for = 0
            was_jogging = 0
          else:
            no_cuts_for += 1
          if was_jogging:
            was_jogging += 1
            if was_jogging > radius*8:
              print t(tick), "**** timed out jogging" , radius
              was_jogging = 0
              # total_cuts += 1

            if get_point(current + P.angle(direction), 2) not in [POINT_NO_GO_RADIUS, POINT_NO_BOUND]:
              print t(tick), "**** jogging about to crash"
              was_jogging = 0


          if show_debug:
            print t(tick), "cuts", total_cuts, "previous", last_cuts, "# since cut", no_cuts_for
            print t(tick), "was jogging", was_jogging
            print t(tick), "jog distance", jogging_distance

          if was_jogging or no_cuts_for > 1:
            if prior_last_on and math.hypot(prior_last_on.x - current.x, prior_last_on.y - current.y) < 1.5:
              was_jogging = 0
              no_cuts_for = radius * 8
            else:
              for last_on in last_ons:
                if last_on == last_on_radius:
                  continue
                if current_bound != POINT_NO_GO_RADIUS:
                  continue
                if math.hypot(last_on.x - current.x, last_on.y - current.y) < 1.5:
                  was_jogging = 0
                  no_cuts_for = radius * 8
                  last_ons.remove(last_on)
                  prior_last_on = last_on
                  break

          # if current // 1.0 in last_ons and current // 1.0 != last_on_radius and no_cuts_for > radius*2:
          #   # last_ons.remove(current // 1.0)
          #   was_jogging = 0
          #   no_cuts_for = radius * 8
          #   print "*" * 30
          if was_jogging <= 0 and no_cuts_for >= radius * 8 and jogging_distance <= 0 and current_bound == next_bound:
            if show_debug:
              print t(tick), "current {}, old {}".format(current//1, old_current//1)
              print t(tick), "total cuts {}, jogging {}".format(total_cuts, jogging_distance)
            # if current_bound == POINT_NO_GO_RADIUS and last_offs:
            if last_offs:
              ### XXX copied
              # last_offs.extend(last_ons[::-1])
              # last_ons = []
              last_offs.sort(key=lambda (p, _): math.hypot(p.x - current.x, p.y - current.y))
              last_off_radius, last_off_direction = last_offs.pop(0)
              if show_debug:
                print t(tick), "jogging from {} to last_off {}".format(current, last_off_radius, a(last_off_direction))
              destination = last_off_radius - current
              jogging_destination = last_off_radius
              jogging_direction = last_off_direction
              closest_distance = math.hypot(destination.x, destination.y)
              jogging_distance = max(int(closest_distance)-2,1)
              direction = int(math.atan2(destination.x, destination.y) * 65520 / (2 * math.pi))
              was_jogging = 0
            # elif current_bound != POINT_NO_GO_RADIUS and last_ons:
            #   last_on_radius, last_on_direction = last_ons.pop()
            #   if show_debug or True:
            #     print t(tick), "*********** jogging from {} to last_on {}".format(current, last_on_radius, a(last_on_direction))
            #   destination = last_on_radius - current
            #   jogging_direction = last_on_direction
            #   jogging_destination = last_on_radius
            #   closest_distance = math.hypot(destination.x, destination.y)
            #   jogging_distance = max(int(closest_distance)-2,1)
            #   direction = int(math.atan2(destination.x, destination.y) * 65520 / (2 * math.pi))
            #   was_jogging = 0
            else:
              if show_debug or True:
                print t(tick), "Scan fail 3"
                print t(tick), current, a(direction)
                # assert False
              # last_ons.clear()
              # last_offs = []
              #XXX also copied
              closest_distance = math.hypot(d.x, d.y)
              closest = None
              destination = None
              for y in range(d.y):
                for x in range(d.x):
                  point = P(x, y)
                  material = get_point(point)
                  if material not in [POINT_MATERIAL]:
                    continue
                  bound = get_point(point, 2)
                  if bound not in [POINT_NO_BOUND]:
                    continue

                  point -= current
                  distance = math.hypot(point.x, point.y)
                  if distance <= closest_distance and distance > radius+1:
                    closest = point
                    closest_distance = distance
                    destination = P(x, y)
              if closest is None:
                print t(tick), "Nothing to do here"
                raise NothingToDo
              direction = int(math.atan2(closest.x, closest.y) * 65520 / (2 * math.pi)) % 65520
              jogging_distance = int(closest_distance) - radius - 1
              jogging_destination = destination
              jogging_direction = direction
              print t(tick), m(get_point(jogging_destination)), jogging_destination
              if show_debug or True:
                print t(tick), "long jog (1) {} {}".format(jogging_distance, a(direction)), len(last_ons), len(last_offs)
              if jogging_distance <= 0:
                assert False

        if show_path:
          if jogging_distance > 0:
            for p in offset_points_with_center:
              set_point(current, 0x88226622, 1)
          elif was_jogging > 0:
              set_point(current, 0x88ff0000, 1)
          elif no_cuts_for > 0:
              set_point(current, 0x880000ff, 1)
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

        # if current_bound in [POINT_NO_GO_RADIUS]:
        #   last_on_radius = current // 1.0


        if jogging_distance <= 0 and current_bound in [POINT_NO_GO_MASK]:
          print t(tick), current, was_jogging, jogging_distance
          print t(tick), "In forbidden area", last_off_radius, m(current_bound), a(next_off_direction), m(last_bound), a(last_off_direction)

          assert False

        if not skip % 10:
          skip = 0

        if was_jogging:
          timer = timer
        if timer:
          time.sleep(timer)

    except NothingToDo:
      return
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

