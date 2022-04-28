from __future__ import annotations
from fileinput import filename
from posixpath import basename
from pprint import pprint
import sys,glob
from types import new_class
from typing import TYPE_CHECKING, Callable, Type
from unittest.util import sorted_list_difference


from script import Treatment
from script import CONSTANT, S1Product
from script import Tools 
from script import QualityIndicator

from script.ConfigParser import ROI
from script.Treatment import CropROI, DiapOtb, Step, stepInfo
if TYPE_CHECKING:
    from script import Inferno

from dataclasses import dataclass, field
import numpy as np
from abc import ABC, abstractclassmethod
from collections import namedtuple
from typing import List,Tuple



import datetime
import os

def reformatText(text):
    return " ".join(text.split()) 


description1 ="""
Group all products from the same satellite with the same orbit where the ROI (region of interest) is in a single swath."""

description2 ="""
Group all products from the same satellite with the same orbit where the ROI (region of interest) is between 2 consécutif products."""

description3 ="""
Group all products with the same orbit and the same orbit type (Ascending or Descending ) where the ROI (region of interest) is between 2 swaths of the same product.
(mix up S1A and S1B product)"""

description4 ="""
Group all products from the same satellite with the same orbit and the same orbit type (Ascending or Descending )
The ROI (region of interest) can be in multiple swaths.
The result interferogram may not includ the all ROI (region of interest) """

description1 = reformatText(description1)
description2 = reformatText(description2)
description3 = reformatText(description3)
description4 = reformatText(description4)


@dataclass
class TreatmentProduct():
    filePath:str
    filename:str
    missionId:str
    swath:str
    productType:str
    polarization:str
    dataStart: datetime.datetime 
    dataEnd: datetime.datetime

    @staticmethod
    def _parsename(filePath)->tuple:
        filename = os.path.basename(filePath)
        (missionId,
        swath    ,
        productType,
        polarization,
        dataStart,
        dataEnd,
        *_) = filename.split("-")
        dataStart = datetime.datetime.strptime(dataStart,"%Y%m%dt%H%M%S")
        dataEnd = datetime.datetime.strptime(dataEnd,"%Y%m%dt%H%M%S")
        return (filename,missionId, swath, productType, polarization, dataStart, dataEnd)

    @classmethod
    def fromPath(cls,filePath):
        parseEle = cls._parsename(filePath)
        return cls(filePath,*parseEle)

def formJson(JsonDict):
    class_name = JsonDict.pop("Scenario")
    res = eval(f'{class_name}')
    for key,value in JsonDict["id"].items():
        if key == "satellite":
            JsonDict["id"][key] = CONSTANT.SATELLITE[value]
        elif key == "orbitType":
            JsonDict["id"][key] = CONSTANT.ORBIT_TYPE[value]
        pass
    JsonDict["id"] = res.IdConstructor(**JsonDict["id"])
    
    products = []
    for product_dict in JsonDict["list"]:
        products.append(S1Product.S1Product._fromdict(product_dict))
    JsonDict["list"] = products
    JsonDict["chosenPolarization"] = CONSTANT.POLARIZATION[JsonDict["chosenPolarization"]]
    JsonDict["chosenPolarization"]
    return res(**JsonDict)

