from dataclasses import dataclass, field
import dataclasses 

from re import L
import yaml
import datetime
import numpy as np
import os
from pathlib import Path
from copy import deepcopy
from script import CONSTANT, InfernoException

from typing import List

@dataclass
class ROI:
    upperLeftX:float
    upperLeftY:float
    lowerRigthX:float
    lowerRigthY:float

    def __post_init__(self):
        self.upperLeftX  =float(self.upperLeftX)
        self.upperLeftY  =float(self.upperLeftY)
        self.lowerRigthX =float(self.lowerRigthX)
        self.lowerRigthY =float(self.lowerRigthY)

        if self.upperLeftX > self.lowerRigthX:
            self.upperLeftX, self.lowerRigthX = self.lowerRigthX, self.upperLeftX
            print( f" upperLeftX > lowerRigthX : upperLeftX and lowerRigthX will be inverted "  )
        
        if self.lowerRigthY > self.upperLeftY:
            self.lowerRigthY, self.upperLeftY = self.upperLeftY, self.lowerRigthY
            print( f" lowerRigthY > upperLeftY : upperLeftX and lowerRigthX will be inverted ")

    @classmethod
    def fromYamlDict(cls,data:dict):
        lower_rigth_x  = data["ROI"]["Lower_rigth_x"]
        lower_rigth_y  = data["ROI"]["Lower_rigth_y"]
        upper_left_x   = data["ROI"]["Upper_left_x"]
        upper_left_y   = data["ROI"]["Upper_left_y"]
        roi = ROI(
            lowerRigthX=lower_rigth_x,
            lowerRigthY=lower_rigth_y,
            upperLeftX=upper_left_x,
            upperLeftY=upper_left_y)
        return roi

    def getGeom(self):
        geom = [
            [self.upperLeftX,self.upperLeftY],
            [self.lowerRigthX,self.upperLeftY],
            [self.lowerRigthX,self.lowerRigthY],
            [self.upperLeftX,self.lowerRigthY],
        ]
        return np.array(geom)

    def get_surface(self):
        surface = (self.lowerRigthX-self.upperLeftX)*(self.upperLeftY-self.lowerRigthY)
        return surface

    geom = property(fget=getGeom)
    
@dataclass
class Dates:
    begin : datetime.datetime
    end   : datetime.datetime

    def __post_init__(self):
        self.begin = self.check_date(self.begin)
        self.end = self.check_date(self.end)

    def check_date(self,date):
        if isinstance(date,datetime.datetime):
            return date
        try:
            return datetime.datetime.strptime(date, '%d/%m/%Y')
        except ValueError:
            raise ValueError("Incorrect data format, should be JJ/MM/AAAA")

    @classmethod
    def fromYamlDict(cls,data:dict):
        date_begin = data["Date"]["begin"]
        date_end   = data["Date"]["end"]

        date = Dates(
            begin=date_begin,
            end=date_end
        )
        return date


@dataclass
class Auth():
    provider:CONSTANT.PROVIDER
    id:str = ""
    password:str = ""

    def __post_init__(self):
        if isinstance(self.provider,str):
            self.provider = CONSTANT.PROVIDER[self.provider.upper()]
  
    @classmethod
    def defaultListAuth(cls):
        output:List[Auth] = []
        for provider in CONSTANT.PROVIDER:
            output.append(Auth(provider=provider))
        return output


    @classmethod
    def fromFile(cls,file:str):
        with open(file, "r") as stream:
            data:dict = yaml.safe_load(stream)

        output:List[Auth] = cls.defaultListAuth()
        for auth in output:
                if auth.provider.name.upper() in data:
                    _auth:dict = data[auth.provider.name.upper()]
                    auth.id = _auth["ID"]
                    auth.password = _auth["PASSWORD"]
        return output
    
    def _asdict(self):
        output = {}
        output["provider"] = str(self.provider)
        output["id"] = self.id
        output["password"] = self.password

        return output
    
    @classmethod
    def _fromDict(cls,jsonDict):
        output = jsonDict.copy()
        output["provider"] = CONSTANT.PROVIDER[output["provider"]]
        return cls(**output)


