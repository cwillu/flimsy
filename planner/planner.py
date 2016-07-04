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

def t(tick=''):
  return "{:8}".format(tick)



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
    l.sort(key=lambda p: (math.atan2(p.y, p.x) * point.RADS_TO_BIN) % 65520)
    return l
  def scanline_sorted(l):
    l = list(set(l))
    l.sort(key=lambda p: (p.y, p.x))
    return l
  def distance_sorted(current, l):
    l = list(set(l))
    l.sort(key=lambda p: math.hypot(p.x - current.x, p.y - current.y))
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
        # print (direction-1) / (65520/8) * (65520/8)
        index = (direction) / (65520/8) % 8

        no_go_offsets = offset_points_solid[index:] + offset_points_solid[:index]
        if show_debug:
          print
          print t(tick), "radpoint ", p, a(direction), " "
          print t(tick), "offset_points_solid"
          for ii, offset in enumerate(offset_points_solid):
            print t(ii), offset
          print t(), "index", index, offset_points_solid[index]

          print t(tick), "no_go_mask_offsets"
          for ii, offset in enumerate(no_go_offsets):
            print t(ii), offset


        for no_go_index, neighbour in enumerate(no_go_offsets):
          bound = get_point(p + neighbour, 2)
          if bound == POINT.NO_GO_MASK:
            break
        else:
          return None
        if show_debug:
          print t(), "no_go_index", no_go_index, no_go_offsets[no_go_index], neighbour

        next_radius_offsets = (no_go_offsets[no_go_index:] + no_go_offsets[:no_go_index])[::-1]
        if show_debug:
          print t(tick), "next radius offsets"
          for ii, offset in enumerate(next_radius_offsets):
            print t(), ii, offset



        for next_radius_index, neighbour in enumerate(next_radius_offsets):
          bound = get_point(p + neighbour, 2)
          if show_debug:
            print 'Neighbour:', neighbour, m(bound)
          if bound == POINT.NO_GO_RADIUS:
            if show_debug:
              print t(), "next_radius_index", next_radius_index, next_radius_offsets[next_radius_index], neighbour
              print "Got it", p
            break
        else:
          assert False
        if show_debug:
          print t('*****'), a(direction), p
          print t('search'), index, offset_points_solid[index], p + offset_points_solid[index]
          print t('no-go'), no_go_index, offset_points_solid[no_go_index], p + offset_points_solid[no_go_index]
          print t(), "next:", neighbour
        next_radius = p + neighbour

        for next_radius_index, neighbour in enumerate(next_radius_offsets[::-1]):
          bound = get_point(p + neighbour, 2)
          if bound == POINT.NO_GO_RADIUS:
            break
        else:
          assert False
        if show_debug:
          print t(), "previous:", neighbour
        previous_radius = p + neighbour

        return next_radius, previous_radius

      def direct_path_to(current, p):
        """
        p will be offset to 0.5 due to our use of truncation elsewhere
        """

        p //= 1.0
        p += 0.5
        return int(math.atan2(p.y - current.y, p.x - current.x) * point.RADS_TO_BIN) % 65520

      def best_path_to(current, p):
        """
        p will be offset to 0.5 due to our use of truncation elsewhere
        """

        p //= 1.0
        p += 0.5
        trial_angle = int(math.atan2(p.y - current.y, p.x - current.x) * point.RADS_TO_BIN) % 65520
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

      jogging_target = None
      jogging_direction = direction

      last_on_radius = None
      last_on_direction = None
      last_off_radius = None
      last_off_direction = None

      prior_last_on = None

      cuts = 0
      no_cuts_for = 0
      total_cuts_for_path = 0

      recent_off_radius = None
      last_offs = {}
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

        if jogging_target is None:
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
              scan_angle = direction - step
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
          next_bound = get_point(current + P.angle(direction), 2)

          on_radius = nextprev_radius_point(current, direction)
          if on_radius:
            if show_debug:
              print t(tick), "on rad", a(direction), current
              print t(), "next", on_radius[0], "", "prev", on_radius[-1]
              print t(), "current bound", m(current_bound), "", "next (trial) bound", m(next_bound)

            if get_point(current, 4):
              if show_debug:
                print t("***"), "current and last:", current, old_current
              # we've been at this radius point before, so we can potentially jog
              if last_offs:
                jogging_target = distance_sorted(current, last_offs)[0]
                jogging_direction = last_offs.pop(jogging_target)
                set_point(jogging_target, 0xff0000ff, 4)

                if show_debug or True:
                  print t(), "jogging1 from {} to {} ({})".format(current, jogging_target, a(jogging_direction))
            elif last_bound == POINT.NO_BOUND:
              if show_debug:
                print t(), "add on rad mark"
              last_ons.add(on_radius[-1])
              set_point(on_radius[0], 0xffffff88, 5)
              if recent_off_radius:
                jogging_target = distance_sorted(current, last_offs)[0]
                jogging_direction = last_offs.pop(jogging_target)
                set_point(jogging_target, 0xff0000ff, 4)

                if show_debug or True:
                  print t(), "jogging2 from {} to {} ({})".format(current, jogging_target, a(jogging_direction))

              recent_off_radius = None


            if next_bound == POINT.NO_GO_MASK or last_checked == None:
              if show_debug:
                print t('clamping'), current, on_radius[0], a(direction)
              direction = best_path_to(current, on_radius[0])
              if show_debug:
                print t(), "no go clamp", a(direction)
                print t(), m(get_point(current + P.angle(direction), 2))
                print t(), "next point", current + P.angle(direction)
                print t(), "new_angle", P.angle(direction)
            elif next_bound == POINT.NO_BOUND:
              last_on = nextprev_radius_point(on_radius[-1], direction)
              last_dir = best_path_to(on_radius[-1], last_on[0])
              if show_debug:
                print t(), "add off rad mark"
                print t(), "from {}: {}".format(current, repr(on_radius))
                print t(), "  so {}: {}".format(on_radius[-1], repr(last_on)), a(last_dir)
              last_offs[on_radius[-1]] = last_dir
              set_point(on_radius[-1], 0xffccccff, 4)
              recent_off_radius = on_radius[-1]



        if show_debug:
          print
          print t(tick), "loc:", current
          print t(tick), "dir", P.angle(direction), a(direction)
          print t(tick), "old:", old_current
          print t(tick), "oldv", P.angle(old_direction), a(old_direction)
          print t(tick), "mat", m(current_bound)
        if jogging_target is None and current // 1 != old_current // 1:
          next_bound = get_point((current) + P.angle(direction), 2)
          last_cuts = cuts
          cuts = 0
          for cut_point in cut_points:
            # was = set_point(old_current + cut_point, POINT.REMOVED, 0)
            was = set_point(current + cut_point, POINT.REMOVED, 0)
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

          # if was_jogging or no_cuts_for > 1:
          # if no_cuts_for > radius:
          #   assert False
          #   if prior_last_on and math.hypot(prior_last_on.x - current.x, prior_last_on.y - current.y) < 1.5:
          #     no_cuts_for = radius * 8
          #     print t(tick), "ping"
          #   else:
          #     for last_on in last_ons:
          #       if last_on == last_on_radius:
          #         continue
          #       if current_bound != POINT.NO_GO_RADIUS:
          #         continue
          #       if math.hypot(last_on.x - current.x, last_on.y - current.y) < 1.5:
          #         no_cuts_for = radius * 8
          #         last_ons.remove(last_on)
          #         set_point(last_on_radius, 0xff88880, 4)
          #
          #         prior_last_on = last_on
          #         break



        if show_path:
          if jogging_target:
            if not skip % 3:
              for offset in offset_points:
                set_point(current + offset + offset, 0xff226622, 7)
          elif no_cuts_for > 0:
            set_point(current, 0xcc999999, 1)
          else:
            set_point(current, 0xccffffff, 1)

        direction %= 65520
        if show_heading and not skip % 3 and not jogging_target:
          for r in range(1, int(radius / 2)):
            set_point(current + P.angle(direction + 65520/4, r), 0x88888800, 6)

        last_bound = current_bound
        old_current = current
        old_direction = direction

        if jogging_target is not None:
          distance = math.hypot(current.x - jogging_target.x, current.y - jogging_target.y)

          if distance < 10 and not timer:
            timer = 0.05

          if distance < 2:
            timer = 0.001


          if distance > 1:
            direction = direct_path_to(current, jogging_target)
          else:
            current = jogging_target
            direction = jogging_direction
            jogging_target = None
            jogging_direction = None

            no_cuts_for = 0
            cuts = 0
            total_cuts_for_path = 0

            # no_cuts_for = -radius
            # direction = jogging_direction
            # current = jogging_target
            # old_current = current
            # cuts = 1
            # total_cuts_for_path = 0
            # current_bound = get_point(current, 2)

          vector = P.angle(direction)

        if current == old_current:  #if jogging cause the current location to snap to the destination
          current += P.angle(direction)

        current_bound = get_point(current, 2)
        next_bound = get_point(current + P.angle(direction), 2)

        # if current_bound in [POINT.NO_GO_RADIUS]:
        #   last_on_radius = current // 1.0


        if jogging_target is None and current_bound in [POINT.NO_GO_MASK, POINT.CANT_REACH]:
          print t(tick), current, jogging_target
          print type(direction), type(last_off_direction)
          print t(tick), "In forbidden area", last_off_radius, m(current_bound), a(direction)

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

