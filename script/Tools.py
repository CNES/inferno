import os
import sys
import numpy as np
from script import S1Product
from script import CONSTANT 
from typing import Dict, List


def writeToJson(dictionary:Dict,outputFilePath):
    import json 
    # Serializing json  
    with open(outputFilePath, "w") as outfile:
        json.dump(dictionary, outfile, indent=4)

def createAllDirToFile(filePath):
        filePath = os.path.dirname(filePath)
        
        if not os.path.isdir(filePath):
            os.makedirs(filePath,exist_ok=True)

def create_dir(dirname):
        if not os.path.isdir(dirname):
            os.makedirs(dirname,exist_ok=True)

def getBurstCount(filePath:str):
    """ 
    filePath : image path
    """
    xmlFilePath = getAnnotationPathFromImagePath(filePath)
    count = _getBurstCount(xmlFilePath)
    return count

def getAnnotationPathFromImagePath(filePath:str):
    from pathlib import Path

    parent = Path(filePath).parents[1]
    output = Path(os.path.join(parent,"annotation",os.path.basename(filePath)))
    output.with_suffix('.xml')
    return output.with_suffix('.xml')

def _getBurstCount(xmlFilePath:str) -> int:
    import xmltodict
    with open(xmlFilePath) as fd:
        doc:dict = xmltodict.parse(fd.read())

    return int(doc["product"]["swathTiming"]["burstList"]["@count"])


def getGeomFromTif(filename:str):
    """ 
    read Sentienel1 images (.tiff) header 
    return geom (4 corner georef coordinate [i,j,lon,lat])
    """
    from osgeo import gdal,gdalconst
    order  = [[0,0],[0,-1],[-1,-1],[-1,0] ] 
    ds  :gdal.Dataset   =  gdal.Open(filename,gdalconst.GA_ReadOnly)
    gcps:List[gdal.GCP] = ds.GetGCPs()
    gcps_array = np.array(
            [
                [gcp.GCPLine, gcp.GCPPixel,gcp.GCPX,gcp.GCPY,gcp.GCPZ] for gcp in gcps
            ]
        )
    nb_line  = len( np.unique( gcps_array[:,0] ) )
    nb_pixel = len( np.unique( gcps_array[:,1] ) )
    N = len(gcps)
    gcps_array = gcps_array.reshape(nb_line,nb_pixel,5)
    geom = np.array([ gcps_array[i,j,2:-1] for i,j in order  ])
    ds = None
    return geom

def pointInBurst(geom:np.ndarray,point,burstCount:int,orbitType:CONSTANT.ORBIT_TYPE=CONSTANT.ORBIT_TYPE.ASC)->np.ndarray:
    # le segment [AB] forme une longeur du cadre de l'image
    B = geom[-1]
    A = geom[0]
    C = point
    nbBurst = (burstCount)* (C-A).dot(B-A)/ (B-A).dot(B-A)
    # nbBurst = np.floor(nbBurst)
    # return (nbBurst).astype(np.int8)
    return nbBurst

def pointInsidePoly(geom,point)->bool:
    edge = np.roll(geom,-1,axis=0)-geom
    vect = point-geom
    areaPoly = abs(np.cross(edge[::2],edge[1::2])).sum()/2
    a4 = (abs(np.cross(edge,vect))/2).sum()
    return np.isclose(a4,areaPoly)

def roiInGeom(geom,ROI)->bool:
    for point in ROI:
        if not pointInsidePoly(geom,point):
            return False
    return True
        
def pointsToSwathNo(geom,point,nbSwaths,orbitType:CONSTANT.ORBIT_TYPE)-> int:
    """ 
    geom : [[lon,lat],...] S1Produit.geom 
    point: [lon,lat]
    """
    geom_ = np.zeros( (len(geom),4) )
    geom_[:  ,2:] = geom 
    geom_[:-1,:2] = geom[1:]-geom[0:-1]
    geom_[ -1,:2] = geom[0]-geom[-1]
    point  = np.array(point)

    geom_ = np.array(
        sorted(geom_.tolist(), key=lambda x : (x[0] / np.sqrt( ( x[0]**2 + x[1]**2 ))) )
    )
    scope = ( np.sum(geom_[-1,:2]**2) )
    d1 = geom_[-1,:2].dot(point- geom_[-1,2:]) / ( np.sum(geom_[-1,:2]**2) )
    d2 = (-geom_[0,:2]).dot(point-geom_[-1,2:]) / ( np.sum(geom_[0,:2]**2) )
    d = (d1+d2)/2
    swath_float = nbSwaths*d
    # scope = (geom.max(axis=0)-geom.min(axis=0))[0]
    # d = (point[0]-geom[:,0].min(axis=0))

    # swath_float = nbSwaths*d/scope
    # if ( swath_float-int(swath_float) ) > 0.9:
    #     swath_float += 1
    # elif ( swath_float-int(swath_float) ) < 0.1:
    #     swath_float -= 1  
        
    swath_float = int(np.floor(np.round(swath_float,decimals=1)))
    if orbitType == CONSTANT.ORBIT_TYPE.ASC:
        return int(swath_float)
    if orbitType == CONSTANT.ORBIT_TYPE.DES:
        return int(nbSwaths - swath_float)-1
        

