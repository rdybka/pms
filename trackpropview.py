import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from trackpropviewpopover import TrackPropViewPopover
from sequencepropviewpopover import SequencePropViewPopover

class TrackPropView(Gtk.DrawingArea):
	def __init__(self, clear_popups, trk = None, seq = None, seqview = None, propview = None, index = -1):
		Gtk.DrawingArea.__init__(self)

		self.connect("draw", self.on_draw);
		
		self.clear_popups = clear_popups
				
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK )
		self.connect("button-press-event", self.on_click)
		self.connect("motion-notify-event", self.on_mouse_move)
		if trk:
			self.popover = TrackPropViewPopover(self, trk)
		else:
			self.popover = SequencePropViewPopover(self, seq)
			
		self.popover.set_position(Gtk.PositionType.BOTTOM)
		self.popover.set_modal(False)
		self.popover.set_transitions_enabled(False)
		
		self.seq = seq
		self.trk = trk
		self.propview = propview
		self.seqview = seqview
		self.index = index
		self.padding = 3
		self.button_rect = Gdk.Rectangle()

	def add_track(self):
		port = 0
		channel = 1
		if (len(self.seq)):
			port = self.seq[-1].port
			channel = self.seq[-1].channel

		trk = self.seq.add_track(port, channel)
		self.seqview.add_track(trk)
		self.propview.add_track(trk)

	
	def del_track(self):
		self.popover.popdown()
		self.seqview.del_track(self.trk)
		self.propview.del_track(self.trk)
	
	def move_left(self):
		self.seq.swap_track(self.trk.index, self.trk.index - 1)
		self.seqview.update_order()
		self.propview.update_order()

	def move_right(self):
		self.seq.swap_track(self.trk.index, self.trk.index + 1)
		self.seqview.reorder()
		self.propview.reorder()
				
	def on_mouse_move(self, widget, data):
		if data.x >= self.button_rect.x:
			if data.x <= self.button_rect.x + self.button_rect.width:
				if data.y >= self.button_rect.y:
					if data.y <= self.button_rect.y + self.button_rect.height:		
						self.clear_popups()
						self.popover.popup()
						return
		
		self.popover.popdown()
		
	def on_click(self, widget, data):
		pass 
		
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(0,.3,0)
		cr.rectangle(0, 0, w, h)
		cr.fill()

		cr.set_source_rgb(0, .8, 0)
		cr.select_font_face("Roboto Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL )
		cr.set_font_size(12)
				
		if self.trk == None:
			(x, y, width, height, dx, dy) = cr.text_extents("000")
		
			if w != (width + (self.padding * 2)):
				self.set_size_request(width + (self.padding * 3) + self.padding, ((height + (self.padding)) * 2) + self.padding)
			
				cr.set_source_rgb(0, .5, 0)
				cr.move_to(width + (self.padding * 2) + self.padding, self.padding)
				cr.line_to(width + (self.padding * 2) + self.padding, ((height + (self.padding)) * 2) - self.padding)
				cr.stroke()

				cr.move_to(self.padding, 2 * (height + self.padding))
				cr.show_text("***")
				
				self.button_rect.width = width
				self.button_rect.height = height + 5
				self.button_rect.x = self.padding;
				self.button_rect.y = height + self.padding
				self.popover.set_pointing_to(self.button_rect)
				return

		(x, y, width, height, dx, dy) = cr.text_extents("000 000")
		
		if w != (width + (self.padding * 2)):
			self.set_size_request(len(self.trk) * (width + (self.padding * 2)) + self.padding * 2, (height + (self.padding)) * 2 + self.padding)
		
		cr.set_source_rgb(0, 1, 0)		
		cr.set_source_rgb(0, .7, 0)
		cr.move_to(self.padding, height + self.padding)
		cr.show_text("p%02d c%02d" % (self.trk.port, self.trk.channel))

		# ## button
		(x, y, width2, height2, dx, dy) = cr.text_extents("***")
		cr.move_to(self.padding + len(self.trk) * (self.padding * 2 + width) - (width2 + self.padding), 2 * (height + self.padding))
		
		self.button_rect.width = width2
		self.button_rect.height = height2 + 5
		self.button_rect.x = self.padding + len(self.trk) * (self.padding * 2 + width) - (width2 + self.padding)
		self.button_rect.y = 2 * (height + self.padding) - self.button_rect.height
		
		cr.move_to(self.button_rect.x, self.button_rect.y + self.button_rect.height)
		cr.show_text("***")
		
		(x, y, width2, height2, dx, dy) = cr.text_extents("***")

		self.button_rect.width = width2
		self.popover.set_pointing_to(self.button_rect)
	
		cr.set_source_rgb(0, .5, 0)
		cr.move_to(len(self.trk) * (width + (self.padding * 2)) + self.padding, self.padding)
		cr.line_to(len(self.trk) * (width + (self.padding * 2)) + self.padding, ((height + (self.padding)) * 2) - self.padding)
		cr.stroke()
		