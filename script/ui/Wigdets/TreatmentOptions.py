from dataclasses import dataclass
from typing import ItemsView
from PyQt5 import QtCore, QtGui, QtWidgets
from numpy import product

from script import Scenarios

from ... import CONSTANT
from ..  import Common
from ... import S1Product
from ... import Inferno

from typing import List

class MemoyEstimation(Common.UIcomponent):
    def __init__(self, parent: QtWidgets.QWidget,inferno:Inferno.Inferno) -> None:
        super().__init__(parent)
        self.inferno = inferno
        self.Proposition = self.inferno.chosenPriorityProposition
        self.estimation = inferno.sizeEstimation(self.Proposition)
        self.downloadSizeEstimation = self.estimation.downloadSize
        self.totalSizeEstimation = self.estimation.totalSize
        
        
        self.QWidget:QtWidgets.QGroupBox = QtWidgets.QGroupBox(parent=parent)
        self.downloadSizeLabel = QtWidgets.QLabel(parent)
        self.totalSizeLabel = QtWidgets.QLabel(parent)

        self.QWidget.setLayout(QtWidgets.QVBoxLayout())
        self.QWidget.layout().addWidget(self.downloadSizeLabel)
        self.QWidget.layout().addWidget(self.totalSizeLabel)


        self.retranslateUi()

        self.setEstimationLabels(
            downloadSizeEstimation=self.downloadSizeEstimation,
            totalSizeEstimation=self.totalSizeEstimation
        )
    

    def updateEstimation(self):
        self.estimation = self.inferno.sizeEstimation(self.Proposition)
        self.downloadSizeEstimation = self.estimation.downloadSize
        self.totalSizeEstimation = self.estimation.totalSize
        self.setEstimationLabels(
            downloadSizeEstimation=self.downloadSizeEstimation,
            totalSizeEstimation=self.totalSizeEstimation
        )

    def setEstimationLabels(self,downloadSizeEstimation:int,totalSizeEstimation:int):
        downloadSizeLabelTexte = f"Download File Sizes Estimation: {downloadSizeEstimation/1e3:.2f} GB" 
        totalSizeLabelTexte = f"Total Size Estimation: {totalSizeEstimation/1e3:.2f} GB" 

        self.downloadSizeLabel.setText(downloadSizeLabelTexte)
        self.totalSizeLabel.setText(totalSizeLabelTexte)

    def retranslateUi(self):
        super().retranslateUi()
        self.QWidget.setTitle("Memory Size Estimation")
    pass

class AmplitudePhase(Common.OptionQGroupBox):
    def setupUi(self, inferno: Inferno.Inferno):
        super().setupUi(inferno.parameters)
        self.defaultCheckboxSetUp(inferno.parameters.treatment.amplitudePhase)
        self.retranslateUi()

        self._getCheckBox("activate").stateChanged.connect(self.onActivateStateChanged)
        self.onActivateStateChanged()

    def onActivateStateChanged(self):
        state = self.checkBoxIsChecked("activate")
        self._getCheckBox("orthorectification").setEnabled(state)


    def retranslateUi(self):
        super().retranslateUi()
        self.setCheckBoxText("activate","Compute Amplitude/Phase images ")
        self.setCheckBoxText("orthorectification","Orthorectification")

class SwathChoises(Common.OptionQGroupBox):
    def setupUi(self, inferno: Inferno.Inferno):
        self.inferno = inferno
        self.proposition = self.inferno.chosenPriorityProposition
        
        self.setLayout(QtWidgets.QHBoxLayout())
        for swath in self.proposition.swathsChoises:
            checkbox = self.newCheckBox(swath)
            self.setCheckBoxText(swath,swath)
            self.layout().addWidget(checkbox)
        self.setEnabled(self.proposition.chosenSwathsIsEdible)
        self.loadInfernoParameters()
        self.retranslateUi()
        
    def retranslateUi(self):
        self.setTitle("Swath")

    def loadInfernoParameters(self):
        for swath in self.proposition.chosenSwaths:
            self.setChecked(swath,True)

    def saveInfernoParameters(self):
        if not self.proposition.chosenSwathsIsEdible:
            return 

        self.proposition.chosenSwaths = []
        for swath in self.proposition.swathsChoises:
            if self.checkBoxIsChecked(swath):
                self.proposition.chosenSwaths.append(swath)
        return super().saveInfernoParameters()

