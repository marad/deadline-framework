# -*- coding: utf-8 -*-

import re

class MyTestWorker(object):
	namePattern = re.compile('^(.*)-[^-]*$')

	def name(self):
		return u"Moduł testowy"

	def install(self):
		print "Installing", self.name()

	def remove(self):
		print "Removing", self.name()

	def work(self):
		self.client.shoot(2, 5)
		#print "Working", threading.current_thread().name

worker = MyTestWorker()
