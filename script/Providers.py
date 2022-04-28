from ast import Constant
from datetime import datetime
from script import CONSTANT
from script.ConfigParser import InputConfig
from . import S1Product

from eodag import EODataAccessGateway
from eodag import setup_logging
import os

from xml.etree import ElementTree
from io import StringIO
import asyncio

def create_dir(dir_path):
    #c Create directory if not existe
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path,exist_ok=True)
        
class Eodag():
    ## https://eodag.readthedocs.io/en/stable/index.html
    provider = "PEPS"

    def __init__(self,config:InputConfig) -> None:
        self.config = config
        
        setup_logging(0)
        create_dir(self.config.workingDir)
 
        os.environ["EODAG__PEPS__AUTH__CREDENTIALS__USERNAME"] = self.config.auth.id
        os.environ["EODAG__PEPS__AUTH__CREDENTIALS__PASSWORD"] = self.config.auth.password
        os.environ["EODAG__PEPS__DOWNLOAD__OUTPUTS_PREFIX"] = os.path.abspath(self.config.workingDir)
        self._set_search_config()

    def _set_search_config(self):
        # x = latitude
        # y = longitude
        # https://peps.cnes.fr/rocket/plus/img/PEPS-IF-0-0170-ATOS_01_00_[2].pdf
        latmin,latmax  = sorted([self.config.ROI.lowerRigthY,self.config.ROI.upperLeftY])
        lonmin,lonmax= sorted([self.config.ROI.upperLeftX,self.config.ROI.lowerRigthX])
        date_start  = self.config.dates.begin.strftime("%Y-%m-%d")
        date_end    = self.config.dates.end.strftime("%Y-%m-%d")
        self.search_param = {
                    "items_per_page":100,
                    "collection":"S1",
                    "productType":"SLC",
                    "sensorMode":"IW",
                    "geom":{'lonmin': lonmin,
                            'latmin': latmin,
                            'lonmax': lonmax,
                            'latmax': latmax
                            },
                    "start":date_start,
                    "end":date_end
                    }
   
    def search(self):
        dag = EODataAccessGateway()
        # search_results, total_count = dag.search(
        #     collection = self.search_param["collection"],
        #     geom = self.search_param["geom"],
        #     start = self.search_param["start"],
        #     end = self.search_param["end"] 
        #     )        
        search_results = dag.search_all(**self.search_param
            )
        self.search_results = search_results
        self.total_count = len(search_results) 
        return self.search_results , self.total_count

    @staticmethod
    def get_geom(res):
        import numpy as np
        # tmp = res["geometry"]["coordinates"]
        # tmp = np.array(tmp[0][0])
        # lond_min,lat_min = np.min(tmp,axis=0)
        # lond_max,lat_max = np.max(tmp,axis=0)
        # return np.array([[lat_min,lat_max],
        #                  [lond_min,lond_max]])
        geom =  np.array(res["geometry"]["coordinates"][0])
        if len(geom)<5:
            geom =  np.array(res["geometry"]["coordinates"][0][0])
        return geom[:-1]     
    
    @staticmethod
    def _parseSatellite(txt):
        if txt == "S1B":
            return CONSTANT.SATELLITE.S1B
        return CONSTANT.SATELLITE.S1A

    @staticmethod
    def _parseOrbitType(txt):
        if txt == "descending":
            return CONSTANT.ORBIT_TYPE.DES
        return CONSTANT.ORBIT_TYPE.ASC

    @staticmethod
    def _parseSize(size:str):
        size = int(size)//1e6
        return size

    def get_product_list(self)-> list:
        self.search()
        product_list = []

        quicklooks_dir = os.path.join(self.config.workingDir, "quicklooks","PEPS")
        for i, product in enumerate(self.search_results):
            res  = product.as_dict()
            name = res["id"]
            date            :str = res["properties"]["startTimeFromAscendingNode"]
            orbitNumber     :str = res["properties"]["relativeOrbitNumber"]
            orbitType       :str = self._parseOrbitType(res["properties"]["orbitDirection"])
            satellite       :str = self._parseSatellite(res["properties"]["platformSerialIdentifier"])
            # swath           :str = res["properties"]["sensorMode"] #sous-fauchée
            size            :str = self._parseSize(res["properties"]["resourceSize"])
            swath           :str = res["properties"]["swathIdentifier"] #sous-fauchée
            polarization    :str = res["properties"]["polarizationMode"] 
            quicklook_path  :str = product.get_quicklook(base_dir=quicklooks_dir)
            geom            :str = Eodag.get_geom(res)
            location        :str = product.location
            available       :str = res["properties"]["storage"]["mode"] 
            available = (available == "disk") 


            # parse Polarization
            listPolarization = []
            for _polarization in polarization.split(" "):
                listPolarization.append(CONSTANT.POLARIZATION[_polarization])

            # parse date
            date = datetime.strptime(date,'%Y-%m-%dT%H:%M:%S.%fZ')
            s1prod= S1Product.S1Product(
            name = name,
            date = date,
            orbitNumber = orbitNumber,
            orbitType = orbitType,
            satellite = satellite,
            swath = swath,
            polarization = listPolarization,
            quicklook    = quicklook_path,
            provider     =self.provider,
            geom    = geom,
            location=location,
            size=int(size),
            available = available )

            product_list.append(s1prod)
        self. product_list = product_list
        return product_list

