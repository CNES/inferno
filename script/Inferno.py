# Copyright 2022 CNES 
from dataclasses import dataclass, field
import dataclasses 
import os
from typing import Callable, Dict, Type
from enum import Enum,auto,unique
# from importlib_metadata import sys
import yaml
import numpy as np
import sys

from script import ConfigParser
from script import S1Product 
from script import CONSTANT
from script import Scenarios
from script import Treatment
from script import Tools
from script.Treatment import Calibration, Step, stepInfo
from collections import namedtuple
from typing import List
import logging


OutputSizeEstimation = namedtuple("OutputSizeEstimation",["totalSize","downloadSize"])

@dataclass
class OptionWithParameters():
    activate : bool = False

@dataclass
class SnapHuParameters(OptionWithParameters):
    class StatisticalCost(Enum):
        TOPO = auto()
        DEFO = auto()
        SMOOTH = auto()
        NOSTATCOSTS = auto()

        def __str__(self) -> str:
            return self.name
        
        def toOptionKey(self):
            if self is SnapHuParameters.StatisticalCost.TOPO:
                return "-t"
            elif self is SnapHuParameters.StatisticalCost.DEFO:
                return "-d"
            elif self is SnapHuParameters.StatisticalCost.SMOOTH:
                return "-s"
            elif self is SnapHuParameters.StatisticalCost.NOSTATCOSTS:
                return "-p"


    class InitializationAlgorithm(Enum):
        MST = auto()
        MCF = auto()

        def __str__(self) -> str:
            return self.name

        def toOptionKey(self):
            if self is SnapHuParameters.InitializationAlgorithm.MST:
                return "--mst"
            elif self is SnapHuParameters.InitializationAlgorithm.MCF:
                return "--mcf"

    def parse(self):
        options = []
        options.append(self.initializationAlgorithm.toOptionKey())
        
        options.append(self.statisticalCost.toOptionKey())
        if self.statisticalCost == SnapHuParameters.StatisticalCost.NOSTATCOSTS:
            options.append(self.lpNorm)
        return options


    # singleTile : bool = False
    # nproc : int = 1
    lpNorm : float = 2.0
    initializationAlgorithm : InitializationAlgorithm =  InitializationAlgorithm.MST
    statisticalCost : StatisticalCost = StatisticalCost.DEFO

    def __post_init__(self):
        if isinstance(self.initializationAlgorithm,str):
            self.initializationAlgorithm = SnapHuParameters.InitializationAlgorithm[self.initializationAlgorithm]
        if isinstance(self.statisticalCost,str):
            self.statisticalCost = SnapHuParameters.StatisticalCost[self.statisticalCost]
    pass

@dataclass
class Orthorectification(OptionWithParameters):
    spacingXY:float = 0.0001

@dataclass
class PhaseFiltering(OptionWithParameters):
    filteredInterferogramMlran : int = 4
    filteredInterferogramMlazi : int = 4

    def __post_init__(self):
        self.filteredInterferogramMlran = int(self.filteredInterferogramMlran)
        self.filteredInterferogramMlazi = int(self.filteredInterferogramMlran)

class PostTreatmentHelper():
    @dataclass
    class QualityIndicator():
        meanConsistency :bool = False 
        altitudeAmbiguity :bool = False
        criticalBase :bool = False
        orthogonalBase :bool = False
        recoveryRate :bool = False
        # phaseDiscontinuity :bool = False
        # residue :bool = False
        # diachronism :bool = False

    @dataclass
    class CoregistrationPrecision():
        coregistrationPrecision : bool = False


    @dataclass
    class ImageComparison():
        imageComparison : bool = False
        interferogramsDifferences : bool = False
        videoFlow : bool = False

