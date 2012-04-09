# -*- coding: utf-8 -*-

import itertools, math, random
from pygraph.classes.graph import graph as Graph

def distanceTaxicab(va,vb) :
	return sum([abs(d[0]-d[1]) for d in zip(e[0],e[1])])

def distanceEuclid(va,vb) :
	return math.sqrt(sum([(d[0]-d[1])**2 for d in zip(va,vb)]))

#-----------------------------------------------------------------------

class GridGraph(object) :

	def __init__(self,metric) :
		self._metric = metric
		self._nodes = []

	def add_node(self,node) :
		self._nodes.append(node)

	def add_nodes(self,nodes) :
		self._nodes.extend(nodes)

	def nodes(self) :
		return self._nodes

	def edge_weight(self,e) :
		return self._metric(e[0],e[1])

#-----------------------------------------------------------------------

def exact(graph) :
	N = len(graph.nodes())
	db = None
	tour = {}
	for p in itertools.permutations(graph.nodes()) :
		d = sum([graph.edge_weight((p[i-1],p[i])) for i in range(1,N)]) + graph.edge_weight((p[N-1],p[0]))
		if db is None or d<db :
			db = d
			tour = dict(zip(p[0:N-1],p[1:N]))
			tour[p[N-1]] = p[0]
	return db,tour

def nearest(graph) :
	dSum = 0
	tour = {}
	start = random.choice(graph.nodes())
	va = start
	tovisit = set(graph.nodes())
	tovisit.remove(va)
	while True :
		vb = None
		db = None
		for v in tovisit :
			d = graph.edge_weight( (va,v) )
			if db is None or d<db :
				vb = v
				db = d
		if vb is None : break
		tovisit.remove(vb)
		tour[va] = vb
		dSum += db
		va = vb
	if va != start :
		tour[va] = start
		dSum += graph.edge_weight( (va,start) )
	return dSum,tour


if __name__=='__main__' :

	gr = GridGraph(distanceEuclid)
	gr.add_node( (0,0) )
	gr.add_node( (2,0) )
	gr.add_node( (2,2) )
	gr.add_node( (3,3) )
	gr.add_node( (1,2) )

	dist,tour = nearest(gr)
	print "NN route: {}".format(dist)
	print tour

	dist,tour = exact(gr)
	print "Exact route: {}".format(dist)
	print tour
