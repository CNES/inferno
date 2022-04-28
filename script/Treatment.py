from __future__ import annotations
from abc import ABC, abstractclassmethod
from typing import TYPE_CHECKING, Union

import numpy as np
from script import Tools

if TYPE_CHECKING:
    from script import Inferno
from script import CONSTANT
from script.S1Product import S1Product
from script import QualityIndicator
    
from dataclasses import dataclass
from collections import namedtuple

import os
import sys
import glob

from typing import Callable
# from script import Inferno
from typing import List
import signal
import atexit


def create_dir(dir_path):
    #c Create directory if not existe
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path,exist_ok=True)

@dataclass
class stepInfo:
    description:str
    maxProgress:int = 0

class Step(ABC):
    def __init__(self,
            inferno:Inferno.Inferno,
            callbackStepInfo = None,
            callbackProgress=None,
            stdout=None
        ) -> None:
        self.info = stepInfo(self.title())
        self.inferno = inferno
        self._callbackStepInfo : Callable[[stepInfo],None] = callbackStepInfo
        self._callbackProgress : Callable[[int],None] = callbackProgress
        self.stdout = stdout
        if stdout is not None:
            # sys.stderr = stdout
            sys.stdout = stdout
            pass

    def __del__(self):
        if self.stdout is not None:
            sys.stdout = sys.__stdout__
    
    def printInfo(self,*args,**kwargs):
        print(*args,**kwargs)

    @classmethod
    def title(cls)->str:
        return cls.__class__.__name__

    @abstractclassmethod
    def run(self):
        ...

    def callbackProgress(self,progress:int):
        if self._callbackProgress is not None:
            self._callbackProgress(progress)

    def callbackStepInfo(self,description:str=None,maxProgress:int=None):
        self.printInfo(description)
        if description is not None:
            self.info.description=description
        if maxProgress is not None:
            self.info.maxProgress=maxProgress
        if self._callbackStepInfo is not None:
            self._callbackStepInfo(self.info)

class CreateDir(Step):
    def __init__(self, inferno: Inferno.Inferno, callbackStepInfo=None, callbackProgress=None, stdout=None) -> None:
        super().__init__(inferno, callbackStepInfo, callbackProgress, stdout)
        self.folderToCreate = []
        self.folderToCreate.append(self.inferno.getDownloadFolder())
        self.folderToCreate.append(self.inferno.getRawFolder())
        self.folderToCreate.append(self.inferno.getOutputDir())
        self.folderToCreate.append(self.inferno.getWorkingDir())
        self.folderToCreate.append(self.inferno.getTmpFolder())
        # self.removeTmpDir()

    def run(self):
        for folder in self.folderToCreate:
            create_dir(folder)

    def removeTmpDir(self):
        import shutil
        file  = self.inferno.getTmpFolder()
        if os.path.exists(file) and os.path.isdir(file):
            shutil.rmtree(file)
    
class Download(Step):

    def __init__(self,*args,**kwargs ) -> None:
        super().__init__(*args,**kwargs)
        self.NoCurrent = 0
        self.NbElement = len(self.inferno.chosenPriorityProposition.list)
        self.currentProduct :S1Product = None

    def run(self):
        """ 
        download all production in self.inferno.chosenPriorityProposition.list
        and for each S1product in self.inferno.chosenPriorityProposition.list
        set S1product.location to the path of downloaded product
        """
        self.callbackStepInfo(description="Download")
        self.download()

    def download(self):
        import requests

        auth = self.inferno.parameters.inputConfig.auth
        downloadfolder =  self.inferno.getDownloadFolder()
        create_dir(downloadfolder)
        for product in self.inferno.chosenPriorityProposition.list:
            if product.locationType != CONSTANT.LOCATION_TYPE.URL:
                continue
            self.currentProduct = product
            filename = product.download(
                auth = auth,
                dir_name = downloadfolder,
                callbackCurrentSize = self.callbackProgress,
                callbackMaxInfo = lambda x: self.onMaxInfo(x,product),
                bufsize=CONSTANT.DOWNLAOD_BUFSIZE
                )
            product.location = filename


    def onMaxInfo(self,max:int,product:S1Product):
        self.NoCurrent +=1
        self.callbackStepInfo(
            description=f"Download: {self.NoCurrent}/{self.NbElement}",
            maxProgress=max )
        self.printInfo(f'Download:{product.name}')

class Unzip(Step):

    def run(self):
        """ 
        unzip each element in self.inferno.chosenPriorityProposition.list
        if needed
        """
        self.unzipall()
    
    def unzipall(self):
        self.NbElement = len(self.inferno.chosenPriorityProposition.list)
        self.NoCurrent = 0

        targetFolder = os.path.join(self.inferno.getWorkingDir(),CONSTANT.RAW_FOLDER)
        create_dir(targetFolder)
        for no,product in enumerate(self.inferno.chosenPriorityProposition.list):
            if product.locationType != CONSTANT.LOCATION_TYPE.ZIP:
                continue
            file = product.location
            self.callbackStepInfo(description=f"Unzip {no+1}/{self.NbElement}" )
            self.printInfo(f'Unzip: {product.name}')
            filename = self.unzipProduct(file,targetFolder)
            self.delectZipFile(file)
            product.location = filename       

    def unzipProduct(self,filename,target):
        import zipfile
        with zipfile.ZipFile(filename,'r') as zip_ref:
            info = zip_ref.infolist()
            self.callbackStepInfo(maxProgress=len(info))
            for progress,member in enumerate(info):
                self.printInfo(f'unzip: {member.filename}')
                if  self.exists(member,target):
                    continue
                self.callbackProgress(progress)
                zip_ref.extract(member,target)
        return os.path.join(self.inferno.getRawFolder(), info[0].filename)

    def delectZipFile(self,zipPath:str):
        os.remove(zipPath)

    @staticmethod
    def exists(member,target) ->bool:
        filename = os.path.join(target,member.filename)
        b0 = os.path.exists( filename ) and  os.path.getsize(filename)
        b1 = os.path.isfile( filename )
        return b1 or b0

