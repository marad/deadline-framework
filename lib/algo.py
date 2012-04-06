#-*- coding: utf-8 -*-

import sys
from heapq import heappush, heappop, heapify

def dijkstra(graph, start):
	"""
	Implementacja algorytmu Dijkstry.
	Wyznacza odległość od zadanego punktu do wszystkich pozostałych

	Parametry:
		graph - graf reprezentowany jako lista sąsiedztwa w hash mapie:
			graph = {
				'A': ['B', 'C'],
				'B': ['A'],
				'C': ['A']
			}

		start - wierzchołek początkowy (np. 'A')

	Zwraca:
		Zwraca hash mapę w której każdemu wierzchołkowi przypisana jest
		jego odległość od wierzchołka startowego i wierzcholek poprzedni
		dla optymalnej sciezki.
			out = {
				'A': (0, None),
				'B': (1, 'A'),
				'C': (1, 'A')
			}
	"""

	out = {}
	removed = []
	#for vertex, neighbours in zip(graph.keys(), graph.values()):
	for vertex in graph.keys():
		out[vertex] = (sys.maxint, None)

	out[start] = (0, None)
	heap = [ [k, v] for k,v in zip (
		[ out[v][0] for v in out.keys() ],
		graph.keys()
		) ]

	heapify(heap)

	while len(heap):
		u = heappop(heap)
		dist = u[0]
		vertex = u[1]
		removed.append(vertex)

		if dist == sys.maxint:
			break # All remaining vertices are inaccessible

		for neigh in graph[vertex]:
			if neigh in removed:
				continue
			alt = out[vertex][0] + 1
			if alt < out[neigh][0]:
				out[neigh] = (alt, vertex)

				for tmp in heap:
					if tmp[1] == neigh:
						tmp[0] = alt
						break
				heapify(heap)
	return out


def dijkstra2(graph, start):
	"""
	Implementacja algorytmu Dijkstry.
	Wyznacza odległość od zadanego punktu do wszystkich pozostałych

	Parametry:
		graph - graf reprezentowany jako lista sąsiedztwa w hash mapie:
			graph = {
				'A': ['B', 'C'],
				'B': ['A'],
				'C': ['A']
			}

		start - wierzchołek początkowy (np. 'A')

	Zwraca:
		Zwraca hash mapę w której każdemu wierzchołkowi przypisana jest
		jego odległość od wierzchołka startowego i wierzcholek poprzedni
		dla optymalnej sciezki.
			out = {
				'A': (0, None),
				'B': (1, 'A'),
				'C': (1, 'A')
			}
	"""

	out = {}
	removed = []
	#for vertex, neighbours in zip(graph.keys(), graph.values()):
	for vertex in graph.keys():
		out[vertex] = (sys.maxint, None)

	out[start] = (0, None)
	#heap = [ [k, v] for k,v in zip (
	#	[ out[v][0] for v in out.keys() ],
	#	graph.keys()
	#	) ]

	#heapify(heap)
	heap = []
	heappush(heap, (0, start))

	while len(heap):
		u = heappop(heap)
		dist = u[0]
		vertex = u[1]
		removed.append(vertex)

		#if dist == sys.maxint:
		#	break # All remaining vertices are inaccessible

		for neigh in graph[vertex]:
			#if neigh in removed:
			#	continue
			alt = out[vertex][0] + 1
			if alt < out[neigh][0]:
				out[neigh] = (alt, vertex)
				heappush(heap, (alt, neigh))
				#for tmp in heap:
				#	if tmp[1] == neigh:
				#		tmp[0] = alt
				#		break
				#heapify(heap)
	return out

def find_path(dijData, end):
	ret = []
	cur = end
	while cur != None:
		ret.append(cur)
		cur = dijData[cur][1]
	ret.reverse()
	return ret

graph = {
	'A': ['B', 'C',],
	'B': ['A', 'D'],
	'C': ['A'],
	'D': ['B', 'E'],
	'E': ['D']
}

from time import time
import timeit

start = time()
out = dijkstra2(graph, 'C')
for i in xrange(1000000):
	find_path(out, 'E')
end = time()

print 'First:', (end-start)

from dijkstra import dijkstra as dij

start = time()
for i in xrange(1000000):
	dij(graph, 'C', 'E')
end = time()

print 'Second:', (end-start)


print find_path(out, 'E')
print dij(graph, 'C', 'E')