class PolarizationChoises(Common.UIcomponent):

    def __init__(self, parent: QtWidgets.QWidget,inferno:Inferno.Inferno) -> None:
        super().__init__(parent)
        self.inferno = inferno
        self.proposition = self.inferno.chosenPriorityProposition
        self.QWidget    :QtWidgets.QGroupBox = QtWidgets.QGroupBox(self.parent)
        self.comboBox   :QtWidgets.QComboBox = QtWidgets.QComboBox(self.QWidget)
        
        self.comboBoxChoises = self.proposition.polarizationChoises
        # self.comboBoxChoises = CONSTANT.POLARIZATION.allCombinations(self.proposition.polarizationChoises)
        for polarizationChoise in self.comboBoxChoises:
            self.comboBox.addItem(str(polarizationChoise))

        self.QWidget.setLayout(QtWidgets.QVBoxLayout())
        self.QWidget.layout().addWidget(self.comboBox)
        self.loadInferno()
        self.retranslateUi()

    def retranslateUi(self):
        self.QWidget.setTitle("Polarization Choices")
    
    def chosenPolarization(self):
        ind = self.comboBox.currentIndex()
        return self.comboBoxChoises[ind]

    def loadInferno(self):
        index = self.comboBoxChoises.index(self.proposition.chosenPolarization)
        self.comboBox.setCurrentIndex(index)

    def updateInferno(self, inferno: Inferno.Inferno):
        inferno.chosenPriorityProposition.chosenPolarization = self.chosenPolarization()

class TableWidget(Common.TableWidget):
    '''
    Display selected elements
    '''
    list_attribut = [
            "Name",
            "Date",
            'Orbit Numer',
            'Orbit Type',
            'Satellite',
            "Polarization",
            'Quicklook',
            'Provider',
            "location",
            "Available"

        ]
    class Item():
        pixelMapScale = (200,200)

        def __init__(self,product:S1Product.S1Product) -> None:
            self.product = product

        def displayItem(self,tableWidget:Common.TableWidget):
            itemRow = tableWidget.rowCount()
            tableWidget.setRowCount(itemRow+1)
            tableWidget.set_text(itemRow,'Name'     ,self.product.name  , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'Date'     ,self.product.date  , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'Orbit Numer'  ,self.product.orbitNumber   , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'Orbit Type'   ,self.product.orbitType , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'Satellite'    ,self.product.satellite , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'Polarization' ,self.product.polarization  , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'Provider'     ,self.product.provider  , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'location'      ,self.product.location , inRed= (not self.product.available))
            tableWidget.set_text(itemRow,'Available'      ,self.product.available , inRed= (not self.product.available))
            tableWidget.setQuicklook(itemRow            ,self.product)

    def __init__(self, parent: QtWidgets,chosenPriorityProposition:Scenarios.Proposition):
        super().__init__(parent, self.list_attribut)
        self.setSortingEnabled(True)
        PriorityProposition = chosenPriorityProposition
        self.PriorityPropositionList = PriorityProposition.list
        self.PriorityPropositionKey = PriorityProposition.name
        self.fillTable()        

    def fillTable(self):    
        self.setSortingEnabled(False)
        liste = self.PriorityPropositionList
        for ele in liste:
            TableWidget.Item(ele).displayItem(self)
        self.setSortingEnabled(True)