class CreateTmpCopy(Step):

    def run(self):
        self.main()
    
    def main(self):
        productList = self.inferno.chosenPriorityProposition.list
        outputDir = os.path.join(
                self.inferno.getTmpFolder(),
                CONSTANT.RAW_FOLDER)

        for product in productList:
            src = product.location
            fileName = os.path.basename(src)
            dst = os.path.join(
                outputDir,
                fileName)

            Tools.createAllDirToFile(dst)
            os.symlink(src, dst)
            product.location = dst
        pass

class CropROI():

    @staticmethod
    def _cropProduct(filePath,outputFilePath,ulx,lrx,lry,uly):
        Tools.createAllDirToFile(outputFilePath)
        import otbApplication
        app = otbApplication.Registry.CreateApplication("ExtractROI")
        app.SetParameterString("in", filePath)
        app.SetParameterString("mode","extent")
        app.SetParameterFloat("mode.extent.ulx",ulx)
        app.SetParameterFloat("mode.extent.uly",uly)
        app.SetParameterFloat("mode.extent.lrx",lrx)
        app.SetParameterFloat("mode.extent.lry",lry)
        app.SetParameterString("mode.extent.unit","lonlat")
        app.SetParameterString("out",outputFilePath)
        app.ExecuteAndWriteOutput()

    @staticmethod
    def cropProduct(inferno:Inferno.Inferno,filePath:str):
        diapOTB_file = inferno.getDiapOtbOutputDir()
        filename = filePath[len(diapOTB_file)+ (not diapOTB_file[-1]=="/"): ]
        filename = "_".join(filename.split("/"))

        outputFolder = os.path.join(inferno.getTmpFolder(),CONSTANT.EXTRACT_ROI_FOLDER)
        create_dir(outputFolder)
        outputFilePath = os.path.join(outputFolder,filename)

        ulx=inferno.parameters.inputConfig.ROI.upperLeftX
        lrx=inferno.parameters.inputConfig.ROI.lowerRigthX

        uly=inferno.parameters.inputConfig.ROI.lowerRigthY
        lry=inferno.parameters.inputConfig.ROI.upperLeftY


        CropROI._cropProduct(filePath,outputFilePath,ulx,lrx,lry,uly)
        return outputFilePath

    @staticmethod
    def getOtbApplicationOrthoExtract(ulx,uly,lrx,lry):
        import otbApplication
        app = otbApplication.Registry.CreateApplication("OrthoRectification")
        app.SetParameterString("map","wgs")
        app.SetParameterString("outputs.mode","outputroi")

        app.SetParameterFloat("outputs.ulx",ulx)
        app.SetParameterFloat("outputs.uly",lry)
        app.SetParameterFloat("outputs.lrx",lrx)
        app.SetParameterFloat("outputs.lry",uly)
        # app.SetParameterFloat("opt.gridspacing",0.01)
        return app

    
    @staticmethod
    def orthoRectificationExtractROI(filePath,outputFilePath,ulx,uly,lrx,lry,prefix="ortho_"):
        Tools.createAllDirToFile(outputFilePath)
        outputFilePath = os.path.join(
            os.path.dirname(outputFilePath),
            f'{prefix}{os.path.basename(outputFilePath)}',
        )
        app = CropROI.getOtbApplicationOrthoExtract(ulx,uly,lrx,lry)
        app.SetParameterString("io.in", filePath)
        app.SetParameterString("io.out",outputFilePath )

        print(" ")
        import pprint
        pprint.pprint(app.GetParameters())
        print(" ")

        app.ExecuteAndWriteOutput()
        return outputFilePath

class CheckIfProductExist(Step):
    def run(self):
        self.callbackStepInfo(description="Initialisation")
        self.setLocationType()
        self.checkIfExistInWorkingDir()

    def setLocationType(self):
        for product in self.inferno.chosenPriorityProposition.list:
            if product.location.startswith("http"):
                product.locationType = CONSTANT.LOCATION_TYPE.URL
            elif product.location.endswith(".zip"):
                product.locationType = CONSTANT.LOCATION_TYPE.ZIP
            else:
                product.locationType = CONSTANT.LOCATION_TYPE.FOLDER


    def checkIfExistInWorkingDir(self):
            zipFolder = self.inferno.getDownloadFolder()
            ZipFilenames = os.listdir(zipFolder)

            productFolder = self.inferno.getRawFolder()
            productFilenames = os.listdir(productFolder)

            for product in self.inferno.chosenPriorityProposition.list:
                self.checkIfProductExist(product,productFolder,productFilenames)
                self.checkIfZipExist(product,zipFolder,ZipFilenames)

    def checkIfZipExist(self,
            product:S1Product,
            zipFolder:str,
            ZipFilenames:List[str])->bool:
        filename = product.name+".zip"
        try:
            ZipFilenames.remove(filename)
        except Exception:
            return False
        product.location = os.path.join(zipFolder,filename)
        product.locationType = CONSTANT.LOCATION_TYPE.ZIP
        self.printInfo(f"{filename} is available")
        return True

    def checkIfProductExist(self,
            product:S1Product,
            productFolder:str,
            productFilenames:List[str]
            ):
        filename = product.name+".SAFE"
        try:
            productFilenames.remove(filename)
        except Exception:
            return False
        product.location = os.path.join(productFolder,filename)
        product.locationType = CONSTANT.LOCATION_TYPE.FOLDER
        self.printInfo(f"{filename} is available")

        return True