import requests
import xmltodict

class Scihub():
    provider = "SCIHUB"
    url = 'https://scihub.copernicus.eu/dhus/search?q='
    max_item_per_page = 100

    def __init__(self,config:InputConfig) -> None:
        self.config = config    
        create_dir(self.config.workingDir)
        self.auth = (   self.config.auth.id,
                        self.config.auth.password)
        
        self._set_search_param()

    def _set_search_param(self):
        # x = latitude
        # y = longitude
        # https://scihub.copernicus.eu/userguide/FullTextSearch#Search_Keywords
        latmin,latmax = sorted([self.config.ROI.upperLeftY,self.config.ROI.lowerRigthY])
        lonmin,lonmax = sorted([self.config.ROI.upperLeftX,self.config.ROI.lowerRigthX])
        date_start  = self.config.dates.begin.isoformat(timespec='milliseconds')
        date_end    = self.config.dates.end.isoformat(timespec='milliseconds')

        self.search_param = {
                'platformname':'Sentinel-1',
                'producttype':"SLC",
                "sensoroperationalmode":"IW",
                'footprint':f'"Intersects( POLYGON(({lonmin} {latmin},{lonmax} {latmin},{lonmax} {latmax},{lonmin} {latmax},{lonmin} {latmin})))"',
                'beginposition':f"[{date_start}Z TO {date_end}Z]"
              }
        self.quicklooks_dir = os.path.join(self.config.workingDir, "quicklooks")

    def search(self):
        def get_next_link(res_dict):
            """
            Get next page link from a request dict 
            Return link of the next page if it exist,
                    None otherwise
            """
            for ele in res_dict["feed"]["link"]:
                if ele["@rel"] == "next":
                    return ele["@href"]
            return None

        self.response = []
        self.res_dict = []
        self.links = []
        # if not (hasattr(self,"response") or hasattr(self,"res_dict") ) :
        payload_str = "+".join( "(%s:%s)" %(k,v) for k,v in self.search_param.items())
        request_link = Scihub.url+payload_str+f"&rows={self.max_item_per_page}"
        while not (request_link is None):
            response = requests.get(request_link,auth=self.auth)
            if response.status_code != 200:
                response.raise_for_status()
                return
            res_dict = xmltodict.parse(response.text)
            self.response.append(response)
            self.res_dict.append(res_dict)
            request_link = get_next_link(res_dict)

    @staticmethod
    def _general_get(entry,entry_key,name,default_pos = 0)-> str:
        output = None
        if  (   len(entry[entry_key])<default_pos 
            and (entry[entry_key][default_pos]["@name"] == name) ):

            output  = entry[entry_key][default_pos]["#text"]
        else:
            for date in entry[entry_key]:
                if (date["@name"] == name):
                    output  = date["#text"] 
                    break
        return output
        
    @staticmethod
    def get_date_from_entry(entry): 
        return Scihub._general_get(
            entry=entry,
            entry_key="date",
            name= "beginposition",
            default_pos=0)

    @staticmethod
    def get_orbitnumber_from_entry(entry):
        return Scihub._general_get(
            entry=entry,
            entry_key="int",
            name= "relativeorbitnumber",
            default_pos=3)

    @staticmethod
    def get_orbitType_from_entry(entry):
        txt =  Scihub._general_get(
            entry=entry,
            entry_key="str",
            name= "orbitdirection",
            default_pos=6)

        if txt == "DESCENDING":
            return CONSTANT.ORBIT_TYPE.DES
        return CONSTANT.ORBIT_TYPE.ASC

    @staticmethod
    def get_satellite_from_entry(entry):
        sat = entry['title'].split("_")[0]
        if sat == "S1A":
            return CONSTANT.SATELLITE.S1A 
        return CONSTANT.SATELLITE.S1B 

    @staticmethod
    def get_swath_from_entry(entry):
        # name= "sensoroperationalmode",
        return Scihub._general_get(
            entry=entry,
            entry_key="str",
            name = "swathidentifier",            
            default_pos=7)

    @staticmethod
    def get_polarisationmode_from_entry(entry):
        return Scihub._general_get(
            entry=entry,
            entry_key="str",
            name= "polarisationmode",
            default_pos=15)

    @staticmethod
    def get_quicklook_url_from_entry(entry):
        quicklook_url = None
        if  ("@rel" in entry["link"][2] ) and (entry["link"][2]["@rel"] == 'icon'):
            quicklook_url  = entry["link"][2]["@href"] 
        else:
            for link in entry["link"]:
                if ("@rel" in link) and (link["@rel"] == 'icon'):
                    quicklook_url  = entry["link"][2]["@href"] 
                    break
        return quicklook_url
    
    @staticmethod
    def get_name_from_entry(entry):
        return entry['title']

    @staticmethod
    def _parse_geom(geom_footprint):
        import numpy as np
        in_float =  [
                [float(i.split(" ")[0]),float(i.split(" ")[1])] 
                for i in geom_footprint[len("MULTIPOLYGON ((("):-len(')))')].split(', ')
            ]
        in_float  = np.array(in_float)
        # lond_min,lat_min = np.min(in_float,axis=0)
        # lond_max,lat_max = np.max(in_float,axis=0)

        # return np.array([ [lat_min ,lat_max],
        #                   [lond_min,lond_max]])
        return in_float[:-1]

    @staticmethod
    def get_geom(entry):
        geom_footprint = Scihub._general_get(entry,entry_key="str",name="footprint")
        return Scihub._parse_geom(geom_footprint)

    @staticmethod
    def get_location(entry):
        id = entry["id"]
        partern = "https://scihub.copernicus.eu/dhus/odata/v1/Products('{id}')/$value"
        return partern.format(id=id)

    @staticmethod
    def get_size(entry):
        size = Scihub._general_get(entry,entry_key="str",name="size")
        return int(float(size.split(" ")[0])*10**3)*1.1

    @staticmethod
    async def download_quicklook_from_entry(entry,directory,quicklook_url,auth):
        prefix = "SCIHUB"

        # Generate quicklook file name 
        # Example : quicklook_file_name S1A_IW_GRDH_1SDV_20210830T060738_20210830T060803_039455_04A951_108F
        name = entry["title"]        
        quicklook_file_name = "_".join([name])

        # Get quicklook folder path
        # Example :   
        #   directory   = ./working_dir
        #   prefix      = "SCIHUB"
        output_folder = os.path.join(directory,prefix)

        # Check output_folder exist and create if not
        create_dir(output_folder)

        quicklook_path = os.path.join(output_folder,quicklook_file_name)
        # Check if quicklook already existe, exit fonction if so 
        if os.path.isfile(quicklook_path):
            return quicklook_path

        # Download quicklook
        # with requests.get(quicklook_url, stream=True, auth=auth) as stream:
        #     stream_size = int(stream.headers.get("content-length", 0))
        #     with open(quicklook_path, "wb") as fhandle:
        #         for chunk in stream.iter_content(chunk_size=64 * 1024):
        #             if chunk:
        #                 fhandle.write(chunk)
        #         return quicklook_path
        import shutil
        with requests.get(quicklook_url, stream=True, auth=auth) as stream:
            stream_size = int(stream.headers.get("content-length", 0))
            with open(quicklook_path, "wb") as file:
                shutil.copyfileobj(stream.raw, file,length=CONSTANT.DOWNLAOD_BUFSIZE)
                return quicklook_path

    async  def get_isAvailable(self,entry):
        # import xml.etree.ElementTree as ET

        
        def get_namespaces(xml_string):
            namespaces = dict([
                    node for _, node in ElementTree.iterparse(
                        StringIO(xml_string), events=['start-ns']
                    )
            ])
            namespaces["ns0"] = namespaces[""]
            return namespaces

        pattern = "https://scihub.copernicus.eu/dhus/odata/v1/Products('{id}')/Products"
        id = entry['id']
        link = pattern.format(id=id)
        res =  requests.get(link,auth=self.auth) 
        tree = ElementTree.fromstring(res.text)
        namespaces = get_namespaces(res.text)

        available = tree.find(".//d:Online",namespaces).text
        return available == "true"

    def _entry_to_S1Product(self,entry,task_available,task_quicklook_path):
            # available = self.get_isAvailable(entry)
            # quicklook_path  = Scihub.download_quicklook_from_entry(
            #     entry = entry,
            #     directory = self.quicklooks_dir,
            #     auth = self.auth,
            #     quicklook_url = quicklook_url)
            quicklook_url   = Scihub.get_quicklook_url_from_entry(entry)

            task_available.append( asyncio.ensure_future( self.get_isAvailable(entry) ) )
            task_quicklook_path.append( asyncio.ensure_future( Scihub.download_quicklook_from_entry(
                entry = entry,
                directory = self.quicklooks_dir,
                auth = self.auth,
                quicklook_url = quicklook_url)
            )
            )
                
            name = Scihub.get_name_from_entry(entry)
            date            = Scihub.get_date_from_entry(entry)
            orbitNumber     = Scihub.get_orbitnumber_from_entry(entry)
            orbitType       = Scihub.get_orbitType_from_entry(entry)
            satellite       = Scihub.get_satellite_from_entry(entry)
            swath           = Scihub.get_swath_from_entry(entry)
            polarization    = Scihub.get_polarisationmode_from_entry(entry)
            geom            = Scihub.get_geom(entry)
            size            = Scihub.get_size(entry)
            location        = Scihub.get_location(entry)

            listPolarization = []
            for _polarization in polarization.split(" "):
                listPolarization.append(CONSTANT.POLARIZATION[_polarization])
            date = datetime.strptime(date,'%Y-%m-%dT%H:%M:%S.%fZ')

            # available   = await task_available
            # quicklook_path  = await task_quicklook_path

            s1prod= S1Product.S1Product(
            name        = name,
            date        = date,
            orbitNumber = orbitNumber,
            orbitType   = orbitType,
            satellite   = satellite,
            swath       = swath,
            polarization= listPolarization,
            quicklook   = "quicklook_path",
            provider    = self.provider,
            geom        = geom,
            location    = location,
            size        = size,
            available   = True)
            return s1prod

    def _get_product_list(self):
        self.search()
        product_list = []

        for res_dict in self.res_dict:
            for entry in res_dict["feed"]["entry"]:
                s1prod = self._entry_to_S1Product(entry)
                product_list.append(s1prod)

        
        self. product_list = product_list
        return product_list

    def get_product_list(self):
        self.search()
        product_list = []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []
        task_available = []
        task_quicklook_path = []
        for res_dict in self.res_dict:
            for entry in res_dict["feed"]["entry"]:
                s1prod = self._entry_to_S1Product(entry,task_available=task_available,task_quicklook_path=task_quicklook_path)
                product_list.append(s1prod)
                
        availables = loop.run_until_complete(asyncio.gather(*task_available))
        quicklooks = loop.run_until_complete(asyncio.gather(*task_quicklook_path))
        for product,available,quicklook in zip(product_list,availables,quicklooks):
            product.quicklook = quicklook
            product.available = available
        self. product_list = product_list
        return product_list

