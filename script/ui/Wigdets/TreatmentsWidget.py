import io
from PyQt5 import QtCore, QtGui, QtWidgets
from queue import Queue

from script.Inferno import Inferno
from script.Treatment import stepInfo 

class Worker(QtCore.QObject):
    # https://realpython.com/python-pyqt-qthread/
    # https://qt-labs.developpez.com/thread/qthread-movetothread/
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)
    updateStepInfo = QtCore.pyqtSignal(stepInfo)

    def __init__(self,inferno:Inferno,stdout=None,*args,**kwargs  ) -> None:
        super().__init__(*args,**kwargs)
        self.inferno = inferno
        self.stdout = stdout

    def run(self):
        self.inferno.runTreatement(
            callbackUpdateStepInfo=self.updateStepInfo.emit ,
            callbackProgress=self.progress.emit,
            stdout=self.stdout
        )
        self.finished.emit()


    def start(self,thread):
        self.moveToThread(thread)
        thread.started.connect(self.run)
        self.finished.connect(thread.quit)
        self.finished.connect(self.deleteLater)
        thread.start()
        

class TextEdit(QtWidgets.QPlainTextEdit):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        self.stream = ConsoleStream()
        self.initMyReceiver()

    def initMyReceiver(self):
        self.thread1 = QtCore.QThread()
        self.my_receiver = MyReceiver(self.stream)
        self.my_receiver.newText.connect(self.append_text)
        self.my_receiver.moveToThread(self.thread1)
        self.thread1.started.connect(self.my_receiver.run)
        self.thread1.start()

    def append_text(self,text):
        self.moveCursor(QtGui.QTextCursor.End)
        self.insertPlainText( text )

class ProgressBar(QtWidgets.QFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.title = QtWidgets.QLabel(self)
        self.title.setText("Current Treatment Title")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar = QtWidgets.QProgressBar(self)

        self.layout().addWidget(self.title)
        self.layout().addWidget(self.progressBar)
        # spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        # self.layout().addItem(spacerItem)

        self.setInfinit()

    def setInfinit(self):
        self.progressBar.setMaximum(0)
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)

    def setProgress(self,value:int,maximum:int=None):
        if maximum is not None:
            self.progressBar.setMaximum(maximum)
        self.progressBar.setValue(value)


# Redirection stdout Thread safe (inutile normalement pcq 1 thread...)
# https://stackoverflow.com/questions/21071448/redirecting-stdout-and-stderr-to-a-pyqt4-qtextedit-from-a-secondary-thread
class ConsoleStream(io.IOBase):
    def __init__(self):
        super().__init__()
        self.queue :Queue = Queue()

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        with self.queue.mutex:
            self.queue.queue.clear()

class MyReceiver(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)

    def __init__(self,ConsoleStream:ConsoleStream,*args,**kwargs):
        QtCore.QObject.__init__(self,*args,**kwargs)
        self.consoleStream = ConsoleStream

    def run(self):
        while True:
            text = self.consoleStream.queue.get()
            self.newText.emit(text)
