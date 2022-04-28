from dataclasses import dataclass
from typing import List
import typing
from PyQt5 import QtCore, QtGui, QtWidgets
from enum import Enum,Flag, IntEnum,auto,unique

from script.ui import Wigdets
from .. import S1Product
from .. import Inferno


class UIcomponent():
    def __init__(self,parent:QtWidgets.QWidget) -> None:
        self.parent = parent
        self.QWidget:QtWidgets.QWidget = None
    
    def retranslateUi(self):
        pass

    def setlabelSizePolicy(self,label:QtWidgets.QLabel):
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(label.sizePolicy().hasHeightForWidth())
        label.setSizePolicy(sizePolicy)

    def loadInferno(self, inferno:Inferno.Inferno)->None:
        pass

    def updateInferno(self,inferno:Inferno.Inferno):
        pass

class window(QtWidgets.QWidget):
    '''
    Define some default setting and common methodes
    '''
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.saveInfernoParameters()
        return super().closeEvent(a0)

    def isComplete(self)->bool:
        pass

    def setupUi(self,inferno:Inferno.Parameters):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.loadInfernoParameters()

    def saveInfernoParameters(self) -> None:
        pass

    def loadInfernoParameters(self)-> None:
        pass
    
class OnThread_PushButton(QtWidgets.QPushButton):
    """
    Define a PushButton which will run a function in a thread.
    start_function  : function run before the thread (run out the thread)
    run_function    : function run on the thread
    end_function    : function run after the thread have finished (run out the thread) 
    """

    def __init__(self,parent,
        run_function,
        before_run_function=None,
        end_function = None ) -> None:
        super().__init__(parent)
        self.before_run_function = before_run_function
        self.run_function = run_function
        self.end_function = end_function
        self.clicked.connect( self.runLongTask )
        self.before_run_out = False


    def finish(self):
        self.setEnabled(True)
        if callable(self.end_function):
            self.end_function()
    
    def before_run(self):
        self.setEnabled(False)
        if callable(self.before_run_function):
            return self.before_run_function()
        return True

    class Worker(QtCore.QObject):
        finished = QtCore.pyqtSignal()
        progress = QtCore.pyqtSignal(int)

        def __init__(self,func) -> None:
            super().__init__()
            self.func = func

        def run(self):
            """Long-running task."""
            self.func()
            self.finished.emit()

    def runLongTask(self):
        if self.before_run() is False:
            return self.setEnabled(True)

        # Step 2: Create a QThread object
        self.thread = QtCore.QThread()
        # Step 3: Create a worker object
        self.worker = self.Worker(self.run_function)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Step 6: Start the thread

        self.thread.start()
        self.thread.finished.connect(self.finish)

class TableWidget(QtWidgets.QTableWidget):

    def __init__(self,parent:QtWidgets,list_attribut:List[str]):
        super().__init__(parent)
        self.list_attribut = list_attribut
        self.init_column()
        self.init_row()
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.list_item = []

    def init_column(self):
            nb_col = len(self.list_attribut)
            self.setColumnCount(nb_col)

            for i,col_name in enumerate(self.list_attribut):
                item = QtWidgets.QTableWidgetItem()
                item.setText(col_name)
                
                self.setHorizontalHeaderItem(i, item)
            # self.horizontalHeader().setSortIndicatorShown(True)
            self.setSortingEnabled(True)

    def init_row(self):
        self.setRowCount(0)

    def clearContents(self) -> None:
        self.list_item.clear()
        super().clearContents()
        self.setRowCount(0)
        # self.setSortingEnabled(False)
    
    def getImageLabel(self,product:S1Product.S1Product):
        """ 
        Load S1Product.S1Product quicklook into quicklookLabel
        """
        image_path = product.quicklook
        imageLabel = quicklookLabel(self,product)
        imageLabel.setText("")
        imageLabel.setScaledContents(True)
        pixmap = QtGui.QPixmap()
        pixmap.load(image_path)
        pixmap = pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio) 

        imageLabel.setPixmap(pixmap)
        imageLabel.setScaledContents(True)
        return imageLabel

    def set_text(self,
        itemRow:int,
        attribut:str,
        text:str,
        inRed:bool):
        """ Set text on   """
        item = QtWidgets.QTableWidgetItem()
        self.setItem(itemRow, self.list_attribut.index(attribut), item)
        item.setText(str(text))
        if inRed:
            _brush = QtGui.QBrush(QtCore.Qt.red)
            item.setForeground(_brush)

    def setQuicklook(self,itemRow,product):
        self.setCellWidget(
                itemRow,
                self.list_attribut.index("Quicklook"),
                self.getImageLabel(product)
            )
        self.horizontalHeader().setSectionResizeMode(
            self.list_attribut.index("Quicklook"),
            QtWidgets.QHeaderView.ResizeToContents
            )
        self.verticalHeader().setSectionResizeMode(
            itemRow,
            QtWidgets.QHeaderView.ResizeToContents
            )        

