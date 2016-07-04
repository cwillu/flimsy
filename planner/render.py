from __future__ import absolute_import
import sdl
from planner import point
from planner.point import P
import os
import sys
import blessings

terminal = blessings.Terminal()

class Display(object):
  def __init__(self):
    self.frame = 0
    self.surface = point.Surface()
    d = self.d = self.surface.d
    self.data = self.surface.data

    self.keys_down = set()
    self.cursor = P(0, 0)
    self.cursor_move = P(0, 0)
    self.cursor_surface = 2
    self.show_material = True
    self.show_bounds = True
    self.show_paths = True
    self.show_jogs = True
    self.show_headings = True
    self.show_scans = True
    self.show_path_meets_bound = True
    self.show_path_leaves_bound = True

    sdl.init(sdl.INIT_EVERYTHING)
    sdl.ttf.init()
    sdl.setHint("render_scale_quality", "linear")

    self.window = sdl.createWindow("Test", sdl.WINDOWPOS_UNDEFINED, sdl.WINDOWPOS_UNDEFINED, d.x, d.y, sdl.WINDOW_RESIZABLE)

    self.render = self.window.createRenderer(-1, sdl.RENDERER_ACCELERATED)
    # self.render = self.window.createRenderer(-1, sdl.RENDERER_TARGETTEXTURE)

    # self.frame_texture = self.render.createTexture(sdl.PIXELFORMAT_ARGB8888, sdl.TEXTUREACCESS_TARGET, d.x, d.y)
    # self.overlay_texture = self.render.createTexture(sdl.PIXELFORMAT_ARGB8888, sdl.TEXTUREACCESS_TARGET, d.x, d.y)

    self.animation_textures = []
    for frame in range(9):
      texture = self.render.createTexture(sdl.PIXELFORMAT_ARGB8888, sdl.TEXTUREACCESS_STATIC, d.x, d.y)
      self.animation_textures.append(texture)

    self.animation_textures[0].setTextureBlendMode(sdl.BLENDMODE_NONE)
    self.animation_textures[1].setTextureBlendMode(sdl.BLENDMODE_BLEND)
    self.animation_textures[2].setTextureBlendMode(sdl.BLENDMODE_BLEND)
    self.animation_textures[3].setTextureBlendMode(sdl.BLENDMODE_BLEND)
    self.animation_textures[4].setTextureBlendMode(sdl.BLENDMODE_BLEND)
    self.animation_textures[5].setTextureBlendMode(sdl.BLENDMODE_BLEND)
    self.animation_textures[6].setTextureBlendMode(sdl.BLENDMODE_BLEND)
    self.animation_textures[7].setTextureBlendMode(sdl.BLENDMODE_BLEND)
    self.animation_textures[8].setTextureBlendMode(sdl.BLENDMODE_BLEND)

    self.render.setRenderTarget(sdl.ffi.NULL)

    self._io_event = sdl.Event()

    self.event_map = {
      sdl.KEYDOWN: (self.io_keydown, lambda e: e.key),
      sdl.KEYUP: (self.io_keyup, lambda e: e.key),
      sdl.MOUSEMOTION: (self.io_mousemotion, lambda e: e.motion),
      sdl.MOUSEBUTTONDOWN: (self.io_mousedown, lambda e: e.button),
      sdl.MOUSEBUTTONUP: (self.io_mouseup, lambda e: e.button),
      sdl.MOUSEWHEEL: (self.io_mousewheel, lambda e: e.wheel),
      sdl.QUIT: (self.io_quit, lambda e: e.quit),
      sdl.SYSWMEVENT: (self.io_syswm, lambda e: e.syswm),
      sdl.WINDOWEVENT: (self.io_window, lambda e: e.window),
    }

  def loop(self):
    self.frame += 1
    self.check_events()

    self.cursor += self.cursor_move

    sys.stdout.write('\r')
    sys.stdout.write(terminal.el)
    sys.stdout.write('{0.cursor.x:4}x{0.cursor.y:<4}@{0.cursor_surface}:{1:08x}  '.format(self, self.surface.get_point(self.cursor, self.cursor_surface)))
    sys.stdout.write(" ".join("{0}:{1:1}".format(k.replace('show_', '').replace('_bound', '').replace('_', ''), "*" if v else " ") for k, v in vars(self).items()[::-1] if k.startswith('show_')))
    sys.stdout.flush()
    sys.stdout.write('\r' + terminal.el)

    self.render_frame()

  def check_events(self):
    while sdl.pollEvent(self._io_event):
      callback, event_property = self.event_map.get(self._io_event.type, (None, None))
      if not callback:
        continue
      callback(event_property(self._io_event))

  def io_keydown(self, event):
    if event.repeat:
      return
    keycode = event.keysym.sym
    keyname = sdl.getKeyName(event.keysym.sym).lower()
    core = keyname.split()[-1]

    name = '_'.join(list(sorted(self.keys_down))+[core])
    callback = getattr(self, 'io_key_' + name, None)
    if not event.repeat:
      self.keys_down.add(core)
    if callback is not None:
      callback()
      if not event.repeat:
        self.keys_down.remove(core)
    # else:
    #   if not event.repeat:
    #     print repr(keyname), name

  def io_keyup(self, event):
    keycode = event.keysym.sym
    keyname = sdl.getKeyName(event.keysym.sym).lower()
    core = keyname.split()[-1]

    self.keys_down.discard(core)

    name = '_'.join(list(sorted(self.keys_down))+[core])
    callback = getattr(self, 'io_keyrelease_' + name, None)
    if callback is not None:
      callback()

  def io_mousemotion(self, event):
    pass
  def io_mousedown(self, event):
    if event.button == sdl.BUTTON_LEFT:
      self.cursor = P(event.x, event.y)
  def io_mouseup(self, event):
    pass
  def io_mousewheel(self, event):
    timestamp = event.timestamp
    window = event.windowID
    mouse = event.which
    x = event.x
    y = event.y
  def io_syswm(self, event):
    print "syswm"
  def io_window(self, event):
    self.size = self.window.getWindowSize()

  def io_quit(self, event):
    os._exit(0)

  def io_key_ctrl_c(self):
    os._exit(0)
  def io_key_ctrl_w(self):
    os._exit(0)

  def io_key_up(self):
    self.cursor_move += P(0, -1)
  def io_key_down(self):
    self.cursor_move += P(0, 1)
  def io_key_left(self):
    self.cursor_move += P(-1, 0)
  def io_key_right(self):
    self.cursor_move += P(1, 0)
  def io_keyrelease_up(self):
    self.cursor_move -= P(0, -1)
  def io_keyrelease_down(self):
    self.cursor_move -= P(0, 1)
  def io_keyrelease_left(self):
    self.cursor_move -= P(-1, 0)
  def io_keyrelease_right(self):
    self.cursor_move -= P(1, 0)

  def io_key_space(self):
    print self.cursor,
    for x in range(8):
      print '{:08x}'.format(self.surface.get_point(self.cursor, x)),
    print

  def io_key_tab(self):
    self.cursor_surface += 1
    self.cursor_surface %= 8
  def io_key_shift_tab(self):
    self.cursor_surface -= 1
    self.cursor_surface %= 8
  def io_key_1(self):
    self.show_material ^= True
  def io_key_t(self):
    self.show_material ^= True
  def io_key_2(self):
    self.show_bounds ^= True
  def io_key_b(self):
    self.show_bounds ^= True
  def io_key_3(self):
    self.show_paths ^= True
  def io_key_p(self):
    self.show_paths ^= True
  def io_key_4(self):
    self.show_jogs ^= True
  def io_key_j(self):
    self.show_jogs ^= True
  def io_key_5(self):
    self.show_headings ^= True
  def io_key_h(self):
    self.show_headings ^= True
  def io_key_6(self):
    self.show_scans ^= True
  def io_key_s(self):
    self.show_scans ^= True
  def io_key_7(self):
    self.show_path_meets_bound ^= True
  def io_key_m(self):
    self.show_path_meets_bound ^= True
  def io_key_8(self):
    self.show_path_leaves_bound ^= True
  def io_key_l(self):
    self.show_path_leaves_bound ^= True

  def render_frame(self):
    d = self.d
    # self.render.setRenderTarget(self.frame_texture)
    # self.render.renderSetLogicalSize(d.x, d.y)

    self.render.renderClear()

    if self.show_material:
      self.animation_textures[0].updateTexture(sdl.ffi.NULL, self.data[0], d.x*4)
      self.render.renderCopy(self.animation_textures[0], None, None)

    if self.show_bounds:
      self.animation_textures[1].updateTexture(sdl.ffi.NULL, self.data[2], d.x*4)
      self.render.renderCopy(self.animation_textures[1], None, None)

    if self.show_paths:
      self.animation_textures[2].updateTexture(sdl.ffi.NULL, self.data[1], d.x*4)
      self.render.renderCopy(self.animation_textures[2], None, None)

    if self.show_jogs:
      self.animation_textures[7].updateTexture(sdl.ffi.NULL, self.data[7], d.x*4)
      self.render.renderCopy(self.animation_textures[7], None, None)

    if self.show_scans:
      self.animation_textures[3].updateTexture(sdl.ffi.NULL, self.data[3], d.x*4)
      self.render.renderCopy(self.animation_textures[3], None, None)

    if self.show_path_meets_bound:
      self.animation_textures[4].updateTexture(sdl.ffi.NULL, self.data[4], d.x*4)
      self.render.renderCopy(self.animation_textures[4], None, None)

    if self.show_path_leaves_bound:
      self.animation_textures[5].updateTexture(sdl.ffi.NULL, self.data[5], d.x*4)
      self.render.renderCopy(self.animation_textures[5], None, None)

    if self.show_headings:
      self.animation_textures[6].updateTexture(sdl.ffi.NULL, self.data[6], d.x*4)
      self.render.renderCopy(self.animation_textures[6], None, None)

    self.render.renderPresent()

    # self.render.setRenderTarget(sdl.ffi.NULL)

    # self.render.renderCopy(self.frame_texture, None, None)
    # self.render.renderPresent()

if __name__ == "__main__":
  d = Display()
  import time
  import thread
  # def loop(x, data, texture):
  #   while True:
  #     texture.updateTexture(sdl.ffi.NULL, data, x)
  #     time.sleep(1/60.)
  # print d.d.x*4
  # thread.start_new_thread(loop, (d.d.x*4, d.data[0], d.animation_textures[0]))
  # thread.start_new_thread(loop, (d.d.x*4, d.data[2], d.animation_textures[1]))
  # thread.start_new_thread(loop, (d.d.x*4, d.data[1], d.animation_textures[2]))

  while True:
    d.loop()
    time.sleep(1/60.)