class DiapOtb(Step):
    def __init__(
            self,
            inferno: Inferno.Inferno,
            orthoRectification:bool=False,
            callbackStepInfo=None,
            callbackProgress=None,
            stdout=None,
            ) -> None:

        super().__init__(inferno, callbackStepInfo, callbackProgress, stdout)
        self.configJsonFiles = []
        self.outputDirPattern = ""
        self.filePattern = ""
        self.filteredFiles :List[str]= []
        self.notFilteredFiles :List[str]= []
        self.orthoRectification = orthoRectification  or self.needOrtho()
        self.process = None
    
    def createConfigJsonFiles(self,
        paths:List[str]=None,
        prefix:str = ""):
        
        self.callbackStepInfo(description="DiapOtb:Create Json Files")

        inferno = self.inferno
        strategy = inferno.parameters.treatment.masterImage.strategy
        if strategy == CONSTANT.MASTER_IMAGE.FIX:
            configDict = CONSTANT.config_MultiSlc_IW.copy()
            self.fillCommon(inferno=inferno,configDict=configDict)
            filenames = self.fillFixJson(inferno=inferno,configDict=configDict,paths=paths,prefix=prefix)
            outputPattern = "output_*/*_m_*"
        elif strategy == CONSTANT.MASTER_IMAGE.MOVING:
            configDict = CONSTANT.config_DiaoOtb_IW.copy()
            self.fillCommon(inferno=inferno,configDict=configDict)
            filenames = self.fillMovingJson(inferno=inferno,configDict=configDict,Paths=paths,prefix=prefix)
            outputPattern = ""
        
        self.printInfo(f"Create: {filenames}")
        self.configJsonFiles.extend(filenames)
        self.outputDirPattern = self._getOutputDirPattern(prefix=prefix,outputPattern=outputPattern)
        return filenames

    def start(self):
        self.callbackStepInfo(
            description="DiapOtb: Execution",
            maxProgress=len(self.configJsonFiles))
    
        for i,configJson in enumerate(self.configJsonFiles):
            self.callbackProgress(progress=i+0.5)
            self.printInfo(f"Run DiapOtb with {configJson}")
            self.run(configJsonPath=configJson,inferno=self.inferno)
            self.callbackProgress(progress=i+1)
 

        outputFiles = self.getOutputfiles()
        self.notFilteredFiles = outputFiles[0]
        self.filteredFiles =    outputFiles[1]

        return self.notFilteredFiles,self.filteredFiles

    def needOrtho(self):
        creationOption = self.inferno.parameters.treatment.creationOption
        return True and creationOption.orthorectification or creationOption.phaseFiltering.activate

    def getOutputfiles(self):
        import glob
        filesPatterns = self._getFilePattern()

        self.notFilteredFiles = glob.glob(filesPatterns[0])
        self.filteredFiles = glob.glob(filesPatterns[1])
        return [self.notFilteredFiles,self.filteredFiles]

    def _getFilePattern(self):
        filePattern = ""
        filteredFilePattern = ""
        if self.inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.MOVING:
            filteredFilePattern = "filtered_interferogram.tif"
            filePattern = "interferogram_swath.tif"

        elif  self.inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.FIX:
            filteredFilePattern = "S*_Filtred-Interferogram.tif"
            filePattern = "S*_Interferogram.tif"

        filePattern = os.path.join(self.outputDirPattern,filePattern)
        filteredFilePattern = os.path.join(self.outputDirPattern,filteredFilePattern)
        return filePattern,filteredFilePattern

    def _getOutputDirPattern(self,outputPattern,prefix = ""):
        path = self.inferno.getDiapOtbOutputDir()
        ind = ""
        if prefix!="":
            prefix="*"


        strategy = self.inferno.parameters.treatment.masterImage.strategy
        if strategy == CONSTANT.MASTER_IMAGE.MOVING:
            ind = "*"
        return os.path.join(path,prefix,ind,outputPattern)

    @staticmethod
    def _readOutPutdir(filePath):
        import json
        with open(filePath) as f:
            data = json.load(f)
        try :
            return data["Global"]["out"]["output_dir"]
        except Exception:
            return data["Global"]["out"]["Output_Path"]

    def run(self,configJsonPath:str,inferno:Inferno.Inferno):
        import subprocess
        import sys

        env = dict(os.environ)
        # DIAPOTB_HOME = env["DIAPOTB_HOME"]
        DIAPOTB_HOME = CONSTANT.DIAPOTB_INSTALL_DIRNAME
        if inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.MOVING:
            exe_name = CONSTANT.EXE_MOVING
        elif  inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.FIX:
            exe_name = CONSTANT.EXE_FIX
        exe_name = os.path.join(DIAPOTB_HOME,exe_name)
        
        self.removelogFile(configJsonPath)

        configPath = configJsonPath
        commande = []
        commande.append("python")
        commande.append(exe_name)
        commande.append(configPath)

        process =  subprocess.Popen(
            commande,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            ) 
            # self.process = process
        
        def terminate():
            process.kill()
        atexit.register(terminate)

        DiapOtbLogFile = self.waitForlogFile(configPath)
        self.printLogFile(DiapOtbLogFile,process)

        _, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"DiapOTB {stderr}")
        
        self.__deletectBurstFile()
        return

    def __deletectBurstFile(self):
        import shutil
        output_dir = self.inferno.getDiapOtbOutputDir()
        patern = os.path.join(output_dir,"**/burst*/")
        folders = glob.glob(patern,recursive=True)
        for folder in folders:
            shutil.rmtree(folder)
        

    def removelogFile(self,configPath):
        try:
            DiapOtbLogFile = os.path.join(self._readOutPutdir(configPath),"info.log")
            os.remove(DiapOtbLogFile)
        except OSError:
            pass

    def waitForlogFile(self,configPath):
        from time import sleep
        DiapOtbLogFile = os.path.join(self._readOutPutdir(configPath),"info.log")
        while not os.path.isfile(DiapOtbLogFile) :
            sleep(1)
        return DiapOtbLogFile
    
    def printLogFile(self,DiapOtbLogFile,process):
        from time import sleep
        with open(DiapOtbLogFile,"r") as f:
            while True:
                if process.poll() is not None:
                    break
                res = f.readline()
                if not res:
                    sleep(5)
                    continue
                print(res,end="")
        

    @classmethod
    def createConfigJson(cls,
        inferno:Inferno.Inferno,
        paths:List[str]=None,
        prefix:str = ""):

        strategy = inferno.parameters.treatment.masterImage.strategy
        if strategy == CONSTANT.MASTER_IMAGE.FIX:
            configDict = CONSTANT.config_MultiSlc_IW.copy()
            cls.fillCommon(inferno=inferno,configDict=configDict)
            filenames = cls.fillFixJson(inferno=inferno,configDict=configDict,paths=paths,prefix=prefix)
        elif strategy == CONSTANT.MASTER_IMAGE.MOVING:
            configDict = CONSTANT.config_DiaoOtb_IW.copy()
            cls.fillCommon(inferno=inferno,configDict=configDict)
            filenames = cls.fillMovingJson(inferno=inferno,configDict=configDict,Paths=paths,prefix=prefix)
        return filenames

    @staticmethod
    def boolToYesNo(b:bool):
        if b:
            return "yes"
        return "no"

    @staticmethod
    def parsePhaseFiltering(inferno:Inferno.Inferno):
        return DiapOtb.boolToYesNo(inferno.parameters.treatment.creationOption.phaseFiltering.activate)

    @classmethod
    def fillCommon(cls,inferno:Inferno.Inferno,configDict:dict) -> dict:
        # output = CONSTANT.config_IW_Common.copy() 

        configDict["Pre_Processing"]["out"]["doppler_file"]    = "dop0.txt"

        configDict["Ground"] = {}
        configDict["DIn_SAR"]["parameter"]["GridStep_range"]   = 160
        configDict["DIn_SAR"]["parameter"]["GridStep_azimut"]  = 160 
        configDict["DIn_SAR"]["parameter"]["Grid_Threshold"]   = 0.3 
        configDict["DIn_SAR"]["parameter"]["Grid_Gap"] = 1000
        configDict["DIn_SAR"]["parameter"]["Interferogram_gain"]   = 0.1 
        configDict["DIn_SAR"]["parameter"]["ESD_iter"] = 2 

        creationOption = inferno.parameters.treatment.creationOption
        configDict["Post_Processing"]["parameter"]["Activate_Ortho"] =  "no"
        configDict["Post_Processing"]["parameter"]["Spacingxy"] = 0
        # configDict["Post_Processing"]["parameter"]["Activate_Ortho"] =  cls.parseOrthorectification(inferno)
        # configDict["Post_Processing"]["parameter"]["Spacingxy"] = creationOption.orthorectification.spacingXY     
        configDict["Post_Processing"]["parameter"]["Activate_Filtering"] = cls.parsePhaseFiltering(inferno)
        configDict["Post_Processing"]["parameter"]["Filtered_Interferogram_mlran"] = int(creationOption.phaseFiltering.filteredInterferogramMlran) 
        configDict["Post_Processing"]["parameter"]["Filtered_Interferogram_mlazi"] = int(creationOption.phaseFiltering.filteredInterferogramMlazi)    
        return configDict

    @staticmethod
    def getBurstRange(filepath:str,inferno:Inferno.Inferno)->np.ndarray:
        
        geom = Tools.getGeomFromTif(filepath)

        points = inferno.parameters.inputConfig.ROI.getGeom()

        burstCount = Tools.getBurstCount(filepath)

        orbitType=inferno.chosenPriorityProposition.orbitType
        burstIndex = Tools.pointInBurst(geom,points,burstCount,orbitType=orbitType)
        burstIndex =  np.array(
            [   np.floor(burstIndex.min()),
                np.round(burstIndex.max(),decimals=0)]).astype(np.int8)

        burstIndex = np.unique(burstIndex)

        burstIndex[burstIndex<0] = 0
        burstIndex[burstIndex>( burstCount-1)] = burstCount-1

        if len(burstIndex) == 1:
            return burstIndex
            

        print( np.array([burstIndex.min(),burstIndex.max()]) )
        return np.array([burstIndex.min(),burstIndex.max()])
    
    @classmethod
    def parse_DEM_Path(cls,inferno:Inferno.Inferno,master_image):
        DEM_Path = inferno.parameters.inputConfig.mntPath
        if os.path.isfile(DEM_Path):
            return DEM_Path
        # we assume DEM_Path is folder 
        output_dir = os.path.join(inferno.getTmpFolder(), CONSTANT.VRT_FOLDER)
        Tools.create_dir(output_dir)
        srtm_shapefile = CONSTANT.SRTM_SHAPEFILE_PATH
        dem = Tools.build_virutal_raster(master_image, srtm_shapefile, DEM_Path, output_dir)
        return dem

    @classmethod
    def fillMovingJson(cls,
        configDict:dict,
        inferno:Inferno.Inferno,
        Paths:List[str],
        prefix:str = ""):
        
        import json
        outFilenames = []

        filenamePathern = os.path.join(inferno.getWorkingDir(),"config_{}_{}.json")
        outputJson = CONSTANT.config_IW_DiaoOtb_Header.copy() 
        outputJson.update(configDict)

        outputJson["Pre_Processing"]["parameter"]["ML_range" ] = 8
        outputJson["Pre_Processing"]["parameter"]["ML_azimut" ] = 2
        outputJson["Pre_Processing"]["parameter"]["ML_gain" ] = 0.2

        for i in range(len(Paths[:-1])):
            outputJson["Global"]["in"]["DEM_Path"] = cls.parse_DEM_Path(inferno, Paths[i])
            outputJson["Global"]["out"]["output_dir"] = cls.getOutputDir(inferno=inferno,ind =i,prefix=prefix)

            outputJson["Global"]["in"]["Master_Image_Path"] = Paths[i]
            outputJson["Global"]["in"]["Slave_Image_Path"] = Paths[i+1]
            burst_index = cls.getBurstRange(Paths[i],inferno)

            outputJson["Global"]["parameter"]["burst_index"]    = "-".join( [str(ele) for ele in burst_index])

            filename = filenamePathern.format(prefix,f"{i+1}{i+2}")

            with open(filename, 'w') as outfile:
                json.dump(outputJson, outfile, indent=4)
            outFilenames.append(filename)
        return outFilenames

    @classmethod
    def getOutputDir(cls,inferno:Inferno.Inferno,prefix:str="",ind:int=""):
        path = inferno.getDiapOtbOutputDir()
        return os.path.join(path,prefix,str(ind))

    @classmethod
    def fillFixJson(cls,
        configDict:dict,
        inferno:Inferno.Inferno,
        paths:List[str],
        prefix:str = "") -> List[CONSTANT.config_IW_MultiSlc_Header]:

        import json
        header = CONSTANT.config_IW_MultiSlc_Header.copy()
        header.update(configDict)

        header["Pre_Processing"]["parameter"]["ML_ran" ] = 8
        header["Pre_Processing"]["parameter"]["ML_azi" ] = 2
        header["Pre_Processing"]["parameter"]["ML_gain" ] = 0.2


        infernoConfig = inferno.parameters.inputConfig
        header["Global"]["in"]["SRTM_Shapefile"]= CONSTANT.SRTM_SHAPEFILE_PATH
        header["Global"]["in"]["Geoid"]         = CONSTANT.GEOID_PATH
        # header["Global"]["in"]["SRTM_Path"]     = "/work/datalake/static_aux/MNT/SRTM_30_hgt/"
        header["Global"]["in"]["SRTM_Path"]     = inferno.parameters.inputConfig.mntPath
        header["Global"]["in"]["Master_Image"]  = os.path.basename(paths[0])
        header["Global"]["in"]["Start_Date"]    = infernoConfig.dates.begin.strftime("%Y%m%d")
        header["Global"]["in"]["End_Date"]      = infernoConfig.dates.end.strftime("%Y%m%d")
        header["Global"]["in"]["Input_Path"]    = inferno.getRawFolder()

        
        header["Global"]["out"]["Output_Path"]    = cls.getOutputDir(inferno=inferno,prefix=prefix)
        burst_index = cls.getBurstRange(paths[0],inferno)
        header["Global"]["parameter"]["burst_index"]    = "-".join( [str(ele) for ele in burst_index])
        if prefix == "":
            filename = os.path.join(inferno.getWorkingDir(),f"config.json")
        else:
            filename = os.path.join(inferno.getWorkingDir(),f"config_{prefix}.json")
        with open(filename, 'w') as outfile:
            json.dump(header, outfile, indent=4)
        return [filename]       