class TreatmentHelper():
    @dataclass
    class MasterImage():
        strategy   : CONSTANT.MASTER_IMAGE = CONSTANT.MASTER_IMAGE.FIX
        masterImageProduct    :S1Product.S1Product = None 

        def __post_init__(self):
            if not isinstance(self.strategy,CONSTANT.MASTER_IMAGE):
                self.strategy = CONSTANT.MASTER_IMAGE[self.strategy.upper()]

        def getFilePath(self,productDir, swath):
            pass

        def _asdict(self):
            output = {}
            output["strategy"] = str(self.strategy)
            if self.masterImageProduct is None:
                output["masterImageProduct"] = None
            else:
                output["masterImageProduct"] = self.masterImageProduct.name
            return output


        @classmethod
        def _fromdict(cls,listS1:List[S1Product.S1Product],output):          
            output["strategy"] = CONSTANT.MASTER_IMAGE[output["strategy"]]
            for ele in listS1:
                if ele.name == output["masterImageProduct"]:
                    output["masterImageProduct"] = ele
                    break
            return cls(**output)

    @dataclass
    class AmplitudePhase:
        activate : bool = False
        orthorectification : bool = False  

        def run(
            self,
            listProduct:List[S1Product.S1Product],
            outputDir:str,
            polarization: CONSTANT.POLARIZATION,
            chosenSwath:List[str] = None,
            callbackStepInfo: Callable[[stepInfo],None]=None,
            callbackProgress: Callable[[int],None]=None,
            ):

            outputAmpliPhaseFiles = []
            _stepInfo = stepInfo(description="Generate Amplitude Phase Images",maxProgress=0) 
            if callbackStepInfo is not None:
                if callbackProgress is not None:
                    _stepInfo.maxProgress = len(listProduct)
                callbackStepInfo(_stepInfo)               


            for indProduct,product in enumerate(listProduct,start=1):

                _outputFile = Treatment.AmpliPhase.ampliPhaseFromS1Product(
                    product=product,
                    outputDir=outputDir,
                    chosenSwath=chosenSwath,
                    polarization = polarization,
                )
                outputAmpliPhaseFiles.extend(_outputFile)
                if callbackProgress is not None:
                    callbackProgress(indProduct)


            if self.orthorectification:
                _stepInfo = stepInfo(description="Amplitude Phase: Orthorectification",maxProgress=0) 
                if callbackStepInfo is not None:
                    if callbackProgress is not None:
                        _stepInfo.maxProgress = len(outputAmpliPhaseFiles)
                    callbackStepInfo(_stepInfo)      
                if callbackProgress is not None:
                    callbackProgress(indProduct)

                for indFile,file in enumerate(outputAmpliPhaseFiles, start=1):
                    if callbackProgress is not None:
                        callbackProgress(indProduct)
                    Treatment.OrthoRectification.orthoRectification(
                        inFile=file)

    @dataclass
    class CreationOption():
        orthorectification                  : bool = True
        phaseFiltering                      : PhaseFiltering = PhaseFiltering()
        phaseUnwrapping                     : SnapHuParameters = SnapHuParameters()
        # phaseUnwrapping                     : bool = False
        sigma0ComplexAmplitudeCalibration   : bool = False
        logSigma0ComplexAmplitudeCalibration   : bool = False

        # antiSpeckle                         : bool = False
        # orthorectification                  : Orthorectification = Orthorectification()
        # s2GridProjection                    : bool = False

        def __post_init__(self):
            # getion du fromDict (a changer)
            if not isinstance(self.phaseFiltering,PhaseFiltering):
                self.phaseFiltering = PhaseFiltering(**(self.phaseFiltering))
            if not isinstance(self.phaseUnwrapping,SnapHuParameters):
                self.phaseUnwrapping = SnapHuParameters(**(self.phaseUnwrapping))
            
            # if not isinstance(self.orthorectification,Orthorectification):
            #     self.orthorectification = Orthorectification(**(self.orthorectification))

class ParametersHelper():
    class Common():
        def fromDict(self,dict:dict):
            for attr,constructor in self.__class__.__annotations__.items():
                if attr in dict: 
                    setattr(self,attr,constructor(**dict[attr]))
        
        def toDict(self)->dict:
            import dataclasses
            def dict_factory(data):
                output = []
                for ele in data:
                    if isinstance(ele[1],Enum):
                        output.append( (ele[0],ele[1].name) )
                    else:
                        output.append(ele)
                return dict(output)

            return dataclasses.asdict(self,dict_factory=dict_factory)

    @dataclass
    class Treatment(Common):
        masterImage : TreatmentHelper.MasterImage = TreatmentHelper.MasterImage()
        creationOption :TreatmentHelper.CreationOption = TreatmentHelper.CreationOption()
        amplitudePhase :TreatmentHelper.AmplitudePhase = TreatmentHelper.AmplitudePhase()

        def toDict(self) -> dict:
            output = super().toDict()
            output.pop("masterImage")
            return output

    @dataclass
    class PostTreatment(Common):
        qualityIndicator:PostTreatmentHelper.QualityIndicator = PostTreatmentHelper.QualityIndicator()
        # coregistrationPrecision:PostTreatmentHelper. CoregistrationPrecision = PostTreatmentHelper.CoregistrationPrecision()
        # imageComparison:PostTreatmentHelper.ImageComparison = PostTreatmentHelper.ImageComparison()

