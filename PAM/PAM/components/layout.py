from __future__ import division
import numpy, pylab, time
import PAM.PAMlib as PAMlib


class Layout(object):

    def __init__(self, Lx, Ly, edges):
        self.Lx = Lx
        self.Ly = Ly
        self.importEdges(edges)
        self.computeIntersections()
        self.addConnectors()
        self.computeIntersections()
        self.splitPolygons()
        self.extractSurfaces()

    def importEdges(self, edges):
        self.edges = PAMlib.getedges(edges.shape[0], edges)
        self.verts = PAMlib.getverts(numpy.max(self.edges[:,:2]), edges.shape[0], edges, self.edges)
        self.nedge = self.edges.shape[0]
        self.nvert = self.verts.shape[0]

    def computeIntersections(self):
        nint = PAMlib.numintersections(self.nvert, self.nedge, self.verts, self.edges)
        self.verts = PAMlib.addintersections(self.nvert + nint, self.nvert, self.nedge, self.verts, self.edges)
        self.nvert = self.verts.shape[0]

        ndup = PAMlib.countduplicateverts(self.nvert, self.verts)
        self.verts, self.edges = PAMlib.deleteduplicateverts(self.nvert - ndup, self.nvert, self.nedge, self.verts, self.edges)
        self.nvert = self.verts.shape[0]
        self.nedge = self.edges.shape[0]

        nsplit = PAMlib.countedgesplits(self.nvert, self.nedge, self.verts, self.edges)
        self.edges = PAMlib.splitedges(self.nedge + nsplit, self.nvert, self.nedge, self.verts, self.edges)
        self.nedge = self.edges.shape[0]

        ndup = PAMlib.countduplicateedges(self.nedge, self.edges)
        self.edges = PAMlib.deleteduplicateedges(self.nedge - ndup, self.nedge, self.edges)
        self.nedge = self.edges.shape[0]

    def addConnectors(self):
        ncon, quadrants = PAMlib.countconnectors(self.nvert, self.nedge, self.Lx, self.Ly, self.verts, self.edges)
        self.verts, self.edges = PAMlib.addconnectors(self.nvert + ncon, self.nedge + ncon, self.nvert, self.nedge, self.verts, self.edges, quadrants)
        self.nvert = self.verts.shape[0]
        self.nedge = self.edges.shape[0]

    def computePolygons(self):
        self.npent, self.nquad, self.ntri = PAMlib.countpolygons(self.nvert, self.nedge, self.Lx, self.Ly, self.verts, self.edges)
        npoly = 5*self.npent + 4*self.nquad + 3*self.ntri
        poly_vert, poly_edge = PAMlib.computepolygons(npoly, self.nvert, self.nedge, self.Lx, self.Ly, self.verts, self.edges)
        self.npoly = self.npent + self.nquad + self.ntri 
        self.poly_vert, self.poly_edge = PAMlib.deleteduplicatepolygons(self.npoly, npoly, poly_vert, poly_edge)

    def splitPolygons(self):
        self.computePolygons()
        self.edges = PAMlib.splitpentagons(self.nedge + self.npent, self.nvert, self.nedge, self.npoly, self.Lx, self.Ly, self.verts, self.edges, self.poly_vert)
        self.nedge = self.edges.shape[0]
        self.computePolygons()
        self.edge_group = PAMlib.computegroups(self.nedge, self.npoly, self.poly_edge)
        self.ngroup = max(self.edge_group)
        group_split = PAMlib.computetrisplits(self.nedge, self.ngroup, self.npoly, self.edge_group, self.poly_edge)
        nsplit = PAMlib.countquadsplits(self.nedge, self.ngroup, self.npoly, self.poly_edge, self.edge_group, group_split)
        self.verts, self.edges = PAMlib.addpolysplits(self.nvert + 4*self.ntri + 2*nsplit, self.nedge + 3*self.ntri + nsplit, self.nvert, self.nedge, self.ngroup, self.npoly, self.verts, self.edges, self.edge_group, self.poly_vert, self.poly_edge, group_split)
        self.nvert = self.verts.shape[0]
        self.nedge = self.edges.shape[0]
        self.computeIntersections()
        self.computePolygons()

    def extractSurfaces(self):
        self.P = []
        for p in range(self.npoly):
            self.P.append(PAMlib.extractsurface(p+1, 10, self.nvert, self.npoly, self.verts, self.poly_vert))

    def extractFlattened(self, JQ):
        n = 6
        if len(JQ)==0:
            return PAMlib.extractflattened(n, 1, (self.npoly-len(JQ))*n**2, self.nvert, self.npoly, [-1], self.verts, self.poly_vert)            
        else:
            return PAMlib.extractflattened(n, len(JQ), (self.npoly-len(JQ))*n**2, self.nvert, self.npoly, JQ, self.verts, self.poly_vert)

    def getQuadIndices(self, JQ):
        if len(JQ)==0:
            return PAMlib.getquadindices(1, self.npoly, [-1])
        else:
            return PAMlib.getquadindices(len(JQ), self.npoly, JQ)

    def plot(self):
        print '# verts:', self.nvert
        print '# edges:', self.nedge
        print '# quads:', self.nquad
        v = self.verts
        for e in range(self.edges.shape[0]):
            v0,v1 = self.edges[e,:2]
            v0 -= 1
            v1 -= 1
            if self.edges[e,2]==0:
                line = 'k:'
            else:
                line = 'k'
            pylab.plot([v[v0,0],v[v1,0]],[v[v0,1],v[v1,1]],line)
        pylab.plot(self.verts[:,0],self.verts[:,1],'ok')
        pylab.show()

    def plot2(self):
        for k in range(len(self.P)):
            P = self.P[k]
            for i in range(P.shape[0]):
                pylab.plot(P[i,:,0],P[i,:,1],'k')
            for j in range(P.shape[1]):
                pylab.plot(P[:,j,0],P[:,j,1],'k')
        pylab.show()


if __name__ == '__main__':
        
    l = Layout()
    #l.addMembers('Spars2', 1, 2, SP1=[0.1,0.1], EP1=[0.8,0.2], SP2=[0.3,0.4], EP2=[0.9,0.9])
    l.addMembers('Spars', 1, 5, SP1=[0.1,0.1], EP1=[0.8,0.2], SP2=[0.1,0.9], EP2=[1,1])
    l.addMembers('Ribs', 1, 5, SP1=[0.1,0.1], EP1=[0,1], SP2=[1,0], EP2=[1,1])
    #l.addMembers('Ribs', 1, 5, SP1=[0.1,0], EP1=[0,1], SP2=[1,0], EP2=[1,1])
    #l.addMembers('Spars', 1, 5, SP1=[0,0], EP1=[1,0], SP2=[0,1], EP2=[1,1])
    l.build()
    l.plot()
    
