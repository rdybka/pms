import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo
from trackview import TrackView
from tracksideview import TrackSideView

class SequenceView(Gtk.ScrolledWindow):
	def __init__(self, pms):
		Gtk.ScrolledWindow.__init__(self)
		self.connect("draw", self.on_draw);
		
		self.pms = pms
		self.seq = pms[0];

		self._track_box = Gtk.Box()
		self._track_box.add(TrackSideView(self.seq))
		for trk in self.seq:
			self._track_box.add(TrackView(trk))
		
		self._track_box.set_spacing(0)
		
		self.add_with_viewport(self._track_box)
		
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(0,.3,0)
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		super()
