# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'untitled.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!

from script import CONSTANT, ConfigParser, Inferno
from copy import deepcopy

from datetime import date, datetime
from PyQt5 import QtCore, QtGui, QtWidgets

from typing import List, Tuple
import os

class UIcomponent():
    def __init__(self,mainWidgets:QtWidgets.QGroupBox) -> None:
        self.mainWidgets = mainWidgets
    
    def retranslateUi(self):
        pass

    def setlabelSizePolicy(self,label:QtWidgets.QLabel):
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(label.sizePolicy().hasHeightForWidth())
        label.setSizePolicy(sizePolicy)

    def loadInferno(self, inferno:Inferno.Inferno):
        pass

    def updateInferno(self,inferno:Inferno.Inferno):
        pass

class FileBrowser():
    def __init__(self, parent: QtWidgets.QWidget,label:str="",caption:str = None) -> None:
        self.caption  = caption
     

        self.QWidget  = QtWidgets.QFrame(parent)
        self.lineEdit =  QtWidgets.QLineEdit(parent)
        self.button   =  QtWidgets.QToolButton(parent)
        self.callFunc = self.launchFolderDialog

        QtWidgets.QHBoxLayout(self.QWidget)
        self.QWidget.layout().setContentsMargins(0,0,0,0)
        self.QWidget.layout().addWidget(self.lineEdit)
        self.QWidget.layout().addWidget(self.button)

        self.button.clicked.connect(lambda : self.callFunc())
        self.QWidget.setWindowModality(True)

        self.retranslateUi()

    def launchFolderDialog(self):
        resonse = QtWidgets.QFileDialog.getExistingDirectory(
            parent = self.QWidget,
            caption=self.caption,
            directory=os.getcwd()
        )
        if not (resonse==""):
            self.lineEdit.setText(resonse)

    def launchFileDialog(self):
        resonse = QtWidgets.QFileDialog.getOpenFileName(
            parent = self.QWidget,
            caption=self.caption,
            directory=os.getcwd()
        )
        if not (resonse[0]==""):
            self.lineEdit.setText(resonse[0])

    def launchFolderOrFileDialog(self):
        # https://stackoverflow.com/questions/64336575/select-a-file-or-a-folder-in-qfiledialog-pyqt5
        import os
        dialog = QtWidgets.QFileDialog(
            parent = self.QWidget,
            caption=self.caption,
            directory=os.getcwd()
        )

        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog,True)


        dialog.accept = lambda: QtWidgets.QDialog.accept(dialog)
        stackedWidget = dialog.findChild(QtWidgets.QStackedWidget)
        view = stackedWidget.findChild(QtWidgets.QListView)

        def updateText():
            # update the contents of the line edit widget with the selected files
            selected = []
            for index in view.selectionModel().selectedRows():
                selected.append('"{}"'.format(index.data()))
            lineEdit.setText(' '.join(selected))

        view.selectionModel().selectionChanged.connect(updateText)
        lineEdit = dialog.findChild(QtWidgets.QLineEdit)
        dialog.directoryEntered.connect(lambda: lineEdit.setText(''))
        
        response = ""
        if dialog.exec_():
            response = dialog.selectedFiles()[0]

        if not (response==""):
            self.lineEdit.setText(response)


    def retranslateUi(self):
        self.button.setText("...")
        pass