class Calibration(Step):

    def run(self,inputDir:str,listFilePaths:List,calibration:bool,logCalibration:bool):
        """
        example:
        listFilePaths[0] = ~/scratch/working/PALMA_P4/diapOTB/S1A_iw1/output_20210901_to_20210930_m_20210902/20210902_m_20210926_s/S1_M_20210902t191349_S_20210926t191350_Filtred-Interferogram.tif
        inputDir = ~/scratch/working/PALMA_P4/diapOTB
        """
        calibrationFilePaths = []
        calibrationLogFilePaths = []

        self.callbackStepInfo(
            description="Calibration",
            maxProgress=len(listFilePaths))

        dirname = os.path.dirname(inputDir)
        self.outputdir = os.path.join(dirname,CONSTANT.CALIBRATION_OUTPUTDIR)
        for idx,filePath in enumerate(listFilePaths,start=1):
            self.printInfo(f"Calibrate {filePath}")

            # _outputDir = inputDir
            dirname = os.path.dirname(inputDir)
            filename = filePath[
                len(inputDir)+ (not inputDir[-1]==os.path.sep):]

            outFilePath = os.path.join(self.outputdir,filename)
            self.SARCalibration(
                inFilePath=filePath,
                outFilePath=outFilePath,
                ram=CONSTANT.OPT_RAM)

            self.callbackProgress(idx-0.5)
            
            
            if logCalibration:
                self.printInfo(f"Calibrate (log scale) {filePath}")
                _folder = os.path.dirname(outFilePath)
                _file =  os.path.basename(outFilePath)
                outLogFilePath = os.path.join(_folder,"Log{}".format(_file))
                self.SARCalibrationLog(
                    normCalibrationPath=outFilePath,
                    outFilePath=outLogFilePath,
                    ram=CONSTANT.OPT_RAM)
                calibrationLogFilePaths.append(outLogFilePath)
            
            if not(calibration):
                pass
                # os.remove(outFilePath)
            else:
                calibrationFilePaths.append(outFilePath)
                
            self.callbackProgress(idx)  
        return calibrationFilePaths,calibrationLogFilePaths


    def SARCalibration(self,inFilePath:str,outFilePath,ram:int=CONSTANT.OPT_RAM):
        print(f"""

        SARCalibration:
            inFilePath:{inFilePath}
            outFilePath:{outFilePath}
        
        """)
        Tools.createAllDirToFile(outFilePath)
        import otbApplication
        OtbSARCalibration = otbApplication.Registry.CreateApplication("SARCalibration")
        OtbSARCalibration.SetParameterInt("ram",ram)
        OtbSARCalibration.SetParameterString("lut","sigma")
        OtbSARCalibration.IN = inFilePath

        # "will concatenate their results into a unique multiband output image"
        OtbBandMathX = otbApplication.Registry.CreateApplication("BandMathX")
        OtbBandMathX.SetParameterInt("ram",ram)
        OtbBandMathX.SetParameterString(
            "exp",
            "im1b1*im2b1/sqrt(im1b1^2+im1b2^2);im1b2*im2b1/sqrt((im1b1^2+im1b2^2))")
        OtbBandMathX.SetParameterStringList("il", [inFilePath])
        OtbBandMathX.ConnectImage('il',OtbSARCalibration,"out")

        ulx=self.inferno.parameters.inputConfig.ROI.upperLeftX
        lrx=self.inferno.parameters.inputConfig.ROI.lowerRigthX
        uly=self.inferno.parameters.inputConfig.ROI.lowerRigthY
        lry=self.inferno.parameters.inputConfig.ROI.upperLeftY
        OtbOrthoCrop = CropROI.getOtbApplicationOrthoExtract(ulx=ulx,lrx=lrx,uly=uly,lry=lry)
        OtbOrthoCrop.ConnectImage("io.in", OtbBandMathX, "out")
        OtbOrthoCrop.SetParameterString("io.out",outFilePath )
        OtbOrthoCrop.ExecuteAndWriteOutput()



    def SARCalibrationLog(self,normCalibrationPath:str,outFilePath,ram:int=2000):
        Tools.createAllDirToFile(outFilePath)
        import otbApplication

        appMaskCreate = otbApplication.Registry.CreateApplication("ManageNoData")
        appMaskCreate.SetParameterString("in", normCalibrationPath)
        appMaskCreate.SetParameterFloat("mode.buildmask.inv", 1)
        appMaskCreate.SetParameterFloat("mode.buildmask.outv", 0)


        # "will concatenate their results into a unique multiband output image"
        OtbBandMathX = otbApplication.Registry.CreateApplication("BandMath")
        OtbBandMathX.SetParameterInt("ram",ram)
        OtbBandMathX.SetParameterStringList("il", [normCalibrationPath])
        OtbBandMathX.ConnectImage("il", appMaskCreate, "out")
        OtbBandMathX.SetParameterString("exp","im2b1*10*log10(sqrt(im1b1^2+im1b2^2))")
        OtbBandMathX.SetParameterString("out",outFilePath )
        OtbBandMathX.ExecuteAndWriteOutput()


    def moveOutputDir(self,targetDir):
        import shutil
        tmp = os.path.join(targetDir,os.path.basename(self.outputdir))
        if os.path.isdir(tmp):
            shutil.rmtree(tmp)
        shutil.move(self.outputdir, targetDir)


