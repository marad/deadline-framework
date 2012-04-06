# -*- coding: utf-8 -*-
'''
Created on 03-04-2012

@author: morti
'''

import sys, traceback, imp, pickle, os, threading
from threading import RLock
from utils import Client #@UnresolvedImport
from PyQt4.QtCore import SIGNAL, Qt, QAbstractListModel, QModelIndex, QSize,\
    QRegExp, QTimer
from PyQt4.QtGui import QWidget, QVBoxLayout, \
    QHBoxLayout, QTextEdit, QSizePolicy, QLineEdit, \
    QPushButton, QFileDialog, QListView, \
    QPixmap, QColor, QIcon, QSyntaxHighlighter, QTextCharFormat, \
    QMdiArea, QAction, QTextCursor

from contextlib import contextmanager

from multiprocessing import Manager


## ======================================================================= ##

class SharedDict(object):
    def __init__(self, d):
        self.dict = d
        self.lock = RLock()
    
    def __setitem__(self, index, item):
        self.lock.acquire()
        try:
            return self.dict[index]
        finally:
            self.lock.release()

    def __getitem__(self, index):
        return self.dict[index]

## ======================================================================= ##

class NoServerConnection( BaseException ):
    pass

## ======================================================================= ##

class PythonSyntaxHighlighter( QSyntaxHighlighter ):
    def __init__(self, parent = None, theme = None, prefix = ''):
        QSyntaxHighlighter.__init__(self, parent)
        self.rules = []
        self.prefix = prefix
        
        kwFormat = QTextCharFormat()
        kwFormat.setForeground( Qt.blue )
        #kwFormat.setFontWeight( QFont.Bold )
        
        quoteFormat = QTextCharFormat()
        quoteFormat.setForeground( Qt.red )
        
        commentFormat = QTextCharFormat()
        commentFormat.setForeground( Qt.darkGray )
        
        keywords = ["and", "del", "for", "is", "raise",
                    "assert", "elif", "from", "lambda", 
                    "break", "else", "global", "not", "try",
                    "class", "except", "if", "or", "while",
                    "continue", "exec", "import", "pass", "yield",
                    "def", "finally", "in", "print", "self"
                    ]
        
        for kw in keywords:
            self.rules.append( (QRegExp("\\b" + kw + "\\b"), kwFormat) )
            
        self.rules.append( (QRegExp(r'"(?:[^"\\]|\\.)*"'), quoteFormat) )
        self.rules.append( (QRegExp(r"'(?:[^\']+|\.)*'"), quoteFormat) )
        
        self.rules.append( (QRegExp(r"#.*$"), commentFormat) )

    def highlightBlock(self, text):
        
        if not text.startsWith(self.prefix):
            return
        
        for rule in self.rules:
            index = 0
            while True:
                #index = text.indexOf( rule[0], index )
                index = rule[0].indexIn( text, index )
                if index < 0: break
                length = rule[0].matchedLength()
                self.setFormat(index, length, rule[1])
                index += length
                
        self.setCurrentBlockState( 0 )

class SnippetEditor(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        
        self.editor = QTextEdit()        
        self.editor.setTabStopWidth(20)
        self.highlighter = PythonSyntaxHighlighter( self.editor )
        
        lay = QHBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.editor)
        self.setLayout(lay)
    
    def runCode(self, context):
        name = threading.current_thread().name
        sys.stdout.flush(name)        
        try:
            scode = str(self.editor.toPlainText()).strip()
            code = compile(scode, '', 'exec')
            exec code in context
        except:
            traceback.print_exc()
        finally:
            data = sys.stdout.getOutput(name)
            self.emit(SIGNAL('codeOutput'), data) 
                
## ======================================================================= ##

