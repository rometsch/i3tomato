#!/usr/bin/env python
# Productivity timer following the pomodoro method.
import os
import datetime
import sys

# config
focus_minutes = 25
short_break_minutes = 5
long_break_minutes = 20
number_session_in_row = 4

focus_length = datetime.timedelta(minutes=focus_minutes)
short_break_length = datetime.timedelta(minutes=short_break_minutes)
long_break_length = datetime.timedelta(minutes=long_break_minutes)

class Session:

	def __init__(self):
		self.now = datetime.datetime.now()
		self.runpath = os.path.join('/run/user', '{}'.format(os.getuid()), 'tomatotimer')
		self.read_runfile()

	def start(self):
		if self.status == "paused":
			self.status = "running"
			self.tstop = self.now + datetime.timedelta(seconds=self.remaining_seconds)
		elif self.stage in ["break", "idle"]:
			self.stage = "focus"
			self.status = "running"
			self.Nsession += 1
			self.tstop = self.now + focus_length
		elif self.stage == "focus":
			self.stage = "break"
			self.status = "running"
			if self.Nsession >= number_session_in_row:
				self.tstop = self.now + long_break_length
				self.Nsession = 0
			else:
				self.tstop = self.now + short_break_length
		self.write_runfile()

	def pause(self):
		if self.status == "paused":
			self.start()
		elif self.stage in ['focus', 'break']:
			self.status = "paused"
			self.write_runfile(calc_remaining=True)

	def stop(self):
		self.stage = "idle"
		self.status = "running"
		self.Nsession = 0
		self.tstop = self.now
		self.write_runfile()

	def write_runfile(self, calc_remaining=False):
		with open(self.runpath, 'w') as rf:
			rf.write("{}\n{}\n{}\n{}\n{}".format(
				self.stage,
				self.status,
				self.Nsession,
				self.tstop.isoformat(sep=' '),
				self.remaining(force=calc_remaining) ))


	def read_runfile(self):
		try:
			with open(self.runpath, 'r') as rf:
				self.stage = rf.readline().strip()
				self.status = rf.readline().strip()
				self.Nsession = int(rf.readline().strip())
				self.tstop = datetime.datetime.strptime(rf.readline().strip(), '%Y-%m-%d %H:%M:%S.%f')
				self.remaining_seconds = float(rf.readline().strip())
		except FileNotFoundError:
			self.stage = "idle"
			self.status = "running"
			self.Nsession = 0
			self.tstop = self.now

	def remaining(self, formatted=False, force=False):
		if force or self.status == 'running':
			delta = self.tstop - self.now
		else:
			delta = datetime.timedelta(seconds=self.remaining_seconds)
		if formatted:
			minutes = int(delta.seconds / 60)
			seconds = int(delta.seconds%60)
			return "{:02d}:{:02d}".format(minutes, seconds)
		else:
			return delta.total_seconds()

	def __str__(self):
		return "stage : {}\nstatus : {}\nN : {}\ntstop : {}\nremaining : {}".format(self.stage, self.status, self.Nsession, self.tstop, self.remaining(formatted=True))


if __name__ == "__main__":
	args = sys.argv

	s = Session()
	if len(args) == 2:
		cmd = args[1]
		if cmd == 'start':
			s.start()
		elif cmd == 'pause':
			s.pause()
		elif cmd == 'stop':
			s.stop()
		elif cmd == 'print':
			print(s)
		else:
			print("Command {} not known. Use 'start'/'pause'/'stop'/'print'")

	else:
		print(s)
