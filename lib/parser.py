# -*- coding: utf-8 -*-

import re

innerCounter_ = 0

class ParserException(BaseException) :
	pass

#-----------------------------------------------------------------------

def cast(d):
	try: d = int(d)
	except:
		try: d = float(d)
		except: pass
	return d

def stripAll(string) :
	return string,''

def stripString(string) :
	val,sep,rest = string.partition(' ')
	return val,rest

def stripValue(fun=cast) :
	def inner(string) :
		val,sep,rest = string.partition(' ')
		return fun(val),rest
	return inner

def repeatStrip(it, custom, repeats, newlines) :
	def inner(string) :
		ret = []
		for i in range(0,repeats) :
			if newlines and i>0 : string = it.next()
			val,string = custom(string)
			ret.append(val)
		return ret,string
	return inner

#-----------------------------------------------------------------------

def indentCode(lines) :
	return ['\t'+s for s in lines]

def makeFunction(name,args,lines) :
	return ["def {}({}) :".format(name,args)] + indentCode(lines)

def stripItem(fmt) :
	item = ""
	braces = 0
	for c in fmt :
		if c=='{' : braces += 1
		elif c=='}' : braces -= 1
		if braces<0 :
			raise ParserException('unmatched closing brace')
		if c in (',','/') and not braces :
			break
		item += c

	if braces>0 :
		raise ParserException('unmatched opening brace')
	return item, fmt[len(item):]

def parseMap(fmt) :
	lines = []
	keys = []
	while fmt :
		item,fmt = stripItem(fmt)

		key,sep,typ = item.partition(':')
		if not key.isalpha() :
			raise ParserException("map key '{}' is invalid".format(key))
		keys.append(key)
		lines += parseType(key,typ)

		if fmt :
			if fmt[0]=='/' : lines.append("str_ = iter_.next()")
			fmt = fmt[1:]

	args = ",".join(map(lambda k: '"{0}":{0}'.format(k), keys))
	lines.append("return {"+args+"},str_")
	return lines

def parseType(key,typ) :
	global innerCounter_

	lines = []
	repeatNewlines = None
	if typ and (typ[-1] in (']','>')) :
		repeatNewlines = (typ[-1]=='>')
		c = '<' if repeatNewlines else '['
		i = typ.rfind(c)
		j = len(typ)-1
		repeats = typ[i+1:j]
		typ = typ[0:i]

	if not typ :
		callfunc = 'stripValue()'
	elif typ=='d' :
		callfunc = 'stripValue(int)'
	elif typ=='f' :
		callfunc = 'stripValue(float)'
	elif typ=='s' :
		callfunc = 'stripString'
	elif typ=='ss' :
		callfunc = 'stripAll'
	elif typ[0]=='{' and typ[-1]=='}' :
		innerCounter_ += 1
		callfunc = "inner{}".format(innerCounter_)
		lines += makeFunction(callfunc,"str_",parseMap(typ[1:-1]))
	else :
		raise ParserException("unrecognized data type: "+typ)

	if repeatNewlines is not None :
		callfunc = "repeatStrip(iter_,{},int({}),{})".format(callfunc, repeats, repeatNewlines)

	lines.append("{},str_ = {}(str_)".format(key,callfunc))
	return lines

def generate(fmt) :
	lines = ["str_ = iter_.next()"]
	lines += parseType('val',fmt)
	lines.append("return val")
	return "\n".join(makeFunction('parser','iter_',lines))

def build(fmt) :
	code = compile(generate(fmt), fmt, 'exec')
	symbols = {}
	eval(code, globals(), symbols)
	return symbols['parser']

#-----------------------------------------------------------------------

if __name__=='__main__' :

	import sys

	class InputReader(object) :
		def __iter__(self) :
			return self
		def next(self) :
			return sys.stdin.next().rstrip('\n')

	if len(sys.argv)==2 :
		fmt = sys.argv[1]
	else :
		print "Usage: parser format"
		sys.exit(1)

	print generate(fmt)
	F = build(fmt)
	print "waiting for input... (terminate with Ctrl+D)"
	try :
		print F(InputReader())
	except :
		print "input is too short"
