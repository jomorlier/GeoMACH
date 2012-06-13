from __future__ import division
from PAM.components import Component, Property, body_sections
import numpy, pylab
import mpl_toolkits.mplot3d.axes3d as p3


class Body(Component):

    def __init__(self, nx, ny, nz, full=False):
        if full:
            self.faces = numpy.zeros((6,2),int)
        else:
            self.faces = numpy.zeros((5,2),int)
        self.faces[0,:] = [-2,3]
        self.faces[1,:] = [3,1]
        self.faces[2,:] = [-2,1]
        self.faces[3,:] = [-3,1]
        self.faces[4,:] = [-2,-3]
        if full:
            self.faces[5,:] = [2,1]

        Ps = []
        Ks = []

        P, K = self.createSurfaces(Ks, ny, nz, -2, 3, 0)
        Ps.extend(P)
        Ks.append(K)
         
        P, K = self.createSurfaces(Ks, nz, nx, 3, 1, 1)
        Ps.extend(P) 
        Ks.append(K)
           
        P, K = self.createSurfaces(Ks, ny, nx, -2, 1, 1)
        Ps.extend(P)  
        Ks.append(K)  
      
        P, K = self.createSurfaces(Ks, nz[::-1], nx, -3, 1, 0)
        Ps.extend(P)   
        Ks.append(K)

        P, K = self.createSurfaces(Ks, ny, nz[::-1], -2, -3, 1)
        Ps.extend(P) 
        Ks.append(K) 

        if full:
            P, K = self.createSurfaces(Ks, ny, nx, 2, 1, 0)
            Ps.extend(P) 
            Ks.append(K)             

        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.Ps = Ps   
        self.Ks = Ks  
        self.full = full

        self.oml0 = [] 

    def setDOFs(self):
        for f in range(len(self.Ks)):
            self.setC1('surf', f)
        if not self.full:
            self.setC1('surf', 0, j=0, v=0, val=False)
            self.setC1('surf', 1, i=0, u=0, val=False)
            self.setC1('surf', 3, i=-1, u=-1, val=False)
            self.setC1('surf', 4, j=-1, v=-1, val=False)
            self.setC1('edge', 0, j=0, v=0)
            self.setC1('edge', 1, i=0, u=0)
            self.setC1('edge', 3, i=-1, u=-1)
            self.setC1('edge', 4, j=-1, v=-1)

    def isExteriorDOF(self, f, uType, vType, i, j):
        check = self.check
        value = False
        if self.full:
            value = False
        elif f==0:
            value = check(uType,vType,v=0)
        elif f==1:
            value = check(uType,vType,u=0)
        elif f==3:
            value = check(uType,vType,u=-1)
        elif f==4:
            value = check(uType,vType,v=-1)
        return value

    def initializeParameters(self):
        Ns = self.Ns
        self.offset = numpy.zeros(3)
        self.props = {
            'posx':Property(Ns[1].shape[1]),
            'posy':Property(Ns[1].shape[1]),
            'ry':Property(Ns[1].shape[1]),
            'rz':Property(Ns[1].shape[1]),
            't1U':Property(Ns[1].shape[1]),
            't2U':Property(Ns[1].shape[1]),
            't1L':Property(Ns[1].shape[1]),
            't2L':Property(Ns[1].shape[1]),
            'noseL':0.1,
            'tailL':0.05
            }
        self.setSections()

    def setSections(self, sections=[], t1U=0, t2U=1, t1L=0, t2L=1):
        Ns = self.Ns
        for j in range(Ns[2].shape[1]):
            for i in range(Ns[2].shape[0]):
                val = Ns[2][i,j,3]
                if not val == -1:
                    break
            found = False
            for k in range(len(sections)):
                found = found or (val==sections[k])
            if found or sections==[]:
                self.props['t1U'].data[j] = t1U
                self.props['t2U'].data[j] = t2U
                self.props['t1L'].data[j] = t1L
                self.props['t2L'].data[j] = t2L

    def propagateQs(self):
        wR = 0.8
        wL = 0.9
        wD = 1.1
        Ns = self.Ns
        Qs = self.Qs
        for f in range(len(Ns)):
            if f==0 or f==4:
                if f==0:
                    sect = 1
                    i1 = 1
                    i2 = 2
                    L = wL*self.props['noseL']
                else:
                    sect = -2
                    i1 = -3
                    i2 = -2
                    L = -wL*self.props['tailL']
                posx = self.props['posx'].data[sect]
                posy = self.props['posy'].data[sect]
                rz = wR*self.props['rz'].data[sect]
                ry = wR*self.props['ry'].data[sect]
                dx = self.props['posx'].data[i2] - self.props['posx'].data[i1]
                dy = self.props['ry'].data[i2] - self.props['ry'].data[i1]
                dz = self.props['rz'].data[i2] - self.props['rz'].data[i1]    
                d = wD*abs(dy/dx)
                e = wD*abs(dz/dx)
                for j in range(Ns[f].shape[1]):
                    for i in range(Ns[f].shape[0]):
                        yy = 1 - 2*i/(Ns[f].shape[0]-1)
                        if self.full:
                            zz = -1 + 2*j/(Ns[f].shape[1]-1)
                        elif f==0:
                            zz = j/(Ns[f].shape[1]-1)
                        elif f==4:
                            zz = -1 + j/(Ns[f].shape[1]-1)
                        x,y,z = body_sections.cone(L,rz,ry,d,e,yy,zz)
                        Qs[f][i,j,:] = self.offset + [posx,posy,0] + [x,y,z] 
                        Qs[f][i,j,0] -= self.props['posx'].data[1]
                        if f==4:
                            Qs[f][i,j,0] += self.props['noseL']
                            Qs[f][i,j,0] += (1-wL)*self.props['tailL']
            else:
                pi = numpy.pi
                for j in range(Ns[f].shape[1]):
                    posx = self.props['posx'].data[j]
                    posy = self.props['posy'].data[j]
                    rz = self.props['rz'].data[j]
                    ry = self.props['ry'].data[j]
                    t1U = self.props['t1U'].data[j]
                    t2U = self.props['t2U'].data[j]
                    t1L = self.props['t1L'].data[j]
                    t2L = self.props['t2L'].data[j]
                    for i in range(Ns[f].shape[0]):
                        ii = i/(Ns[f].shape[0]-1)
                        if f==1 and self.full:
                            t = 3/4.0 - ii/2.0
                        elif f==1 and not self.full:
                            t = 1/2.0 - ii/4.0
                        elif f==2:
                            t = 1/4.0 - ii/2.0
                        elif f==3 and self.full:
                            t = 7/4.0 - ii/2.0
                        elif f==3 and not self.full:
                            t = 7/4.0 - ii/4.0
                        elif f==5:
                            t = 5/4.0 - ii/2.0
                        if t < 0:
                            t += 2
                        if t <= 1:
                            z,y = body_sections.rounded(rz, ry, t, t1U, t2U)
                        else:
                            z,y = body_sections.rounded(rz, ry, t, t1L, t2L)
                        Qs[f][i,j,:] = self.offset + [posx,posy,0] + [0,y,z]
                        Qs[f][i,j,0] += self.props['noseL'] - self.props['posx'].data[1]
