from PyQt5 import QtCore, QtGui, QtWidgets

from script import Scenarios

from ... import CONSTANT
from ... import S1Product
from ... import Inferno
from .. import Common 

class _HeaderFrame(QtWidgets.QFrame):
    
    @classmethod
    def show_popup(self,event,text1,text2):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Scenario type info")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.buttonClicked.connect(self.popup_button)

        msg.setText(text1)
        msg.setInformativeText(text2)
        x = msg.exec_()
    
    @classmethod
    def popup_button(self, i):
        pass

    def _getSpacerItem(self):
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        return spacerItem

    def setupUi(self,inferno:Inferno.Inferno):
        self.inferno = inferno
        
        QtWidgets.QHBoxLayout(self)
        self.currentPriorityLabel = QtWidgets.QLabel(self)
        self.nextPriorityPushButton = QtWidgets.QPushButton(self)
        self.previousPriorityPushButton = QtWidgets.QPushButton(self)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.helpPushButton = QtWidgets.QPushButton(self)
        
        self.helpPushButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarContextHelpButton))
        self.helpPushButton.clicked.connect(lambda : self.currentPriorityLabel.mousePressEvent(None))


        self.layout().addWidget(self.previousPriorityPushButton)
        self.layout().addItem(spacerItem1)
        self.layout().addWidget(self.currentPriorityLabel)
        self.layout().addWidget(self.helpPushButton)

        self.layout().addItem(spacerItem2)
        self.layout().addWidget(self.nextPriorityPushButton)
        self.retranslateUi()

    def retranslateUi(self):
        self.currentPriorityLabel.setText("Current Proposition")
        self.nextPriorityPushButton.setText("Next Type>")
        self.previousPriorityPushButton.setText("< Previus Type")

class _TableWidget(Common.TableWidget):
    list_attribut = [
        "Selection",
        "Name",
        "Date",
        'Orbit Numer',
        'Orbit Type',
        'Satellite',
        "Polarization",
        'Quicklook',
        'Provider',
        "Available"

    ]   

    class Item():
        def __init__(self,proposition:Scenarios.Proposition) -> None:
            self.proposition : Scenarios.Proposition = proposition

        def setSelected(self,bool):
            self.proposition.chosen = bool
            
        def getCheckbox(self,TableWidget:Common.TableWidget)->QtWidgets.QCheckBox:
            checkboxWidget = Common.CenteredCheckBock(TableWidget)
            
            checkBox = checkboxWidget.checkBox
            if self.proposition.chosen:
                checkBox.setCheckState(QtCore.Qt.Checked)
            else:
                checkBox.setCheckState(QtCore.Qt.Unchecked)
            checkBox.stateChanged.connect(lambda : self.setSelected(checkBox.checkState()))
            
            return checkboxWidget

        def display(self,TableWidget:Common.TableWidget):
            nb_row_initial = TableWidget.rowCount()
            nb_element_in_priority = len(self.proposition.list)
            for product in self.proposition.list:
                self._displayItemElement(TableWidget,product)
            TableWidget.setSpan(nb_row_initial,0,nb_element_in_priority,1)
        
            # Set checkbox for the proposition
            cell_widget = self.getCheckbox(TableWidget)
            TableWidget.setCellWidget(nb_row_initial, 0, cell_widget)

        def _displayItemElement(self,
                tableWidget:Common.TableWidget,
                product:S1Product.S1Product):
            
            itemRow = tableWidget.rowCount()
            tableWidget.setRowCount(itemRow+1)
            tableWidget.set_text(itemRow,'Name',product.name, inRed= (not product.available) )
            tableWidget.set_text(itemRow,'Date',product.date, inRed= (not product.available) )
            tableWidget.set_text(itemRow,'Orbit Numer',product.orbitNumber, inRed= (not product.available) )
            tableWidget.set_text(itemRow,'Orbit Type',product.orbitType, inRed= (not product.available) )
            tableWidget.set_text(itemRow,'Satellite',product.satellite, inRed= (not product.available) )
            tableWidget.set_text(itemRow,'Polarization',product.polarization, inRed= (not product.available) )
            tableWidget.set_text(itemRow,'Provider',product.provider, inRed= (not product.available) )
            tableWidget.set_text(itemRow,'Available',product.available, inRed= (not product.available) )

            # set Quicklook
            tableWidget.setQuicklook(itemRow,product)

    def __init__(self, parent: QtWidgets):
        super().__init__(parent, self.list_attribut)
        self.setSortingEnabled(False)



    def setupUi(self,inferno:Inferno.Inferno):
        self.inferno = inferno
        self.priorityProposition = self.inferno.priorityProposition

    def display(self,ind:int):
        ind = ind%len(self.priorityProposition)

        self.clearContents()
        for proposition in self.priorityProposition[ind]:
            _TableWidget.Item(proposition).display(self)

    def saveInfernoParameters(self):
        self.inferno.updateChosenProposition()

class ScenariosTable(QtWidgets.QWidget):
    def loadInfernoParameters(self):
        pass

    def saveInfernoParameters(self):
        self.tableWidget.saveInfernoParameters()

    def displayCurrentScenarios(self):
        ind = self.currentPriorityInd
        ind = ind % len(self.inferno.priorityProposition)
        nextInd = (ind+1) % len(self.inferno.priorityProposition)
        currentPriorityProposition = self.inferno.priorityProposition[ind]

        # Update Texte
        self.header.currentPriorityLabel.setText(
            f"{ currentPriorityProposition.getName() }"
        )
        self.header.currentPriorityLabel.mousePressEvent =lambda event : _HeaderFrame.show_popup(
            event,
            currentPriorityProposition.getName(),
            currentPriorityProposition.description(),
            )
        
        # Update Table
        self.tableWidget.display(ind)        

    def nextScenario(self):
        self.currentPriorityInd += 1
        self.displayCurrentScenarios()
        
    def previousScenario(self):
        self.currentPriorityInd -= 1
        self.displayCurrentScenarios()



    def setupUi(self,inferno:Inferno.Inferno):
        self.inferno = inferno
        self.infernoParameters = inferno.parameters
        self.currentPriorityInd:int = 0
        QtWidgets.QVBoxLayout(self)
        self.header = _HeaderFrame(self)
        self.header.setupUi(inferno)
        self.header.nextPriorityPushButton.clicked.connect(self.nextScenario)
        self.header.previousPriorityPushButton.clicked.connect(self.previousScenario)
        self.layout().addWidget(self.header)

        self.tableWidget = _TableWidget(self)
        self.tableWidget.setupUi(inferno)
        self.layout().addWidget(self.tableWidget)

        self.displayCurrentScenarios()