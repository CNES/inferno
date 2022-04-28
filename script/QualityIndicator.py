import glob
from collections import namedtuple
import numpy as np
from numpy import (cos,sin,arccos,tan)
import dataclasses
import os
from pathlib import Path
import datetime 
from typing import Callable, List

acos = arccos
BIPM_LIGHT_SPEED = 3e8


def parseXML(xmlFilePath):
    import xml.etree.ElementTree as ET
    tree = ET.parse(xmlFilePath)
    root = tree.getroot()
    return root

def _CartesianToGeodetic():
    from pyproj import Transformer,Proj
    lla = Proj(proj='longlat', ellps='WGS84', datum='WGS84')
    ecef = Proj(proj='geocent', ellps='WGS84', datum='WGS84')
    transformer = Transformer.from_proj(ecef,lla)
    return transformer.transform

def _longlat2cart():
    from pyproj import Transformer,Proj
    lla = Proj(proj='longlat', ellps='WGS84', datum='WGS84')
    ecef = Proj(proj='cart', ellps='WGS84', datum='WGS84')
    transformer = Transformer.from_proj(lla,ecef)
    return transformer.transform

_longlat2cart = _longlat2cart()
_CartesianToGeodetic = _CartesianToGeodetic()

longlat2cart = lambda x,y,z : Point3D(*_longlat2cart(x,y,z))
# cartesianToGeodetic = lambda x,y,z : Point3D(*_CartesianToGeodetic(x,y,z))[[1,0,2]]
cartesianToGeodetic = lambda x,y,z : Point3D(*_CartesianToGeodetic(x,y,z))

class Point3D(np.ndarray):
    def __new__(cls,*args, **kwargs):
        zeros = np.zeros(3)
        obj = np.asarray(zeros).view(cls)
        return obj

    def __init__(self,x=0,y=0,z=0) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.z = z

    @property
    def x(self):
        """I'm the 'x' property."""
        return self[0]

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self):
        """I'm the 'x' property."""
        return self[1]

    @y.setter
    def y(self, value):
        self[1] = value

    @property
    def z(self):
        """I'm the 'x' property."""
        return self[2]

    @z.setter
    def z(self, value):
        self[2] = value

@dataclasses.dataclass
class GeolocationGrid():
    time : datetime.datetime
    pixel : Point3D
    position : Point3D
        
    @classmethod
    def fromXml(cls,xmlElement):
        time = datetime.datetime.fromisoformat(xmlElement.find("azimuthTime").text)
        position = Point3D(
            x = xmlElement.find("longitude").text,
            y = xmlElement.find("latitude").text,
            z = xmlElement.find("height").text,
        )
        pixel = Point3D(
            x = xmlElement.find("line").text,
            y = xmlElement.find("pixel").text,
            z = 0
        )

        position = longlat2cart(*position)
        # print(position)
        return cls(time=time,position=position, pixel=pixel)
    
@dataclasses.dataclass
class Orbit():
    time:datetime.datetime
    position : Point3D
    vitesse : Point3D

    @classmethod
    def fromXml(cls,xmlElement):
        time = datetime.datetime.fromisoformat(xmlElement.find("time").text)
        position = Point3D(
            x = xmlElement.find("position/x").text,
            y = xmlElement.find("position/y").text,
            z = xmlElement.find("position/z").text,
        )
        vitesse = Point3D(
            x = xmlElement.find("velocity/x").text,
            y = xmlElement.find("velocity/y").text,
            z = xmlElement.find("velocity/z").text,
        )        
        return Orbit(time=time,position=position,vitesse=vitesse)

    @staticmethod
    def orbitPoly(orbits:List):
        # import numpy.polyfit         
        t0 = orbits[0].time
        t = [(orbit.time - orbits[0].time).total_seconds() for orbit in orbits]
       
        X = [ orbit.position.x for orbit in orbits]
        Y = [ orbit.position.y for orbit in orbits]
        Z = [ orbit.position.z for orbit in orbits]

        VX = [ orbit.vitesse.x for orbit in orbits]
        VY = [ orbit.vitesse.y for orbit in orbits]
        VZ = [ orbit.vitesse.z for orbit in orbits]
        deg = len(t)-1
        
        Px = np.polyfit(t, X, deg = deg )
        Py = np.polyfit(t, Y, deg = deg )
        Pz = np.polyfit(t, Z, deg = deg )
        Vx = np.polyfit(t, VX, deg = deg )
        Vy = np.polyfit(t, VY, deg = deg )
        Vz = np.polyfit(t, VZ, deg = deg )
        
        # poly = lambda t : (
        #     np.poly1d(Px)( (t-t0).total_seconds() ),
        #     np.poly1d(Py)( (t-t0).total_seconds() ),
        #     np.poly1d(Pz)( (t-t0).total_seconds() )
        # )
        return t0,Px,Py,Pz,Vx,Vy,Vz,