class FileBrowser(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUI()
    
    def setupUI(self):
        lay = QHBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        self.button = QPushButton('Wybierz plik')
        self.text = QLineEdit()
        
        lay.addWidget(self.text)
        lay.addWidget(self.button)
        self.setLayout(lay)
        
        QWidget.connect(self.button, SIGNAL('clicked()'), self.click)
        
    def click(self):
        text = QFileDialog.getOpenFileName(parent=self, caption=u"Wybierz plik", filter=u"Moduły Python (*.py)")
        self.text.setText(text)
        
## ======================================================================= ##

class Model(QAbstractListModel):
    
    def __init__(self, parent = None):
        QAbstractListModel.__init__(self, parent)
        self.list = []     
        self.strategies = parent            
        self.play = QPixmap()
        self.play.load("img/Play.png")
        self.none = QPixmap(32, 32)
        self.none.fill(QColor(0, 0, 0, 0))
        
    def add(self, obj):
        self.list.append(obj)
        index = QModelIndex()            
        self.dataChanged.emit(index, index)
    
    def remove(self, index):
        del self.list[index.row()]
        self.dataChanged.emit(index.child(0, 1), index.child(len(self.list), 1))
        
    def rowCount(self, parent):
        return len(self.list)
    
    def data(self, index, role):
        #print index
        if index.row() < 0 or index.row() >= len(self.list):
            return None
        
        if role == Qt.DisplayRole:
            return unicode(self.list[index.row()].name())
        
        elif role == Qt.DecorationRole:
            module = self.list[index.row()]
            if module == self.strategies.activeStrategy:
                return self.play
            else:
                return self.none
            
    def get(self, index):
        return self.list[index.row()]

class Strategies(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setMinimumSize(250, 1)
        self.setupUI()
        
        self.activeStrategy = None
        
    def setupUI(self):
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)        
                
        self.removeButton = QPushButton(QIcon(QPixmap("img/moduleRemove.png")), "")
        self.addButton = QPushButton(QIcon(QPixmap("img/moduleAdd.png")),"")
        self.reloadButton = QPushButton(QIcon(QPixmap("img/moduleReload.png")), "")
        
        self.model = Model(self)
        self.list = QListView()
        self.list.setModel(self.model)
        self.list.setIconSize(QSize(32, 32))
        
        lay.addWidget(self.list)
        
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.addWidget(self.reloadButton)
        hlay.addStretch()
        hlay.addWidget(self.removeButton)
        hlay.addWidget(self.addButton)
        lay.addLayout(hlay)
        self.setLayout(lay)
        
        self.addButton.clicked.connect(self.addButtonClick)
        self.removeButton.clicked.connect(self.removeButtonClick)
        self.reloadButton.clicked.connect(self.reloadButtonClick)
        
        self.list.doubleClicked.connect(self.selectStrategy)
        self.modules = {}
        

    def load(self, path):
        if path:
            module = self._createModule(path)
            if module != None:
                self.model.add(module)
                self.emit(SIGNAL('moduleLoaded'), module)
    
    # Kompiluje moduł do wykonywania i dodaje go do listy strategii
    def addButtonClick(self):
        path = str( QFileDialog.getOpenFileName(parent=self, caption=u"Wybierz plik", filter=u"Moduły Python (*.py)", directory="../") )
        if path:
            module = self._createModule(path)
            if module != None:
                self.model.add(module)
                self.emit(SIGNAL('moduleLoaded'), module)    
                    
    # Przeladowuje podany modul
    def reloadButtonClick(self):
        try:
            index = self.list.selectedIndexes()[0];
            module = self.model.get(index)
            
            newModule = self._createModule(module.__path__)
            
            self.model.list[index.row()] = newModule    
            
            if self.activeStrategy == module:
                #self.activeStrategy = newModule
                #self.model.dataChanged.emit(index, index)                
                self.emit(SIGNAL('moduleReloaded'), newModule)
                self.selectStrategy(index)            
        except IndexError:
            pass
        

    # Usuwa zaznaczoną strategię
    def removeButtonClick(self):
        module = self.model.get(self.list.selectedIndexes()[0])
        self.model.remove(self.list.selectedIndexes()[0])
        self.emit(SIGNAL('moduleRemoved'), module)
        if self.activeStrategy == module:
            self.activeStrategy = None
            self.emit(SIGNAL('strategyChanged'), module, None)
        
    # Wybiera aktywną strategię (2xklik na liście)
    def selectStrategy(self, index = None):
        if index == None:
            index = self.list.selectedIndexes()[0];
        old = self.activeStrategy
        new = self.model.get(index)
        
        if old != new:
            self.activeStrategy = new            
        else:
            self.activeStrategy = None
            
        self.model.dataChanged.emit(index, index)
        self.emit(SIGNAL('strategyChanged'), old, self.activeStrategy)
        
    def _verifyModule(self, module):
        return hasattr(module, 'name') and hasattr(module, 'work')
    
    def _compileCode(self, path):
        with open(path) as f:
            scode = f.read()
        try:            
            return compile(scode, path, 'exec')
        except Exception as e:
            self.emit(SIGNAL('moduleLoadError'), e, path)
            
            
    def _createModule(self, path):
        
        code = self._compileCode(path)
        module = imp.new_module('ad-hoc module')
        exec code in module.__dict__
        
        
        with optional():
            if self._verifyModule(module.worker):
                self.modules[module.worker.name()] = module
                module.worker.__path__ = path            
                return module.worker
            else:
                return None
        
## ======================================================================= ##

@contextmanager
def output(name, optional=False):
    old = threading.current_thread().name
    try:
        threading.current_thread().name = name
        #print threading.current_thread().name
        yield
    except AttributeError:
        if not optional:
            traceback.print_exc()
    except:
        traceback.print_exc()
    finally:
        threading.current_thread().name = old
        #print threading.current_thread().name
        
@contextmanager
def optional():
    try:
        yield
    except AttributeError:
        pass
                    
class MultiThreadedOutput(object):
    def __init__(self):
        self.buffer = {}
    
    def read(self, size=-1):
        return None

    def flush(self, name):
        self.buffer[name] = ''

    def write(self, data, name = None):
        if name == None:
            name = threading.current_thread().name
        try:
            self.buffer[str(name)] += data
        except:
            self.buffer[str(name)] = data
    
    def close(self):
        pass
    
    def getOutput(self, name=None):
        
        if name == None:
            name = threading.current_thread().name
        
        try:
            buf = self.buffer[str(name)]
            self.buffer[str(name)] = ''
            return buf
        except:
            return None
        

class Interpreter(QWidget):
    lastCommands = []
    lastIndex = 0
    
    
    def __init__(self, context):
        QWidget.__init__(self)
        self.context = context
        
        self.setupUI()
        self.setWindowTitle('Interpreter')
        self.setMinimumSize(400, 250)
    
    def setupUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)        
        
        self.out = QTextEdit()        
        self.out.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.out.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.highlighter = PythonSyntaxHighlighter( self.out, prefix = ">>>" )        
        
        self.input = QLineEdit()        
        self.input.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum )        
        layout.addWidget(self.out, 1)
        layout.addWidget(self.input, 0)
        
        self.setLayout(layout)
        
        QWidget.connect(self.input, SIGNAL('returnPressed()'), self.run)
    
    def run(self):
        scode = str(self.input.text()).strip()
        self.out.append(">>> " + scode + "\n")
        self.input.setText('')
        
        name = threading.current_thread().name
        try:
            sys.stdout.flush(name)
            if len(self.lastCommands) == 100:
                del self.lastCommands[0]
            self.lastCommands.append(scode)
            self.lastIndex = 0
            
            try:
                out = eval(scode, self.context)
                if out:
                    print out
            except:
                code = compile(scode, '', 'exec')
                exec code in self.context
        except:
            traceback.print_exc()
        finally:
            self.write( sys.stdout.getOutput(name) )
            
    def keyPressEvent(self, event):
        
        # Prev in command history
        if event.key() == Qt.Key_Up:
            try:
                self.lastIndex -= 1
                self.input.setText(self.lastCommands[self.lastIndex])
            except:
                self.lastIndex += 1
        
        # Next in command history
        elif event.key() == Qt.Key_Down:
            try:                
                self.lastIndex += 1
                if self.lastIndex >= 0:
                    self.lastIndex = 0
                    self.input.setText('')
                else:
                    self.input.setText(self.lastCommands[self.lastIndex])
            except:
                self.lastIndex -= 1
                
        # Clear screen
        elif event.key() == Qt.Key_L:
            if event.modifiers() == Qt.ControlModifier:
                lines = self.out.height() / self.out.fontMetrics().height()
                #for i in xrange(lines):
                #    self.out.append('')
                self.write('\n' * lines)
                self.out.moveCursor( QTextCursor.End )
    
    #def getOutStream(self):
    #    return self.TextOutput(self.out)
    
    def write(self, data):
        self.out.moveCursor( QTextCursor.End )
        try:
            self.out.insertPlainText( unicode(data) )
        except:
            self.out.insertPlainText( data )
        self.out.moveCursor( QTextCursor.End )
    
    