class DateGroupBox(UIcomponent):
    def __init__(self,mainWidgets:QtWidgets.QGroupBox) -> None:
        super().__init__(mainWidgets)
        self.gridLayout = QtWidgets.QGridLayout(mainWidgets)
        
        self.beginLabel = QtWidgets.QLabel(mainWidgets)
        self.gridLayout.addWidget(self.beginLabel, 0, 0, 1, 1)
        self.beginDateEdit = QtWidgets.QDateEdit(mainWidgets)
        self.gridLayout.addWidget(self.beginDateEdit, 0, 1, 1, 1)

        self.endLabel = QtWidgets.QLabel(mainWidgets)
        self.gridLayout.addWidget(self.endLabel, 1, 0, 1, 1)
        self.endDateEdit = QtWidgets.QDateEdit(mainWidgets)
        self.gridLayout.addWidget(self.endDateEdit, 1, 1, 1, 1)
        
        self.getDates()

    def retranslateUi(self):
        self.mainWidgets.setTitle("Date")
        self.endLabel.setText("End ")
        self.beginLabel.setText("Begin")

    def getDates(self)->Tuple[datetime,datetime]:
        """ 
        read the dates and return it as a Tuple[datetime,datetime]
        return (beginDate:datetime,endDate : datetime) 
        """
        beginDate = datetime.fromordinal( self.beginDateEdit.date().toPyDate().toordinal())
        endDate = datetime.fromordinal(   self.endDateEdit  .date().toPyDate().toordinal())
        return beginDate,endDate
    
    def loadInferno(self, inferno: Inferno.Inferno):
        def toQDate(date:datetime)-> QtCore.QDate:
            strDate = date.strftime('%d/%m/%Y')
            return QtCore.QDate.fromString(strDate,"dd/MM/yyyy")

        inputConfig = inferno.parameters.inputConfig
        date_begin : datetime = inputConfig.dates.begin
        end_date : datetime = inputConfig.dates.end

        self.beginDateEdit.setDate(toQDate(date_begin))
        self.endDateEdit.setDate(toQDate(end_date))

    def updateInferno(self, inferno:Inferno.Inferno):
        beginDate,endDate = self.getDates()
        inferno.parameters.inputConfig.dates.begin = beginDate
        inferno.parameters.inputConfig.dates.end = endDate

class IoGroupBox(UIcomponent):
    def __init__(self, mainWidgets: QtWidgets.QGroupBox) -> None:
        super().__init__(mainWidgets)
        self.gridLayout_2 = QtWidgets.QGridLayout(mainWidgets)
        
        self.outputDirLabel = QtWidgets.QLabel(mainWidgets)
        self.outputFileBrowser =  FileBrowser(mainWidgets,caption="Select Output Directory")
        self.setlabelSizePolicy(self.outputDirLabel)
        self.gridLayout_2.addWidget(self.outputDirLabel, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.outputFileBrowser.QWidget, 0, 1, 1, 2)


        self.workingDirLabel = QtWidgets.QLabel(mainWidgets)
        self.setlabelSizePolicy(self.workingDirLabel)
        self.gridLayout_2.addWidget(self.workingDirLabel, 1, 0, 1, 1)
        self.workingDirFileBrowser = FileBrowser(mainWidgets,caption="Select Working Directory")
        self.gridLayout_2.addWidget(self.workingDirFileBrowser.QWidget, 1, 1, 1, 2)

        self.mntLabel = QtWidgets.QLabel(mainWidgets)
        self.setlabelSizePolicy(self.mntLabel)
        self.gridLayout_2.addWidget(self.mntLabel, 2, 0, 1, 1)
        self.mntDirFileBrowser = FileBrowser(mainWidgets,caption="Select Working DSM")
        self.mntDirFileBrowser.callFunc = self.mntDirFileBrowser.launchFolderOrFileDialog
        self.gridLayout_2.addWidget(self.mntDirFileBrowser.QWidget, 2, 1, 1, 2)

    def retranslateUi(self):
        self.mainWidgets.setTitle("IO")
        self.workingDirLabel.setText("Working directory")
        self.outputDirLabel.setText("Output directory")
        self.mntLabel.setText("DSM")

    def getDirs(self):
        workingDir = self.workingDirFileBrowser.lineEdit.text()
        outputDir = self.outputFileBrowser.lineEdit.text()
        MNTFile = self.mntDirFileBrowser.lineEdit.text()
        return workingDir,outputDir,MNTFile

    def loadInferno(self, inferno: Inferno.Inferno):
        inputConfig = inferno.parameters.inputConfig
        self.workingDirFileBrowser.lineEdit.setText(inputConfig.workingDir)
        self.outputFileBrowser.lineEdit.setText(inputConfig.outputDir)
        self.mntDirFileBrowser.lineEdit.setText(inputConfig.mntPath)
    
    def updateInferno(self, inferno: Inferno.Inferno):
        workingDir,outputDir,MNTFile = self.getDirs()
        inferno.parameters.inputConfig.workingDir = workingDir
        inferno.parameters.inputConfig.outputDir = outputDir
        inferno.parameters.inputConfig.mntPath = MNTFile