@dataclasses.dataclass
class ImagesS1():
    TifPath : str
    AnnotationPath : str = None
    waveLength : float = None
    bandwidth : float = None
    geolocationGrids : List[GeolocationGrid] = None
    orbit : Callable = None


    def __post_init__(self):
        self.AnnotationPath = self.getAnnotationPathFromImagePath(self.TifPath)
        xmlFile = parseXML(self.AnnotationPath)
        self.waveLength = self._readWaveLength(xmlFile)
        self.bandwidth = self._readBandwidth(xmlFile)
        self.geolocationGrids = self._readGeolocationGrids(xmlFile)
        orbits = self._readOrbits(xmlFile)
        self.orbitsInfo = orbits
        t0,Px,Py,Pz,Vx,Vy,Vz = Orbit.orbitPoly(orbits=orbits)
        self.Px = Px
        self.Py = Py
        self.Pz = Pz
        self.Vx = Vx
        self.Vy = Vy
        self.Vz = Vz
        self.orbitPoly = [
            np.poly1d(Px),
            np.poly1d(Py),
            np.poly1d(Pz),
        ]
        self.vitessePoly = [
            np.poly1d(Vx),
            np.poly1d(Vy),
            np.poly1d(Vz),
        ]
        self.orbit = lambda t : (
            np.poly1d(Px)( (t-t0).total_seconds() ),
            np.poly1d(Py)( (t-t0).total_seconds() ),
            np.poly1d(Pz)( (t-t0).total_seconds() )
        )
        self.vitesse = lambda t : (
            np.poly1d(Vx)( (t-t0).total_seconds() ),
            np.poly1d(Vy)( (t-t0).total_seconds() ),
            np.poly1d(Vz)( (t-t0).total_seconds() )
        )
    @staticmethod
    def getAnnotationPathFromImagePath(filePath: str):
        parent = Path(filePath).parents[1]
        output = Path(os.path.join(parent,"annotation",os.path.basename(filePath)))
        output.with_suffix('.xml')
        return output.with_suffix('.xml')

    @staticmethod
    def _readWaveLength(xmlFile):
        freq = float(xmlFile.find(".//productInformation/radarFrequency").text)
        waveLength = BIPM_LIGHT_SPEED/freq
        return waveLength

    @staticmethod
    def _readBandwidth(xmlFile):
        bandwidth = xmlFile.find(".//rangeDecimation/decimationFilterBandwidth").text
        # bandwidth = xmlFile.find(".//rangeDecimation/processingBandwidth").text
        return float(bandwidth)     

    @staticmethod
    def _readGeolocationGrids(xmlFile,date=None):
        Positions = xmlFile.findall("./geolocationGrid/geolocationGridPointList/geolocationGridPoint")
        Positions = [GeolocationGrid.fromXml(position) for position in Positions]
        return Positions

    @staticmethod
    def _readOrbits(xmlFile):
        orbits = xmlFile.findall("./generalAnnotation/orbitList/orbit")
        orbits = [Orbit.fromXml(orbit) for orbit in orbits]
        return orbits

def unitary(u):
    return u/np.sqrt(np.dot(u,u))

def norme(u):
    return np.sqrt(np.sum(np.array(u)**2))


@dataclasses.dataclass
class Info():
    Pground : Point3D
    incidence : float = 0.0 
    distance : float  = 0.0 
    baseline : float  = 0.0 
    orthobase : float = 0.0 
    parabase : float  = 0.0 
    ambiguity_height : float  = 0.0 
    spectral_shift : float= 0.0 
    bandwidth : float = 0.0 
    critical_baseline : float = 0.0 
    recovery_rate : float = 0.0
    
    slope : float = 0.0 

    @staticmethod
    def compute(master,slave,Pground,waveLength,bandwidth):
        output = Info(Pground)
        output._compute(master,slave,Pground,waveLength,bandwidth)
        return output

    def _compute(self,master,slave,Pground,waveLength,bandwidth,slope=0):

        self.distance = norme(Pground - master) 
        self.baseline = norme(slave - master)

        u = unitary(Pground - master)
        v = slave - master
        x = np.dot(u,v)

        self.parabase = abs(x)
        self.orthobase = norme(v-x*u)

        v = cartesianToGeodetic(*Pground); 
        
        v[0:2] = v[0:2]*np.pi/180
        x = cos(v.y) 
        v.z = sin(v.y) 
        v.y = sin(v.x)*x 
        v.x = cos(v.x)*x 


        self.incidence = acos( -np.dot(v,u) )
        x = waveLength * self.distance 

        self.ambiguity_height = 0
        if (self.orthobase > 0.0):
            self.ambiguity_height = (x*sin(self.incidence)*0.5)/self.orthobase  

        y = x * tan(self.incidence-slope) / BIPM_LIGHT_SPEED 

        self.spectral_shift = 0
        if (y != 0.0): 
            self.spectral_shift = -self.orthobase/y 

        self.slope = slope 
        self.bandwidth  = bandwidth 
        self.critical_baseline = norme(y*bandwidth) 
        self.recovery_rate = 1- abs(self.spectral_shift)/self.bandwidth