@dataclass
class InputConfig:
    ROI: ROI        = None
    dates : Dates   = None
    mntPath    : str  = None
    parametersFile : str = ""
    workingDir : str = None
    outputDir  : str = None
    provider:CONSTANT.PROVIDER = CONSTANT.PROVIDER.PEPS
    authList:List[Auth] =  field(default_factory=Auth.defaultListAuth)
    authFile : str = None
    
    def authIsSet(self):
        auth  = self.getProviderAuth()
        if auth.id != "" or auth.password != "":
            return True
        return False

    @property
    def auth(self)->Auth:
        return self.getProviderAuth()

    def __post_init__(self):
        if isinstance(self.provider,str):
            self.provider = CONSTANT.PROVIDER[self.provider.upper()]

    @classmethod
    def fromFile(cls,file:str):
        def getAbsolutePath(filePath:List[str]):
            output:List[str] = []

            current_dir = os.getcwd()
            # move to config_file_path parent folder
            p = Path(file).resolve().parent
            os.chdir(p)
            
            for path in filePath:
                _path = Path(os.path.expanduser(path)).resolve()
                output.append(str(_path))
            os.chdir(current_dir)
            return output

        with open(file, "r") as stream:
            data = yaml.safe_load(stream)
        roi = ROI.fromYamlDict(data)
        dates = Dates.fromYamlDict(data)
        mntPath,workingDir, outputDir  = getAbsolutePath( 
            [   data["MNT"],
                data["IO"]["working_dir"],
                data["IO"]["output_dir"],
            ])
        
        provider = None
        authList = None
        authFile = None
        parametersFile = ""

        if ("Paremeters_File" in data) and (data["Paremeters_File"] ):
            parametersFile, = getAbsolutePath([data["Paremeters_File"]])

        try:
            provider,authFile = next(iter(data["auth"].items()))
            authFile, = getAbsolutePath( [authFile])
            authList = Auth.fromFile(authFile)
        except Exception:
            provider = CONSTANT.PROVIDER.SCIHUB
            authList = Auth.defaultListAuth()
            # InfernoException.printError()

        inputConfig = InputConfig(
            ROI=roi,
            dates=dates,
            mntPath=mntPath,
            workingDir=workingDir,
            outputDir=outputDir,
            provider=provider,
            authFile=authFile,
            authList=authList,
            parametersFile=parametersFile
            )
        return inputConfig

    def getAuth(self,provider:CONSTANT.PROVIDER)->Auth:
        for auth in self.authList:
            if auth.provider == provider:
                return auth 

    def getProviderAuth(self)->Auth:
        return self.getAuth(self.provider)

    @classmethod
    def default(cls):
        def getAbsolutePath(path:str):

            current_dir = os.getcwd()
            # move to config_file_path parent folder
            p = Path(current_dir).resolve().parent
            os.chdir(p)
            
            _path = Path(path).resolve()
            os.chdir(current_dir)
            return str(_path)


        Date_begin  = "10/09/2021"
        Date_end    = "10/10/2021"
        output_dir  = getAbsolutePath("output")
        working_dir = getAbsolutePath("working")
        MNT = "path/to/srtm"
        Upper_left_x    = "105.7"
        Upper_left_y    = "10.21"
        Lower_rigth_x   = "105.71"
        Lower_rigth_y   = "10.2"

        _ROI = ROI(
            lowerRigthX=Lower_rigth_x,
            lowerRigthY=Lower_rigth_y,
            upperLeftX=Upper_left_x,
            upperLeftY=Upper_left_y) 
        dates = Dates(
            begin=Date_begin,
            end=Date_end)
        workingDir = working_dir
        outputDir  = output_dir
        mntPath = MNT
        SRTM_Shapefile = None
        Geoid = None
        SRTM_Path : str = None

        output  = InputConfig(
            dates=dates,
            mntPath=mntPath,
            outputDir=outputDir,
            ROI=_ROI,
            workingDir=workingDir,
            # Geoid=Geoid,
            # SRTM_Shapefile=SRTM_Shapefile,
            # SRTM_Path=SRTM_Path,
            authFile="")
        return output

    def asdict(self):
        asdict = {
                "Date":{
                "begin": self.dates.begin.strftime('%d/%m/%Y'),
                "end": self.dates.end.strftime('%d/%m/%Y'),
                },
                "IO":{
                    "output_dir": self.outputDir,
                    "working_dir": self.workingDir,
                },
                "MNT": self.mntPath,
                "ROI":{
                    "Upper_left_x": self.ROI.upperLeftX,
                    "Upper_left_y": self.ROI.upperLeftY,
                    "Lower_rigth_x":self.ROI.lowerRigthX,
                    "Lower_rigth_y":self.ROI.lowerRigthY,
                },
                "auth":{
                    str(self.provider): self.authFile,
                },
                "Paremeters_File": self.parametersFile

        }
        return asdict


    def auth_asdict(self):
        return self.getProviderAuth()._asdict()

    def auth_fromDict(self,jsonDict):
        auth = Auth._fromDict(jsonDict)
        self.provider = auth.provider
        self.authList = [auth] 

    def toFile(self,filePath:str="config.yaml"):
        asdict = self.asdict()

        with open(filePath, 'w') as f:
            yaml.dump(asdict,f,sort_keys =False)
        return filePath
        
if __name__=="__main__":
    import pprint 
    inputConfig = InputConfig.default()
    pprint.pprint(inputConfig.toFile())