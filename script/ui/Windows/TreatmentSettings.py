from PyQt5 import QtCore, QtGui, QtWidgets
from numpy import product

from script.ui import Common

from ..Wigdets import PostTreatment
from ..Wigdets import TreatmentOptions
from ... import Inferno



class MainQWidget(Common.window):
    def _setupUi_selectionTable(self):
            # Priority label         
        self.label = QtWidgets.QLabel(self)
        self.mainLayout.addWidget(self.label)
        
            # Selection TableWigdet
        self.selectionTableWidget = TreatmentOptions.TableWidget(self,self.inferno.chosenPriorityProposition)
        self.mainLayout.addWidget(self.selectionTableWidget)
    
    def isComplete(self) -> bool:
        self.saveInfernoParameters()
        return True

    def _setupUi_SeparationLine(self):
                    # separation line
        self.line = QtWidgets.QFrame(self)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.mainLayout.addWidget(self.line)

    def saveInfernoParameters(self):
        self.creationOptionGroupBox.saveInfernoParameters()
        self.MasterImage_groupBox.saveInfernoParameters()
        self.postTreatmentGroupBox.saveInfernoParameters()
        self.swathChoises.saveInfernoParameters()
        self.polarizationChoises.updateInferno(self.inferno)
        self.amplitudePhase.saveInfernoParameters()
        self.inferno.runLater = self.runLater.isChecked()

    def loadInfernoParameters(self) -> None:
        self.creationOptionGroupBox.loadInfernoParameters()
        self.MasterImage_groupBox.loadInfernoParameters()
        self.postTreatmentGroupBox.loadInfernoParameters()
        self.swathChoises.loadInfernoParameters()
        self.polarizationChoises.loadInferno()
        self.amplitudePhase.loadInfernoParameters()
        self.runLater = self.inferno.runLater

    def export(self):
        self.saveInfernoParameters()
        self.inferno.exportParameters()

    def refreshMemoryEstimation(self):
        self.saveInfernoParameters()
        self.memoyEstimation.updateEstimation()

    def setupUi(self,inferno:Inferno.Inferno):
        self.inferno = inferno
        
        # Main Layout
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self._setupUi_selectionTable()
        self._setupUi_SeparationLine()

        self.hLayout = QtWidgets.QHBoxLayout()



        hLayout = QtWidgets.QVBoxLayout()

        swathPolarisationLayout = QtWidgets.QHBoxLayout()

        self.swathChoises = TreatmentOptions.SwathChoises()
        self.swathChoises.setupUi(inferno=inferno)
        swathPolarisationLayout.addWidget(self.swathChoises)
        
        self.polarizationChoises = TreatmentOptions.PolarizationChoises(parent=self,inferno=inferno)
        swathPolarisationLayout.addWidget(self.polarizationChoises.QWidget)
        hLayout.addLayout(swathPolarisationLayout)


        self.MasterImage_groupBox = TreatmentOptions.MasterImage(self)
        self.MasterImage_groupBox.setupUi(self.inferno )
        hLayout.addWidget(self.MasterImage_groupBox)


        # creationOption QHBoxLayout
        # creationOption

        creationOptionAndAmplitudePhaseLayout = QtWidgets.QHBoxLayout()

        self.creationOptionGroupBox = TreatmentOptions.CreationOption(self)
        self.creationOptionGroupBox.setupUi(self.inferno)
        self.creationOptionGroupBox.setFunOnStateChanged(self.refreshMemoryEstimation)
        creationOptionAndAmplitudePhaseLayout.addWidget(self.creationOptionGroupBox)
        # hLayout.addWidget(self.creationOptionGroupBox)


        self.amplitudePhase = TreatmentOptions.AmplitudePhase(self)
        self.amplitudePhase.setupUi(self.inferno)
        self.amplitudePhase.setFunOnStateChanged(self.refreshMemoryEstimation)
        creationOptionAndAmplitudePhaseLayout.addWidget(self.amplitudePhase)
        hLayout.addLayout(creationOptionAndAmplitudePhaseLayout)

        spacerItem = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        hLayout.addItem(spacerItem)
        self.hLayout.addLayout(hLayout)


        self.postTreatmentGroupBox = PostTreatment.MainQWidget(self)
        self.postTreatmentGroupBox.setupUi(self.inferno)
        self.hLayout.addWidget(self.postTreatmentGroupBox)
        self.mainLayout.addLayout(self.hLayout)

        self.memoyEstimation = TreatmentOptions.MemoyEstimation(self,inferno)
        self.mainLayout.addWidget(self.memoyEstimation.QWidget)


        self.exportPushButton = QtWidgets.QPushButton(self)
        self.exportPushButton.clicked.connect(self.export)
        self.exportPushButton.hide()
        self.mainLayout.addWidget(self.exportPushButton)

        self.runLater = QtWidgets.QCheckBox(self)
        self.mainLayout.addWidget(self.runLater)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("Form", "Selected Product"))
        self.exportPushButton.setText("Export")
        self.runLater.setText("Run in command line")

        pass 
