from PyQt5 import QtCore, QtGui, QtWidgets
from numpy import product
from .. import  Common
from ... import S1Product
from ... import Inferno

class QualityIndicator(Common.OptionQGroupBox):
    def setupUi(self, inferno: Inferno.Inferno):
        super().setupUi(inferno.parameters)
        self.defaultCheckboxSetUp(inferno.parameters.postTreatment.qualityIndicator)
        self.retranslateUi()

    def retranslateUi(self):
        self.setCheckBoxText("meanConsistency","mean coherence")
        self.setCheckBoxText("altitudeAmbiguity","Height of ambiguity")
        self.setCheckBoxText("criticalBase","Critical baseline")
        self.setCheckBoxText("orthogonalBase","Orthogonal Base")
        self.setCheckBoxText("recoveryRate","Recovery rate")

# class CoregistrationPrecision(Common.OptionQGroupBox):
#     def setupUi(self, inferno: Inferno.Inferno):
#         super().setupUi(inferno.parameters)
#         self.defaultCheckboxSetUp(inferno.parameters.postTreatment.coregistrationPrecision)

# class ImageComparison(Common.OptionQGroupBox):
#     def setupUi(self, inferno: Inferno.Inferno):
#         super().setupUi(inferno.parameters)
#         self.defaultCheckboxSetUp(inferno.parameters.postTreatment.imageComparison)

class MainQWidget(QtWidgets.QWidget):
    def setupUi(self,inferno: Inferno.Inferno):
        self.infernoParameters =inferno

        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.qualityIndicator = QualityIndicator(self)
        self.qualityIndicator.setupUi(inferno)
        self.mainLayout.addWidget(self.qualityIndicator)

        # self.coregistrationPrecision = CoregistrationPrecision(self)
        # self.coregistrationPrecision.setupUi(inferno)
        # self.coregistrationPrecision.hide()
        # self.mainLayout.addWidget(self.coregistrationPrecision)

        # self.imageComparison = ImageComparison(self)
        # self.imageComparison.setupUi(inferno)
        # self.mainLayout.addWidget(self.imageComparison)

        spacerItem = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.mainLayout.addItem(spacerItem)

    def close(self) -> bool:
        return super().close()

    def loadInfernoParameters(self):
        self.qualityIndicator.loadInfernoParameters()
        # self.coregistrationPrecision.loadInfernoParameters()
        # self.imageComparison.loadInfernoParameters()

    def saveInfernoParameters(self):
        self.qualityIndicator.saveInfernoParameters()
        # self.coregistrationPrecision.saveInfernoParameters()
        # self.imageComparison.saveInfernoParameters()

