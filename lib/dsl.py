from utils import *
import types

class StdinClient():
	def readLine(self):
	    return raw_input()

def array(client, *sep, **kwsep):
	return map(cast, client.readLine().split(*sep))

def value(client, *sep, **kwsep):
	return cast(client.readLine().strip())
def c_value(client):
    return Conv(client, value)
def c_array(client):
    return Conv(client, array)
def c_void(client):
    return Conv(client)

class Conv():
    def __init__(self, client=None, *functions):
        self.functions = functions
        self.client = client
    def __call__(self, client=None, *args, **kwargs):
        if client is None: client = self.client
        result = []
        vars = {}
        if len(self.functions) == 1:
            return self.functions[0](client, **vars)
        for f in self.functions:
            if type(f) is types.TupleType:
                vars[f[0]]=result[-1][f[1]]
            elif type(f) is types.StringType:
                vars[f]=result[-1]
            else:
                result.append(f(client, **vars))
        return result
    def to(self, f):
        return Compose(f,self)

class Times():
    def __init__(self, number, function):
        self.number = number
        self.function = function
    def __call__(self, client, *args, **kwargs):
        try:
            times = int(self.number)
        except:
            times = int(kwargs[self.number])
        return [self.function(client, *args, **kwargs) for i in range(0,times)]

class Compose()
    def __init__(self, f1, f2):
        self.f1 = f1
        self.f2 = f2
    def __call__(self, client, *args, **kwargs):
        return  f1(f2(client,*args, **kwargs))
Compose(lambda l:{'x':l[0],'y':l[1]}, array)
