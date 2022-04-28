from datetime import datetime
from typing import Callable, List
import numpy as np
import os
import sys


from . import ConfigParser
from . import CONSTANT
from script import InfernoException

from dataclasses import dataclass, field
from typing import List,Tuple
import time

@dataclass
class S1Product():
    name : str
    date : datetime
    orbitNumber: int
    orbitType: CONSTANT.ORBIT_TYPE
    satellite: CONSTANT.SATELLITE
    swath : str
    polarization :List[CONSTANT.POLARIZATION]
    quicklook : str
    provider : str
    geom : np.ndarray # 4 corner georef coordinate [[lon,lat],...]
    location : str
    revisit : int = 0
    size: int = 0 # Mo
    available: bool = True 
    _revisit_id : str = ""
    _location : str = field(init=False, repr=False, default=None)
    locationType:CONSTANT.LOCATION_TYPE = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self.geom = np.array(self.geom)

    def _asdict(self):
        output = self.__dict__.copy()
        output["date"] = self.date.strftime("%d/%m/%Y")
        output["orbitType"] = str(self.orbitType)
        output["satellite"] = str(self.satellite)
        output["polarization"] = [str(p) for p in self.polarization]
        output["geom"] = self.geom.tolist()
        output["location"] = self.location
        output.pop("_revisit_id")
        output.pop("_location")
        output.pop("locationType")
        return output

    @classmethod
    def _fromdict(cls,jsonDict):
        output = jsonDict.copy()
        output["orbitType"] = CONSTANT.ORBIT_TYPE[output["orbitType"]]
        output["satellite"] = CONSTANT.SATELLITE[output["satellite"]]
        output["date"] = datetime.strptime(output["date"] ,"%d/%m/%Y")
        
        output["polarization"] = [CONSTANT.POLARIZATION[p] for p in output["polarization"]]
        return cls(**output)
    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if type(value) is property:
            # initial value not specified, use default
            value = S1Product._location
        self._location = value
        self.setLocationType()

    def setLocationType(self):
        if self.location.startswith("http"):
            self.locationType = CONSTANT.LOCATION_TYPE.URL
        elif self.location.endswith(".zip"):
            self.locationType = CONSTANT.LOCATION_TYPE.ZIP
        else:
            self.locationType = CONSTANT.LOCATION_TYPE.FOLDER
    
    def set_revisit(self,revisit,id):
        self.revisit = int(revisit)
        self._revisit_id = id

    def nb_swath(self):
        if self.swath is None:
            return None
        return len( (self.swath).upper().split(' ') )

    def download(self,
            auth:ConfigParser.Auth,
            dir_name:str,
            callbackMaxInfo:Callable[[int],None] = None,
            callbackCurrentSize:Callable[[int],None] = None,
            bufsize=1024 * 1024*10
        )->str:
        """ 
        Download the S1product and return the filename (.) 
        """
        import re
        import os
        import requests
        import pathlib
        def getInfo(headers) -> Tuple[str,int]:
            #return filename and fileSize in octet
            filename = re.findall('filename=(\S+)', headers["Content-Disposition"])[0][1:-1]
            size = int(headers.get("content-length")) # octet  
            return filename,size


        (user, password) = auth.id,auth.password
        url = self.location

        downloadedOctet = 0
        nb_test = 0
        while True:
            with requests.get(url, stream=True, auth=(user, password)) as r:
                if nb_test>10:
                    r.raise_for_status()

                nb_test+=1
                _status_code =  r.status_code
                try:
                    r.raise_for_status()
                except Exception as e:
                    print(e)

                if _status_code == 500:
                    delay = 60
                    print(f"Retry in {delay}s")
                    time.sleep(delay)
                    continue
                elif _status_code == 401:
                    r.raise_for_status()
                    
                elif _status_code != 200:
                    delay = 300
                    print(f'Product Not available: {url}')
                    print(f"Retry in {delay}s")
                    time.sleep(delay)
                    continue

                filename,size = getInfo(headers=r.headers)
                if callbackMaxInfo:
                    callbackMaxInfo(size//1000)

                fileFullName = os.path.join(dir_name,filename)
                tmp_fileFullName = f"{fileFullName}.tmp"
                
                if pathlib.Path(fileFullName).exists():
                    callbackCurrentSize(size//1000)
                    return fileFullName

                with open( tmp_fileFullName , 'wb') as f:
                    while True:
                        buff = r.raw.read(bufsize)
                        if len(buff)==0:
                            break
                        if callbackCurrentSize:
                            downloadedOctet += len(buff)
                            callbackCurrentSize(downloadedOctet//1000)
                        f.write(buff)

                    # shutil.copyfileobj(r.raw, f)
                os.rename(tmp_fileFullName, fileFullName)
                break
        return fileFullName

    def get_surface(self):
        geom_ = self.geom
        vec = np.zeros(self.geom.shape)
        vec[:-1] = geom_[1:] -  geom_[0:-1]
        vec[-1] = geom_[0] -  geom_[-1]
        u = sorted(vec,key= lambda x : x[0]/np.sum(x**2))[0]
        v = sorted(vec,key= lambda x : x[1]/np.sum(x**2))[0]
        return abs(np.cross(u,v))

    @classmethod
    def example(cls):
        cls(
    name  = "name", 
    date  = "27/04/1997",
    orbitNumber = 10,
    orbitType = CONSTANT.ORBIT_TYPE.ASC,
    satellite = "S1A",
    swath = "W1",
    polarization = [CONSTANT.POLARIZATION.VH,CONSTANT.POLARIZATION.VV],
    quicklook = None,
    provider = "MOI" ,
    geom = np.array([-1000,1000],[1000,1000],[1000,-1000],[-1000,-1000]),
    location = "foo.bar",
    revisit = 0,
    size = 0,
            )


class InfernoProducts():
    def __init__(self,
                list_S1product:List[S1Product],
                config:ConfigParser.InputConfig) -> None:

        self.config :ConfigParser.config_parser = config
        self.list   :List[S1Product] = list_S1product
        self.set_revisit()
        _DOWNLOAD_DIR = os.path.join(self.config.workingDir,"download")
        self._DOWNLOAD_DIR = os.path.abspath(_DOWNLOAD_DIR)

    @staticmethod
    def request(config:ConfigParser.InputConfig,provider:CONSTANT.PROVIDER):
        from . import Providers

        output_list = []
        if not config.authIsSet():
            return InfernoProducts(config=config,list_S1product=[])

        try:
            if provider == CONSTANT.PROVIDER.PEPS:
                provider_eodag = Providers.Eodag(config)
                output_list.extend(provider_eodag.get_product_list())
            elif provider == CONSTANT.PROVIDER.SCIHUB:
                provider_scihub = Providers.Scihub(config)
                output_list.extend(provider_scihub.get_product_list())
            else:
                exit()
        except Exception  as e:
            raise(e)
        output = InfernoProducts(output_list,config)

        check_datalake(output_list)

        listS1product = sorted(output.list,key=lambda x:x.date)
        output.list = listS1product
        return output

    def set_revisit(self):
        list_prod = self.list
        list_attribut_to_check = [ "orbitNumber", "satellite"]
        count = {}
        for ele in list_prod:
            id = tuple([getattr(ele,attr) for attr in list_attribut_to_check ])
            if id in count:
                count[id] += 1
            else:
                count[id] = 1

        for ele in list_prod:
            id = tuple([getattr(ele,attr) for attr in list_attribut_to_check ])
            ele.set_revisit(count[id],id) 
            
    def example(n = 20):
        from . import ConfigParser
        path = "input.yml"
        config = ConfigParser.read(path)

        output = InfernoProducts([S1Product.example() for i in range(n)],config)
        output.set_revisit()

        for ele in output:
            ele.geom = config.geom
            ele.orbitNumber = np.random.randint(10)
        return output
        
    def download(self):
        """
        Download all products 
        """
        for product in self.list:
            if product.location.startswith('http'):
                product.download(product,self.config,dir_name = self._DOWNLOAD_DIR)

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

def check_datalake(InfernoProducts:InfernoProducts):
    try:
        from libamalthee import Amalthee
        amalthee = Amalthee('peps')

        _list_peps_product = []
        for  product in InfernoProducts:
            if product.provider.upper() == "PEPS":
                _list_peps_product.append(product)

        # Check if avable on datalake
        amalthee.add([product.name for product in _list_peps_product])
        for idx in range(len(amalthee.products)):
            if amalthee.products.iloc[idx,1]:
                localisation =  amalthee.products.iloc[idx,0]
                _list_peps_product[idx].provider = "PEPS (Datalake)"
            else:
                _list_peps_product[idx].provider = "PEPS (Not on Datalake)"    
    except Exception:
        pass        


