# -*- coding: utf-8 -*-

import socket, new, parser

LOGIN		 = 'morti'
PASSWORD = 'haslo'
HOST		 = 'localhost' #'universum.dl24'

class DeadlineError(Exception):

	def __init__(self, err=0, msg="unknown error"):
		self.err = err
		self.msg = msg

	def __str__(self):
		return "DeadlineError({}): {}".format(self.err, self.msg)

	def __repr__(self):
		return self.__str__()

#-----------------------------------------------------------------------

class Socket(object):

	def __init__(self, sock):
		self.socket = sock;
		self.socket.setsockopt(
			socket.SOL_TCP,
			socket.TCP_NODELAY, 1)

	def readLine(self):
		line = ''
		while True:
			c = self.socket.recv(1)
			if not c:
				raise socket.error('connection closed')
			elif c=='\n':
				return line
			else:
				line += c

	def readArray(self):
		return map(parser.cast, self.readLine().split())

	def readValue(self):
		return parser.cast(self.readLine().strip())

	def writeLine(self, *args):
		self.socket.sendall(" ".join(map(str,args))+"\n")

	def __iter__(self):
		return self

	def next(self):
		try:
			return self.readLine()
		except:
			raise StopIteration()

	def close(self):
		self.socket.shutdown(socket.SHUT_RDWR)
		self.socket.close()

#-----------------------------------------------------------------------

class Client(Socket):

	def __init__ (self, port, doLogin=True):
		super(Client,self).__init__(
			socket.socket(
				socket.AF_INET,
				socket.SOCK_STREAM))
		self.socket.connect( (HOST, port) )
		self.parsers = {}
		self.port = port
		if doLogin:
			self.login()

	def expect(self, what="OK"):
		line = self.readLine()
		key,sep,params = line.partition(' ');

		if key != what:
			if key == "FAILED":
				raise DeadlineError(*params.split(" ", 1))
			raise DeadlineError(0, 'expected "{}", read "{}"'.format(what, key));

		return params.split()

	def command(self, *args):
		self.writeLine(*args)
		self.expect()

	def login(self):
		self.expect("LOGIN")
		self.writeLine(LOGIN)
		self.expect("PASS")
		self.writeLine(PASSWORD)
		self.expect()

	def wait(self,async=False):
		self.command("WAIT")
		ret = self.expect("WAITING")
		if not async: self.expect()
		try:
			return float(ret[0])
		except:
			return 0.0

	def bindParser(self, name, what=""):
		name = name.upper()
		if what is None:
			if name in self.parsers:
				del self.parsers[name]
		else:
			if callable(what):
				fun = what
			else:
				fun = parser.build(str(what))
			self.parsers[name] = new.instancemethod(fun, self, Client)

	def __getattr__(self,name):
		name = name.upper()
		def inner(*args):
			self.command(name,*args)
			result = None
			if name in self.parsers:
				result = self.parsers[name]()
			return result
		return inner
