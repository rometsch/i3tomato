#!/usr/bin/env python
# Productivity timer following the pomodoro method.
import os
import datetime
import sys
from subprocess import Popen, PIPE, STDOUT

# config
focus_minutes = 25
short_break_minutes = 5
long_break_minutes = 20
number_session_in_row = 4

focus_length = datetime.timedelta(minutes=focus_minutes)
short_break_length = datetime.timedelta(minutes=short_break_minutes)
long_break_length = datetime.timedelta(minutes=long_break_minutes)

symbols = { "focus" : "∞",
			"break" : "☕",
			"paused" : "P",
			"idle" : " "} #"†"}


def prompt(session):
	choices = { 'start break/focus' : session.start,
				'pause' : session.pause,
				'stop' : session.stop }

	choices_str = "|".join([k for k in choices])

	CMD = ['rofi', '-sep', '|', '-dmenu',
		   '-p', 'Time is up! Continue with']

	p = Popen(CMD, stdout=PIPE, stdin=PIPE, stderr=PIPE)
	stdout_data = p.communicate(input=choices_str.encode('utf-8'))
	selected = stdout_data[0].decode('utf-8').strip()

	try:
		choices[selected]()
	except KeyError:
		pass


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
			if self.Nsession >= number_session_in_row:
				self.Nsession = 1
			else:
				self.Nsession += 1
			self.tstop = self.now + focus_length
		elif self.stage == "focus":
			self.stage = "break"
			self.status = "running"
			if self.Nsession >= number_session_in_row:
				self.tstop = self.now + long_break_length
			else:
				self.tstop = self.now + short_break_length
		self.write_runfile()

	def pause(self):
		if self.stage in ['focus', 'break']:
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
				self.tstop.isoformat(),
				self.remaining(force=calc_remaining) ))


	def read_runfile(self):
		try:
			with open(self.runpath, 'r') as rf:
				self.stage = rf.readline().strip()
				self.status = rf.readline().strip()
				self.Nsession = int(rf.readline().strip())
				self.tstop = datetime.datetime.strptime(rf.readline().strip(), '%Y-%m-%dT%H:%M:%S.%f')
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
			if delta.total_seconds() >= 0:
				minutes = int(delta.seconds / 60)
				seconds = int(delta.seconds%60)
			else:
				minutes = 0
				seconds = 0
			return "{:02d}:{:02d}".format(minutes, seconds)
		else:
			return delta.total_seconds()

	def report(self):
		print("stage : {}\nstatus : {}\nN : {}\ntstop : {}\nremaining : {}".format(self.stage, self.status, self.Nsession, self.tstop, self.remaining(formatted=True)))

	def logline(self):
		line = ""

	def __str__(self):
		status_str = ""
		status_str += "{}".format(symbols[self.stage])
		if self.status == "paused":
			status_str += " {}".format(symbols["paused"])
		else:
			status_str += " {}".format(self.Nsession)
		status_str += " {}".format(self.remaining(formatted=True))
		return status_str

	def prompt(self):
		prompt(self)

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
		elif cmd == 'report':
			s.report()
		elif cmd == 'print':
			print(s)
		else:
			print("Command {} not known.\nUse 'start'/'pause'/'stop'/'report'/'print'".format(cmd))

	else:
		prompt(s)
