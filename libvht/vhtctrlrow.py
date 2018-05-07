
class VHTCtrlRow():
	def __init__(self, vht, crowptr):
		self._vht_handle = vht
		self._crowptr = crowptr

		self._velocity = vht.ctrlrow_get_velocity(self._crowptr)		
		self._linked = vht.ctrlrow_get_linked(self._crowptr)
		self._smooth = vht.ctrlrow_get_smooth(self._crowptr)
		self.update_strrep()
		
	def __eq__(self, other):
		if self._velocity != other._velocity:
			return False
		if self._linked != other._linked:
			return False
			
		return True

	def update_strrep(self):
		lnk = " "
		if self._linked == 1:
			lnk = "L"

		if self._velocity > -1:
			self._strrep = "%3d %s %d" % (self._velocity, lnk, self._smooth) 
		else:
			self._strrep = "--- - -" + lnk
	
	def copy(self, row):
		self._velocity = row._velocity
		self._linked = row._linked
		self._smooth = row._smooth
		self._vht_handle.ctrlrow_set(self._crowptr, self._velocity, self._linked, self._smooth)
		self.update_strrep()
		
	def clear(self):
		self._velocity = -1
		self.linked = 0
		self.smooth = 0
		self._vht_handle.ctrlrow_set(self._crowptr, -1, 0, 0)
		self.update_strrep()
						
	@property
	def velocity(self):
		return self._velocity
	
	@velocity.setter
	def velocity(self, value):
		self._velocity = int(value)
		self._vht_handle.ctrlrow_set_velocity(self._crowptr, self._velocity)

	@property
	def linked(self):
		return self._velocity
	
	@linked.setter
	def linked(self, value):
		self._linked = int(value)
		self._vht_handle.ctrlrow_set_linked(self._crowptr, self._linked)

	@property
	def smooth(self):
		return self._smooth
	
	@smooth.setter
	def smooth(self, value):
		self._smooth = int(value)
		self._vht_handle.ctrlrow_set_smooth(self._crowptr, self._smooth)

	def __str__(self):
		return self._strrep

