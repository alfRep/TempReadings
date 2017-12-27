#!/usr/bin/env Python3
#  TempReaderApp.py
#  TempReadings
#  
#  Created by author 'ALF' on 25 Dec 2017
#  Copyright(c) 2017.  All Rights Reserved.
# -------------------------------------------------------

"""What this module does
Usage:   

"""
import json
import os
import sys
import time

import plotly
import plotly.figure_factory as ff
import plotly.graph_objs as go
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QSplashScreen

qtCreatorFile = "UI" + os.sep + "tempR1.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)   #uic.loadUiType(qtCreatorFile)


class TempReaderApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.loadBtn.setEnabled(False)
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon("Images" + os.sep + "Thermometer.png"))
        self.chooseBtn.clicked.connect(self.FileChooser)
        self.webView.setEnabled(False)
        self.webViewTable.setEnabled(False)
        self.tableLbl.setVisible(False)
        self.scatterLbl.setVisible(False)
        self.loadBtn.clicked.connect(self.ProcessData)
        self.setFixedSize(self.size())
        self.fileErrorLbl.setVisible(False)


        # self.dataTable.setHorizontalHeaderLabels(("DATE;READING").split(";"))
        # self.dataTable.setSelectionBehavior(QAbstractItemView.SelectRows)

    def FileChooser(self):
        self.fileErrorLbl.setVisible(False)
        self.fname = QFileDialog.getOpenFileName(self, 'Select file', '/home', 'Temp File (8500_RCTT.json)')
        self.fileEdit.setText(self.fname[0])
        if not self.fname[0]:
            return None
        self.loadBtn.setEnabled(True)
        return self.fname[0]

    def ProcessData(self):
        print("generating chart")

        days, high, low, meta, temps, info = self.ReadData()

        if not all([days, high, low, meta, temps, info]):
            print("Error ProcessData")
            return None

        # self.UpdateTable(days, temps)

        self.CreatePlot(days, meta, temps, high, low, info)

    def ReadData(self):

        temps = []
        days = []
        meta = []
        high = []
        low = []
        info = [["DATE", "TEMP", "TIME", "STATUS", "SN"]]
        try:
            data = json.load(open(self.fname[0]))
            for item in data["Readings"]:
                temps.append(item["AvgTemp"])
                days.append("{0}-{1}-{2}".format(item["Date"][5:7], item["Date"][8:], item["Date"][0:4]))
                meta.append("SN: {0}<br>Status: {1}<br>Time: {2}".format(item["SN"], item["Status"], item["Time"]))
                high.append(item["HighRange"])
                low.append(item["LowRange"])
                info.append([item["Date"], item["AvgTemp"], item["Time"], item["Status"], item["SN"]])
            return days, high, low, meta, temps, info
        except Exception:
            self.fileErrorLbl.setVisible(True)
            print("Error ReadData")
            return None, None, None, None, None



    def CreatePlot(self, days, meta, temps, high, low, info):
        degree = u"\u00b0"
        upper = [high[0]] * len(days)
        lower = [low[0]] * len(days)

        outOfLimit = []
        for i, item in enumerate(temps):
            if item > upper[0] or item < lower[0]:
                outOfLimit.append(
                        go.Annotation(text="<b>Out Of Range</b>", yshift=12, x=i, y=item, font=dict(family='Arial',
                                                                                                    size=7,
                                                                                                    color='red'),
                                      showarrow=False))
        trace1 = go.Scatter(x=days, y=upper, marker={'color': 'black', 'symbol': 104, 'size': "7", 'opacity': '0.9'},
                            mode="markers+lines", name='Upper Limit', showlegend=False)
        trace2 = go.Scatter(x=days, y=lower, marker={'color': 'black', 'symbol': 104, 'size': "7", 'opacity': '0.9'},
                            mode="markers+lines", name='Lower Limit', showlegend=False)
        trace3 = go.Scatter(x=days, y=temps, marker={'symbol': 0, 'color': 'rgb(0,0,255)', 'line': dict(width=1),
                                                     'size': "8"},
                            mode="markers", line=dict(shape='spline'), name='Readings', text=meta)
        data = go.Data([trace1, trace2, trace3])
        layout = go.Layout(title="<b>Reagent Carousel Temperature Readings</b>",
                           titlefont={'family':'Arial','size': 23, 'color': 'rgb(255,255,255)'},
                           xaxis1={'title': '<b>Day of Reading</b>', "anchor": "x1", 'autorange': True, 'tickangle':
                               45, 'titlefont': {'family': 'Arial', 'size': 17, 'color': 'rgb(255,255,255)'},
                                   'color': 'rgb(255, 255, 255)', 'showgrid': True, 'gridcolor': '#CCE5FF'},
                           yaxis1={'title': '<b>Temperature ({0}C)</b>'.format(degree), "anchor": "y1",
                                    'autorange': True,
                                   'titlefont': {'family': 'Arial', 'size': 17, 'color': 'rgb(255,255,255)'},
                                   'color': 'rgb(255, 255, 255)','gridcolor': '#CCE5FF'},
                           margin={'b': 120},
                           plot_bgcolor='rgb(245,245,245)',
                           paper_bgcolor='rgb(0,51,102)',
                           legend={'bgcolor': '#E2E2E2', 'bordercolor': '#FFFFFF', 'borderwidth':2},
                           dragmode='pan'
                           )
        layout.update(dict(annotations=outOfLimit))
        figure = go.Figure(data=data, layout=layout)
        htmlPlot = os.path.join("Plots" + os.sep + 'TempReadings.html')
        itemsToRemove = ['sendDataToCloud', 'toImage', 'hoverClosestCartesian','hoverCompareCartesian', 'hoverClosest3d',
                         'toggleHover', 'toggleSpikelines']
        plotly.offline.plot(figure, filename=htmlPlot, auto_open=False, show_link=False,
                            config={'displaylogo': False, 'modeBarButtonsToRemove': itemsToRemove})
        # plotly.offline.plot(figure, filename=htmlPlot, auto_open=False, show_link=False,
        #                     config={"displayModeBar": True})



        data_matrix = info
        # colorscale = [[0, '#4d004c'], [.5, '#f2e5ff'], [1, '#ffffff']]
        table = ff.create_table(data_matrix)
        table.layout.width = 485
        tablePlot = os.path.join("Plots" + os.sep + 'TempReadingsTable.html')

        plotly.offline.plot(table, filename=tablePlot, auto_open=False,
                            show_link=False, config={"displayModeBar": False})


        self.ShowPlots(htmlPlot, tablePlot)

    def ShowPlots(self, html, table):
        self.webView.load(QUrl(os.path.join("file:///" + os.path.abspath(html))))
        self.webViewTable.load(QUrl(os.path.join("file:///" + os.path.abspath(table))))

        self.webView.setEnabled(True)
        self.webViewTable.setEnabled(True)
        self.tableLbl.setVisible(True)
        self.scatterLbl.setVisible(True)

        self.webViewTable.show()
        self.webView.show()


app = QApplication(sys.argv)
app.setStyle("plastique")
splash_image = QPixmap("Images" + os.sep + "Thermometer.png").scaled(200, 200, QtCore.Qt.KeepAspectRatio)
splash = QSplashScreen(splash_image)
splash.show()
time.sleep(2)
myApp = TempReaderApp()
myApp.show()
splash.finish(myApp)
app.exec_()
