from __future__ import absolute_import
import sdl
from planner import point
from planner.point import P

class Display(object):
  def __init__(self):
    d = self.d = P(1000, 1000)
    self.data = point.make_mmapped_data(d, f=open('mmap', 'rb+'))

    sdl.init(sdl.INIT_EVERYTHING)
    sdl.ttf.init()
    sdl.setHint("render_scale_quality", "linear")

    self.window = sdl.createWindow("Test", sdl.WINDOWPOS_UNDEFINED, sdl.WINDOWPOS_UNDEFINED, d.x, d.y, sdl.WINDOW_RESIZABLE)

    self.render = self.window.createRenderer(-1, sdl.RENDERER_TARGETTEXTURE | sdl.RENDERER_SOFTWARE)

    self.frame_texture = self.render.createTexture(sdl.PIXELFORMAT_ARGB8888, sdl.TEXTUREACCESS_TARGET, d.x, d.y)
    # self.overlay_texture = self.render.createTexture(sdl.PIXELFORMAT_ARGB8888, sdl.TEXTUREACCESS_TARGET, d.x, d.y)

    self.animation_texture = self.render.createTexture(sdl.PIXELFORMAT_RGB888, sdl.TEXTUREACCESS_STATIC, d.x, d.y)
    self.animation_texture.setTextureBlendMode(sdl.BLENDMODE_ADD)

    self.render.setRenderTarget(sdl.ffi.NULL)

  def loop(self):
    d = self.d
    self.render.setRenderTarget(self.frame_texture)
    # self.render.renderSetLogicalSize(d.x, d.y)
    self.render.renderClear()

    self.animation_texture.setTextureBlendMode(sdl.BLENDMODE_ADD)
    self.animation_texture.updateTexture(sdl.ffi.NULL, self.data[0], d.x*4)
    self.render.renderCopy(self.animation_texture, None, None)

    self.animation_texture.setTextureBlendMode(sdl.BLENDMODE_ADD)
    self.animation_texture.updateTexture(sdl.ffi.NULL, self.data[2], d.x*4)
    self.render.renderCopy(self.animation_texture, None, None)

    self.animation_texture.setTextureBlendMode(sdl.BLENDMODE_ADD)
    self.animation_texture.updateTexture(sdl.ffi.NULL, self.data[1], d.x*4)
    self.render.renderCopy(self.animation_texture, None, None)


    self.render.renderPresent()

    self.render.setRenderTarget(sdl.ffi.NULL)

    self.render.renderCopy(self.frame_texture, None, None)
    self.render.renderPresent()

if __name__ == "__main__":
  d = Display()
  import time
  while True:
    d.loop()
    time.sleep(1/60.)
