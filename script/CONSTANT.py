from enum import Enum,Flag, IntEnum,auto,unique

@unique
class MASTER_IMAGE(Enum):
    FIX = auto()
    MOVING = auto()

    def __str__(self) -> str:
        return self.name
        
@unique
class PROVIDER(Enum):
    PEPS = auto()
    SCIHUB = auto()

    def __str__(self) -> str:
        return self.name


@unique
class ORBIT_TYPE(Enum):
    ASC = auto()
    DES = auto()

    def __str__(self) -> str:
        return self.name


@unique
class LOCATION_TYPE(Enum):
    URL = auto()
    FOLDER = auto()
    ZIP = auto()

@unique
class POLARIZATION(IntEnum):
    VV = 0
    VH = 1 

    def __repr__(self) -> str:
        return self.name
    
    def __str__(self) -> str:
        return self.name

    @classmethod
    def allCombinations(cls,polarization_list):
        import itertools
        out = []
        for ii in range(len(polarization_list)):
            for polar in itertools.combinations(polarization_list,ii+1):
                out.append(list(polar))
        return out

@unique
class SATELLITE(IntEnum):
    S1A = auto()
    S1B = auto()

    def __str__(self) -> str:
        return self.name

SNAPHU_INSTALL_DIRNAME = None
DIAPOTB_INSTALL_DIRNAME = None
SRTM_SHAPEFILE_PATH = None
GEOID_PATH = None
EXE_FIX = "python_src/diapotb/SAR_MultiSlc_IW.py"
EXE_MOVING = "python_src/diapotb/diapOTB_S1IW.py"
SNAPHU_EXE = "snaphu"

DOWNLAOD_FOLDER = "download"
DOWNLAOD_BUFSIZE = 1024*1024*16
RAW_FOLDER = "S1Products"
EXTRACT_ROI_FOLDER = "extract_ROI"
DIAPOTB_CONFIG_FILE = "config.json"
DIAPOTB_OUTPUTDIR = "diapOTB"
CONCATENATE_OUTPUTDIR = "concatenate"
CALIBRATION_OUTPUTDIR = "Calibration"
AMPLITUDE_PHASE_OUTPUTDIR = "AmpliPhase"
VRT_FOLDER = "vrt"
TMP_OUTPUTDIR = "tmp"
OPT_RAM = 2000

S1PRODUCT_FILE_SIZE = 7_800

config_MultiSlc_IW = {
    "Global": {
        "in":
        {
            "SRTM_Shapefile": "pathToSHP/srtm.shp",
            "SRTM_Path": "pathToSRTM_30_hgt/",
            "Geoid": "pathToGeoid/egm96.grd",
            "Master_Image": "image_1.tiff",
            "Start_Date": "20150809",
            "End_Date": "20150902",
            "Input_Path": "pathToInputDir"
        },
        "out":
        {
            "Output_Path": "pathToOutputDir"
        },
        "parameter":
        {
            "clean" : "true",
            "burst_index": "0-8",
            "optram" : 256,
	    "tmpdir_into_outputdir": "no"
        }
    },

    "Pre_Processing": {
        "out":
        {
            "doppler_file": "dop0.txt"
        },
        "parameter":
        {
	    "ML_ran": 8,
 	    "ML_azi": 2,
            "ML_gain": 0.1
        }
    },
    "Ground": {},
    "DIn_SAR":
    {
        "parameter":
        {
            "GridStep_range": 160,
            "GridStep_azimut":160,
            "Grid_Threshold": 0.3,
            "Grid_Gap": 1000,
            "Interferogram_gain": 0.1,
	    "Activate_Interferogram": "yes",
	    "ESD_iter": 2
        }
    },
    "Post_Processing":
    {
        "parameter":
        {
            "Activate_Ortho": "yes",
            "Spacingxy": 0.0001,
	    "Activate_Filtering" : "yes",
	    "Filtered_Interferogram_mlran" : 3,
	    "Filtered_Interferogram_mlazi" : 3
        }
    }
}

config_DiaoOtb_IW = {
    "Global": {
        "in": 
        {
            "Master_Image_Path": "image_1.tif",
            "Slave_Image_Path": "image_2.tif",
            "DEM_Path": "./DEM.hgt"
        },
        "out": 
        {
            "output_dir": "./output_diapOTB"
        },
        "parameter":
        {
            "burst_index": "0-8",
            "optram" : 256
        }
    },
    
    "Pre_Processing": {
        "out": 
        {
            "doppler_file": "dop0.txt"
        },
        "parameter":
        {
            "ML_range": 8,
            "ML_azimut": 2,
            "ML_gain": 0.2
        }
    },
    "Ground": {},
    "DIn_SAR": 
    {
        "parameter":
        {
            "GridStep_range" : 160,
            "GridStep_azimut" : 160,
            "Grid_Threshold" : 0.3,
            "Grid_Gap" : 1000,
            "Interferogram_gain" : 0.1,
            "ESD_iter" : 2
        }
    },
    "Post_Processing":
    {
        "parameter":
        {
            "Activate_Ortho": "yes",
            "Spacingxy": 0.0001,
            "Activate_Filtering" : "yes",
            "Filtered_Interferogram_mlran" : 3,
            "Filtered_Interferogram_mlazi" : 3
        }
    }
}

