# -*- coding: utf-8 -*-
'''
Created on 03-04-2012

@author: morti
'''

import utils #@UnresolvedImport @UnusedImport
from PyQt4 import QtGui as gui #QHBoxLayout, QLabel

class MyWorker(object):

    licznik = 1
    label = None

    def name(self):
        return u"Mega"

    def updateUI(self):
        self.label.setText("%d" % self.licznik)

    def install(self):
        print "Installing", self.name()
        print "Pamięć:",self.mem
        print "Widget:",self.widget
        print "Klient:",self.client

        self.label = gui.QLabel("%d" % self.licznik)
        lay = gui.QHBoxLayout()
        lay.addWidget(self.label)
        self.widget.setLayout(lay)
        self.widget.show()

        self.client.bindParser("energy")

    def remove(self):
        print "Removing", self.name()

    def work(self):
        self.licznik += 1
        #print 'hello', self.client.port

worker = MyWorker()