## ======================================================================= ##

class WorkerThread(threading.Thread):
    def __init__(self, client, module, uiUpdateEvent):
        threading.Thread.__init__(self)
        #QThread.__init__(self)
        self.client = client
        self.module = module        
        self.uiUpdateEvent = uiUpdateEvent
        self.snippetQueue = []
        #th.setName( module.name() )        
        
    def run(self):
        th = threading.current_thread()
        th.name = "%d" % self.client.port
        
        #self.module.install()
        
        self.work = True
        while self.work:
            self.client.wait(async=True)
            try:
                self.module.meanwhile()
            except AttributeError:
                pass
            except:
                traceback.print_exc()
            self.client.expect()
            
            try:
                try:
                    if len(self.snippetQueue) > 0:
                        snippet, context = self.snippetQueue.pop()
                        snippet.runCode(context)
                    else:
                        self.module.work()
                except Exception as e:
                    traceback.print_exc()
                   
                self.uiUpdateEvent.set()

                with open('%d.mem' % self.client.port, 'w') as f:
                    pickle.dump(self.module.mem, f)
            except:
                traceback.print_exc()
                print "[BŁĄD] Zapisywanie pamięci nieudane!"                

        #self.module.remove()


class Environment(QWidget):    
    def __init__(self, port, parent=None):
        QWidget.__init__(self, parent=parent)
        self.port = port
        
        try:
            with open('%d.mem' % port) as f:
                self.sharedMemory = pickle.load(f)
                sys.stdout.write("[INFO] Wczytano zapisaną pamięć.\n", name=port)                
        except:
            sys.stdout.write("[BŁĄD] Bład odczytywania pamięci. Resetuję!\n", name=port)
            self.sharedMemory = {}
        try:
            self.client = Client(port)
        except:
            #print "Brak połączenia z serwerem!"
            #self.client = None
            raise NoServerConnection()
                
        self.workerThread = None
        self.uiUpdateEvent = threading.Event()
        
        self.snippetQueue = []
            
        self.context = {}
        self.context['mem'] = self.sharedMemory
        self.context['active'] = None
        self.context['client'] = self.client # TODO: polaczenie z klientem
        
        self.timer = QTimer()
        self.timer.setInterval(0)    
        self.timer.timeout.connect(self.tick)
        self.timer.start()
                
        self.actions = []
        self.setupUI()
        
        # Autoload modules
        for modulePath in [ x for x in os.listdir('..') if x[-3:] == '.py' ]:
            self.strategies.load(os.path.join("..", modulePath))
    
    def setupUI(self):
        self.setWindowTitle("%d" % self.port)
        self.mdi = QMdiArea()
        self.mdi.setHorizontalScrollBarPolicy( Qt.ScrollBarAsNeeded )
        self.mdi.setVerticalScrollBarPolicy( Qt.ScrollBarAsNeeded )

        self.inter = Interpreter(self.context)
        self.mdi.addSubWindow(self.inter, 
                            Qt.WindowTitleHint | 
                            Qt.WindowMinimizeButtonHint | 
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowMaximized)
        
        #self.mdi.addSubWindow(FileBrowser())
        
        # Dock windows
        
        self.strategies = Strategies()       
        
        #stratDock = QDockWidget("Strategies", self)        
        #stratDock.setWidget(self.strategies)        
        #self.addDockWidget(Qt.RightDockWidgetArea, stratDock)
        
        # Actions
        newDocIcon = QIcon(QPixmap("img/newdoc.png"))
        playIcon = QIcon(QPixmap("img/Play.png"))
        
        newSnippetAction = QAction(newDocIcon, "Nowy skrawek", self)
        newSnippetAction.setShortcut('F1')
        self.actions.append(newSnippetAction)        
        runSnippetAction = QAction(playIcon, "Uruchom skrawek", self)
        runSnippetAction.setShortcut('F9')
        self.actions.append(runSnippetAction)        

        layout = QHBoxLayout()
        layout.addWidget(self.mdi)
        layout.addWidget(self.strategies)
        
        self.setLayout(layout)
        
        # Connecting
        QWidget.connect(self.strategies, SIGNAL('strategyChanged'), self.strategyChanged)
        QWidget.connect(newSnippetAction, SIGNAL('triggered()'), self.newSnippet)
        QWidget.connect(runSnippetAction, SIGNAL('triggered()'), self.runSnippet)
    
    def strategyChanged(self, old, new):
        if old != None: 
            with output(self.port, True): old.remove()            
            self.workerThread.work = False
            self.workerThread.join()  # wait for QThread
            self.workerThread = None
            if hasattr(old, '__widget__'):
                self.mdi.removeSubWindow(old.__widget__.parent())
            self.tick()
            
        self.context['active'] = new        
        
        if new:
            with output(self.port): print "Starting new worker..."
            widget = QWidget()
            widget.setWindowTitle(new.name())
            self.mdi.addSubWindow(widget, 
                            Qt.WindowTitleHint | 
                            Qt.WindowMinimizeButtonHint | 
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowMaximized)            
            new.__widget__ = widget            
            new.mem = self.sharedMemory
            new.widget = widget
            new.client = self.client
            
            with output(self.port): new.install()            
            widget.parent().adjustSize()
            
            self.workerThread = WorkerThread(self.client, new, self.uiUpdateEvent)
            self.workerThread.daemon = True        
            self.workerThread.start()
        
    # czyta stdout dla danego interpretera i robi update GUI
    def tick(self):
        if self.context['active'] and self.uiUpdateEvent.isSet():
            self.uiUpdateEvent.clear()
            with output(self.port, True): self.context['active'].updateUI()
                       
        
        data = sys.stdout.getOutput(self.port)
        if data:
            count = len( self.inter.out.toPlainText().split('\n') ) - 100
            if count > 0:
                cursor = self.inter.out.textCursor()
                cursor.movePosition( QTextCursor.Start )
                cursor.movePosition( QTextCursor.Down, QTextCursor.KeepAnchor, count)
                cursor.removeSelectedText()
            
            self.inter.write(data)
    
    def newSnippet(self):
        w = SnippetEditor()
        QWidget.connect(w, SIGNAL('codeOutput'), self.inter.write)        
        self.mdi.addSubWindow(w)
        w.show()

    
    def runSnippet(self):
        w = self.mdi.activeSubWindow().widget()
        if hasattr(w, 'runCode') and callable(w.runCode):
            w.runCode(self.context)
            
    def queueSnippet(self):
        w = self.mdi.activeSubWindow().widget()
        if hasattr(w, 'runCode') and callable(w.runCode):
            self.workerThread.snippetQueue.append( (w, self.context) )
            
    def cleanup(self):
        self.client.close()
        self.workerThread.work = False
        