class RoiGroupBox(UIcomponent):
    def __init__(self, mainWidgets: QtWidgets.QWidget) -> None:
        super().__init__(mainWidgets)
        self.layout = QtWidgets.QGridLayout(mainWidgets)
        self.upperLeftXLabel = QtWidgets.QLabel(mainWidgets)
        self.lowerRigthXLabel = QtWidgets.QLabel(mainWidgets)
        self.lowerRigthYLabel = QtWidgets.QLabel(mainWidgets)
        self.upperLeftYLabel = QtWidgets.QLabel(mainWidgets)

        self.ULXSpinBox = self.createSpinBox(mainWidgets,-180,180)
        self.LRXSpinBox = self.createSpinBox(mainWidgets,-180,180)
        self.ULYSpinBox = self.createSpinBox(mainWidgets,-90,90)
        self.LRYSpinBox = self.createSpinBox(mainWidgets,-90,90)

        self.layout.addWidget(self.upperLeftXLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.upperLeftYLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.lowerRigthYLabel, 3, 0, 1, 1)
        self.layout.addWidget(self.lowerRigthXLabel, 2, 0, 1, 1)

        self.layout.addWidget(self.ULXSpinBox, 0, 1, 1, 1)
        self.layout.addWidget(self.ULYSpinBox, 1, 1, 1, 1)
        self.layout.addWidget(self.LRXSpinBox, 2, 1, 1, 1)
        self.layout.addWidget(self.LRYSpinBox, 3, 1, 1, 1)
    
    def createSpinBox(self,mainWidgets,min:float=-180,max:float=180)->QtWidgets.QDoubleSpinBox:
        spinBox = QtWidgets.QDoubleSpinBox(mainWidgets)
        spinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        spinBox.setDecimals(5)
        spinBox.setMinimum(min)
        spinBox.setMaximum(max)
        return spinBox


    def retranslateUi(self):
        self.mainWidgets.setTitle( "ROI (Region Of Interest)")
        self.upperLeftXLabel.setText ( "Upper Left X  | Long min (°)")
        self.lowerRigthXLabel.setText( "Lower Rigth X | Long max (°)")
        self.lowerRigthYLabel.setText( "Lower Rigth Y | Lat min (°)")
        self.upperLeftYLabel.setText ( "Upper Left Y  | Lat max (°)")

    def getRoi(self):
        ulx = float(self.ULXSpinBox.value())
        uly = float(self.ULYSpinBox.value())
        lrx = float(self.LRXSpinBox.value())
        lry = float(self.LRYSpinBox.value())
        return [ulx,uly,lrx,lry]

    def loadInferno(self, inferno: Inferno.Inferno):
        config = inferno.parameters.inputConfig
        self.ULXSpinBox.setValue(config.ROI.upperLeftX)
        self.ULYSpinBox.setValue(config.ROI.upperLeftY)
        self.LRXSpinBox.setValue(config.ROI.lowerRigthX)
        self.LRYSpinBox.setValue(config.ROI.lowerRigthY)

    def updateInferno(self, inferno: Inferno.Inferno):
        ulx,uly,lrx,lry = self.getRoi()
        inferno.parameters.inputConfig.ROI.upperLeftX = ulx
        inferno.parameters.inputConfig.ROI.upperLeftY = uly
        inferno.parameters.inputConfig.ROI.lowerRigthX = lrx
        inferno.parameters.inputConfig.ROI.lowerRigthY = lry