class CreationOption(Common.OptionQGroupBox):
    class SnapHUSettings(Common.OptionQGroupBox.AdvanceSettingsWindows):
        def setupUi(self):
            mainWidget: QtWidgets = self.mainWidget
            option : Inferno.SnapHuParameters = self.option

            gridlayout = QtWidgets.QGridLayout()
            mainWidget.layout().addLayout(gridlayout)


            self.lpNormeLabel = QtWidgets.QLabel(self.mainWidget)
            self.lpNormeInput =  QtWidgets.QLineEdit(self.mainWidget)
            validator = QtGui.QRegExpValidator(QtCore.QRegExp(r'([0-9]*[.])?[0-9]+'))
            self.lpNormeInput.setValidator(validator)


            self.initAlgoLabel = QtWidgets.QLabel(self.mainWidget)
            self.initAlgoComboBox = QtWidgets.QComboBox()
            for ele in option.initializationAlgorithm.__class__:
                self.initAlgoComboBox.addItem(str(ele))

            self.statisticalCostLabel = QtWidgets.QLabel(self.mainWidget)
            self.statisticalCostComboBox = QtWidgets.QComboBox()
            for ele in option.statisticalCost.__class__:
                self.statisticalCostComboBox.addItem(str(ele))

            gridlayout.addWidget(self.initAlgoLabel,0,0)
            gridlayout.addWidget(self.initAlgoComboBox,0,1)

            gridlayout.addWidget(self.statisticalCostLabel,1,0)
            gridlayout.addWidget(self.statisticalCostComboBox,1,1)

            gridlayout.addWidget(self.lpNormeLabel,2,0)
            gridlayout.addWidget(self.lpNormeInput,2,1)


            
            self.loadParameters()
            self.retranslate()


        def retranslate(self):
            self.initAlgoLabel.setText("Initialization algorithm")
            self.statisticalCostLabel.setText("Statistical-cost")
            self.lpNormeLabel.setText("Lp-norm (NOSTATCOSTS only)")

        def updateInferno(self):
            option : Inferno.SnapHuParameters = self.option
            initializationAlgorithm = self.initAlgoComboBox.currentText()
            StatisticalCost = self.statisticalCostComboBox.currentText()
            
            lpNorm = self.lpNormeInput.text()
            option.initializationAlgorithm = Inferno.SnapHuParameters.InitializationAlgorithm[initializationAlgorithm]
            option.statisticalCost = Inferno.SnapHuParameters.StatisticalCost[StatisticalCost]
            try:
                option.lpNorm = float(lpNorm)
            except Exception as e:
                print(e)
            print(option)
            pass
        
        def loadParameters(self):
            initializationAlgorithm = self.option.initializationAlgorithm
            StatisticalCost = self.option.statisticalCost
            lpNorm = self.option.lpNorm

            self.lpNormeInput.setText(str(lpNorm))
            index = self.initAlgoComboBox.findText(str(initializationAlgorithm), QtCore.Qt.MatchFixedString)
            print(index)
            if index >= 0:
                self.initAlgoComboBox.setCurrentIndex(index)

            index = self.statisticalCostComboBox.findText(str(StatisticalCost), QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.statisticalCostComboBox.setCurrentIndex(index)
            pass

    def openSnapHuWindow(self):
        Dialog = QtWidgets.QDialog(self)
        advanceSettingsWindows = CreationOption.SnapHUSettings(
            Dialog=Dialog,
            option=self.infernoParameters.treatment.creationOption.phaseUnwrapping)
        Dialog.show()

    def setupUi(self, inferno: Inferno.Inferno):
        super().setupUi(inferno.parameters)
        self.defaultCheckboxSetUp(inferno.parameters.treatment.creationOption)
        self.retranslateUi()
        self._getCheckBox("orthorectification").setEnabled(False)

        self.setOptionWithParametersCallFunction(
            "phaseUnwrapping",
            lambda : self.openSnapHuWindow())


class MasterImage(QtWidgets.QGroupBox):
    """
    Class to handle the choise of master image strategy: 
        - moving or fix
        - choice which master image for the fix option  
    """
    def setupUiComboBox(self)->QtWidgets.QComboBox: 
        self.ComboBox = QtWidgets.QComboBox(self)

        for product in sorted(self.inferno.chosenPriorityProposition.list,key=lambda x:x.date):
            self.ComboBox.addItem(product.name)

        def hideComboBox():
            self.ComboBox.hide()
        def showComboBox():
            self.ComboBox.show()  
        self.fixRadioButton.clicked.connect(showComboBox)
        self.movingRadioButton.clicked.connect(hideComboBox)
        self.layout().addWidget(self.ComboBox)

    def setupUi(self,inferno:Inferno.Inferno):
        self.inferno = inferno
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        
        self.setupUiChoiceLayout()
        self.setupUiComboBox()
        
        self.loadInfernoParameters()
        self.retranslateUi()
    
    def setupUiChoiceLayout(self):
        # Layout
        frame = QtWidgets.QFrame(self)
        choiceLayout = QtWidgets.QHBoxLayout(frame)
        # self.choiceLayout.setContentsMargins(9, 0, 9, 0)
        # fix Master Image option
        self.fixRadioButton = QtWidgets.QRadioButton(frame)
        self.fixRadioButton.setChecked(True)
        choiceLayout.addWidget(self.fixRadioButton)
        # moving Master Image Option
        self.movingRadioButton = QtWidgets.QRadioButton(self)
        choiceLayout.addWidget(self.movingRadioButton)

        self.layout().addWidget(frame)

    def retranslateUi(self):
        self.setTitle("Master Image")
        self.fixRadioButton.setText("Fix")
        self.movingRadioButton.setText("Moving")

    def getState(self)->CONSTANT.MASTER_IMAGE:
        if self.fixRadioButton.isChecked():
            return CONSTANT.MASTER_IMAGE.FIX
        elif self.movingRadioButton.isChecked():
            return CONSTANT.MASTER_IMAGE.MOVING
        return None

    def getChosenMasterImageIndex(self)->int:
        return self.ComboBox.currentIndex()

    def loadInfernoParameters(self):
        if self.inferno.parameters.treatment.masterImage.strategy == CONSTANT.MASTER_IMAGE.FIX:
            self.fixRadioButton.setChecked(True)
            self.ComboBox.show()
        elif self.inferno.parameters.treatment.masterImage.strategy ==  CONSTANT.MASTER_IMAGE.MOVING:
            self.movingRadioButton.setChecked(True)
            self.ComboBox.hide()

    def saveInfernoParameters(self):
        self.inferno.parameters.treatment.masterImage.strategy =  self.getState()
        if self.getState() == CONSTANT.MASTER_IMAGE.FIX:
            productInd = self.getChosenMasterImageIndex() 
            product = self.inferno.chosenPriorityProposition.list[productInd]
            self.inferno.parameters.treatment.masterImage.masterImageProduct = product

if __name__ == "__main__":
    import argparse
    from .... import ConfigParser    
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", default="input.yml", type=str)
    parser.add_argument("-p", default="PEPS", type=str)
    args = parser.parse_args()
    config_path = args.i
    provider = args.p

    # Parse config file
    config = ConfigParser.read(config_path)
    # list_product  = S1Product.InfernoProducts.request(config,provider)
    list_product  = S1Product.InfernoProducts.example()

    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = MainQWidget()
    ui.setupUi(list_product)
    ui.show()
    sys.exit(app.exec_())
