points = None

def install() :
	client.bindParser('points','d')
	client.bindParser('last', 'd')

def work() :
	global points
	points = client.points()

	if 'last' in mem :
		d = client.last()
		if d>0 :
			x = mem['last'] + d
		else :
			x = mem['last'] + 1
	else :
		x = 1

	client.shoot(x)
	mem['last'] = x