class ProviderGroupBox(UIcomponent):
    def __init__(self, mainWidgets: QtWidgets.QWidget) -> None:
        super().__init__(mainWidgets)
        self.gridLayout_4 = QtWidgets.QGridLayout(mainWidgets)
        
        self.pepsRadioButton = QtWidgets.QRadioButton(mainWidgets)
        self.pepsRadioButton.setChecked(True)
        self.gridLayout_4.addWidget(self.pepsRadioButton, 0, 0, 1, 1)
        self.SciHubradioButto = QtWidgets.QRadioButton(mainWidgets)
        self.gridLayout_4.addWidget(self.SciHubradioButto, 0, 1, 1, 1)

        self.idLabel = QtWidgets.QLabel(mainWidgets)
        self.gridLayout_4.addWidget(self.idLabel, 1, 0, 1, 1)
        self.idLineEdit = QtWidgets.QLineEdit(mainWidgets)
        self.gridLayout_4.addWidget(self.idLineEdit, 1, 1, 1, 1)
        

        self.passwordLabel = QtWidgets.QLabel(mainWidgets)
        self.gridLayout_4.addWidget(self.passwordLabel, 2, 0, 1, 1)
        self.passwordLineEdit = QtWidgets.QLineEdit(mainWidgets)
        self.passwordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.gridLayout_4.addWidget(self.passwordLineEdit, 2, 1, 1, 1)
        

    def retranslateUi(self):
        self.mainWidgets.setTitle("Provider")
        self.passwordLabel.setText("Password")
        self.idLabel.setText("ID")
        self.pepsRadioButton.setText("PEPS")
        self.SciHubradioButto.setText("Scihub")

    def getProviderSettings(self):
        if self.pepsRadioButton.isChecked():
            PROVIDER = "PEPS"
        else:
            PROVIDER = "SCIHUB"
        
        ID = self.idLineEdit.text()
        PASSWORD = self.passwordLineEdit.text()
        return PROVIDER,ID,PASSWORD

    def onclick(self, inferno:Inferno.Inferno):
        config = inferno.parameters.inputConfig
        if self.pepsRadioButton.isChecked():
            PROVIDER = "PEPS"
        else:
            PROVIDER = "SCIHUB"

        provider = CONSTANT.PROVIDER[PROVIDER]
        auth = config.getAuth(provider)
        if auth is not None:
            self.idLineEdit.setText(auth.id)
            self.passwordLineEdit.setText(auth.password)

    def getProvider(self)->CONSTANT.PROVIDER:
        if self.pepsRadioButton.isChecked():
            PROVIDER = "PEPS"
        else:
            PROVIDER = "SCIHUB"
        return CONSTANT.PROVIDER[PROVIDER]

    def updateInferno(self, inferno: Inferno.Inferno):
        provider = self.getProvider()
        id = self.idLineEdit.text()
        password = self.passwordLineEdit.text() 
        inferno.parameters.inputConfig.provider = provider
        inferno.parameters.inputConfig.auth.id = id
        inferno.parameters.inputConfig.auth.password = password

    def loadInferno(self, inferno: Inferno.Inferno):


        config = inferno.parameters.inputConfig
        if config.provider == CONSTANT.PROVIDER.PEPS:
            self.pepsRadioButton.setChecked(True)
        else:
            self.SciHubradioButto.setChecked(True)

        self.idLineEdit.setText(config.getProviderAuth().id)
        self.passwordLineEdit.setText(config.getProviderAuth().password)

        self.pepsRadioButton.clicked.connect(lambda:self.onclick(inferno))
        self.SciHubradioButto.clicked.connect(lambda:self.onclick(inferno))

class LoadParametersGroupBox(UIcomponent):
    def __init__(self, mainWidgets: QtWidgets.QWidget) -> None:
        super().__init__(mainWidgets)


        self.gridLayout_5 = QtWidgets.QGridLayout(mainWidgets)
        self.parametersFileBrowser =  FileBrowser(mainWidgets)
        self.gridLayout_5.addWidget(self.parametersFileBrowser.QWidget, 0, 1, 1, 2)
        self.setupUi()

    def setupUi(self):
        self.parametersFileBrowser.callFunc = self.parametersFileBrowser.launchFileDialog
    
    def retranslateUi(self):
        self.mainWidgets.setTitle("Load parameters")

    def loadInferno(self,inferno):
        self.parametersFileBrowser.lineEdit.setText(inferno.parameters.inputConfig.parametersFile)

    def updateInferno(self, inferno: Inferno.Inferno):
        parametersPath = self.parametersFileBrowser.lineEdit.text()
        if parametersPath=="":
            return 

        try:
            inferno.importParameters(parametersPath)
        except Exception as e :
            import traceback
            print("error:LoadParametersGroupBox.updateInferno")
            print(traceback.format_exc())
            
