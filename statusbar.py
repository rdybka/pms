import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from pypms import pms
from trackview import TrackView
class StatusBar(Gtk.DrawingArea):
	def __init__(self):
		super(StatusBar, self).__init__()
		
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.LEAVE_NOTIFY_MASK |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK)
		
		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)		
		self.connect("motion-notify-event", self.on_motion)
		self.connect("scroll-event", self.on_scroll)
		self.connect("leave-notify-event", self.on_leave)
		self.connect("button-press-event", self.on_button_press)
		self.connect("button-release-event", self.on_button_release)		
				
		self._surface = None
		self._context = None
		self.min_char_width = 60
		
		self.pos = []
		self.active_field = None
		self.add_tick_callback(self.tick)

	def redraw(self):
		cr = self._context
		w = self.get_allocated_width()
		h = self.get_allocated_height()
		
		(x, y, width, height, dx, dy) = cr.text_extents("PMS" * self.min_char_width)

		self.set_size_request(1, height * 1.5)

		gradient = cairo.LinearGradient(0, 0, 0, h)
		gradient.add_color_stop_rgb(0.0, *(col *  pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
		gradient.add_color_stop_rgb(1.0, *(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.set_source(gradient)
		
		cr.rectangle(0, 0, w, h)
		cr.fill()

		trk = pms.active_track
				
		t = 0
		r = 0
		c = 0
		cs = pms.curr_seq
		
		self.pos = []
		
		self.pos.append(0)
		xx = 0
		
		if trk:
			t = trk.trk.index
			if trk.edit:
				c = trk.edit[0]
				r = trk.edit[1]


		txt = "%02d:%02d:%02d:%03d" % (cs, t, c, r)
		h = height * 1.2

		cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 1:
			cr.set_source_rgb(*(col * 1.0 for col in pms.cfg.colour))
		else:
			cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))
		
		txt = " oct:%d" % pms.cfg.octave
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)	
		xx += dx
		self.pos.append(xx)


		if self.active_field == 2:
			cr.set_source_rgb(*(col * 1.0 for col in pms.cfg.colour))
		else:
			cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))
				
		txt = " vel:%d" % pms.cfg.velocity
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)	
		xx += dx
		self.pos.append(xx)
				

		if self.active_field == 3:
			cr.set_source_rgb(*(col * 1.0 for col in pms.cfg.colour))
		else:
			cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))
						
		txt = " skp:%d" % pms.cfg.skip
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)	
		xx += dx
		self.pos.append(xx)
				
				
		if self.active_field == 4:
			cr.set_source_rgb(*(col * 1.0 for col in pms.cfg.colour))
		else:
			cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))
						
		txt = " hig:%d" % pms.cfg.highlight
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)	
		xx += dx
		self.pos.append(xx)
				
		if self.active_field == 5:
			cr.set_source_rgb(*(col * 1.0 for col in pms.cfg.colour))
		else:
			cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))
		
		txt = " bpm:%d" % pms.bpm
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)	
		xx += dx
		self.pos.append(xx)
		
		cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))		
		txt = "%02d:%03d.%03d ***" % (cs, int(pms[cs].pos), (pms[cs].pos - int(pms[cs].pos)) * 1000)
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(w - dx, h)
		cr.show_text(txt)			
		
		cr.move_to(0, 0)
		cr.line_to(w, 0)
		cr.stroke()

		self.queue_draw()

	def tick(self, wdg, param):
		self.redraw()
		return 1	

	def on_configure(self, wdg, event):
		if self._surface:
			self._surface.finish()

		w = wdg.get_allocated_width()
		h = wdg.get_allocated_width()
		
		self._surface = wdg.get_window().create_similar_surface(cairo.CONTENT_COLOR, w, h)

		self._context = cairo.Context(self._surface)
		self._context.set_antialias(cairo.ANTIALIAS_NONE)
		self._context.set_line_width((pms.cfg.seq_font_size / 6.0) * pms.cfg.seq_line_width)

		self._context.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)	
		
		fs = pms.cfg.seq_font_size	
		fits = False
		while not fits:
			self._context.set_font_size(fs)
			(x, y, width, height, dx, dy) = self._context.text_extents("X" * self.min_char_width)
			if w > width:
				fits = True
			else:
				fs -= 1

		self.redraw()
		return True

	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def on_motion(self, widget, event):
		self.active_field = None
		
		xx = 0
		af = -1
		for pos in self.pos:
			if event.x > xx and event.x < pos:
				self.active_field = af
				
			xx = pos
			af += 1

	def on_scroll(self, widget, event):
		if not self.active_field:
			return True
		
		up = event.direction ==  Gdk.ScrollDirection.UP
		down = event.direction ==  Gdk.ScrollDirection.DOWN
				
		if self.active_field == 1:
			if up:
				pms.cfg.octave	= min(pms.cfg.octave + 1, 8)
			if down:
				pms.cfg.octave	= max(pms.cfg.octave - 1, 0)

		if self.active_field == 2:
			if up:
				pms.cfg.velocity = min(pms.cfg.velocity + 1, 127)
			if down:
				pms.cfg.velocity = max(pms.cfg.velocity - 1, 0)
		
		if self.active_field == 3:
			if up:
				pms.cfg.skip = min(pms.cfg.skip + 1, 16)
			if down:
				pms.cfg.skip = max(pms.cfg.skip - 1, -16)
		
		if self.active_field == 4:
			if up:
				pms.cfg.highlight = min(pms.cfg.highlight + 1, 32)
			if down:
				pms.cfg.highlight = max(pms.cfg.highlight - 1, 1)
		
		if self.active_field == 5:
			if up:
				pms.bpm = min(pms.bpm + 1, 400)
			if down:
				pms.bpm = max(pms.bpm - 1, 30)
		
		return True		
		
	def on_leave(self, wdg, prm):
		self.active_field = None

	def on_button_press(self, widget, event):
		pass
		
	def on_button_release(self, widget, event):
		up = down = False
		
		if event.button == 1:
			down = True
		
		if event.button == 3:
			up = True
		
		if self.active_field == 1:
			if up:
				pms.cfg.octave	= min(pms.cfg.octave + 1, 8)
			if down:
				pms.cfg.octave	= max(pms.cfg.octave - 1, 0)

		if self.active_field == 2:
			if up:
				pms.cfg.velocity = min(pms.cfg.velocity + 1, 127)
			if down:
				pms.cfg.velocity = max(pms.cfg.velocity - 1, 0)
		
		if self.active_field == 3:
			if up:
				pms.cfg.skip = min(pms.cfg.skip + 1, 16)
			if down:
				pms.cfg.skip = max(pms.cfg.skip - 1, -16)
		
		if self.active_field == 4:
			if up:
				pms.cfg.highlight = min(pms.cfg.highlight + 1, 32)
			if down:
				pms.cfg.highlight = max(pms.cfg.highlight - 1, 1)
		
		if self.active_field == 5:
			if up:
				pms.bpm = min(pms.bpm + 1, 400)
			if down:
				pms.bpm = max(pms.bpm - 1, 30)
		