@dataclass
class Proposition(ABC):
    id:Tuple[str] # id[0] must be swathsChoises
    list:List[S1Product.S1Product]
    chosen:bool=False
    polarizationChoises:List[CONSTANT.POLARIZATION] = None
    chosenPolarization : CONSTANT.POLARIZATION = None

    swathsChoises:List[str] = field(default_factory=list)  
    chosenSwaths:List[str]  = field(default_factory=list)  
    chosenSwathsIsEdible : bool = False
    orbitType : CONSTANT.ORBIT_TYPE = CONSTANT.ORBIT_TYPE.ASC
    outputDir:str = ""
    needConcatenation : bool = False

    def toJson(self):
        output = {}
        output["Scenario"] = self.__class__.__name__
        output["id"] = dict(self.id._asdict())
        for key,value in output["id"].items():
            output["id"][key] = str(value)

        output["list"] = [prod._asdict() for prod in self.list]
        output["chosenPolarization"] = str(self.chosenPolarization)
        output["chosenSwaths"] = list(self.chosenSwaths)
        output["needConcatenation"] = self.needConcatenation
        return output

    def __post_init__(self):
        self.name = self.getName()

        tmp_polarizationChoises = set()
        for product in self.list:
            tmp_polarizationChoises.update(product.polarization)
        self.polarizationChoises = list(tmp_polarizationChoises)
        self.chosenPolarization = self.polarizationChoises[0]

        self.swathsChoises  =  self.id[0].split(" ")
        if isinstance(self.swathsChoises,str):
            self.swathsChoises = self.swathsChoises.split(' ')
        
        if not self.chosenSwaths:
            try:
                self.chosenSwaths = self.id.chosenSwath
            except Exception:
                self.chosenSwaths = []
        self.orbitType = self.list[0].orbitType
    

    def runConcatenate(self,filePaths:List[str],ouputDir:str,nodata):
        output = self._concatenate(filePaths,ouputDir,nodata)
        return output

    def _concatenate(self,filePaths:List[str],ouputDir:str) -> List[str]:
        return []

    @staticmethod
    def generateEleToContatenatesSwath(filePaths:List[str],NB_SWATH:int):
        # if strategy == CONSTANT.MASTER_IMAGE.MOVING:
        #     pattern = '/*/filtered_interferogram.tif'
        # if strategy == CONSTANT.MASTER_IMAGE.FIX:
        #     pattern = '/output_*/*_m_*/*_Ortho-Interferogram.tif'
        group_size = len(filePaths)//NB_SWATH
        filePaths = sorted(filePaths)
        filePaths:List[tuple] = list(zip(*(zip(*(iter(filePaths),) * group_size))))
        return filePaths

    @staticmethod
    def _concatenateElements(eleToConcatenate:List[Tuple[str]],ouputDir:str,nodata):
        outputFile = []
        for i,srcDSOrSrcDSTab in enumerate(eleToConcatenate):
            print(f"Concatenate {srcDSOrSrcDSTab} ")
            filename = os.path.basename(srcDSOrSrcDSTab[0])
            check =  os.path.basename(os.path.dirname(srcDSOrSrcDSTab[0]))
            try:
                basename = os.path.basename(filename)
                filename =  "_".join([str(int(check)),basename])
            except ValueError:
                filename =  os.path.basename(filename)
            
            # filename = f"{i}_{os.path.basename(srcDSOrSrcDSTab[0])}"
            destNameOrDestDS = os.path.join(ouputDir,filename)
            Treatment.Concatenate.concatenate(destNameOrDestDS=destNameOrDestDS,srcDSOrSrcDSTab=srcDSOrSrcDSTab,nodata=nodata)
            outputFile.append(destNameOrDestDS)
        return outputFile

    @classmethod
    def idxToSwathsChoises(cls,product:S1Product.S1Product,idx:List[int]): 
            swathsChoises = product.swath.split(" ")
            output = tuple([swathsChoises[ind] for ind in idx ])
            return output

    @classmethod
    def getName(cls)->str:
        return cls.__name__
        
    @classmethod
    def fromDict(cls,dict:dict[str,List[S1Product.S1Product]]):
        list_proposition :List[Proposition] = [cls(id=id,list=ele) for id,ele in dict.items()]
        return list_proposition

    @classmethod
    def generate(cls,
            inferno,
            chosonProduct:List[S1Product.S1Product])->List[Proposition]:

        dict = cls.generateProposition(inferno,chosonProduct)
        output = cls.fromDict(dict=dict)
        return output 

    @abstractclassmethod
    def generateProposition(cls,
            inferno ,
            chosonProduct:List[S1Product.S1Product]
        )->dict[str,List[S1Product.S1Product]] :
        ...

    @classmethod
    # @abstractclassmethod
    def treatment(self,
            inferno:Inferno.Inferno,
            callbackStepInfo: Callable[[Treatment.stepInfo],None] = None,
            callbackProgress: Callable[[int],None] = None,
            stdout=None):
            return []

    def getImagesList(self):
        filenames = []
        swaths = self.chosenSwaths
        polarization = self.chosenPolarization
        for swath in [swaths[0]]:
            for product in self.list:
                patern  = os.path.join(product.location,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
                filenames.extend(glob.glob(patern))
        return filenames

    def description(self):
        description = """ """
        return description

    @staticmethod
    def generate_filename_from_path(diapOTB_file,filePath):
        filename = filePath[len(diapOTB_file)+ (not diapOTB_file[-1]=="/"): ]
        tmp_folder =  filename.split("/")
        try:
            basename = os.path.basename(filename)
            folder_name = ""
            if len(tmp_folder)>2:
                folder_name = os.path.join(*tmp_folder[:-2])
            filename =  "_".join([str(int(tmp_folder[-2])),basename])
            filename = os.path.join(folder_name,filename)
        except ValueError:
            filename =  os.path.basename(filename)
        return filename

class Proposition1(Proposition):
    """ 
    id = (orbitNumber,satellite,swathName)
    """
    list_attribut_to_check = ["swath","orbitNumber","satellite"]
    IdConstructor = namedtuple("Id",list_attribut_to_check+["chosenSwath"])

    def __post_init__(self):
        super().__post_init__()
        self.chosenSwathsIsEdible = False

    @classmethod
    def getName(cls)->str:
        return "Scenario Type 1"

    @classmethod
    def generateProposition(cls, 
            inferno:Inferno.Inferno,
            chosonProduct:List[S1Product.S1Product]):
        '''
        P1 is all list of S1product with same orbitNumber,swath,satellite 
        and where ROI is fully inside the S1product 

        return P1 dict such as 
        output = {  id1:[S1product,...],
                    id2:[S1product,...],...}
        id1 is a tuple with orbitNumber,swath,satellite of the list
        '''
        count = {}
        list_attribut_to_check = cls.list_attribut_to_check
        ROI = inferno.parameters.inputConfig.ROI.geom
        for ele in chosonProduct:
            geom = ele.geom
            roiToSwath = Tools.roiToSwath(geom=geom,ROI=ROI,swaths=ele.swath,orbitType=ele.orbitType)
            if (Tools.roiInGeom(geom=geom,ROI=ROI) and 
                len(roiToSwath)==1 and (roiToSwath.min()>=0 and roiToSwath.max()<3) ):
                id = [getattr(ele,attr) for attr in list_attribut_to_check ]
                id.append(cls.idxToSwathsChoises(ele,roiToSwath.tolist()))
                id =  cls.IdConstructor(*id)
                if id in count:
                    count[id].append(ele)
                else:
                    count[id] = [ele]

        eleToRemove = []
        for id,listS1product in count.items():
            if len(listS1product) <2:
                eleToRemove.append(id)
                continue
        [count.pop(ele) for ele in eleToRemove]  
        return count

    def treatment(self,
            inferno:Inferno.Inferno,
            callbackStepInfo = None,
            callbackProgress=None,
            stdout=None):

        paths = self.generateListOfTreatmentProduct(inferno)

        diapOTB = Treatment.DiapOtb(
            inferno=inferno,
            orthoRectification=False,
            callbackProgress=callbackProgress,
            callbackStepInfo=callbackStepInfo)

        diapOTB.createConfigJsonFiles(paths=paths)
        diapOtbOutputFilePaths =  diapOTB.start()


        import itertools
        allOutputFiles = list(itertools.chain(*diapOtbOutputFilePaths))

        outputDir,cropOutputFilePaths = self.crop(
            inferno=inferno,
            inputFilePaths=allOutputFiles)

        self.outputDir = outputDir
        self.outputPaths = cropOutputFilePaths
        self.diapOtbOutputFilePaths = diapOtbOutputFilePaths
        return cropOutputFilePaths

    def crop(self,inferno:Inferno.Inferno,inputFilePaths:List[str]):
        outputDir = inferno.getOutputDir()
        outputDir = os.path.join(outputDir,CONSTANT.DIAPOTB_OUTPUTDIR)

        diapOTB_file = inferno.getDiapOtbOutputDir()
        ROI = inferno.parameters.inputConfig.ROI
        ulx = ROI.upperLeftX
        lrx = ROI.lowerRigthX
        lry = ROI.upperLeftY
        uly = ROI.lowerRigthY


        outputFile  = []
        for filePath in inputFilePaths:
            # filename = filePath[len(diapOTB_file)+ (not diapOTB_file[-1]=="/"): ]
            # check =  filename.split("/")[-2]
            # try:
            #     basename = os.path.basename(filename)
            #     filename =  "_".join([str(int(check)),basename])
            # except ValueError:
            #     filename =  os.path.basename(filename)
            filename = self.generate_filename_from_path(diapOTB_file,filePath)
            outputFilePath = os.path.join(outputDir,filename)
            outputFilePath = Treatment.CropROI.orthoRectificationExtractROI(
                filePath = filePath,
                outputFilePath = outputFilePath,
                ulx = ulx,
                lrx = lrx,
                lry = lry,
                uly = uly,
            )
            outputFile.append(outputFilePath)
        return outputDir,outputFile

    def generateListOfTreatmentProduct(self,inferno:Inferno.Inferno)->List[TreatmentProduct]:
        import glob,os
        proposition = self
        swath = proposition.chosenSwaths[0]
        
        polarization = proposition.chosenPolarization
        filenames = []

        if inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.FIX:
            masterFile = inferno.parameters.treatment.masterImage.masterImageProduct.location
            patern  = os.path.join(masterFile,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
            filenames.extend(glob.glob(patern))
            
        elif inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.MOVING:
            for product in proposition.list:
                patern  = os.path.join(product.location,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
                filenames.extend(glob.glob(patern))
        
        treatmentProducts = [TreatmentProduct.fromPath(filename) for filename in filenames]
        treatmentProductsSorted = sorted(treatmentProducts,key=lambda x:x.dataStart)
        paths = [ele.filePath for ele in treatmentProductsSorted]
        return paths

    @classmethod
    def description(self):
        return description1

class Proposition2(Proposition):
    list_attribut_to_check = ["swath","orbitNumber","satellite"]
    IdConstructor = namedtuple("Id",list_attribut_to_check+["chosenSwath"])

    def __post_init__(self):
        super().__post_init__()
        self.chosenSwathsIsEdible = False
        self.needConcatenation = True

    @classmethod
    def getName(cls)->str:
        return "Scenario Type 2"
        
    @classmethod
    def generateProposition(cls, 
            inferno:Inferno.Inferno,
            chosonProduct:List[S1Product.S1Product]):
        '''
        ROI in 2 successive S1 product (same orbitNumber,satellite, swath)
        output = {  id1:[S1product,...],
                    id2:[S1product,...],...}
        id1 is a tuple with (orbitNumber,satellite,swath) of the list
        '''
        count = {}
        list_attribut_to_check = cls.list_attribut_to_check
        IdConstructor = cls.IdConstructor

        ROI = inferno.parameters.inputConfig.ROI.geom
        for ele in chosonProduct:
            geom = ele.geom
            roiToSwath:np.ndarray = Tools.roiToSwath(geom=geom,ROI=ROI,swaths=ele.swath,orbitType=ele.orbitType)
            if  ( Tools.roiInGeom(geom=geom,ROI=ROI)==False and  len(roiToSwath)==1 and 
                    (roiToSwath.min()>=0 and roiToSwath.max()<3) ): 
                id = [getattr(ele,attr) for attr in list_attribut_to_check ]
                id.append(cls.idxToSwathsChoises(ele,roiToSwath.tolist()))
                id = IdConstructor(*id)
                if id in count:
                    count[id].append(ele)
                else:
                    count[id] = [ele]

        eleToRemove = []
        for id,listS1product in count.items():
            if len(listS1product) <4:
                eleToRemove.append(id)
                continue

            listS1product = sorted(listS1product,key=lambda x:x.date)
            count[id] = listS1product

            if len(listS1product)%2 == 0:
                continue

            if (listS1product[1].date-listS1product[0].date)<datetime.timedelta(days=1):
                count[id] = listS1product[1:]
            else:
                count[id] = listS1product[:-1]

        [count.pop(ele) for ele in eleToRemove]  
        return count


    def treatment(self,
        inferno:Inferno.Inferno,
        callbackStepInfo = None,
        callbackProgress=None,
        stdout=None):

        paths = self.generateListOfTreatmentProduct(inferno)

        diapOTB = Treatment.DiapOtb(
            inferno=inferno,
            orthoRectification=False,
            callbackProgress=callbackProgress,
            callbackStepInfo=callbackStepInfo)

        for i,listPath in enumerate(paths):  
            diapOTB.createConfigJsonFiles(paths=listPath,prefix=f'P{i}')

        diapOtbOutputFilePaths =  diapOTB.start()

        import itertools
        allOutputFiles = list(itertools.chain(*diapOtbOutputFilePaths))

        outputDir,cropOutputFilePaths = self.crop(
            inferno=inferno,
            inputFilePaths=allOutputFiles)

        self.outputDir = outputDir
        self.outputPaths = cropOutputFilePaths
        self.diapOtbOutputFilePaths = diapOtbOutputFilePaths
        return cropOutputFilePaths
        

    def crop(self,inferno:Inferno.Inferno,inputFilePaths:List[str]):
        _outputDir = inferno.getWorkingDir()
        _tmpDir = inferno.getTmpFolder()
        _diapOTB_file = inferno.getDiapOtbOutputDir()
        outputDir = os.path.join(_outputDir,_tmpDir,CONSTANT.EXTRACT_ROI_FOLDER)

        ROI = inferno.parameters.inputConfig.ROI
        ulx = ROI.upperLeftX
        lrx = ROI.lowerRigthX
        lry = ROI.upperLeftY
        uly = ROI.lowerRigthY


        outputFile  = []
        for filePath in inputFilePaths:
            # filename = filePath[len(_diapOTB_file)+ (not _diapOTB_file[-1]=="/"): ]
            filename = self.generate_filename_from_path(_diapOTB_file,filePath)

            outputFilePath = os.path.join(outputDir,filename)
            Tools.createAllDirToFile(outputFilePath)
            outputFilePath = Treatment.CropROI.orthoRectificationExtractROI(
                filePath = filePath,
                outputFilePath = outputFilePath,
                ulx = ulx,
                lrx = lrx,
                lry = lry,
                uly = uly,
            )
            outputFile.append(outputFilePath)
        return outputDir,outputFile

    @staticmethod
    def generateListOfTreatmentProduct(inferno:Inferno.Inferno)->List[List[str],List[str]]:
        import glob,os
        proposition = inferno.chosenPriorityProposition 
        swath = proposition.chosenSwaths[0] # exemple: [iw0,iw1]
        polarization = proposition.chosenPolarization

        # get all chosen images paths sorted according to dates
        filenames = []
        for product in proposition.list:
            patern  = os.path.join(product.location,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
            filenames.extend(glob.glob(patern))
        treatmentProducts = [TreatmentProduct.fromPath(filename) for filename in filenames]
        treatmentProductsSorted = sorted(treatmentProducts,key=lambda x:x.dataStart)

        # separate into 2 list according to "orbit" 
        treatmentProducts1 =  treatmentProductsSorted[::2]       
        treatmentProducts2 =  treatmentProductsSorted[1::2]       

        if inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.FIX:
            masterFile = inferno.parameters.treatment.masterImage.masterImageProduct.location
            patern  = os.path.join(masterFile,f"measurement/*-{swath.lower()}-*-{polarization.name.lower()}-*.tiff")
            _filenames = (glob.glob(patern))
            ind = treatmentProducts.index(TreatmentProduct.fromPath(_filenames[0]))
            output =  [[treatmentProducts1[ind].filePath],[treatmentProducts2[ind].filePath]]

        if inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.MOVING:
            output = []
            list1  = [ele.filePath for ele in  treatmentProducts1]
            list2  = [ele.filePath for ele in  treatmentProducts2]
            output.append(list1)
            output.append(list2)

            
        return output

    @staticmethod
    def generateEleToContatenates(filePaths:List[str]):
        # if strategy == CONSTANT.MASTER_IMAGE.MOVING:
        #     pattern = '/*/filtered_interferogram.tif'
        # if strategy == CONSTANT.MASTER_IMAGE.FIX:
        #     pattern = '/output_*/*_m_*/*_Ortho-Interferogram.tif'
        group_size = len(filePaths)//2
        filePaths = sorted(filePaths)
        filePaths:List[tuple] = list(zip(*(zip(*(iter(filePaths),) * group_size))))

        return filePaths


    def _concatenate(self,filePaths:List[str],ouputDir:str,nodata):
        eleToConcatenate = self.generateEleToContatenates(
            filePaths=filePaths)
            
        outputFiles = self._concatenateElements(
            eleToConcatenate=eleToConcatenate,
            ouputDir=ouputDir,
            nodata=nodata)
        return outputFiles 

    @classmethod
    def description(self):
        return description2

class Proposition3(Proposition):
    NB_SWATH = 2
    list_attribut_to_check = ["swath","orbitType","orbitNumber"]
    IdConstructor = namedtuple("Id",list_attribut_to_check+["chosenSwath"])

    def __post_init__(self):
        super().__post_init__()
        self.chosenSwathsIsEdible = False
        self.needConcatenation = True

    @classmethod
    def getName(cls)->str:
        return "Scenario Type 3"

    @classmethod
    def generateProposition(cls, 
            inferno:Inferno.Inferno,
            chosonProduct:List[S1Product.S1Product]):
        '''
        ROI in 2 swath 
        '''
        count:dict[tuple,List[S1Product.S1Product]] = {}
        # list_attribut_to_check = []
        # list_attribut_to_check.append("swath")
        # list_attribut_to_check.append("orbitType")
        # list_attribut_to_check.append("orbitNumber")
        # IdConstructor = namedtuple("Id",list_attribut_to_check+["chosenSwath"])
        list_attribut_to_check = cls.list_attribut_to_check
        IdConstructor = cls.IdConstructor

        ROI = inferno.parameters.inputConfig.ROI.geom
        for ele in chosonProduct:
            geom = ele.geom
            roiInSwath:np.ndarray = Tools.roiToSwath(geom=geom,ROI=ROI,swaths=ele.swath,orbitType=ele.orbitType)
            if  (   Tools.roiInGeom(geom=geom,ROI=ROI)==True and
                    (len(roiInSwath)== cls.NB_SWATH) and 
                    (roiInSwath.min()>=0 and roiInSwath.max()<3) ):   # Roi in 2 swath of same S1product
                id = [getattr(ele,attr) for attr in list_attribut_to_check ]
                id.append(cls.idxToSwathsChoises(ele,roiInSwath.tolist()))

                id  = IdConstructor(*id)
                if id in count:
                    count[id].append(ele)
                else:
                    count[id] = [ele]

        eleToRemove = []
        for id,listS1product in count.items():
            newlist = []
            for sat in CONSTANT.SATELLITE:
                listS1productSat = [ele for ele in listS1product if ele.satellite==sat ]
                if len(listS1productSat) >=2:
                    newlist.extend(listS1productSat)
                    continue

            if len(newlist)==0:
                eleToRemove.append(id)
            count[id] = newlist
        [count.pop(ele) for ele in eleToRemove]  
        return count


    def treatment(self,
        inferno:Inferno.Inferno,
        callbackStepInfo = None,
        callbackProgress=None,
        stdout=None):

        paths = self.generateListOfTreatmentProduct(inferno)


        diapOTB = Treatment.DiapOtb(
            inferno=inferno,
            orthoRectification=True,
            callbackProgress=callbackProgress,
            callbackStepInfo=callbackStepInfo)


        self._createConfigJson(diapOTB,paths=paths)
        diapOtbOutputFilePaths =  diapOTB.start()

        import itertools
        allOutputFiles = list(itertools.chain(*diapOtbOutputFilePaths))

        outputDir,cropOutputFilePaths = self.crop(
            inferno=inferno,
            inputFilePaths=allOutputFiles)

        self.outputDir = outputDir
        self.outputPaths = cropOutputFilePaths
        self.diapOtbOutputFilePaths = diapOtbOutputFilePaths
        return cropOutputFilePaths


    def crop(self,inferno:Inferno.Inferno,inputFilePaths:List[str]):
        _outputDir = inferno.getWorkingDir()
        _tmpDir = inferno.getTmpFolder()
        _diapOTB_file = inferno.getDiapOtbOutputDir()
        outputDir = os.path.join(_outputDir,_tmpDir,CONSTANT.EXTRACT_ROI_FOLDER)

        ROI = inferno.parameters.inputConfig.ROI
        ulx = ROI.upperLeftX
        lrx = ROI.lowerRigthX
        lry = ROI.upperLeftY
        uly = ROI.lowerRigthY


        outputFile  = []
        for filePath in inputFilePaths:
            # filename = filePath[len(_diapOTB_file)+ (not _diapOTB_file[-1]=="/"): ]
            filename = self.generate_filename_from_path(_diapOTB_file,filePath)
            outputFilePath = os.path.join(outputDir,filename)
            Tools.createAllDirToFile(outputFilePath)
            outputFilePath = Treatment.CropROI.orthoRectificationExtractROI(
                filePath = filePath,
                outputFilePath = outputFilePath,
                ulx = ulx,
                lrx = lrx,
                lry = lry,
                uly = uly,
            )
            outputFile.append(outputFilePath)
        return outputDir,outputFile


    def _createConfigJson(self,diapOTB:Treatment.DiapOtb,paths:dict):
        for key,listPath in paths.items():
            diapOTB.createConfigJsonFiles(
                paths=listPath,
                prefix="_".join([str(ele) for ele in key] ) )

    @staticmethod
    def generateListOfTreatmentProduct(inferno:Inferno.Inferno)->dict[str,List[str]]:
        """ 
        return dict[(satellite,swath) , List[path_image]]
        """

        import glob,os
        proposition = inferno.chosenPriorityProposition 
        
        swaths = proposition.chosenSwaths # exemple: [0,1]
        polarization = proposition.chosenPolarization
        output = {}
        
        globalPatern = "measurement/*-{swath}-*-{polarization}-*.tiff"
        for swath in swaths:
            filenames = []
            # scelect Produts according to swath

            if inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.FIX:
                masterFile = inferno.parameters.treatment.masterImage.masterImageProduct.location
                patern  = os.path.join(
                    masterFile,
                    globalPatern.format(swath=swath.lower(),polarization=polarization.name.lower()) )
                filenames.extend(glob.glob(patern))
                
            elif inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.MOVING:
                for product in proposition.list:
                    patern  = os.path.join(
                        product.location,
                        globalPatern.format(swath=swath.lower(),polarization=polarization.name.lower()))
                    filenames.extend(glob.glob(patern))
                    if len(filenames)==0:continue
            
            treatmentProducts = [TreatmentProduct.fromPath(filename) for filename in filenames]
            treatmentProductsSorted = sorted(treatmentProducts,key=lambda x:x.dataStart)
            paths = [ele.filePath for ele in treatmentProductsSorted]
            id = (swath.lower(),)
            output[id] = paths.copy()
        return output


    def _concatenate(self,filePaths:List[str],ouputDir:str,nodata):
        eleToConcatenate = self.generateEleToContatenatesSwath(
            filePaths=filePaths,
            NB_SWATH=self.NB_SWATH)
            
        outputFiles = self._concatenateElements(
            eleToConcatenate=eleToConcatenate,
            ouputDir=ouputDir,
            nodata=nodata)
        return outputFiles 

    @classmethod
    def description(self):
        return description3

class Proposition4(Proposition):
    list_attribut_to_check = ["swath","orbitNumber","satellite"]
    IdConstructor = namedtuple("Id",list_attribut_to_check+["Geom","chosenSwath"])

    @classmethod
    def getName(cls)->str:
        return "Scenario Type 4"


    def __post_init__(self):
        super().__post_init__()
        self.chosenSwathsIsEdible = False
        self.needConcatenation = True

    @classmethod
    def generateProposition(cls, 
            inferno:Inferno.Inferno,
            chosonProduct:List[S1Product.S1Product]):
        count : dict[str,list]= {}
        list_attribut_to_check = cls.list_attribut_to_check
        IdConstructor = cls.IdConstructor

        ROI = inferno.parameters.inputConfig.ROI.geom
        for ele in chosonProduct:
                geom = ele.geom
                roiInSwath:np.ndarray = Tools.roiToSwath(geom=geom,ROI=ROI,swaths=ele.swath,orbitType=ele.orbitType)
                roiInSwath = roiInSwath[ np.logical_and(roiInSwath>=0,roiInSwath<3) ]

                id = [getattr(ele,attr) for attr in list_attribut_to_check ]
                id.append( (tuple(ele.geom.round(decimals=1).flatten().tolist())) )
                id.append(cls.idxToSwathsChoises(ele,roiInSwath.tolist()))
                id = IdConstructor(*id)
                if id in count:
                    count[id].append(ele)
                else:
                    count[id] = [ele]

        eleToRemove = [id for id,listS1product in count.items() if len(listS1product) <2]
        [count.pop(ele) for ele in eleToRemove]  

        return count


    def treatment(self,
        inferno:Inferno.Inferno,
        callbackStepInfo = None,
        callbackProgress=None,
        stdout=None):


        paths = self.generateListOfTreatmentProduct(inferno)

        diapOTB = Treatment.DiapOtb(
            inferno=inferno,
            orthoRectification=True,
            callbackProgress=callbackProgress,
            callbackStepInfo=callbackStepInfo)
        self._createConfigJson(diapOTB,paths=paths)
        diapOtbOutputFilePaths =  diapOTB.start()

        import itertools
        allOutputFiles = list(itertools.chain(*diapOtbOutputFilePaths))

        outputDir,cropOutputFilePaths = self.crop(
            inferno=inferno,
            inputFilePaths=allOutputFiles)

        self.outputDir = outputDir
        self.outputPaths = cropOutputFilePaths
        self.diapOtbOutputFilePaths = diapOtbOutputFilePaths
        return cropOutputFilePaths



    def crop(self,inferno:Inferno.Inferno,inputFilePaths:List[str]):
        _outputDir = inferno.getWorkingDir()
        _tmpDir = inferno.getTmpFolder()
        _diapOTB_file = inferno.getDiapOtbOutputDir()
        outputDir = os.path.join(_outputDir,_tmpDir,CONSTANT.EXTRACT_ROI_FOLDER)

        ROI = inferno.parameters.inputConfig.ROI
        ulx = ROI.upperLeftX
        lrx = ROI.lowerRigthX
        lry = ROI.upperLeftY
        uly = ROI.lowerRigthY


        outputFile  = []
        for filePath in inputFilePaths:
            # filename = filePath[len(_diapOTB_file)+ (not _diapOTB_file[-1]=="/"): ]
            filename = self.generate_filename_from_path(_diapOTB_file,filePath)
            outputFilePath = os.path.join(outputDir,filename)
            Tools.createAllDirToFile(outputFilePath)
            outputFilePath = Treatment.CropROI.orthoRectificationExtractROI(
                filePath = filePath,
                outputFilePath = outputFilePath,
                ulx = ulx,
                lrx = lrx,
                lry = lry,
                uly = uly,
            )
            outputFile.append(outputFilePath)
        return outputDir,outputFile


    def _createConfigJson(self,diapOTB:Treatment.DiapOtb,paths:dict):
        for key,listPath in paths.items():
            diapOTB.createConfigJsonFiles(
                paths=listPath,
                prefix="_".join([str(ele) for ele in key] ) )
   

    def generateListOfTreatmentProduct(self,inferno:Inferno.Inferno)->dict[str,List[str]]:
        """ 
        return dict[(satellite,swath) , List[path_image]]
        """

        import glob,os
        proposition = self
        swaths = self.chosenSwaths # exemple: [0,1]
        polarization = self.chosenPolarization
        satellite = self.id.satellite
        output = {}
        
        # globalPatern = f"measurement/{satellite}-iw{swath.lower()}-*-{polarization.name.lower()}-*.tiff"
        globalPatern = "measurement/{satellite}-{swath}-*-{polarization}-*.tiff"
        for swath in swaths:
            filenames = []
            # scelect Produts according to swath

            if inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.FIX:
                masterDate =  inferno.parameters.treatment.masterImage.masterImageProduct.date
                tmplist = [ele for ele in proposition.list if ele.satellite==satellite]
                tmplist = sorted(tmplist,key=lambda x: abs(x.date-masterDate))
                masterFile = tmplist[0].location
                patern  = os.path.join(
                    masterFile,
                    globalPatern.format(satellite=str(satellite).lower(), swath=swath.lower(),polarization=polarization.name.lower()) )
                filenames.extend(glob.glob(patern))
                
            elif inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.MOVING:
                for product in proposition.list:
                    patern  = os.path.join(
                        product.location,
                        globalPatern.format(satellite=str(satellite).lower(), swath=swath.lower(),polarization=polarization.name.lower()))
                    filenames.extend(glob.glob(patern))
            
            treatmentProducts = [TreatmentProduct.fromPath(filename) for filename in filenames]
            treatmentProductsSorted = sorted(treatmentProducts,key=lambda x:x.dataStart)
            paths = [ele.filePath for ele in treatmentProductsSorted]
            id = (satellite ,swath.lower())
            output[id] = paths.copy()
        return output


    def _concatenate(self,filePaths:List[str],ouputDir:str,nodata):
        if len(self.chosenSwaths)<2:
            outputFiles = self.moveFiles(filePaths,ouputDir)
            return outputFiles

        eleToConcatenate = self.generateEleToContatenatesSwath(
            filePaths=filePaths,
            NB_SWATH=len(self.chosenSwaths))
            
        # outputFiles = self._concatenateElements(
        #     eleToConcatenate=eleToConcatenate,
        #     ouputDir=ouputDir)
        outputFiles = self._concatenateElements(
            eleToConcatenate=eleToConcatenate,
            ouputDir=ouputDir,
            nodata=nodata)
        return outputFiles 


    def moveFiles(self,filePaths:List[str],ouputDir:str):
        outputFiles = []
        for file in filePaths:
            filename = os.path.basename(file)
            outputfilepath = os.path.join(ouputDir,filename)
            Tools.createAllDirToFile(outputfilepath)
            os.replace(file,outputfilepath)
            outputFiles.append(outputfilepath)
        return outputFiles


    @classmethod
    def description(self):
        return description4

from typing import List
class PropositionList(List[Proposition]):
    def __init__(self,PropositionType:type[Proposition1],*args):
        list.__init__(self, *args)
        self.propositionType = PropositionType

    def getName(self)->str:
        return self.propositionType.getName()

    def description(self)->str:
        return self.propositionType.description()
