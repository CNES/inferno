from typing import Callable
from PyQt5 import QtCore, QtGui, QtWidgets

from script.Treatment import stepInfo


from ... import Inferno
from ..Wigdets import TreatmentsWidget
from script.ui import Common, Wigdets

class MainWindow(Common.window):

    def setupUi(self,inferno:Inferno.Inferno):
        self.inferno = inferno
        self.stepInfo = stepInfo(description="",maxProgress=0)

        self.progressbar = TreatmentsWidget.ProgressBar(self)
        self.console = TreatmentsWidget.TextEdit(self)
        
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.progressbar)
        self.layout().addWidget(self.console)
        self.retranslateUi()


        self.backendThread = QtCore.QThread()
        self.worker = TreatmentsWidget.Worker(self.inferno,self.console.stream)
        self.worker.progress.connect(self.updateProgresse)
        self.worker.updateStepInfo.connect(self.onUpdateStepInfo)
        
        self.worker.finished.connect(self.progressbar.hide)
    
    def onfinish(self,fun:Callable):
        self.worker.finished.connect(fun)

    def start(self):
        self.worker.start(self.backendThread)

    def updateProgresse(self,val:int):
        if val==0:
            return self.progressbar.setInfinit()
        self.progressbar.title.setText(self.stepInfo.description)
        self.progressbar.setProgress(val,self.stepInfo.maxProgress)


    def onUpdateStepInfo(self,stepInfo:stepInfo):
        self.stepInfo = stepInfo
        self.progressbar.title.setText(stepInfo.description)
        self.progressbar.setProgress(0,stepInfo.maxProgress)
        self.progressbar.setInfinit()


    def retranslateUi(self):
        pass