class CenteredCheckBock(QtWidgets.QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        QtWidgets.QHBoxLayout(self)
        self.layout().setAlignment(QtCore.Qt.AlignCenter)
        self.checkBox = QtWidgets.QCheckBox()
        self.layout().addWidget(self.checkBox)

class quicklookLabel(QtWidgets.QLabel):
    '''
    Define QtWidgets.QLabel to dispay an image 
    which open a new window when clicked
    '''
    class ImageWindows(object):
        """ 
        New open winwdow caracteristics
        """
        def setupUi(self, 
                MainWindow: QtWidgets.QMainWindow,
                product : S1Product.S1Product):

            image_path = product.quicklook
            image_name = product.name    
            MainWindow.resize(800, 600)
            self.centralwidget = QtWidgets.QWidget(MainWindow)
            MainWindow.setWindowTitle(image_name)

            self.imageLabel = QtWidgets.QLabel(self.centralwidget)
            self.imageLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
            self.imageLabel.setText("")
            
            pixmap1 = QtGui.QPixmap(image_path)
            width, height =pixmap1.size().width(),pixmap1.size().height()
            self.imageLabel.setPixmap(pixmap1)

            self.imageLabel.setGeometry(QtCore.QRect(0, 0, width, height))
            self.imageLabel.setScaledContents(False)
            # MainWindow.resize(width, height)
            MainWindow.setFixedSize(width, height)
            self.imageLabel.setAlignment(QtCore.Qt.AlignCenter)
            MainWindow.setCentralWidget(self.centralwidget)
            
            # self.retranslateUi(MainWindow)
            QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def __init__(self,parent:QtWidgets,product):
        super(quicklookLabel,self).__init__(parent)
        self.S1product = product
        self.parent = parent

    def mousePressEvent(self, event):
        if not hasattr(self,"MainWindow"):
            self.MainWindow = QtWidgets.QMainWindow(self.parent)

        ui = quicklookLabel.ImageWindows()
        ui.setupUi(self.MainWindow,self.S1product)
        self.MainWindow.show()
        self.MainWindow.activateWindow()



    # def retranslateUi(self, MainWindow):
    #     _translate = QtCore.QCoreApplication.translate
    #     MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

class OptionQGroupBox(QtWidgets.QGroupBox):
    """
    Define a class to handle the creation of a widget with only checkboxes
    """
    class AdvanceSettingsWindows():
        def __init__(self,Dialog:QtWidgets.QDialog,option:Inferno.OptionWithParameters) -> None:
            self.mainWidget = Dialog
            self.option = option
            # self.items = []

            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
            Dialog.setSizePolicy(sizePolicy)
            QtWidgets.QVBoxLayout(Dialog)

            self.setupUi()
            self.dialogButtonBox = QtWidgets.QDialogButtonBox(Dialog)
            self.dialogButtonBox.setOrientation(QtCore.Qt.Horizontal)
            self.dialogButtonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)


            self.dialogButtonBox.accepted.connect(lambda : self.accept(Dialog))
            self.dialogButtonBox.rejected.connect(lambda : self.reject(Dialog)) 
            self.mainWidget.layout().addWidget( self.dialogButtonBox )


        def setupUi(self):
            option = self.option
            # print(option.__annotations__.items())
            for optionName,optionClass in option.__annotations__.items():
                print("optionClass",optionClass)
                if issubclass(optionClass,int) or issubclass(optionClass,float): 
                    self.mainWidget.layout().addWidget(
                        self.newline(optionName,optionClass))
                elif issubclass(optionClass,Enum):
                    self.mainWidget.layout().addWidget(
                        self.addChoiceList(optionName,optionClass))

            self.loadParameters()
            self.mainWidget.setWindowTitle(camelCaseToText(option.__class__.__name__))

        def addChoiceList(self,optionName,optionClass):
            widget   = QtWidgets.QFrame(self.mainWidget)
            title    = QtWidgets.QLabel(self.mainWidget)
            comboBox = QtWidgets.QComboBox(self.mainWidget)
            for ele in optionClass:
                comboBox.addItem(str(ele))
            # self.items.append(optionName)
            title.setText(camelCaseToText(optionName).capitalize())
            QtWidgets.QVBoxLayout(widget)
            widget.layout().addWidget(title)
            widget.layout().addWidget(comboBox)

            return widget

        def newline(self,optionName:str,optionClass):
            """ 
            add a QDoubleSpinBox attribut to self named as optionName
            """
            widget   = QtWidgets.QFrame(self.mainWidget)
            title    = QtWidgets.QLabel(self.mainWidget)
            # inputText=  QtWidgets.QDoubleSpinBox(self.mainWidget)
            inputText =  QtWidgets.QLineEdit(self.mainWidget)
            inputText.setText("0")
            # validator = QtGui.QRegExpValidator(QtCore.QRegExp(r'[0-9].+'))

            validator = ""
            if issubclass(optionClass,int):
                validator = QtGui.QRegExpValidator(QtCore.QRegExp(r'[0-9]+$'))
            else:
                validator = QtGui.QRegExpValidator(QtCore.QRegExp(r'\d+\.?\d*'))
            inputText.setValidator(validator)
            setattr(self,optionName,inputText)

            title.setText(camelCaseToText(optionName))
            QtWidgets.QHBoxLayout(widget)
            widget.layout().addWidget(title)
            # widget.layout().addWidget(title)
            widget.layout().addWidget(inputText)
            # self.items.append(optionName)
            return widget

        def accept(self,Dialog):
            try:
                self.updateInferno()#self.option)
                Dialog.accept()
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                print(e)
                Dialog.reject()
                
        def reject(self,Dialog):
            Dialog.reject()

        def updateInferno(self):
            option = self.option
            for optionName,optionClass in option.__annotations__.items():
                if issubclass(optionClass,int) or issubclass(optionClass,float): 
                    inputText : QtWidgets.QDoubleSpinBox = getattr(self,optionName)
                    setattr(option,optionName,optionClass(inputText.text()))
                elif issubclass(optionClass,Enum):
                    pass

        def loadParameters(self):#,option:Inferno.OptionWithParameters):
            option = self.option
            for optionName,optionClass in option.__annotations__.items():
                if issubclass(optionClass,int) or issubclass(optionClass,float): 
                    attrbut = getattr(option,optionName)
                    inputText : QtWidgets.QLineEdit = getattr(self,optionName)
                    inputText.setText(str(attrbut))
                elif issubclass(optionClass,Enum):
                    pass
                # setattr(option,optionName,optionClass(inputText.text()))

    def newCheckBox(self,name:str):
        # Create new QtWidgets.QCheckBox attribut to self 
        # and save it in self.list_CheckBox list.
        # The new attibut name is to checkBox_{name}, for example:
        # 
        # self.newCheckBox("toto") 
        # type(self.checkBox_toto) -> QtWidgets.QCheckBox

        if not hasattr(self,"list_CheckBox"):
            self.list_CheckBox:List[QtWidgets.QCheckBox] = []
            self.list_CheckBox_name = []
        attr_name = "checkBox_{}".format(name)
        checkBox = QtWidgets.QCheckBox(self)
        checkBox.setChecked(False)
        setattr(self,attr_name,checkBox)
        self.list_CheckBox.append(checkBox )
        self.list_CheckBox_name.append( name )
        return checkBox

    def _getCheckBox(self,attri) ->QtWidgets.QCheckBox:
        checkBox = getattr(self,"checkBox_{}".format(attri) )
        return checkBox

    def setCheckBoxText(self,attri,text):
        checkBox = self._getCheckBox(attri)
        checkBox.setText(text)
    
    def setupUi(self,infernoParameters:Inferno.Parameters):
        self.infernoParameters = infernoParameters
        pass
    
    def checkBoxIsChecked(self,attri):
        checkBox = self._getCheckBox(attri)
        return checkBox.isChecked()

    def setChecked(self,name,status:bool):
        checkBox = self._getCheckBox(name)
        checkBox.setChecked(status)

    def saveInfernoParameters(self):
        if hasattr(self,"_default"):
            self.defaultSaveInfernoParameters()
        
    def loadInfernoParameters(self):
        if hasattr(self,"_default"):
            self.defaultLoadInfernoParameters()
    
    def openAdvanceSetting(self,option:Inferno.OptionWithParameters):
        Dialog = QtWidgets.QDialog(self)
        advanceSettingsWindows = OptionQGroupBox.AdvanceSettingsWindows(
            Dialog=Dialog,
            option=option)
        Dialog.show()

    def setupUiOptionWithParameters(self,optionName,option):
        widget = QtWidgets.QFrame(self)
        button   =  QtWidgets.QToolButton(widget)
        checkBox = self.newCheckBox(optionName)

        if not hasattr(self,"advanceSetting_call_fonction"):
            self.advanceSetting_call_fonction = {}

        button.setText("...")
        self.advanceSetting_call_fonction[optionName] = lambda : self.openAdvanceSetting(option)
        self.setCheckBoxText(optionName ,camelCaseToText(optionName).capitalize())
        button.clicked.connect(
            lambda : (self.advanceSetting_call_fonction[optionName]())
            )
        # button.clicked.connect(lambda : self.openAdvanceSetting(option))
        
        QtWidgets.QHBoxLayout(widget)
        widget.layout().setContentsMargins(0,0,0,0)
        widget.layout().addWidget(checkBox)
        widget.layout().addWidget(button)
        return widget
    
    def setOptionWithParametersCallFunction(self,optionName:str,func):
        # print("setOptionWithParametersCallFunction",self.advanceSetting_call_fonction)
        self.advanceSetting_call_fonction[optionName] = func
        # print("setOptionWithParametersCallFunction",self.advanceSetting_call_fonction)


    def defaultCheckboxSetUp(self,object:dataclass):
        # Create a Checkbox for each attributs of nameList dataclass
        # object : dataclass with only bool attributs
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self._default = object
        for optionName,optionType in object.__annotations__.items():
            if (optionType is bool):
                checkBox = self.newCheckBox(optionName)
                self.mainLayout.addWidget( checkBox ) 
                self.setCheckBoxText(optionName ,camelCaseToText(optionName).capitalize())
            elif issubclass(optionType,Inferno.OptionWithParameters):
                option = getattr(object,optionName)
                checkBox = self.setupUiOptionWithParameters(optionName,option)
                self.mainLayout.addWidget( checkBox ) 
                
        self.setTitle(camelCaseToText(self.__class__.__name__).capitalize())
        self.loadInfernoParameters()

    def defaultSaveInfernoParameters(self):
        for attrName,attrType in self._default.__annotations__.items():
            if issubclass(attrType,Inferno.OptionWithParameters):
                attri:Inferno.OptionWithParameters = getattr(self._default,attrName)
                attri.activate = self.checkBoxIsChecked(attrName)
            elif attrType is bool:
                setattr(self._default,
                        attrName,
                        self.checkBoxIsChecked(attrName))

    def defaultLoadInfernoParameters(self):
        # return
        for attrName,attrType in self._default.__annotations__.items():
            if not ( (attrType is bool) or issubclass(attrType,Inferno.OptionWithParameters) ):
                continue
            if attrType is bool:
                status = getattr(self._default,attrName)
            elif issubclass(attrType,Inferno.OptionWithParameters):
                status = getattr(self._default,attrName).activate
            self.setChecked(attrName,status)

    def retranslateUi(self):
        pass
    
    def setFunOnStateChanged(self,fun:callable):
        if hasattr(self,"_default"):
            for checkbox in self.list_CheckBox:
                checkbox.stateChanged.connect(fun)
        
import re 

def camelCaseToText(label):
    label = re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', label)
    return label
