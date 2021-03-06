#!/usr/bin/env python

import serial
import re
import lifx
from sys import exit, stdout

def limit(low, high, value):
	return max(low, min(value, high))

class Command:
	def __init__(self, uart, callback):
		self.__urt = uart
		self.__callback = callback

	def run(self):
		while True:
			line = self.__readLine()
			#print('[%s]' % line)
			self.__process(line)

	def __process(self, line):
		match = re.search('^([\w\d]+)+=(-?\d+),?', line)
		if match:
			name = match.group(1)
			value = int(match.group(2))
			#print '%s = %d' % (name, value)
			self.__callback(name, value)
	
	def __readLine(self):
		data = b''
		while True:
			char = uart.read()
			data += char
			line = data.decode()
			if re.search(r'\r?\n$', line):
				return line.strip()


class Bulb:
	__MaxBright = 0xffff

	def __init__(self):
		self.__tab = {
			'rot0': self.__rotateLeft,
			'rot1': self.__rotateRight,
			'sw0': self.__switchLeft,
			'sw1': self.__switchRight
		}
		self.__on = True
		self.__brightStep = 0.02
		self.__bright = 0.3
		self.__kelvinMin = 2400
		self.__kelvinMax = 8000
		self.__kelvinStep = (self.__kelvinMax - self.__kelvinMin) / 60.0
		self.__kelvin = 4000
		self.set(self.__bright, self.__kelvin)

	def set(self, bright, kelvin):
		print('SET %0.2f %d K' % (bright, kelvin))
		bright = self.__corr(bright)
		bright = int(bright * self.__MaxBright)
		bright = limit(0, self.__MaxBright, bright)
		lifx.set_color(lifx.BCAST, 0, 0, bright, kelvin, 0)
		lifx.set_color(lifx.BCAST, 0, 0, bright, kelvin, 0)

	def action(self, name, value):
		#print('%s = %d' % (name, value))
		self.__tab[name](value)
	
	def __corr(self, value):
		corr = (10.0 ** value - 1.0) / 9.0
		return limit(0.0, 1.0, corr)
		
	def __rotateLeft(self, value):
		if not self.__on:
			return
		bright = self.__bright + value * self.__brightStep
		bright = limit(0.0, 1.0, bright)
		if bright != self.__bright:
			self.__bright = bright
			self.set(self.__bright, self.__kelvin)

	def __rotateRight(self, value):
		kelvin = self.__kelvin + self.__kelvinStep * value
		kelvin = int(limit(self.__kelvinMin, self.__kelvinMax, kelvin))
		if kelvin != self.__kelvin:
			self.__kelvin = kelvin
			self.set(self.__bright, kelvin)
	
	def __switchLeft(self, value):
		if value == 1:
			return
		self.__on = not self.__on
		if self.__on:
			print('ON')
			self.set(self.__bright, self.__kelvin)
		else:
			print('OFF')
			self.set(0, self.__kelvin)
	
	def __switchRight(self, value):
		pass

def action(name, value):
	print('%s = %d' % (name, value))

uart = serial.Serial('/dev/ttyAMA0', 115200)
bulb = Bulb()
command = Command(uart, bulb.action)
command.run()