@dataclass
class Parameters():
    inputConfig : ConfigParser.InputConfig = ConfigParser.InputConfig()
    treatment     : ParametersHelper.Treatment      = ParametersHelper.Treatment()  
    postTreatment : ParametersHelper.PostTreatment  = ParametersHelper.PostTreatment() 
    provider : str = "" 
        
    def toDict(self)-> dict:
        output = {}
        # output["provider"] = self.provider.name
        output["treatment"] = self.treatment.toDict()
        output["postTreatment"] = self.postTreatment.toDict()
        return output
    
    def fromDict(self,dict:Dict):
        # parameters.provider = CONSTANT.PROVIDER[dict["provider"]]
        self.treatment.fromDict(dict["treatment"])
        self.postTreatment.fromDict(dict["postTreatment"])

    def write(self,fileName="Parameters.yaml"):
        '''
        Export Parameters to a YAML file
        '''
        dictionary = self.toDict()
        with open(f'{fileName}', 'w') as file:
            yaml.dump(dictionary,file,sort_keys=False)

    def read(self,fileName="Parameters.yaml"):
        with open(f'{fileName}', 'r') as file:
            dict = yaml.safe_load(file)
        self.fromDict(dict)

@dataclass
class Inferno():
    parameters : Parameters = Parameters()
    
    requestResults  :S1Product.InfernoProducts = None
    chosenResults   :List[S1Product.S1Product] = None
    priorityProposition     :List[List[Scenarios.Proposition]] = None 
    chosenPriorityProposition   : Scenarios.Proposition = None
    treatmentProducts :List[Scenarios.TreatmentProduct] = None

    interferogramPaths:List[Scenarios.TreatmentProduct] = None
    filteredInterferogramPaths:List[Scenarios.TreatmentProduct] = None
    unwrapedInterferogramPaths:List[Scenarios.TreatmentProduct] = None
    runLater = False 

    def runInCommandeLineHAL(self):
        txt = """
#PBS -N {jobname}
#PBS -l select=1:ncpus=24:mem=60000mb:os=rh7
#PBS -l walltime=24:00:00
#PBS -M {email}
#PBS -m e
module purge
export MODULEPATH=/work/scratch/usseglg/Modules_DiapOTB/modulefiles:$MODULEPATH
module load diapOTB/v1.1.0
conda activate /work/scratch/migelada/envs_conda/inferno
python -s {installDir}/main.py -e {exeJson}
        """
        return txt

    def runLater_ExportHAL(self):
        # def displayInfo(fileName):
        #     print("qsub {}".format(fileName))

        outputFile = self.runLater_Export()
        txt = self.runInCommandeLineHAL()
        auth = self.parameters.inputConfig.getProviderAuth()

        email = ""
        if auth.provider == CONSTANT.PROVIDER.PEPS:
            email = auth.id
        else:
            email = ""

        txt = txt.format(jobname="INFERNO",email=email,exeJson=outputFile,installDir=self.getInstallDir())
        filepath = os.path.join(
            self.getOutputDir(),
            "runHal.sh",
        )
        with open(filepath,"w") as f:
            f.write(txt)

        print("Run the command: \n \t qsub {}".format(filepath))

    def runLater_Export(self):
        def displayInfo(fileName):
            print("To run treatments, run the command below:")
            print(f"\t inferno -e {fileName}")
        Treatment.CreateDir(inferno=self).run()
        exportConfiguration = Treatment.ExportConfiguration(inferno=self)
        exportConfiguration.run()

        output_dict = {}
        output_dict["Parameters"] = exportConfiguration.parametresPath
        output_dict["inputConfig"] = exportConfiguration.inputConfigPath
        output_dict.update(self.exportAuth())
            

        output_dict["masterImage"] = self.parameters.treatment.masterImage._asdict()
        output_dict["scenario"] = self.chosenPriorityProposition.toJson()
        outputFilePath = os.path.join(self.getOutputDir(),"ExecConfig.json")
        print(f'Create: {outputFilePath}')
        Tools.writeToJson(dictionary = output_dict, outputFilePath = outputFilePath)
        displayInfo(outputFilePath)
        return outputFilePath

    @classmethod
    def runLater_Exec(cls,filePath):
        import json
        with open(filePath) as f:
            jsonDict = json.loads(f.read())

        Inferno = cls()
        Inferno.importParameters(jsonDict["Parameters"])
        Inferno.importInputConfig(jsonDict["inputConfig"])
        
        if "auth" in jsonDict:
            logging.info("Read authentification from ExecConfig.json")
            Inferno.parameters.inputConfig.auth_fromDict(jsonDict["auth"])
            # logging.debug(Inferno.parameters.inputConfig)

        Inferno.chosenPriorityProposition = Scenarios.formJson(jsonDict["scenario"])
        Inferno.parameters.treatment.masterImage = TreatmentHelper.MasterImage._fromdict(Inferno.chosenPriorityProposition.list,jsonDict["masterImage"])
        # import pprint
        # pprint.pprint(Inferno.parameters.treatment.creationOption)
        Inferno._runTreatement()
        pass
    
    def exportAuth(self):
        output = {}
        # if not self.parameters.inputConfig.authFile:
        logging.warning("authentification information will be written in ExecConfig.json")
        output["auth"] = self.parameters.inputConfig.auth_asdict()
        return output

    def exportParameters(self,fileName="Parameters.yaml"):
        self.parameters.write(fileName)

    def importParameters(self,fileName="Parameters.yaml"):
        self.parameters.inputConfig.parametersFile = fileName
        self.parameters.read(fileName)

    def exportInputConfig(self,filePath):
        self.parameters.inputConfig.toFile(filePath=filePath)

    def importInputConfig(self,filePath):
        self.parameters.inputConfig = ConfigParser.InputConfig.fromFile(file=filePath)

    def runRequest(self) -> S1Product.InfernoProducts:  
        '''
        Run the requests from provider, and fill self.requestResults with the results
        return self.requestResults
        '''
        config = self.parameters.inputConfig
        provider = self.parameters.inputConfig.provider
        self.requestResults = S1Product.InfernoProducts(list_S1product=[],config=config)
        
        try:
            self.requestResults = S1Product.InfernoProducts.request(config,provider)
        except:
            import traceback
            print(traceback.format_exc())

        # self.requestResults = S1Product.InfernoProducts.request(config,provider)
        return self.requestResults

    def updateScenarios(self)->List[List[Scenarios.Proposition]]:
        """ 
        Compute all proposition, set self.priorityProposition and return it .
        """

        scenarioListConstructor :List[Scenarios.Proposition] = []
        scenarioListConstructor.append(Scenarios.Proposition1)
        scenarioListConstructor.append(Scenarios.Proposition2)
        scenarioListConstructor.append(Scenarios.Proposition3)
        scenarioListConstructor.append(Scenarios.Proposition4)

        scenarioList :List[Scenarios.PropositionList] = []
        for cls in scenarioListConstructor:
            tmp = cls.generate(inferno=Inferno,chosonProduct=self.chosenResults) 
            scenarioList.append( Scenarios.PropositionList(cls,tmp) )

        self.priorityProposition = scenarioList
        return self.priorityProposition 

    def getChosenProposition(self)->Scenarios.Proposition:
        out = []
        for listProposition in self.priorityProposition:
            for proposition in listProposition:
                if proposition.chosen:
                    out.append(proposition)
        if len(out)==0:
            return out
        return out[0]

    def updateChosenProposition(self)->List[Scenarios.Proposition]:
        self.chosenPriorityProposition = self.getChosenProposition()
        return self.chosenPriorityProposition

    def _inside(self,product):
        # return 2x2 boolean np.array
        #   output[0,0] =  roi.latmin  > geom.latmin 
        #   output[0,1] =  roi.latmax  < geom.latmax 
        #   output[1,0] =  roi.longmin > geom.longmin 
        #   output[1,1] =  roi.longmax < geom.longmax
        current_geom = product.geom
        config_roi = self.parameters.inputConfig.get_roi()
        test1 = ((config_roi[:,0]>=current_geom[:,0]))
        test2 = ((config_roi[:,1]<=current_geom[:,1]))
        return np.column_stack([test1,test2])   

    def S1ProductInsideROI(self,product:S1Product):   
        # geom return True if ele is inside the ROI define in config
        inside = (np.sum(self._inside(product)) ==4)
        return inside

    def runTreatement(self,
            callbackUpdateStepInfo: Callable[[stepInfo],None]=None,
            callbackProgress: Callable[[int],None]=None,
            stdout = None):
        

        if self.runLater:
            stdout_old = sys.stdout
            if stdout:
                sys.stdout = stdout

            self.runLater_Export()
            #self.runLater_ExportHAL()
            sys.stdout = stdout_old
            return 

        
        try:
            self._runTreatement(
                callbackProgress=callbackProgress,
                callbackUpdateStepInfo=callbackUpdateStepInfo,
                stdout=stdout)
        except Exception:
            import traceback
            traceback.print_exc(file=sys.stdout)
            return
    
    def _runTreatement(self,
            callbackUpdateStepInfo: Callable[[stepInfo],None]=None,
            callbackProgress: Callable[[int],None]=None,
            stdout = None):

        _steps :List[Type[ Step]] = []   
        _steps.append(Treatment.CreateDir)
        _steps.append(Treatment.ExportConfiguration)
        _steps.append(Treatment.CheckIfProductExist)
        _steps.append(Treatment.Download)
        _steps.append(Treatment.Unzip)
        # _steps.append(Treatment.CreateTmpCopy) 
        stepInstances  = {}       
        for step in _steps:
            currentStep = step(
                inferno=self,
                callbackStepInfo=callbackUpdateStepInfo,
                callbackProgress=callbackProgress,
                stdout=stdout
            )
            stepInstances[step] = currentStep
            try:
                currentStep.run()
            except Exception:
                import traceback
                traceback.print_exc(file=sys.stdout)
                return
        chosenPriorityProposition = self.chosenPriorityProposition

        # amplitudePhase
        if self.parameters.treatment.amplitudePhase.activate:
            _ampliPhase = Treatment.AmpliPhase(
                callbackProgress=callbackProgress,
                callbackStepInfo=callbackUpdateStepInfo,
                inferno=self,
                stdout=stdout,
            )
            _ampliPhase.run(
                listProduct = chosenPriorityProposition.list,
                chosenSwath = chosenPriorityProposition.chosenSwaths,
                polarization = chosenPriorityProposition.chosenPolarization)

        self.computeQuality1()
        
        treatmentFilePaths = chosenPriorityProposition.treatment(
                inferno=self,
                callbackStepInfo=callbackUpdateStepInfo,
                callbackProgress=callbackProgress,
                stdout=stdout
            )

        creationOption = self.parameters.treatment.creationOption
        calibrationFilePaths = []
        logCalibrationFilePaths = []
        
        # Calibration 
        calibrationTreatment = None
        if creationOption.sigma0ComplexAmplitudeCalibration or creationOption.logSigma0ComplexAmplitudeCalibration:
            calibrationTreatment = Treatment.Calibration(
                inferno=self,
                callbackStepInfo=callbackUpdateStepInfo,
                callbackProgress=callbackProgress,
                stdout=stdout
            )
            calibrationHelp = lambda listFilePaths : calibrationTreatment.run(
                inputDir = self.getDiapOtbOutputDir(),
                listFilePaths = listFilePaths,
                calibration = creationOption.sigma0ComplexAmplitudeCalibration,
                logCalibration = creationOption.logSigma0ComplexAmplitudeCalibration
                )

            # Compute calibration for filtered interferogram
            tmp = calibrationHelp(chosenPriorityProposition.diapOtbOutputFilePaths[1])
            calibrationFilePaths.extend(tmp[0])
            logCalibrationFilePaths.extend(tmp[1])

            # Compute calibration for not filtered interferogram
            tmp = calibrationHelp(chosenPriorityProposition.diapOtbOutputFilePaths[0])
            calibrationFilePaths.extend(tmp[0])
            logCalibrationFilePaths.extend(tmp[1])
            
        if chosenPriorityProposition.needConcatenation:
            ouputDir = os.path.join(self.getOutputDir(),CONSTANT.DIAPOTB_OUTPUTDIR)
            treatmentFilePaths = chosenPriorityProposition.runConcatenate(
                filePaths=treatmentFilePaths,
                ouputDir=ouputDir,
                nodata=0
            )
            if creationOption.sigma0ComplexAmplitudeCalibration :
                # for _calibrationFilePaths in calibrationFilePaths:
                    ouputDir = os.path.join(self.getOutputDir(),CONSTANT.CALIBRATION_OUTPUTDIR)
                    calibrationFilePaths = chosenPriorityProposition.runConcatenate(
                        filePaths=calibrationFilePaths,
                        ouputDir=ouputDir,
                        nodata=0.0
                    )
            if creationOption.logSigma0ComplexAmplitudeCalibration:
                    ouputDir = os.path.join(self.getOutputDir(),CONSTANT.CALIBRATION_OUTPUTDIR)
                    calibrationFilePaths = chosenPriorityProposition.runConcatenate(
                        filePaths=logCalibrationFilePaths,
                        ouputDir=ouputDir,
                        nodata="nan"
                    )
        else:
            if creationOption.sigma0ComplexAmplitudeCalibration or creationOption.logSigma0ComplexAmplitudeCalibration :
                calibrationTreatment.moveOutputDir(self.getOutputDir())
        
        if creationOption.phaseUnwrapping.activate:
            phaseUnwrappingTreatment = Treatment.UnwrapPhase(
                inferno=self,
                callbackStepInfo=callbackUpdateStepInfo,
                callbackProgress=callbackProgress,
                stdout=stdout
            )
            phaseUnwrappingTreatment.run(
                inputFilePaths=treatmentFilePaths
            )
            self.unwrapedInterferogramPaths = phaseUnwrappingTreatment

        self.interferogramPaths = treatmentFilePaths
        self.computeQuality()
        return
        
    def computeQuality1(self):
        if (self.parameters.postTreatment.qualityIndicator.altitudeAmbiguity 
            or self.parameters.postTreatment.qualityIndicator.criticalBase
            or self.parameters.postTreatment.qualityIndicator.orthogonalBase 
            or self.parameters.postTreatment.qualityIndicator.recoveryRate):
            
            Treatment.ComputeQualiteIndicator(
                inferno=self,
            ).run()


    def computeQuality(self):
        options = self.parameters.postTreatment.qualityIndicator
        output = {}
        if options.meanConsistency:
            outputFilePath = os.path.join(self.getOutputDir(),"Consistency.json")
            res = Treatment.Consistency.run(self.interferogramPaths)
            Tools.writeToJson(res,outputFilePath=outputFilePath)

        # if options.altitudeAmbiguity:
        #     outputFilePath = os.path.join(self.getOutputDir(),"altitudeAmbiguity.log")
        #     S1FilePaths = self.chosenPriorityProposition.getImagesList()
        #     Treatment.AmbiguityHeight.computeAll(S1FilePaths=S1FilePaths,outfilePath=outputFilePath)
        
    def getInstallDir(self):
        import pathlib
        return str(pathlib.Path(__file__).parents[1].resolve())

    def extractROI(self,files):
        for file in files:
            Treatment.CropROI.cropProduct(inferno=self,filePath=file)    

    def getDownloadFolder(self)->str:
        inputConfig = self.parameters.inputConfig
        return os.path.join(inputConfig.workingDir,CONSTANT.DOWNLAOD_FOLDER)

    def getWorkingDir(self)->str:
        return self.parameters.inputConfig.workingDir

    def getOutputDir(self)->str:
        return self.parameters.inputConfig.outputDir

    def getRawFolder(self)->str:
        return os.path.join(self.getWorkingDir(),CONSTANT.RAW_FOLDER)

    def getDiapOtbOutputDir(self):
        path = self.getWorkingDir()
        return os.path.join(path,CONSTANT.DIAPOTB_OUTPUTDIR)

    def getConcatDir(self):
        path = self.getWorkingDir()
        return os.path.join(path,CONSTANT.CONCATENATE_OUTPUTDIR)

    def ExtractFolder(self):
        return os.path.join(
            self.getWorkingDir(),
            CONSTANT.EXTRACT_ROI_FOLDER
        )

    def getTmpFolder(self):
        return os.path.join(
            self.getWorkingDir(),
            CONSTANT.TMP_OUTPUTDIR
        )
    
    def getConfigJsonFilename(self):
        return os.path.join(
            self.getWorkingDir(),
            CONSTANT.DIAPOTB_CONFIG_FILE
        )
    
    def sizeEstimation(self,proposition:Scenarios.Proposition) -> OutputSizeEstimation:
        """
        return an estimation of totalSize and downloadSize in Mo
        """
        totalSize = 0
        downloadSize = 0
        unzip_size = 0
        estiSwathImageSize = 0
        nbChosenSwaths = len(proposition.chosenSwaths)
        parameters = self.parameters.treatment.creationOption
        orthorectificationCoef = 1
        amplitudePhaseCoef = 0
        amplitudePhaseSize = 0

        scale_factor = (
            self.parameters.inputConfig.ROI.get_surface() /
            proposition.list[0].get_surface() 
         )

        # donwload Product
        for product in proposition.list:
            downloadSize += product.size
            unzip_size += CONSTANT.S1PRODUCT_FILE_SIZE
        # MAX
        estiSwathImageSize = (
            CONSTANT.S1PRODUCT_FILE_SIZE / 
                    (len(product.polarization)*product.nb_swath())
                )


        totalSize += unzip_size # S1 donwload FIles

        # DiapOTB
        totalSize += estiSwathImageSize*(len(proposition.list)-1)*nbChosenSwaths

        # # crop
        # totalSize += estiSwathImageSize*(len(proposition.list)-1)*nbChosenSwaths

    
        # Options
        if parameters.phaseFiltering.activate:
            orthorectificationCoef += 1
        if parameters.sigma0ComplexAmplitudeCalibration:
            orthorectificationCoef += 1
        if parameters.logSigma0ComplexAmplitudeCalibration:
            orthorectificationCoef += 1
        
        totalSize += scale_factor*4*estiSwathImageSize*(len(proposition.list)-1)*orthorectificationCoef
        # print(f'{ (estiSwathImageSize*(len(proposition.list)-1)*orthorectificationCoef/1e3)=}')
        # print(f'{ (len(proposition.list))=}')
        
        if parameters.phaseFiltering.activate:
            totalSize += scale_factor*estiSwathImageSize*(len(proposition.list)-1)

        # amplitudePhase
        if self.parameters.treatment.amplitudePhase.activate:
            amplitudePhaseCoef += 1
            if self.parameters.treatment.amplitudePhase.orthorectification:
                amplitudePhaseCoef += 4
                
            amplitudePhaseSize = CONSTANT.S1PRODUCT_FILE_SIZE*amplitudePhaseCoef*(len(proposition.list)-1)*nbChosenSwaths
            totalSize += amplitudePhaseSize

        estimation = OutputSizeEstimation(totalSize=totalSize,downloadSize=downloadSize)
        return estimation
        
if __name__=="__main__":

    import dataclasses
    from pprint import pprint
    parameters = Parameters()
    pprint(parameters)

    # Test acces to sConstant
    # print( f'{CONSTANT.MASTER_IMAGE.FIX=}')
    # print( f'{CONSTANT.MASTER_IMAGE.MOVING=}')
    # print( f'{CONSTANT.PROVIDER.PEPS=}')
    # print( f'{CONSTANT.PROVIDER.SCIHUB=}')

    # Test to parameters.toDict()
    print("\n Test to parameters.toDict()")
    parameters_dict = parameters.toDict()
    pprint(parameters_dict)

    # Test to parameters.toDict()
    print("\n Test change provider")
    parameters.provider = CONSTANT.PROVIDER.SCIHUB
    pprint(parameters)
    # print(f'{parameters.provider.name=}')
    # pprint(parameters.toDict())

    # Test to write
    print("\n Test to parameters.write()")
    parameters = Parameters()
    parameters.write()

    # Test to read
    print("\n Test to parameters.read()")
    parameters_read = Parameters.read()
    pprint(parameters_read)
    assert (parameters_read == parameters)





    
