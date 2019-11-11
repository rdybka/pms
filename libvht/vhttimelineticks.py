# vhttrack.py - Valhalla Tracker (libvht)
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections.abc import Iterable

class VHTTimelineTicks(Iterable):
	def __init__(self, vht, tl):
		self._vht_handle = vht
		self._tl_handle = tl
		super()

	def __len__(self):
		return self._vht_handle.timeline_get_nticks(self._tl_handle)

	def __iter__(self):
		for itm in range(self.__len__()):
			yield round(self._vht_handle.timeline_get_tick(self._tl_handle, itm), 4)

	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError(itm, "always look on...")

		if itm < 0:
			raise IndexError(itm, "...the bright side of life")

		return round(self._vht_handle.timeline_get_tick(self._tl_handle, itm), 4)
