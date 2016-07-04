from __future__ import absolute_import
import sys
import math
import time
from planner import point
from planner.point import P, POINT

class NothingToDo(Exception):
  pass

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



def path(surface, runs=10, cutter_diameter=20):
  d = surface.d
  get_point = surface.get_point
  set_point = surface.set_point

  #cutter radius in 1/1000 of an inch
  radius = cutter_size / 2

  show_path = 1
  show_heading = 1
  show_scan = 1
  show_debug = 0

  radius_sq = radius ** 2
  initial_scan_yaw = 1

  def clockwise_sorted(l):
    l = list(set(l))
    l.sort(key=lambda p: math.atan2(p.y, p.x) * point.RADS_TO_BIN % 65520)
    return l
  def scanline_sorted(l):
    l = list(set(l))
    l.sort(key=lambda p: (p.y, p.x))
    return l

  cut_points = []
  for angle in range(65520):
    for inwards in range(1):
      p = P.angle(angle) * (radius - inwards)
      p = P(round(p.x), round(p.y))
      cut_points.append(p)

  offset_points = [P(0, -1), P(-1, 0), P(1, 0), P(0, 1)]
  offset_points_solid = [P(0, -1), P(-1, 0), P(1, 0), P(0, 1), P(-1, -1), P(-1, 1), P(1, -1), P(1, 1)]
  offset_points_with_center = [P(0, -1), P(-1, 0), P(1, 0), P(0, 1)]

  no_go_trace_points = []
  for cut_point in cut_points:
    for offset in offset_points_solid:
      p = cut_point + offset
      no_go_trace_points.append(p)

  scanner_points = cut_points + no_go_trace_points

  for point_list in [cut_points, no_go_trace_points]:
    point_list[:] = scanline_sorted(point_list)

  print offset_points_solid
  for point_list in [offset_points, offset_points_solid, scanner_points]:
    point_list[:] = clockwise_sorted(point_list)
  print offset_points_solid

  # for p in offset_points_solid:
  #   print p, int(math.atan2(p.y, p.x) * point.RADS_TO_BIN % 65520)
  # return

  for run in xrange(1, runs+1):
    print "Run {}\r".format(run),
    sys.stdout.flush()

    for f in [1, 3, 4, 5, 6, 7, 8]:
      for p in surface:
        set_point(p, 0x00000000, f)
    for p in surface:
      set_point(p, POINT.MATERIAL, 0)
      set_point(p, POINT.NO_BOUND, 2)

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
            set_point(P(x, y), POINT.NO_GO)
        if x > tl.x and x < br.x:
          if abs(y-tl.y) < 40 or abs(y-br.y) < 40:
            set_point(P(x, y), POINT.NO_GO)

        circle_center = math.hypot(800-x, 800-y)
        if circle_center > 50 and circle_center < 80:
          set_point(P(x, y), POINT.NO_GO)

        for p1, p2 in lines:
          if y >= p1.y and y <= p2.y:
            if x >= p1.x and x <= p2.x:
              set_point(P(x, y), POINT.NO_GO)

        if x == 0 or x == d.x - 1 or y == 0 or y == d.y - 1:
          set_point(P(x, y), POINT.NO_GO)


    c = P(200, 800)
    for r in range(1, 50):
      for offset in offset_points_with_center:
        set_point(c + P.angle(0, r) + offset, POINT.NO_GO, 0)
      set_point(c + P.angle(65520/4, r), POINT.NO_GO, 0)

    print "Copying part rendering"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p) not in [POINT.NO_GO]:
          continue

        set_point(p, POINT.NO_GO, 2)

    print "Filling cutter radius around parts"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p, 0) != POINT.NO_GO:
          continue

        # interior points can be ignored re: radius checks
        for offset in offset_points:
          if get_point(p+offset, 0) != POINT.NO_GO:
            break
        else:
          continue

        for cut_point in cut_points:
          no_go_radius = p + cut_point
          if get_point(no_go_radius, 2) != POINT.NO_BOUND:
            continue
          set_point(no_go_radius, POINT.CANT_REACH, 2)
        for bound in offset_points:
          for rad in range(radius-1):
            no_go_radius = p + bound * rad
            if get_point(no_go_radius, 2) != POINT.NO_BOUND:
              continue
            set_point(no_go_radius, POINT.CANT_REACH, 2)



    print "Tracing limit path"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p, 2) != POINT.CANT_REACH:
          continue

        for offset in offset_points:
          edge = p + offset
          if get_point(edge, 2) != POINT.NO_BOUND:
            continue
          set_point(edge, POINT.NO_GO_RADIUS, 2)

    print "Filling cutter radius around limit path"
    for y in range(d.y):
      for x in range(d.x):
        p = P(x, y)
        if get_point(p, 2) != POINT.NO_GO_RADIUS:
          continue

        for cut_point in cut_points:
          no_go_radius = p + cut_point
          if get_point(no_go_radius, 2) != POINT.CANT_REACH:
            continue
          set_point(no_go_radius, POINT.NO_GO_MASK, 2)
        for bound in offset_points:
          for rad in range(radius-1):
            no_go_radius = p + bound * rad
            if get_point(no_go_radius, 2) != POINT.CANT_REACH:
              continue

            break

    try:
      def nextprev_radius_point(p, direction):
        """
        direction is only needed to make single-pixel radius "rivers" tractable, to set a bias

        Note that the next and previous points may be the same (i.e. if the p is a deadend)
        """
        direction %= 65520
        for index, neighbour in enumerate(offset_points_solid):
          if direction < (math.atan2(neighbour.y, neighbour.x) * point.RADS_TO_BIN) % 65520 + (65520/8):
            break
        else:
          assert False

        for no_go_index, neighbour in enumerate((offset_points_solid[index:] + offset_points_solid[:index])):
          bound = get_point(p + neighbour, 2)
          if bound == POINT.NO_GO_MASK:
            break
        else:
          return None

        for neighbour in (offset_points_solid[no_go_index:] + offset_points_solid[:no_go_index]):
          bound = get_point(p + neighbour, 2)
          if bound == POINT.NO_GO_RADIUS:
            break
        else:
          assert False
        previous_radius = p + neighbour

        for neighbour in (offset_points_solid[no_go_index:] + offset_points_solid[:no_go_index])[::-1]:
          bound = get_point(p + neighbour, 2)
          if bound == POINT.NO_GO_RADIUS:
            break
        else:
          assert False
        next_radius = p + neighbour

        return next_radius, previous_radius

      def best_way_to(current, p):
        """
        p will be offset to 0.5 due to our use of truncation elsewhere
        """

        p //= 1.0
        p += 0.5
        trial_angle = int(math.atan2(current.y - p.y, current.x - p.x) * point.RADS_TO_BIN % 65520)
        for step in xrange(65520):
          if get_point(current + P.angle(trial_angle - step), 2) != POINT.NO_GO_MASK:
            break
        else:
          assert False, current
        return trial_angle - step


      skip = 0
      direction = 0
      current = P(400.0, 500.0)
      last_bound = None
      current_bound = None

      feed_step = 1

      working = P(0.0, 0.0)
      old_current = current
      old_direction = direction

      jogging_distance = 0
      jogging_destination = None
      jogging_direction = direction

      last_on_radius = None
      last_on_direction = None
      last_off_radius = None
      last_off_direction = None

      prior_last_on = None

      cuts = 0
      no_cuts_for = 0
      total_cuts_for_path = 0

      last_offs = []
      last_cuts = {}
      last_ons = set()

      tick = 0
      timer = 0.00
      while True:
        if show_debug:
          print
        tick += 1
        skip += 1

        scan_angle = direction
        # scan_angle += initial_scan_yaw

        if jogging_distance <= 0:
          last_checked = None
          for step in xrange(65520):
            scan_angle = direction + step
            scan_point = current + P.angle(scan_angle, radius+1) // 1
            if scan_point == last_checked:
              continue
            last_checked = scan_point
            material = get_point(scan_point)

            if material in [POINT.MATERIAL]:
              direction = scan_angle
              break
          else:
            scan_angle = direction
            working = current + P.angle(scan_angle + step, radius + 1)
            material = get_point(working)
            last_checked = None


          if material == POINT.MATERIAL:
            for step in xrange(65520):
              scan_angle = direction + step
              scan_point = current + P.angle(scan_angle, radius+1)
              material = get_point(scan_point)

              if show_scan:
                set_point(current + P.angle(scan_angle, radius), 0x88444444, 3)
              if material in [POINT.REMOVED]:
                if show_debug:
                  print t(tick), "scan 1", m(material)
                direction = scan_angle
                break
            else:
              if show_debug or True:
                print t(tick), "Scan fail 1"
          elif last_checked and current_bound not in [POINT.NO_GO_RADIUS]:
            for step in xrange(65520):
              # TODO most of these loops can be massively improved by seeking the angle by bisection instead of stepping like this
              scan_angle = direction - step
              scan_point = current + P.angle(scan_angle, radius+1)
              material = get_point(scan_point)

              if show_scan:
                set_point(current + P.angle(scan_angle, radius), 0xffff0000, 3)
              if material not in [POINT.REMOVED]:
                direction -= step
                direction %= 65520
                if show_debug:
                  print t(tick), "scan 2", m(material)
                break

              # material = get_point(current + P.angle(scan_angle, radius+2))
              # if show_scan:
              #   set_point(current + P.angle(scan_angle, radius), 0xffffffff, 3)
              #   time.sleep(0.01)
              # if material not in [POINT.REMOVED]:
              #   direction -= step
              #   direction %= 65520
              #   if show_debug:
              #     print t(tick), "scan 2a", m(material)
              #   break

            else:
              no_cuts_for = radius * 8
              if show_debug or True:
                print t(tick), "Scan fail 2", cuts, last_cuts, no_cuts_for, len(last_ons), len(last_offs)
              if no_cuts_for > radius:
                print t(tick), "No cut fail 2"
                no_cuts_for = radius * 8
                # TODO We shouldn't get here nearly as often, we're dropping the last cut at intersections with existing material cuts (not at a bound)

        direction %= 65520

        if jogging_distance > 0:
          jogging_distance -= 1
          if jogging_distance < 1:
            no_cuts_for = -radius
            jogging_distance = 0
            direction = jogging_direction
            current = jogging_destination
            old_current = current
            cuts = 1
            total_cuts_for_path = 0
            current_bound = get_point(current, 2)

        next_bound = get_point(current + P.angle(direction), 2)

        if jogging_distance <= 0:
          on_radius = nextprev_radius_point(current, direction)
          if on_radius:
            if next_bound == POINT.NO_GO_MASK or last_checked == None:
              direction = best_way_to(current, on_radius[0])

              if current_bound == POINT.NO_BOUND:
                last_ons.add(on_radius[0])
                set_point(on_radius[0], 0xffffff88, 4)

            elif next_bound == POINT.NO_BOUND:
              last_on = nextprev_radius_point(on_radius[-1], direction)
              print t(tick), "nobound", repr(last_on), repr(on_radius), current
              last_offs.append((on_radius[-1], best_way_to(on_radius[-1], last_on[0])))
              set_point(on_radius[-1], 0xffccccff, 5)


          # if next_bound == POINT.NO_GO_MASK:
          #   # radius_direction = current // 1 - (current + P.angle(direction)) // 1
          #   # assert radius_direction in offset_points_solid, radius_direction
          #   #
          #   # cut = offset_points_solid.index(radius_direction)
          #   # for trial_point in offset_points_solid[cut:] + offset_points_solid[:cut]:
          #   # for step, clamped_vector in enumerate(offset_points_solid[cut:] + offset_points_solid[:cut]):
          #
          #   for step in range(0, 65520, 65520/8):
          #     next_bound = get_point(current + P.angle(direction + step), 2)
          #     if next_bound == POINT.NO_GO_RADIUS:
          #       break
          #     assert next_bound != POINT.NO_BOUND
          #   else:
          #     assert False, "We got too deep in a NO_GO_MASK area somehow " + repr(current)
          #
          #
          #
          #
          #
          # elif next_bound == POINT.NO_BOUND and current_bound == POINT.NO_GO_RADIUS
          #   clamped = False
          #   if next_bound != POINT.NO_GO_RADIUS:
          #     clamped = True
          #     if show_debug:
          #       print t(tick), "clamping"
          #
          #     # direction -= 65520 / 16
          #     # direction /= 65520 / 4
          #     # direction *= 65520 / 4
          #     # direction += 65520 / 16
          #     # print t(tick), "***on radius, initial direction:", a(direction)
          #     step = 1000
          #     trial_direction = direction
          #     while True:
          #     # for step in range(0, 65520, 65520/360):
          #       trial_direction += step
          #       bound = get_point((current) + P.angle(trial_direction), 2)
          #       # print t(tick), 'trial {:08x}'.format(next_bound), a(step), a(trial_direction)
          #       if step > 1 and bound == POINT.NO_GO_RADIUS:
          #         step /= -3
          #       elif step < 0 and bound != POINT.NO_GO_RADIUS:
          #         step /= -3
          #       elif step == 0 or step == 1:
          #         step = 1
          #         if bound == POINT.NO_GO_RADIUS:
          #           trial_direction %= 65520
          #           next_off_direction = direction
          #           next_off_direction /= 65520 / 8
          #           next_off_direction *= 65520 / 8
          #           next_off_direction
          #           next_off_radius = current # + P.angle(next_off_direction)
          #           if next_bound in [POINT.NO_GO_MASK, POINT.CANT_REACH]:
          #             direction = trial_direction
          #             next_bound = bound
          #           if show_debug:
          #             print t(tick), "***", a(step), "direction is now:", a(direction)
          #           # last_clamped_angle = direction
          #           # last_clamped_position = current
          #           break
          #   # if next_bound == current_bound and (current * 2) // 1.0 / 2 == current // 1.0:
          #   if show_debug:
          #     print t(tick), "post clamping direction", a(direction), "clamped?", clamped, "current bound", m(current_bound)
          #   if clamped:
          #     # next_off_radius = current + P.angle(next_off_direction)
          #     # next_bound = get_point((current) + P.angle(trial_direction), 2)
          #     assert next_bound not in [POINT.NO_GO_MASK, POINT.NO_GO, POINT.CANT_REACH], m(next_bound)
          #
          #
          #   if current_bound == POINT.NO_GO_RADIUS and last_bound != POINT.NO_GO_RADIUS:
          #     last_on_radius = current // 1.0
          #     # last_on_radius = old_current // 1.0
          #     last_on_direction = direction
          #     last_ons.add(last_on_radius)
          #     set_point(last_on_radius, 0xffffff88, 4)
          #     if show_debug:
          #       print t(tick), "On radius", last_on_radius, m(current_bound), a(last_on_direction)
          #
          #     # if last_offs:
          #     #   ### XXX copied
          #     #   last_offs.sort(key=lambda (p, _): math.hypot(p.x - current.x, p.y - current.y))
          #     #   last_off_radius, last_off_direction = last_offs.pop(0)
          #     #   set_point(last_off_radius, 0x77000044, 5)
          #     #   print t(tick), "to off", last_off_radius, a(last_off_direction)
          #     #
          #     #   # last_offs.extend(last_ons)
          #     #   last_ons = []
          #     #   destination = last_off_radius - current
          #     #   jogging_destination = last_off_radius
          #     #   jogging_direction = last_off_direction
          #     #   closest_distance = math.hypot(destination.x, destination.y)
          #     #   jogging_distance = max(int(closest_distance)-2,1)
          #     #   direction = int(math.atan2(destination.x, destination.y) * point.RADS_TO_BIN)
          #     #   was_jogging = 0
          #     #   if show_debug:
          #     #     print t(tick), "jogging from {} to last_off {} dir: {}".format(current, last_off_radius, a(last_off_direction))
          #     #     print t(tick), "distance", jogging_distance
          #
          #     # else:
          #     #
          #     #   # last_ons.append((last_on_radius, last_on_direction))
          #     #   for p in offset_points_with_center:
          #     #     for pp in offset_points_with_center:
          #     #       set_point(old_current + p, 0xffffff00, 4)
          #     #       set_point(old_current + p+p+pp, 0xffffff00, 4)
          #     #   if show_debug:
          #     #     print t(tick), "******************** On radius", last_on_radius, m(current_bound), a(last_on_direction)
          #   # else:
          #     # current_bound = last_bound
          #     #we've entered the building
          #
          #     # print t(tick), direction
          # else:
          #   if current_bound not in [None, POINT.NO_BOUND]:
          #     print t(tick), current
          #     print t(tick), m(current_bound), m(last_bound)
          #     assert False
          #
          #   if last_bound == POINT.NO_GO_RADIUS:
          #     last_off_radius = next_off_radius - P.angle(next_off_direction, 1)
          #     last_off_direction = next_off_direction
          #     bnd = get_point(last_off_radius, 2)
          #     if show_debug:
          #       print t(tick), "*"*10, m(bnd), m(current_bound), m(next_bound)
          #       print t(tick), "last_bound==nogorad", last_off_radius, a(last_off_direction)
          #     if total_cuts_for_path > 0:
          #       last_offs.append((last_off_radius, last_off_direction))
          #       set_point(last_off_radius, 0xffccccff, 5)
          #     if show_debug:
          #       print t(tick), "Off radius", last_off_radius, m(current_bound), a(next_off_direction), m(last_bound), a(last_off_direction)
          #     #we've left the building
          #     pass
          #
          # last_bound = current_bound


        if show_debug:
          print
          print t(tick), "loc:", current
          print t(tick), "dir", P.angle(direction), a(direction)
          print t(tick), "old:", old_current
          print t(tick), "oldv", P.angle(old_direction), a(old_direction)
          print t(tick), "mat", m(current_bound)
        # if current // 1 != old_current // 1 and not jogging_distance:
        if not jogging_distance:
          next_bound = get_point((current) + P.angle(direction), 2)
          last_cuts = cuts
          cuts = 0
          for cut_point in cut_points:
            was = set_point(old_current + cut_point, POINT.REMOVED, 0)
            if was == POINT.NO_GO:
              assert False
            elif was == POINT.REMOVED:
              continue
            cuts += 1
          total_cuts_for_path += 1

          if cuts:
            no_cuts_for = 0
          else:
            no_cuts_for += 1
          if show_debug:
            print t(tick), "cuts", cuts, "previous", last_cuts, "# since cut", no_cuts_for
            print t(tick), "jog distance", jogging_distance

          # if was_jogging or no_cuts_for > 1:
          if no_cuts_for > radius:
            if prior_last_on and math.hypot(prior_last_on.x - current.x, prior_last_on.y - current.y) < 1.5:
              no_cuts_for = radius * 8
              print t(tick), "ping"
            else:
              for last_on in last_ons:
                if last_on == last_on_radius:
                  continue
                if current_bound != POINT.NO_GO_RADIUS:
                  continue
                if math.hypot(last_on.x - current.x, last_on.y - current.y) < 1.5:
                  no_cuts_for = radius * 8
                  last_ons.remove(last_on)
                  set_point(last_on_radius, 0xff88880, 4)

                  prior_last_on = last_on
                  break

          # if current // 1.0 in last_ons and current // 1.0 != last_on_radius and no_cuts_for > radius*2:
          #   # last_ons.remove(current // 1.0)
          #   was_jogging = 0
          #   no_cuts_for = radius * 8
          #   print "*" * 30
          if no_cuts_for >= radius and jogging_distance <= 0 and current_bound == next_bound:
            if show_debug:
              print t(tick), "current {}, old {}".format(current//1, old_current//1)
              print t(tick), "cuts {}, jogging {}".format(cuts, jogging_distance)
            # if current_bound == POINT.NO_GO_RADIUS and last_offs:
            if last_offs:
              ### XXX copied
              # last_offs.extend(last_ons[::-1])
              # last_ons = []
              last_offs.sort(key=lambda (p, _): math.hypot(p.x - current.x, p.y - current.y))
              last_off_radius, last_off_direction = last_offs.pop(0)
              set_point(last_off_radius, 0xff0000ff, 5)

              if show_debug:
                print t(tick), "jogging from {} to last_off {}".format(current, last_off_radius, a(last_off_direction))
              destination = last_off_radius - current
              jogging_destination = last_off_radius
              jogging_direction = last_off_direction
              closest_distance = math.hypot(destination.x, destination.y)
              jogging_distance = max(int(closest_distance)-2,1)
              direction = int(math.atan2(destination.y, destination.x) * point.RADS_TO_BIN % 65520)
            # elif current_bound != POINT.NO_GO_RADIUS and last_ons:
            #   last_on_radius, last_on_direction = last_ons.pop()
            #   set_point(last_on_radius, 0xff444400, 4)
            #   if show_debug or True:
            #     print t(tick), "*********** jogging from {} to last_on {}".format(current, last_on_radius, a(last_on_direction))
            #   destination = last_on_radius - current
            #   jogging_direction = last_on_direction
            #   jogging_destination = last_on_radius
            #   closest_distance = math.hypot(destination.x, destination.y)
            #   jogging_distance = max(int(closest_distance)-2,1)
            #   direction = int(math.atan2(destination.x, destination.y) point.RADS_TO_BIN)
            else:
              if show_debug or True:
                print t(tick), "Scan fail 3"
                print t(tick), current, a(direction)
                # timer = 0.001

                # assert False
              last_ons.clear()
              last_bound = None
              next_off_radius = None
              next_off_direction = None
              # last_offs = []
              #XXX also copied
              closest_distance = math.hypot(d.x, d.y)
              closest = None
              destination = None
              search_radius = radius
              while True:
                for y in range((current // 1).y - search_radius, (current // 1).y + search_radius):
                  for x in range((current // 1).x - search_radius, (current // 1).x + search_radius):
                    distance = math.hypot(current.x-x, current.y-y)
                    if distance > search_radius or distance <= search_radius / 2:
                      continue
                    p = P(x, y)
                    material = get_point(p)
                    if material not in [POINT.MATERIAL]:
                      continue
                    bound = get_point(p, 2)
                    if bound not in [POINT.NO_GO_RADIUS, POINT.NO_BOUND]:
                      continue
                      # TODO this needs to find the closest radius point instead
                    if distance <= closest_distance and distance > radius+1:
                      closest = p
                      closest_distance = distance
                      destination = P(x, y)
                if closest:
                  break
                if search_radius > math.hypot(d.x, d.y):
                  break
                search_radius *= 2
              if not closest:
                print t(tick), "Nothing to do here"
                raise NothingToDo
              direction = int(math.atan2(closest.y, closest.x) * point.RADS_TO_BIN) % 65520
              jogging_distance = int(closest_distance) - radius
              jogging_destination = destination
              jogging_direction = direction
              print t(tick), m(get_point(jogging_destination)), jogging_destination
              if jogging_distance:
                if show_debug or True:
                  print t(tick), "long jog (1) {} {}".format(jogging_distance, a(direction)), len(last_ons), len(last_offs)
              # if jogging_distance <= 0:
              #   assert False

        if show_path:
          if jogging_distance > 0:
            set_point(current, 0x88226622, 7)
          elif no_cuts_for > 0:
            set_point(current, 0xcc999999, 1)
          else:
            set_point(current, 0xccffffff, 1)

        direction %= 65520
        if show_heading and not skip % 3 and jogging_distance <= 0:
          for r in range(1, int(radius / 1.5)):
            set_point(current + P.angle(direction -65520/4, r), 0x88888800, 6)

        old_current = current
        old_direction = direction

        current += P.angle(direction)
        current_bound = get_point(current, 2)

        # if current_bound in [POINT.NO_GO_RADIUS]:
        #   last_on_radius = current // 1.0


        if jogging_distance <= 0 and current_bound in [POINT.NO_GO_MASK, POINT.CANT_REACH]:
          print t(tick), current, jogging_distance
          print t(tick), "In forbidden area", last_off_radius, m(current_bound), a(next_off_direction), m(last_bound), a(last_off_direction)

          assert False

        if not skip % 10:
          skip = 0

        if timer:
          time.sleep(timer)

    except NothingToDo:
      failed_points = 0
      for y in range(d.y):
        for x in range(d.x):
          p = P(x, y)
          if get_point(p) != POINT.MATERIAL:
            continue
          if get_point(p, 2) == POINT.CANT_REACH:
            continue

          # set_point(p, 0xffff0000)
          # set_point(p, 0x00000000, 1)
          # set_point(p, 0x00000000, 2)
          failed_points += 1

      if failed_points:
        raise Exception("Failed to cut {} reachable points".format(failed_points))

surface = point.Surface()

cutter_size = int((sys.argv[1:] or ["12"])[0])
runs = int((sys.argv[2:] or ["1"])[0])

try:
  path(surface, cutter_diameter=cutter_size, runs=runs)
except Exception as e:
  import traceback
  traceback.print_exc(e)

