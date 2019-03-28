import networkx as nx
from gurobipy import *
import matplotlib.pyplot as plt
import sys
import math
#import gv
from graphviz import *
import numpy as np
import time


global aux_nom



def fobjetivo(G,y):
	suma=0
	for v in G.nodes():
		if v!=0:
			suma=suma+y[v]
	return suma	

def flujo(G,x,v):
	suma1=0
	suma2=0
	for nv in G.neighbors(v):
		suma1=suma1+x[nv,v]
		suma2=suma2+x[v,nv]
	return suma1-suma2
	
def entrada(G,x,v):
	suma=0
	for nv in G.neighbors(v):
		suma=suma+x[nv,v]		
	return suma


def salida(G,x,v):
	suma=0
	for nv in G.neighbors(v):
		suma=suma+x[v,nv]		
	return suma
	
	
def capacidad(G,x,y):
	sumad=0
	sumav=0
	for e in G.edges(data=True):
		sumad=sumad+e[2]["d"]*x[e[0],e[1]]
		sumad=sumad+e[2]["d"]*x[e[1],e[0]]
	for v in G.nodes(data=True):
		sumav=sumav+(v[1]["p"]*y[v[0]])
	return sumad+sumav

def capacidad2(G,tinicio,tfinal,y):
	sumad=0
	sumav=0
	for e in G.edges(data=True):
		sumad=sumad+(e[2]["d"]*x[e[0],e[1]])
		sumad=sumad+(e[2]["d"]*x[e[1],e[0]])
	
	for v in G.nodes():
		sumav=sumav+(tfinal[v]-tinicio[v])
	
	return sumav+sumad	
	
def dibujar(G,x,y):
	G1=Digraph("preventa",filename=aux_nom,engine='neato')
	G1.attr('node', shape='circle')
	G1.attr('edge', len='3.5')
	G1.attr('edge', minlen='3.5')
	G1.node('0',shape='square',label='Deposito')
	G1.node('1',shape='square',label='Descanso',color="red")
	for v in G.nodes(data=True):
		if v[0]>1:
			if abs(y[v[0]].getAttr("x")) > 0.1 and abs(y[v[0]].getAttr("x")) <= 1.0:
				G1.node(str(v[0]),label=str(v[0])+"\\n" +str(v[1]["p"]))
			else:
				G1.node(str(v[0]),style='invis',label="")
	
	#for e in G.edges():
	#	G1.edge(str(e[0]),str(e[1]),style='invis',color='gray',arrowhead='none')
	for e in G.edges(data=True):
		if abs(x[e[0],e[1]].getAttr("x"))>=0.1 and abs(x[e[0],e[1]].getAttr("x"))<=1.0:
			G1.edge(str(e[0]),str(e[1]),color='blue',label=str(e[2]["d"]))
		if abs(x[e[1],e[0]].getAttr("x"))>=0.1 and abs(x[e[1],e[0]].getAttr("x"))<=1.0:
			G1.edge(str(e[1]),str(e[0]),color='blue',label=str(e[2]["d"]))
	G1.render(aux_nom)							
fh=open(sys.argv[1],'rb')
G=nx.read_edgelist(fh,delimiter=" ",nodetype=int,data=(('d',float),))
fh2=open(sys.argv[2],'rb')


for line in fh2: 
	words=line.split()
	aux = [int(n) for n in words]
	G.nodes[aux[0]]["p"]=aux[1]
	
nombre=sys.argv[1]
aux_nom=nombre.replace('.txt','_salida')
m = Model('preventa')
m.setParam("OutputFlag",1)
m.setParam("TimeLimit",1800)
#m.setParam("PreQLinearize",1)
 

x={}

for e in G.edges():
	x[e[0],e[1]]=m.addVar(vtype=GRB.BINARY, name="x_"+str(e[0])+"_"+str(e[1]))
	x[e[1],e[0]]=m.addVar(vtype=GRB.BINARY, name="x_"+str(e[1])+"_"+str(e[0]))
	
y={}
u={}
tinicio={}
tfinal={}
for v in G.nodes():
	y[v]=m.addVar(vtype=GRB.BINARY,name="y_"+str(v))
	u[v]=m.addVar(vtype=GRB.BINARY,name="u_"+str(v))
	tinicio[v]=m.addVar(vtype=GRB.CONTINUOUS,name="tinicio_"+str(v))
	tfinal[v]=m.addVar(vtype=GRB.CONTINUOUS,name="tfinal_"+str(v))