@dataclasses.dataclass
class InterferometricCouple():
    master : ImagesS1
    slave : ImagesS1
    info : List = None
        
    def findDoppler0(self,master:ImagesS1,Pground):
        def computeF0(orbit,Pground):
            v = orbit.vitesse
            d = orbit.position - Pground
            return np.dot(v,d)

        def _computeF0(master, t,Pground):
            return (Point3D(*master.orbit(t)) - Pground)  @ Point3D( *master.vitesse(t) )

        def findT(master:ImagesS1,Pground):
            orbits = master.orbitsInfo
            orbits = sorted(orbits,key=lambda x:x.time)
            for o1,o2 in (zip(orbits[:],orbits[1:])):
                F01 = computeF0(o1,Pground)
                F02 = computeF0(o2,Pground)
                if F01*F02<0:
                    return o1.time, o2.time, F01, F02
        
        def findZero(imageS1:ImagesS1,t0,t1,Pground):
            td = (t1-t0)/2
            t2 = t0+td
            f0 = _computeF0(imageS1,t0,Pground)
            f1 = _computeF0(imageS1,t1,Pground)
            f2 = _computeF0(imageS1,t2,Pground)
            
            if td< datetime.timedelta(seconds=0.00001):
                return t2
            elif f0*f2>0:
                return findZero(imageS1,t2,t1,Pground)
            elif f1*f2>0:
                return findZero(imageS1,t0,t2,Pground)

        
        t = findT(master,Pground)
        if t is None:
            return 
        t0,t1, f1,f2 = t
        t00 = 0
        t10 = (t1-t0).total_seconds()
        a = (f1 - f2)/(t00-t10)
        b = f2 - t10*a
        t =  datetime.timedelta(seconds=-b/a)
        t0 = findZero(master,t0,t1,Pground)
        return t0
                
    def computeInfos(self):
        master_geolocationGrids = self.master.geolocationGrids.copy()
        slave_geolocationGrids = self.slave.geolocationGrids.copy()
        i = 0
        infos = []
        for Pground in master_geolocationGrids:

            ts = self.findDoppler0(self.slave,Pground.position)
            tm = self.findDoppler0(self.master,Pground.position)

            slavePos = Point3D(*self.slave.orbit(ts))
            masterPos = Point3D(*self.master.orbit(tm))

            rs = norme(slavePos-Pground.position)
            rm = norme(slavePos-Pground.position)

            waveLength = self.master.waveLength
            bandwidth = self.master.bandwidth
            res = Info.compute(
                master = masterPos,
                slave = slavePos,
                Pground = Pground.position,
                waveLength = waveLength,
                bandwidth = bandwidth
            )
            infos.append(res)
            i += 1
            self.info = infos
        return infos              

    def asdict(self):
        info_mean = Info(**{
            key.name:np.mean([getattr(info,key.name) for info in  self.info],axis=0) for key in dataclasses.fields(Info)
        })

        info_std = Info(**{
            key.name:np.std([getattr(info,key.name) for info in  self.info],axis=0) for key in dataclasses.fields(Info)
        })

        mean = {
            "masterImage"       : self.master.TifPath,
            "slaveImage"        : self.slave.TifPath,
        }
        mean.update(dataclasses.asdict(info_mean))
        return mean,dataclasses.asdict(info_std)

    @classmethod
    def computeMean(cls,masterPath, slavePath):
        masterImage = ImagesS1(masterPath)
        slaveImage = ImagesS1(slavePath)
        couple = InterferometricCouple(
            master=masterImage,
            slave=slaveImage)
        couple.computeInfos()
        mean,std = couple.asdict()
        return mean,std

if __name__=="__main__":
   
    masterPath = "/home/mp/migelada/scratch/working/PALMA_P3/S1Products/S1A_IW_SLC__1SDV_20210902T191349_20210902T191419_039507_04AB1F_A0E1.SAFE/measurement/s1a-iw1-slc-vv-20210902t191349-20210902t191417-039507-04ab1f-004.tiff"
    slavePath  = "/home/mp/migelada/scratch/working/PALMA_P3/S1Products/S1A_IW_SLC__1SDV_20210914T191350_20210914T191420_039682_04B134_7407.SAFE/measurement/s1a-iw1-slc-vv-20210914t191350-20210914t191418-039682-04b134-004.tiff"

    masterImage = ImagesS1(masterPath)
    slaveImage = ImagesS1(slavePath)
    couple = InterferometricCouple(masterImage,slaveImage)
    couple.computeInfos()
    