def roiToSwath(geom,ROI,swaths:str,orbitType:CONSTANT.ORBIT_TYPE)->np.ndarray:
    """ 
    return list with all swath contain ROI
    """
    nbSwaths = len(swaths.split(" "))
    b = []
    for point in ROI:
        b.append(pointsToSwathNo(geom,point,nbSwaths,orbitType))
    return np.unique(b)

def getSwathName(roiToSwath,product:S1Product.S1Product):
    noSwath = roiToSwath[0]
    listSwath = [swathId.strip() for swathId in product.swath.split(" ") ]
    swathName = listSwath[noSwath]
    return swathName

def filenameFromPath(filePath):
    return os.path.basename(filePath)





# utils function to define geometry
def image_envelope(in_tif, out_shp):
    """
        This method returns a shapefile of an image
    """
    import otbApplication as otb

    app = otb.Registry.CreateApplication("ImageEnvelope")
    app.SetParameterString("in", in_tif)
    app.SetParameterString("out", out_shp)
    app.ExecuteAndWriteOutput()
    return out_shp

def get_master_geometry(in_shp):
    """
        This method returns the geometry, of an input georeferenced
        shapefile
    """
    try:
        import ogr
    except ImportError:
        import osgeo.ogr as ogr


    driver = ogr.GetDriverByName("ESRI Shapefile")
    mstr_ds = driver.Open(in_shp, 0)
    mstr_layer = mstr_ds.GetLayer()
    for master in mstr_layer:
        master.GetGeometryRef().Clone()
        return master.GetGeometryRef().Clone()

def check_srtm_coverage(in_shp_geo, srtm):
    """
        This method checks and returns the SRTM tiles intersected
    """
    try:
        import ogr
    except ImportError:
        import osgeo.ogr as ogr

    driver = ogr.GetDriverByName("ESRI Shapefile")
    srtm_ds = driver.Open(srtm, 0)
    srtm_layer = srtm_ds.GetLayer()
    needed_srtm_tiles = {}
    srtm_tiles = []
    for srtm_tile in srtm_layer:
        srtm_footprint = srtm_tile.GetGeometryRef()
        intersection = in_shp_geo.Intersection(srtm_footprint)
        if intersection.GetArea() > 0:
            # coverage = intersection.GetArea()/area
            srtm_tiles.append(srtm_tile.GetField('FILE'))  # ,coverage))
    needed_srtm_tiles = srtm_tiles
    return needed_srtm_tiles

def build_virutal_raster(master_image, srtm_shapefile, hgts_path,output_dir):
    """
        Build a vrt file corresponding to a dem from hgt (SRTM) files.
        The hgt file are contained into a global path : hgts_path
    """
    try:
        import gdal
    except ImportError:
        import osgeo.gdal as gdal

    # create a vector envelope of the raster
    master_name = os.path.basename(master_image[:-5])
    master_envelope = os.path.join(output_dir, f"{master_name}_envelope.shp")
    master_envelope = image_envelope(master_image, master_envelope)

    # Get master geometry
    master_footprint = get_master_geometry(master_envelope)

    # Create a virtual raster that will be used as DEM
    hgts = check_srtm_coverage(master_footprint, srtm_shapefile)
    hgts_tuple = []
    for hgt in hgts:
        hgt_path = os.path.join(hgts_path, hgt)
        if os.path.exists(hgt_path):
            hgts_tuple.append(os.path.join(hgts_path, hgt))
        else:
            raise Exception("{} not found. Please check your path to hgts files (only .hgt extension are available)".format(hgt))


    # logger.info("\n Creating virtual raster from intersected hgt files...\n")

    dem = os.path.join(output_dir, f"{master_name}_scene.vrt")
    gdal.BuildVRT(dem, hgts_tuple)

    return dem


