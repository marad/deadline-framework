
import sys

class Entity(object):
	pass
	
def dijkstra(graph, start, end):
	
	out = {}
	stack = []
	stack.append(start)
	for k in graph.keys():
		out[k] = sys.maxint
	out[start] = 0
	
	
	while len(stack):
		k = stack[0]
		del stack[0]
		
		nextLen = out[k] + 1
		neigh = graph[k]
		for n in neigh:
			if out[n] > nextLen:
				out[n] = nextLen
				stack.append(n)
	
	cur = end
	path = []
	while True:
		path.append(cur)
				
		dist = out[cur]
		
		if dist == 0:
			break
			
		neigh = graph[cur]
		for n in neigh:
			if out[n] < dist:
				cur = n				
	path.reverse()
	return path
	
#g = {
#	1 : [ 2, 4 ],
#	2 : [ 3, 1 ],
#	3 : [ 2 ],
#	4 : [ 1 ]
#}

#print dijkstra(g, 4, 3)

			
		
