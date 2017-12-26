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
import sys
import time

import plotly
import plotly.graph_objs as go
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QSplashScreen, QTableWidgetItem

qtCreatorFile = "tempR1.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class TempReaderApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.loadBtn.setEnabled(False)
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon("C:\\Users\\ALF\\Desktop\\Thermometer.png"))
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
        fname = QFileDialog.getOpenFileName(self, 'Select file', '/home', 'Temp File (8500_RCTT.json)')
        print(fname)
        self.fileEdit.setText(fname[0])
        if fname[0]:
            self.loadBtn.setEnabled(True)

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
            data = json.load(open("C:\\Users\\ALF\\Desktop\\8500_RCTT.json"))
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
                           titlefont={'size': 24, 'color': 'rgb(255,255,255)'},
                           xaxis1={'title': '<b>Day of Reading</b>', "anchor": "x1", 'autorange': True, 'tickangle':
                               75, 'titlefont': {'size': 17, 'color': 'rgb(255,255,255)'}, 'color': 'rgb(255, 255, '
                                                                                                    '255)'},
                           yaxis1={'title': '<b>Temperature ({0}C)</b>'.format(degree), "anchor": "y1",
                                   "domain": [15.0, 32.0],
                                   "range": [10.0, 35.0], 'autorange': True,
                                   'titlefont': {'size': 17, 'color': 'rgb(255,255,255)'}, 'color': 'rgb(255, 255, '
                                                                                                    '255)'},
                           margin={'b': 120},
                           plot_bgcolor='rgb(245,245,245)',
                           paper_bgcolor='rgb(0,51,102)',
                           legend={'bgcolor': '#E2E2E2', 'bordercolor': '#FFFFFF', 'borderwidth':2}
                           )
        layout.update(dict(annotations=outOfLimit))
        figure = go.Figure(data=data, layout=layout)
        plotly.offline.plot(figure, filename='C:\\Users\\ALF\\Desktop\\TempReadings.html', auto_open=False,
                            show_link=False, config={"displayModeBar": False})
        self.webView.load(QUrl(r'file:///C:/Users/ALF/Desktop/TempReadings.html'))
        self.webView.setEnabled(True)
        self.webView.show()
        self.scatterLbl.setVisible(True)


        print(info)
        import plotly.figure_factory as ff

        data_matrix = info
        # colorscale = [[0, '#4d004c'], [.5, '#f2e5ff'], [1, '#ffffff']]
        table = ff.create_table(data_matrix)
        table.layout.width = 485
        plotly.offline.plot(table, filename='C:\\Users\\ALF\\Desktop\\TempReadingsTable.html', auto_open=False,
                            show_link=False, config={"displayModeBar": False})
        self.webViewTable.load(QUrl(r'file:///C:/Users/ALF/Desktop/TempReadingsTable.html'))
        self.webViewTable.setEnabled(True)
        self.webViewTable.show()
        self.tableLbl.setVisible(True)

    def UpdateTable(self, days, temps):
        self.dataTable.setRowCount(len(temps))

        self.dataTable.setUpdatesEnabled(False)
        self.dataTable.clearContents()
        self.dataTable.setRowCount(len(temps))
        for i, (date, temp) in enumerate(zip(days, temps)):
            item = QTableWidgetItem(str(date))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.dataTable.setItem(i, 0, item)

            item = QTableWidgetItem(str(temp))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.dataTable.setItem(i, 1, item)
            self.dataTable.setUpdatesEnabled(True)


app = QApplication(sys.argv)
app.setStyle("plastique")

splash_image = QPixmap("C:\\Users\\ALF\\Desktop\\Thermometer.png")
splash = QSplashScreen(splash_image)
splash.show()
time.sleep(2)
myApp = TempReaderApp()
myApp.show()
splash.finish(myApp)
app.exec_()