class Concatenate():

    @classmethod
    def concatenate(cls,destNameOrDestDS:str,srcDSOrSrcDSTab:List[str],nodata,ram:int=2000):
        from osgeo  import gdal
        srcDSOrSrcDSTab = list(srcDSOrSrcDSTab)[::-1]
        Tools.createAllDirToFile(destNameOrDestDS)
        print(f"concatenate\n \t: destNameOrDestDS {destNameOrDestDS}  ")
        print(f"\t: srcDSOrSrcDSTab {srcDSOrSrcDSTab}  ")
        print(f"\t: nodata {nodata}  ")
        gdal.Warp(destNameOrDestDS,srcDSOrSrcDSTab, srcNodata=nodata)
        
        for file in srcDSOrSrcDSTab:
            try:
                import os
                # os.remove(file)
                pass
            except OSError:
                pass


class OrthoRectification(Step):

    def run(self):
        pass

    @staticmethod
    def orthoRectification(inFile):
        import otbApplication
        _dirname = os.path.dirname(inFile)
        _filename = os.path.basename(inFile)
        outFile = os.path.join(_dirname,f"ortho_{_filename}")


        app = otbApplication.Registry.CreateApplication("OrthoRectification")
        app.SetParameterFloat("opt.gridspacing",20)
        app.SetParameterString("io.in", inFile)
        app.SetParameterString("io.out",outFile )

        print (app.GetParametersKeys())
        app.ExecuteAndWriteOutput()
        return outFile