class Ui_Dialog(object):
    def addUIcomponentWidget(self,widget:UIcomponent):
        self.mainWidgets.layout().addWidget(widget.mainWidgets)
        self.listUIcomponent.append(widget)

    def LoadFromFileQPushButton(self, parent: QtWidgets.QWidget) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(parent)
        button.clicked.connect( lambda : self.launchFileDialog())
        return button

    def launchFileDialog(self):
        import os
        resonse = QtWidgets.QFileDialog.getOpenFileName(
            parent = self.mainWidgets,
            caption="Select Input settings file",
            directory=os.getcwd()
        )
        try:
            if resonse[0]:
                self.fileName = resonse[0]
                self.loadInfernoFromFile(self.fileName)
        except Exception:
            print("error: launchFileDialog")
            import traceback
            traceback.print_exc()

    def loadInferno(self,inferno:Inferno.Inferno):
        """ 
        read parameters from self.inferno and display it on the form
        """
        for uiComponent in self.listUIcomponent:
            uiComponent.loadInferno(inferno)
        # self.dateGroupBox.loadInferno(inferno)
        # self.ioGroupBox.loadInferno(inferno)
        # self.roiGroupBox.loadInferno(inferno)
        # self.providerGroupBox.loadInferno(inferno)

    def loadInfernoFromFile(self,filename):
        """ 
        read inferno configuration file and display it on the form 
        """
        tmpInfero = deepcopy(self.inferno)
        # tmpInfero.parameters.inputConfig = ConfigParser.InputConfig.fromFile(filename)
        #  
        tmpInfero.importInputConfig(filename)
        self.loadInferno(tmpInfero)

    def updateInferno(self,inferno:Inferno.Inferno):
        inferno_tmp = deepcopy(self.inferno)
        for uiComponent in self.listUIcomponent:
            uiComponent.updateInferno(inferno)
        return True

    def saveParameters(self):
        resonse = QtWidgets.QFileDialog.getSaveFileName(
            parent = self.mainWidgets,
            caption="Save",
            directory=os.getcwd(),
            filter = "YAML Files (*.yaml *.yml)",
            

        )[0]

        if resonse:
            if os.path.splitext(resonse)[1] in [".yaml",".yml"]:
                pass
            elif os.path.splitext(resonse)[1] == "":
                resonse += ".yaml" 

            print(resonse)
            self.updateInferno(self.inferno)
            self.inferno.exportInputConfig(resonse)


    def setupUi(self, Dialog:QtWidgets.QWidget,inferno:Inferno.Inferno):
        Dialog.setWindowModality(True)
        self.inferno = inferno
        self.listUIcomponent:List[UIcomponent] = []

        self.mainWidgets = Dialog
        Dialog.resize(307, 652)
        self.mainWidgets.setMinimumWidth(500)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)

        self.loadPushButton = self.LoadFromFileQPushButton(Dialog)
        self.verticalLayout.addWidget(self.loadPushButton)
        
        self.dateGroupBox = DateGroupBox(QtWidgets.QGroupBox(Dialog))
        self.addUIcomponentWidget(self.dateGroupBox )

        self.roiGroupBox = RoiGroupBox(QtWidgets.QGroupBox(Dialog))
        self.addUIcomponentWidget(self.roiGroupBox)

        self.ioGroupBox = IoGroupBox(QtWidgets.QGroupBox(Dialog))
        self.addUIcomponentWidget(self.ioGroupBox)

        self.providerGroupBox = ProviderGroupBox(QtWidgets.QGroupBox(Dialog))
        self.addUIcomponentWidget(self.providerGroupBox)

        self.loadParametersGroupBox = LoadParametersGroupBox(QtWidgets.QGroupBox(Dialog))
        self.addUIcomponentWidget(self.loadParametersGroupBox )

        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        
        self.dialogButtonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.dialogButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.dialogButtonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Save)
     
        self.dialogButtonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect( lambda : self.accept(Dialog))
        self.dialogButtonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect( lambda : self.accept(Dialog) )
        self.dialogButtonBox.button(QtWidgets.QDialogButtonBox.Save).clicked.connect( self.saveParameters )

        self.mainWidgets.layout().addWidget( self.dialogButtonBox )
        self.retranslateUi()
        self.loadInferno(self.inferno)

    def accept(self,Dialog):
        res = self.updateInferno(self.inferno)
        if res : return Dialog.accept()
        else: return Dialog.reject()
    
    def reject(self,Dialog):
        Dialog.reject()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        # Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.loadPushButton.setText("Load From File")
        self.mainWidgets.setWindowTitle("Input Settings")
        self.dateGroupBox.retranslateUi()
        self.ioGroupBox.retranslateUi()
        self.roiGroupBox.retranslateUi()
        self.providerGroupBox.retranslateUi()
        self.loadParametersGroupBox.retranslateUi()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())