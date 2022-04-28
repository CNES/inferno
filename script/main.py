from script import ConfigParser
from script import Inferno
from PyQt5 import QtCore, QtGui, QtWidgets
import argparse
import sys
from script.ui import Common
from script.ui.Wigdets import InputSetting, PostTreatment

from script.ui.Windows import TreatmentSettings,Query,Propositions, Treatments
from typing import List
import logging

class Steps():
    def __init__(self,parents,inferno:Inferno.Parameters) -> None:
        self._stepsClasses  = [] 
        self._stepsInstances :List[Common.window] = []
        self._currentStepInd : int = None
        self.inferno = inferno
        self.parent = parents

    def getCurrentStepInd(self) ->int:
        return self._currentStepInd

    def getCurrentStep(self) -> Common.window:
        ind = self.getCurrentStepInd()
        return self.getStep(ind)

    def getStep(self,ind) -> Common.window:
        return self._stepsInstances[ind]

    def getNextStep(self) -> Common.window:
        ind = self.getCurrentStepInd()
        return self.getStep(ind+1)

    def getNextClass(self) -> Common.window:
        ind = self.getCurrentStepInd()
        try:
            return self._stepsClasses[ind+1]
        except IndexError:
            return None 
            
    def nextStepAvailable(self) -> bool:
        return self._currentStepInd <len(self._stepsClasses)-1

    def next(self) -> Common.window:
        if self.nextStepAvailable():
            self.getCurrentStep().close()
            self._currentStepInd += 1
            self.setupUiCurrentStep()
            return self.getCurrentStep()

    def previous(self) -> Common.window:
        ind = self.getCurrentStepInd()
        if 0<ind:
            currentStep = self.getCurrentStep()
            currentStep.close()
            self._currentStepInd -= 1
            self.setupUiCurrentStep()
            return self.getCurrentStep()

    def addStep(self,stepWidget:QtWidgets.QWidget) -> None:
        if self._currentStepInd is None:
            self._currentStepInd = 0
        self._stepsClasses.append(stepWidget)
        self._stepsInstances.append(None)

    def setupUiCurrentStep(self):
        # Call setupUi methode of the current 
        # current step widget
        ind =  self.getCurrentStepInd()
        constructor =  self._stepsClasses[ind]
        self._stepsInstances[ind] = (constructor(self.parent))

        # current_widget = self.getCurrentStep()
        self._stepsInstances[ind].setupUi(self.inferno)
        # self._stepsInstances[ind].show()
    


class Window(QtWidgets.QWidget): 
    def nextButtonFunction(self):
        if self.steps.getNextClass() is Treatments.MainWindow:
            return self.confirmShowDialog()
        else:
            return self.nextFunction()

    def confirmShowDialog(self):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText("Do you want to Continue")
        msgBox.setWindowTitle("Start Proccessing")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        # msgBox.buttonClicked.connect(msgButtonClick)

        returnValue = msgBox.exec()
        if returnValue == QtWidgets.QMessageBox.Yes:
            self.nextFunction()
            self.previousPushButton.hide()
            self.nextPushButton.setText("Quit")
            self.nextPushButton.clicked.connect(sys.exit)
            self.nextPushButton.setEnabled(False)
            currentStep:Treatments.MainWindow = self.steps.getCurrentStep()
            currentStep.onfinish(lambda: self.nextPushButton.setEnabled(True))
            currentStep.start()

    def nextFunction(self):
        currentStep = self.steps.getCurrentStep()
        if currentStep.isComplete():
            # self.settingPushButton.hide()
            nextStep = self.steps.next()        
            self.previousPushButton.show()
            self.mainlayout.addWidget(nextStep)

            # print("coucuo")
            # print(self.steps.getNextClass())
            # if self.steps.getNextClass() is Treatments.MainWindow:
            #     self.nextPushButton.clicked.disconnect()
            #     self.nextPushButton.clicked.connect(self.confirmShowDialog)


    def previousFunction(self):
        nextStep = self.steps.previous()    
        if nextStep is not None:
            self.mainlayout.addWidget(nextStep)

        if self.steps.getCurrentStepInd() == 0:
            self.previousPushButton.hide()
            # self.settingPushButton.show()

    def openSettingWindow(self):
        Dialog = QtWidgets.QDialog(self)
        settingsWindow = InputSetting.Ui_Dialog()
        settingsWindow.setupUi(Dialog,self.inferno)
        Dialog.show()

    def setupStep(self,inferno:Inferno.Parameters):
        self.steps = Steps(self,inferno)
        # self.steps.addStep(MainWindow.MainWindow(self))
        self.steps.addStep(Query.MainWindow)
        self.steps.addStep(Propositions.MainWindow)
        self.steps.addStep(TreatmentSettings.MainQWidget)
        self.steps.addStep(Treatments.MainWindow)
        # self.steps.addStep(TreatmentOptions.MainQWidget(self))
        # self.steps.addStep(PostTreatment.MainQWidget(self))

        self.steps.setupUiCurrentStep()
        widget = self.steps.getCurrentStep()
        self.mainlayout.addWidget(widget)

    def setupUi(self,inferno:Inferno.Parameters):
        self.inferno = inferno

        self.resize(1000,600)
        self.mainlayout = QtWidgets.QVBoxLayout(self)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        # self.settingPushButton = QtWidgets.QPushButton(self)
        # self.settingPushButton.setContentsMargins(100,100,100,100)
        # self.settingPushButton.setStyleSheet(
        #     "padding-left: 20px; padding-right: 20px;"
        #     "padding-top: 5px; padding-bottom: 5px;")

        # self.settingPushButton.clicked.connect(self.openSettingWindow)
        # self.horizontalLayout.addWidget(self.settingPushButton)
            # left side espace
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
            # push button
        self.previousPushButton = QtWidgets.QPushButton(self)
        self.previousPushButton.clicked.connect(self.previousFunction)
        self.previousPushButton.hide()
        self.horizontalLayout.addWidget(self.previousPushButton)

        self.nextPushButton = QtWidgets.QPushButton(self)
        self.nextPushButton.clicked.connect(self.nextButtonFunction)
        self.horizontalLayout.addWidget(self.nextPushButton)

        self.mainlayout.addLayout(self.horizontalLayout)
        self.setupStep(self.inferno)
        self.retranslateUi()

        # self.settingPushButton.hide()
        pass

    def retranslateUi(self):
        # self.settingPushButton.setText("Input Settings")
        self.setWindowTitle("INFERNO")
        self.previousPushButton.setText("Previous")
        self.nextPushButton.setText("Next")

def parseArugment():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",dest="inputPath", default=None, type=str)
    # parser.add_argument("-p",dest="provider", default="PEPS", type=lambda x : Inferno.CONSTANT.PROVIDER[x])
    # parser.add_argument("-s",dest="setting", default=None, type=str)
    parser.add_argument("-e",dest="exec", default=None, type=str)

    args = parser.parse_args()
    return args

def main():
    args = parseArugment()
    logging.basicConfig(format='%(process)d-%(levelname)s-%(message)s')

    if args.exec:
        Inferno.Inferno.runLater_Exec(args.exec)
        sys.exit()
    
    inferno =  Inferno.Inferno()
    if args.inputPath is None:
        inputConfig = ConfigParser.InputConfig.default()
    else: 
        inputConfig= ConfigParser.InputConfig.fromFile(args.inputPath)

    inferno.parameters.inputConfig = inputConfig
    # inferno.parameters.provider = args.provider


    app = QtWidgets.QApplication(sys.argv)

    main_windows = Window()
    main_windows.setupUi(inferno)
    main_windows.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