config_IW_Common = {
    "Pre_Processing": {
        "out": 
        {
            "doppler_file": "dop0.txt"
        },
        "parameter":
        {
            "ML_range": 8,
            "ML_azimut": 2,
            "ML_gain": 0.2
        }
    },
    "Ground": {},
    "DIn_SAR": 
    {
        "parameter":
        {
            "GridStep_range" : 160,
            "GridStep_azimut" : 160,
            "Grid_Threshold" : 0.3,
            "Grid_Gap" : 1000,
            "Interferogram_gain" : 0.1,
            "ESD_iter" : 2
        }
    },
    "Post_Processing":
    {
        "parameter":
        {
            "Activate_Ortho": "yes",
            "Spacingxy": 0.0001,
            "Activate_Filtering" : "yes",
            "Filtered_Interferogram_mlran" : 3,
            "Filtered_Interferogram_mlazi" : 3
        }
    }
}

config_IW_MultiSlc_Header = {
        "Global": {
        "in":
        {
            "SRTM_Shapefile": "pathToSHP/srtm.shp",
            "SRTM_Path": "pathToSRTM_30_hgt/",
            "Geoid": "pathToGeoid/egm96.grd",
            "Master_Image": "image_1.tiff",
            "Start_Date": "20150809",
            "End_Date": "20150902",
            "Input_Path": "pathToInputDir"
        },
        "out":
        {
            "Output_Path": "pathToOutputDir"
        },
        "parameter":
        {
            "clean" : "true",
            "burst_index": "0-8",
            "optram" : 256,
	    "tmpdir_into_outputdir": "yes"
        }
    }
}

config_IW_DiaoOtb_Header = {
        "Global": {
        "in": 
        {
            "Master_Image_Path": "image_1.tif",
            "Slave_Image_Path": "image_2.tif",
            "DEM_Path": "./DEM.hgt"
        },
        "out": 
        {
            "output_dir": "./output_diapOTB"
        },
        "parameter":
        {
            "burst_index": "0-8",
            "optram" : 256
        }
    }
}

def init():
    __init_DIAPOTB_INSTALL_DIRNAME()
    __init_SNAPHU_INSTALL_DIRNAME()
    __init_SRTM_SHAPEFILE_PATH()
    __init_GEOID_PATH()

def __init_DIAPOTB_INSTALL_DIRNAME():
    import os
    
    global DIAPOTB_INSTALL_DIRNAME
    
    if os.getenv("DIAPOTB_HOME"):
        DIAPOTB_INSTALL_DIRNAME = os.getenv("DIAPOTB_HOME")
    else:
        DIAPOTB_INSTALL_DIRNAME = os.environ["DIAPOTB_INSTALL_DIRNAME"]
    

def __init_SNAPHU_INSTALL_DIRNAME():
    import os
    import pathlib

    global SNAPHU_INSTALL_DIRNAME
    PATH = str(pathlib.Path(__file__).parents[1].resolve())
    snapHU_path = os.path.join(str(PATH),"snaphu-v2.0.5/bin/snaphu")
    if os.path.exists(snapHU_path):
        SNAPHU_INSTALL_DIRNAME = os.path.dirname(snapHU_path)
    else:
        try:
            SNAPHU_INSTALL_DIRNAME = os.environ["SNAPHU_INSTALL_DIRNAME"]
        except KeyError as e:
            print("WARNING:SNAPHU_INSTALL_DIRNAME is not set")
            SNAPHU_INSTALL_DIRNAME = None


def __init_SRTM_SHAPEFILE_PATH():
    import os
    from pkg_resources import resource_filename   
    import pathlib

    global SRTM_SHAPEFILE_PATH
    MAIN_PATH = str(pathlib.Path(__file__).parents[0].resolve())
    SRTM_SHAPEFILE_PATH_tmp = os.path.join(MAIN_PATH,"resources/shapefile/srtm.shp")
    if os.path.exists(SRTM_SHAPEFILE_PATH_tmp):
        SRTM_SHAPEFILE_PATH  = SRTM_SHAPEFILE_PATH_tmp
    else:
        SRTM_SHAPEFILE_PATH = str(resource_filename ('script', 'resources/shapefile/srtm.shp'))

def __init_GEOID_PATH():
    import os
    from pkg_resources import resource_filename   
    import pathlib

    global GEOID_PATH
    MAIN_PATH = str(pathlib.Path(__file__).parents[0].resolve())
    SRTM_SHAPEFILE_PATH_tmp = os.path.join(MAIN_PATH,"resources/Geoid/egm96.grd")
    if os.path.exists(SRTM_SHAPEFILE_PATH_tmp):
        GEOID_PATH  = SRTM_SHAPEFILE_PATH_tmp
    else:
        GEOID_PATH = str(resource_filename ('script', 'resources/Geoid/egm96.grd'))