m.addConstr(y[1]==1)
m.addConstr(y[0]==1)
m.addConstr(tinicio[0]==0)
m.addConstr(tfinal[0]==0)
m.addConstr(tinicio[1]<=300)
m.addConstr(tinicio[1]>=240)
m.addConstr(capacidad(G,x,y)<=int(sys.argv[3])*60)	
#r=m.addVar(vtype=GRB.CONTINUOUS,name="r")
#q=m.addVar(vtype=GRB.CONTINUOUS,name="q")		
m.update()
m.setObjective(fobjetivo(G,y), GRB.MAXIMIZE)
#m.addConstr(30-t[4]+p-q==0)
#m.addConstr(30-t[4]<=r)
#m.addConstr(30-t[4]>=-r)	
for v in G.nodes():
	m.addConstr(entrada(G,x,v)==y[v])
	m.addConstr(salida(G,x,v)==y[v])
		


		
#m.addConstr(entrada(G,x,0)==1)
#m.addConstr(salida(G,x,0)==1)		

for e in G.edges():
	m.addConstr(x[e[0],e[1]]+x[e[1],e[0]] <= 1 )
	if e[0]!=0 and e[1]!=0:
		m.addConstr(u[e[0]]-u[e[1]] + G.number_of_nodes()*x[e[0],e[1]] <= G.number_of_nodes()-1 )
		
for i in G.nodes(data=True):
	if i[0]!=0:
		#m.addConstr(tfinal[i[0]]<=int(sys.argv[3])*60*y[i[0]])
		m.addConstr(tinicio[i[0]]<=int(sys.argv[3])*60*y[i[0]])
		m.addConstr(tfinal[i[0]]==tinicio[i[0]]+(i[1]["p"]*y[i[0]]))#-10000* (1-y[i[0]]))
	for j in G.nodes(data=True):
		if i[0]!=j[0] and i[0]!=0:
			try:
				m.addConstr(tinicio[i[0]]>=tfinal[j[0]]+G.edges[j[0],i[0]]["d"]*x[j[0],i[0]]-100000* (1-x[j[0],i[0]]))
				#m.addConstr(tinicio[i[0]]>=(t[j[0]])+(j[1]["p"])*x[j[0],i[0]]+G.edges[j[0],i[0]]["d"]*x[j[0],i[0]]-10000* (1-x[j[0],i[0]]))
				#m.addConstr(t[i[0]]*x[j[0],i[0]]>=t[j[0]]*x[j[0],i[0]])
				#m.addConstr(t[i[0]]<=G.edges[i[0],j[0]]["d"]*x[i[0],j[0]]+j[1]["p"]*y[j[0]])
			except KeyError:
				m.addConstr(tinicio[i[0]]>=tfinal[j[0]]+G.edges[i[0],j[0]]["d"]*x[j[0],i[0]]-100000* (1-x[j[0],i[0]]))
				#m.addConstr(t[i[0]]>=(t[j[0]])+(j[1]["p"])*x[j[0],i[0]]+G.edges[i[0],j[0]]["d"]*x[j[0],i[0]]-10000* (1-x[j[0],i[0]]))
				#m.addConstr(t[i[0]]*x[j[0],i[0]]>=t[j[0]]*x[j[0],i[0]])
				#m.addConstr(t[i[0]]<=G.edges[j[0],i[0]]["d"]*x[i[0],j[0]]+j[1]["p"]*y[j[0]])	
					

#m.addConstr(tfinal[1]==tinicio[1]+G.nodes[1]["p"])
#m.addConstr(x[2,4] == 1)
#m.addConstr(x[4,3] == 1)
m.update()		
m.write('model.lp')
m.optimize()
suma_arcos=0
for e in G.edges(data=True):
	if abs(x[e[0],e[1]].getAttr("x"))>0.1 and abs(x[e[0],e[1]].getAttr("x"))<=1.0:
		suma_arcos=suma_arcos+e[2]["d"]
	elif abs(x[e[1],e[0]].getAttr("x"))>0.1 and abs(x[e[1],e[0]].getAttr("x"))<=1.0:
		suma_arcos=suma_arcos+e[2]["d"]
suma_nodos=0
for v in G.nodes(data=True):
	if abs(y[v[0]].getAttr("x"))>0.1 and abs(y[v[0]].getAttr("x"))<=1.0:
		suma_nodos=suma_nodos+v[1]["p"]

print(suma_arcos,suma_nodos,suma_arcos+suma_nodos)		
for v in G.nodes():
	print(v,abs(y[v].getAttr("x")),abs(tinicio[v].getAttr("x")),abs(tfinal[v].getAttr("x")))

dibujar(G,x,y)
#print "r",abs(r.getAttr("x"))						
