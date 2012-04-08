# -*- coding: utf-8 -*-

context = {}

import sys, pickle, traceback, os

sys.path.append("../")
sys.path.append("../lib/")

from widgets import MultiThreadedOutput, NoServerConnection

sys.stdout = sys.stderr = MultiThreadedOutput()
#sys.stdout = MultiThreadedOutput()

from utils import Client #@UnresolvedImport @UnusedImport

try:
	import models #@UnresolvedImport @UnusedImport
except:
	print "Nie znaleziono modułu models!"

from PyQt4.QtCore import SIGNAL, Qt, QTimer
from PyQt4.QtGui import QApplication, QMainWindow, \
	 QAction, QPixmap, QIcon, QTabWidget, QInputDialog, \
	QMessageBox, QTextEdit, QTextCursor

from widgets import Environment

## ======================================================================= ##
## GUI

class Output(QTextEdit):
	def __init__(self):
		QTextEdit.__init__(self)
		self.setTextInteractionFlags(Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)

	def updateOutput(self):
		data = sys.stdout.getOutput()
		if data:
			self.moveCursor( QTextCursor.End )
			self.insertPlainText( unicode( data ))
			self.moveCursor( QTextCursor.End )

class MainWindow(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)

		self.outputUpdater = QTimer()
		self.outputUpdater.setInterval(0)

		self.setWindowTitle('Deadline 24 - Darkplace Hospital')
		self.setupUI()
		self.resize(800, 600)

		console = Output()
		self.tabWidget.addTab(console, "stdout")
		self.outputUpdater.timeout.connect(console.updateOutput)
		self.outputUpdater.start()

	def setupUI(self):
		self.tabWidget = QTabWidget()
		self.setCentralWidget(self.tabWidget)

		newEnvIcon = QIcon(QPixmap("img/envNew.png"))
		closeEnvIcon = QIcon(QPixmap("img/envClose.png"))
		snipNewIcon = QIcon(QPixmap("img/snipNew.png"))
		snipRunIcon = QIcon(QPixmap("img/snipRun.png"))
		snipQueueIcon = QIcon(QPixmap("img/snipQueue.png"))
		snipRenameIcon = QIcon(QPixmap("img/snipRename.png"))

		newEnvAction = QAction(newEnvIcon, u"Nowe środowisko", self)
		closeEnvAction = QAction(closeEnvIcon, u"Zamknij środowisko", self)
		snipNewAction = QAction(snipNewIcon, u"Nowy snippet (CTRL+N)", self)
		snipRunAction = QAction(snipRunIcon, u"Uruchom snippet (CTRL+R)", self)
		snipQueueAction = QAction(snipQueueIcon, u"Zakolejkuj snippet (CTRL+Q)", self)
		snipRenameAction = QAction(snipRenameIcon, u"Zmień tytuł snippetu (CTRL+T)", self)
		changeViewAction = QAction(u"MDI <-> Taby", self)


		snipNewAction.setShortcut('CTRL+N')
		snipRunAction.setShortcut('CTRL+R')
		snipQueueAction.setShortcut('CTRL+Q')


		self.tools = self.addToolBar("Narzędzia")
		self.tools.addAction(newEnvAction)
		self.tools.addAction(closeEnvAction)
		self.tools.addSeparator()
		self.tools.addAction(snipNewAction)
		self.tools.addAction(snipRenameAction)
		self.tools.addAction(snipRunAction)
		self.tools.addAction(snipQueueAction)
		self.tools.addSeparator()
		self.tools.addAction(changeViewAction)


		self.connect(newEnvAction, SIGNAL('triggered()'), self.newEnvironment)
		self.connect(closeEnvAction, SIGNAL('triggered()'), self.closeEnvironment)
		self.connect(snipNewAction, SIGNAL('triggered()'), self.newSnippet)
		self.connect(snipRunAction, SIGNAL('triggered()'), self.runSnippet)
		self.connect(snipQueueAction, SIGNAL('triggered()'), self.queueSnippet)
		self.connect(snipRenameAction, SIGNAL('triggered()'), self.renameSnippet)
		self.connect(changeViewAction, SIGNAL('triggered()'), self.changeView)

	def addEnvironment(self, port):
		try:
			env = Environment(port)
			self.tabWidget.addTab(env, '%d' % port)
			self.tabWidget.setCurrentWidget(env)
		except NoServerConnection:
			box = QMessageBox()
			box.setText(u"Nie udało się podłączyć do serwera!")
			box.setStandardButtons(QMessageBox.Ok)
			box.exec_()

	def newEnvironment(self):
		port, ok = QInputDialog.getText(self, u"Port serwera", u"Podaj port serwera:")

		if ok and port:
			self.addEnvironment(int(port))

	def closeEnvironment(self):
		if self.tabWidget.currentIndex() == 0:
			return

		reply = QMessageBox.question(self, 'Pytanie',
            u"Zamknąć zaznaczoną kartę?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)

		if reply == QMessageBox.Yes:
			# TODO: wywoływanie close na kliencie
			self.tabWidget.currentWidget().cleanup()
			self.tabWidget.removeTab(self.tabWidget.currentIndex())

	def newSnippet(self):
		self.tabWidget.currentWidget().newSnippet()

	def runSnippet(self):
		self.tabWidget.currentWidget().runSnippet()

	def queueSnippet(self):
		self.tabWidget.currentWidget().queueSnippet()

	def renameSnippet(self):

		window = self.tabWidget.currentWidget().mdi.activeSubWindow()
		title, ok = QInputDialog.getText(self, u'Tytuł', u'Wpisz nowy tytuł dla okna:')

		if ok and title:
			window.setWindowTitle( unicode(title) )
			#self.tabWidget.currentWidget().renameSnippet(unicode(title))

	def changeView(self):
		tab = self.tabWidget.currentWidget()
		if tab:
			tab.mdi.setViewMode( not tab.mdi.viewMode() )

if __name__ == '__main__':
	try:
		app = QApplication(sys.argv)

		mainWindow = MainWindow()
		for port in sys.argv[1:]:
			try:
				mainWindow.addEnvironment(int(port))
			except:
				pass
		mainWindow.setVisible(True)

		app.exec_()
	except:
		traceback.print_exc()
	finally:
		sys.__stdout__.write(sys.stdout.getOutput())
