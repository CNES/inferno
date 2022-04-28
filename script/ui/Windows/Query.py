from PyQt5 import QtCore, QtGui, QtWidgets


from ..Wigdets import QueryTable
from ... import S1Product
from ... import Inferno
from .. import Common
from script.ui.Wigdets import ScenariProposition,InputSetting
import copy 

from typing import List

class MainWindow(Common.window):
    def get_InfernoProducts(self):
        self.list_product  = self.inferno.runRequest()


    def fill_table_from_InfernoProducts(self):
        # self.scenari_pushButton.setEnabled(True)
        ## display results
        for product in self.list_product.list:
            self.InfernoRequest_TableWidget.add_item(product)
            self.InfernoRequest_TableWidget.setEnabled(True)

    def loadInfernoParameters(self):

        if self.inferno.requestResults:
            self.list_product = self.inferno.requestResults
            self.InfernoRequest_TableWidget.clearContents()
            self.fill_table_from_InfernoProducts()
    
    def getSelectectedElements(self) -> List[S1Product.S1Product]:
        return self.InfernoRequest_TableWidget.get_selected_element()

    def saveInfernoParameters(self)->None:
        self.inferno.requestResults = copy.deepcopy(self.list_product)
        self.inferno.chosenResults  = copy.deepcopy( self.getSelectectedElements())

    def isComplete(self) -> bool:
        self.saveInfernoParameters()
        self.inferno.updateScenarios()
        if not self.inferno.chosenResults:
            return False 
        return True

    def before_run_function(self):
        Dialog = QtWidgets.QDialog(self)
        settingsWindow = InputSetting.Ui_Dialog()
        settingsWindow.setupUi(Dialog,self.inferno)
        res = Dialog.exec_()
        if res==1:
            self.InfernoRequest_TableWidget.clearContents()
            return True
        else: return False

    
    def run_function(self):
        
        pass

    def setupUi(self,inferno:Inferno.Inferno):
        self.inferno    = inferno
        self.provider   = inferno.parameters.provider
        self.config     = inferno.parameters.inputConfig
        self.list_product = None

        self.mainlayout = QtWidgets.QVBoxLayout(self)
        self.mainlayout.setContentsMargins(0,0,0,0)
        # Define startPushButton, used for start InfernoProducts.request
        self.start_pushButton = Common.OnThread_PushButton(
            self,
            before_run_function= self.before_run_function,
            run_function = self.get_InfernoProducts,
            end_function = self.fill_table_from_InfernoProducts)
        self.mainlayout.addWidget(self.start_pushButton)

        # Define the TableWidget which display the all the retrieve 
        # data from InfernoProducts.request
        self.InfernoRequest_TableWidget = QueryTable.SearchResultTableWidget(self)
        self.InfernoRequest_TableWidget.setEnabled(False)
        self.mainlayout.addWidget(self.InfernoRequest_TableWidget)
        
        self.retranslateUi()
        self.loadInfernoParameters()
        super().setupUi(inferno)


    def retranslateUi(self):
        self.start_pushButton.setText("Start")
        pass