class AmpliPhase(Step):

    def run(
        self,
        listProduct : List[S1Product],
        polarization : CONSTANT.POLARIZATION,
        chosenSwath : List[str] = None):
        outputDir = self.inferno.getOutputDir()
        outputAmpliPhaseFiles = []

        self.callbackStepInfo(description="Generate Amplitude Phase Images",maxProgress=len(listProduct))

        for indProduct,product in enumerate(listProduct,start=1):

            self.printInfo(f"Processing file: {product.name}")
            _outputFile = self.ampliPhaseFromS1Product(
                product = product,
                outputDir = outputDir,
                chosenSwath = chosenSwath,
                polarization = polarization,
            )
            outputAmpliPhaseFiles.extend(_outputFile)
            self.callbackProgress(indProduct)

        if self.inferno.parameters.treatment.amplitudePhase.orthorectification:
            _orthorectification = OrthoRectification(
                callbackProgress=self._callbackProgress,
                callbackStepInfo=self._callbackStepInfo,
                inferno=self.inferno,
                stdout=self.stdout,
            )
            _orthorectification.callbackStepInfo(
                description="Amplitude Phase: Orthorectification",
                maxProgress=len(outputAmpliPhaseFiles))

            for indFile,file in enumerate(outputAmpliPhaseFiles, start=1):
                _orthorectification.orthoRectification(inFile=file)
                _orthorectification.callbackProgress(indFile)
                _orthorectification.printInfo(f"Amplitude Phase: Orthorectification:{file}")

        

    @classmethod
    def ampliPhase(cls,inFilePath:str,outFilePath,ram:int=CONSTANT.OPT_RAM):
        import otbApplication

        Tools.createAllDirToFile(outFilePath)
        ampliExpr = "norm(im1b1+im1b2*i)"
        phaseExpr = "arg(im1b1+im1b2*i)"
        expr = "{ampliExpr};{phaseExpr}".format(ampliExpr=ampliExpr,phaseExpr=phaseExpr)

        BandMathX = otbApplication.Registry.CreateApplication("BandMathX")
        BandMathX.SetParameterInt("ram",ram)

        BandMathX.SetParameterString('exp',expr)
        BandMathX.SetParameterString('out',outFilePath)
        BandMathX.SetParameterStringList('il', [inFilePath,])
        BandMathX.ExecuteAndWriteOutput()
        return

    @classmethod
    def ampliPhaseFromS1Product(
            cls,
            product:S1Product,
            outputDir:str,
            polarization:CONSTANT.POLARIZATION,
            chosenSwath:List[str]=None):
        if product.locationType != CONSTANT.LOCATION_TYPE.FOLDER:
            return
        # return
        outputFiles = []
        path = product.location
        folderName = os.path.basename(path)

        files = []
        if chosenSwath is not None:
            for swath in chosenSwath:
                _path_end =  "measurement/*-{swath}-*-{polarization}-*".format(swath=swath.lower(),polarization = str(polarization).lower())
                files.extend(
                    glob.glob(
                        os.path.join(
                            path, _path_end )))
        else:
           files = glob.glob(
                    os.path.join(path,"measurement/*")
                ) 
            
        for inFilePath in files:
            fileName = os.path.basename(inFilePath)
            outFilePath = os.path.join(
                outputDir,CONSTANT.AMPLITUDE_PHASE_OUTPUTDIR,folderName,fileName
            )
            cls.ampliPhase(
                inFilePath  = inFilePath,
                outFilePath = outFilePath)
            outputFiles.append(outFilePath)
        return outputFiles

