from PyQt5 import QtCore, QtGui, QtWidgets

from ..Wigdets import QueryTable
from ... import S1Product
from ... import Inferno
from .. import Common
from ..Wigdets import ScenariProposition
import copy 


class MainWindow(Common.window):
    def loadInfernoParameters(self) -> None:
        return super().loadInfernoParameters()

    def isComplete(self) -> bool:
        self.saveInfernoParameters()
        if not self.inferno.chosenPriorityProposition:
            return False
        return True
        
    def saveInfernoParameters(self)-> None:
        self.ScenariosTable.saveInfernoParameters()


    def setupUi(self,inferno:Inferno.Inferno):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.inferno    = inferno
        self.provider   = inferno.parameters.provider
        self.config     = inferno.parameters.inputConfig

        self.mainlayout = QtWidgets.QVBoxLayout(self)
        self.mainlayout.setContentsMargins(0,0,0,0)

        # priority table
        self.ScenariosTable = ScenariProposition.ScenariosTable(self)
        self.ScenariosTable.setupUi(self.inferno)
        self.mainlayout.addWidget(self.ScenariosTable)
        self.retranslateUi()

    def retranslateUi(self):
        pass
        # self.scenari_pushButton.setText("Proposition")
        # self.nextPushButton.setText("Next")