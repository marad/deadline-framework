# -*- coding: utf-8 -*-

import atexit, itertools, os, pickle, sys, threading, utils

def readData(path) :
	data = {}
	if os.path.isfile(path) :
		try :
			with open(path,"r") as theFile :
				data = pickle.load(theFile)
		except Exception as e:
			print "Error reading memory: {}".format(e)
	return data

def writeData(data,path) :
	try :
		with open(path,"w") as theFile :
			pickle.dump(data,theFile)
	except Exception as e:
		print "Error writing memory: {}".format(e)

#-----------------------------------------------------------------------

class FrameThread(threading.Thread) :

	def __init__(self, port) :
		global mem
		super(FrameThread,self).__init__()
		self.daemon = True
		self.memPath = "mem/{}.mem".format(port)
		mem = readData(self.memPath)
		self.client = utils.Client(port)
		self.modLast = None
		self.modNext = None
		self.modQueue = []
		self.running = True

	def _change(self, mod) : # for internal use only
		try :
			if hasattr(mod,'install') and callable(mod.install) :
				mod.install()
			try :
				if hasattr(self.modLast,'remove') and callable(self.modLast.remove) :
					self.modLast.remove()
			except Exception as e :
				print "Error removing previous module: {}".format(e)

			globals()['module'] = self.modLast = mod
			return mod

		except Exception as e :
			print "Error installing new module: {}".format(e)
			return self.modLast

	def _import(self, modname) : # for internal use only
		global mem
		if modname is None :
			mod = None
		else :
			mod = __import__(modname, locals={})
			del sys.modules[modname]
			if not (hasattr(mod,'work') and callable(mod.work)) :
				raise Exception("module <{}> has no function 'work'".format(modname))
			mod.mem = mem
			mod.client = self.client
		return mod

	def run(self) : # for internal use only
		global mem
		while self.running :
			time = self.client.wait(async=True)

			try :
				mod = self.modQueue.pop()
			except IndexError :
				mod = self.modNext
			if mod!=self.modLast :
				mod = self._change(mod)

			if mod :
				if hasattr(mod,'meanwhile') and callable(mod.meanwhile) :
					try : mod.meanwhile(time)
					except Exception as e :
						print "Exception at meanwhile: {}".format(e)

			self.client.expect()

			if mod :
				try : mod.work()
				except Exception as e :
					print "Exception at work: {}".format(e)

			writeData(mem, self.memPath)


	def queue(self, moduleName, repeats=1) :
		mod = self._import(moduleName)
		self.modQueue.extend(itertools.repeat(mod,repeats))

	def replace(self, moduleName) :
		mod = self._import(moduleName)
		self.modNext = mod

	def finish(self) :
		self.running = False
		self.join()
		self.client.close()

#-----------------------------------------------------------------------

mem = None
module = None
port = None
thread = None

def install(moduleName) :
	if thread :
		try :
			thread.replace(moduleName)
			print "Active module will be changed to <{}>.".format(moduleName)
		except Exception as e :
			print "Error: {}".format(e)

def once(moduleName, repeats=1) :
	if thread :
		try :
			thread.queue(moduleName, repeats)
			print "Module <{}> has been added to queue.".format(moduleName)
		except Exception as e :
			print "Error: {}".format(e)

def remove() :
	if thread:
		try :
			thread.replace(None)
			print "No module will be selected."
		except Exception as e :
			print "Error: {}".format(e)

#-----------------------------------------------------------------------

import traceback

if __name__ == '__main__' :

	sys.path.insert(0,'.')
	try :
		if len(sys.argv)<2 :
			raise Exception('port number must be given as command line parameter')

		port = int(sys.argv[1])
		if port<=0 or port>65535 :
			raise Exception("invalid port number ({})".format(port))

		thread = FrameThread(port)
		thread.start()
		atexit.register(thread.finish)
		print "Framework thread started."

		if len(sys.argv)>2 :
			install(sys.argv[2])

	except Exception as e :
		print "Error: {}".format(e)