class UnwrapPhase(Step):

    def __init__(
        self, 
        inferno: Inferno.Inferno,
        callbackStepInfo=None,
        callbackProgress=None,
        stdout=None) -> None:
        super().__init__(inferno, callbackStepInfo, callbackProgress, stdout)
        self.process = None

        
    def run(self,inputFilePaths:List[str]):
        SnapHuParameters = self.inferno.parameters.treatment.creationOption.phaseUnwrapping
        options = SnapHuParameters.parse()
        self.callbackStepInfo("Unwrap Phase",len(inputFilePaths))
        inputFilePaths = sorted(inputFilePaths, key = os.path.getsize)
        for ind,filePath in enumerate(inputFilePaths,start=1):
            tmpbinFilePath = filePath+".bin"
            unwrapeBinFilePath = self.generateOutputFilePath(filePath)
            amp,phase = self.getAmpPhaseFromInterferogram(filePath)
            self.writeToBinFile(amp,phase,tmpbinFilePath)
            self.runSnapHU(
                inputFile=tmpbinFilePath,
                lineLength=phase.shape[1],
                outputFile=unwrapeBinFilePath,
                option=options)
            self.writeBinToTif(filePath,unwrapeBinFilePath,phase.shape[1])
            os.remove(tmpbinFilePath)
            os.remove(unwrapeBinFilePath)
            self.callbackProgress(ind)

    @classmethod
    def _unwrap(cls,filePath:str):
            tmpbinFilePath = filePath+".bin"
            unwrapeBinFilePath = cls.generateOutputFilePath(filePath)
            amp,phase = cls.getAmpPhaseFromInterferogram(filePath)
            cls.writeToBinFile(amp,phase,tmpbinFilePath)
            cls.runSnapHU(
                inputFile=tmpbinFilePath,
                lineLength=phase.shape[1],
                outputFile=unwrapeBinFilePath)
            cls.writeBinToTif(filePath,unwrapeBinFilePath,phase.shape[1])
            os.remove(tmpbinFilePath)
            os.remove(unwrapeBinFilePath)


    @staticmethod
    def getAmpPhaseFromInterferogram(fitePath:str):
        from osgeo import gdal
        ds = gdal.Open(fitePath)
        amp   = np.array(ds.GetRasterBand(1).ReadAsArray())
        phase = np.array(ds.GetRasterBand(2).ReadAsArray())
        return amp,phase

    @staticmethod
    def writeToBinFile(amp,phase,outputFilePath):
        (amp*np.exp(1j*phase)).astype(np.csingle).tofile(outputFilePath)
    
    @staticmethod
    def getSnaphuPath():
        if CONSTANT.SNAPHU_INSTALL_DIRNAME is None:
            raise KeyError("WARNING:SNAPHU_INSTALL_DIRNAME is not set")

        return os.path.join(CONSTANT.SNAPHU_INSTALL_DIRNAME,CONSTANT.SNAPHU_EXE)

    @classmethod
    def runSnapHU(cls,inputFile,lineLength,outputFile,option=None):
        import subprocess

        try:
            snaphu_exe = cls.getSnaphuPath()
        except KeyError as e:
            print(e)
            return

        command = [
            snaphu_exe,
            inputFile,
            "-o",
            outputFile,
            str(lineLength)
        ]
        command.extend(option)
        print(*command,sep=" ")
        process = subprocess.Popen(
            [str(ele) for ele in command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            )

        def terminate():
            process.kill()
        atexit.register(terminate)

        while True:
            line = process.stdout.readline()
            line = line.decode()
            if process.poll() is not None:
                break
            print(line.strip())

        _, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"SnapHU {stderr}")
        return
    

    def _run(self,filePaths:List[str]):
        for filePath in filePaths:
            tmpbinFilePath = filePath+".bin"
            unwrapeFilePath = self.generateOutputFilePath(filePath)
            amp,phase = self.getAmpPhaseFromInterferogram(filePath)
            self.writeToBinFile(amp,phase,tmpbinFilePath)
            self.runSnapHU(
                inputFile=tmpbinFilePath,
                lineLength=phase.shape[1],
                outputFile=unwrapeFilePath)
            self.writeBinToTif(filePath,unwrapeFilePath,phase.shape[1])

    @staticmethod
    def generateOutputFilePath(inputFilePath:str):
        basename = os.path.basename(inputFilePath)
        dirName = os.path.dirname(inputFilePath)

        outputFilename = "unwrapped_{}.bin".format(basename)
        outputFilePath =os.path.join(dirName,outputFilename)
        return outputFilePath

    @staticmethod
    def writeBinToTif(infile,unwrapeFile:str,lineLength:int):
        outfile = unwrapeFile.replace(".bin","")

        import shutil
        shutil.copyfile(infile, outfile)
        arr_out = np.fromfile(unwrapeFile,dtype=np.single)
        colunmsLength = len(arr_out)//(lineLength*2)
        arr_out = arr_out.reshape(colunmsLength,2, lineLength)
        arr_out = arr_out.swapaxes(0,1)
        
        from osgeo import gdal
        outdata = gdal.Open(outfile,gdal.GF_Write)
        outdata.GetRasterBand(1).WriteArray(arr_out[0,:,:])
        outdata.GetRasterBand(2).WriteArray(arr_out[1,:,:])
        # outdata.GetRasterBand(1).SetNoDataValue(10000)##if you want these values transparent
        outdata.FlushCache()
        outdata = None
        band=None
        ds=None


class Consistency():
    @classmethod
    def run(cls,files:List[str]):
        output = {}
        for filePath in files:
            filename = os.path.basename(filePath)
            _consistency = cls.eval(filePath)
            output[filename] = _consistency
        return output

    @classmethod
    def eval(cls,filePath):
        output = {}
        stats = cls.getStatistics(filePath)
        
        output["Consistency"] = {
            "mean":stats.mean,
            "std":stats.std
            }
        return output


    @staticmethod
    def getStatistics(filePath:str):
        from osgeo import gdal
        ds = gdal.Open(filePath)
        ConsistencyStatistics = namedtuple("ConsistencyStatistics",["min","max","mean","std"] )
        stats =   ds.GetRasterBand(int(3)).GetStatistics(
                False,
                True)
        return ConsistencyStatistics(*stats)


class AmbiguityHeight:
    @classmethod
    def computeAll(cls,S1FilePaths:List[str],outfilePath):
        geom = cls.getGeomFromTif(S1FilePaths[0])
        lon,lat,height = geom[2:].mean(axis=0)
        cls.getAltAmbig(S1FilePaths,outfilePath,lon,lat,height)
        return lon,lat,height
    
    
    
    @classmethod
    def compute(cls,master,slaves:List[str]):
        geom = cls.getGeomFromTif(master)
        lon,lat,height = geom[2:].mean(axis=0)
        
        filePaths = [master]
        filePaths.extend(slaves)
        outfilePath = "AmbiguityHeight.log"
        cls.getAltAmbig(filePaths,outfilePath,lon,lat,height)
        return lon,lat,height
    
    @staticmethod
    def getGeomFromTif(filename:str):
        """ 
        read Sentienel1 images (.tiff) header 
        return geom (4 corner georef coordinate [i,j,lon,lat,height])
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
        N = len(gcps)
        gcps_array = gcps_array.reshape(N//21,21,5)
        geom = np.array([ gcps_array[i,j,2:] for i,j in order  ])
        ds = None
        return geom

    @staticmethod
    def getAltAmbig(filePaths:List[str],outfilePath:str,lon,lat,height):
        import otbApplication

        app = otbApplication.Registry.CreateApplication("SARAltAmbig")

        app.SetParameterStringList("inlist", filePaths)
        app.SetParameterFloat("lat", lat)
        app.SetParameterFloat("lon", lon)
        app.SetParameterFloat("height", height)
        app.EnableParameter("bistatic")
         
        app.SetParameterString("outfile", outfilePath)
        
        app.ExecuteAndWriteOutput()


class ExportConfiguration(Step):
    
    def __init__(self,
            inferno:Inferno.Inferno,
            callbackStepInfo = None,
            callbackProgress=None,
            stdout=None
        ) -> None:
        super().__init__(
            inferno = inferno,
            callbackStepInfo = callbackStepInfo,
            callbackProgress = callbackProgress,
            stdout = stdout,
        )
        self.inputConfigPath = None
        self.parametresPath = None 


    def __getParametresPath(self):
        inferno = self.inferno
        outputfolder = inferno.getOutputDir()
        parametresPath = os.path.join(outputfolder,"Parametres.yaml")
        return parametresPath

    def __getInputConfigPath(self):
        inferno = self.inferno
        outputfolder = inferno.getOutputDir()
        parametresPath = os.path.join(outputfolder,"inputConfig.yaml")
        return parametresPath

    def run(self):
        inputConfigPath = self.__getInputConfigPath()
        parametresPath = self.__getParametresPath()

        self.inferno.parameters.inputConfig.parametersFile = parametresPath
        self.printInfo(f'Create: {inputConfigPath}')
        self.inferno.exportInputConfig(filePath=inputConfigPath)

        self.printInfo(f'Create: {parametresPath}')
        self.inferno.exportParameters(fileName=parametresPath)

        self.inputConfigPath = inputConfigPath
        self.parametresPath = parametresPath
        pass


class ComputeQualiteIndicator(Step):
    def run(self):
        qualities = self.computeQuality()
        if len(qualities) == 0:
            return

        outputFilePath = os.path.join(self.inferno.getOutputDir(),"qualityIndicator.json")
        Tools.writeToJson(
            dictionary = qualities,
            outputFilePath = outputFilePath
        )

                
    def computeQuality(self):
        qualityIndicator = self.inferno.parameters.postTreatment.qualityIndicator
        keys = self._getKeys()
        qualities  = self.computeAllQuality()
        output = {}
        for key,value in qualities.items():
            output[key] = {_key:value[_key] for _key in keys}
        return output


    def _getKeys(self):
        qualityIndicator = self.inferno.parameters.postTreatment.qualityIndicator
        keys = [
            "masterImage",
            "slaveImage",
        ]
        if qualityIndicator.altitudeAmbiguity:
            keys.append("ambiguity_height")
        if qualityIndicator.criticalBase:
            keys.append("critical_baseline")
        if qualityIndicator.orthogonalBase:
            keys.append("orthobase")
        if qualityIndicator.recoveryRate:
            keys.append("recovery_rate")
        return keys

    def _getCouple(
        self,
        strategy:Inferno.TreatmentHelper.MasterImage,
        swath:str,
        polarization:CONSTANT.POLARIZATION,
        proposition_list:List[S1Product]
        ):
        couple = []
        if strategy.strategy == CONSTANT.MASTER_IMAGE.FIX:
            masterFile = strategy.masterImageProduct.location 
            patern  = os.path.join(masterFile,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
            masterFile = glob.glob(patern)[0]
            slaves = []
            for product in proposition_list:
                patern  = os.path.join(product.location,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
                slaves.extend(glob.glob(patern))
            slaves.remove(masterFile)
            print(slaves)
            couple = [[masterFile,ele] for ele in slaves]

        elif strategy.strategy == CONSTANT.MASTER_IMAGE.MOVING:
            couple = sorted(proposition_list,key=lambda x : x.date)
            slaves = []
            for product in couple:
                patern  = os.path.join(product.location,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
                slaves.extend(glob.glob(patern))
            couple = [ [ele[0],ele[1]] for ele in zip(slaves,slaves[1:])]

        return couple

    def computeAllQuality(self):
        output = {}
        strategy = self.inferno.parameters.treatment.masterImage
        swath = self.inferno.chosenPriorityProposition.chosenSwaths[0]
        polarization = self.inferno.chosenPriorityProposition.chosenPolarization
        proposition_list = self.inferno.chosenPriorityProposition.list

        couple = self._getCouple(
            strategy = strategy,
            swath = swath,
            polarization = polarization,
            proposition_list = proposition_list,
        )
        for i,paths in enumerate(couple):
            mean,std = QualityIndicator.InterferometricCouple.computeMean(
                        masterPath = paths[0],
                        slavePath = paths[1]
                        ) 
            output[i] = mean
        return output