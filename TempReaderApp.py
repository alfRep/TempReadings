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
import logging
import os
import sys
import time

import plotly
import plotly.graph_objs as go
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QSplashScreen, QTreeWidgetItem

qtCreatorFile = "UI" + os.sep + "tempR3.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)   #uic.loadUiType(qtCreatorFile)


class TempReaderApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.initUI()

        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(funcName)s - Line %(lineno)d - %(levelname)s: %(message)s',
                            datefmt='%m-%d-%Y %I:%M:%S %p',
                            filename="Logs" + os.sep + "TempReaderApp.log",
                            filemode='a')
        logging.debug("Initialized")


    def initUI(self):
        font = QFont()
        font.setPointSize(12)
        self.center()
        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon("Images" + os.sep + "Thermometer.png"))
        self.chooseBtn.clicked.connect(self.FileChooser)
        self.webView.setEnabled(False)
        self.webViewTable.setEnabled(False)
        self.fileErrorLbl.setVisible(False)
        self.plotTabLbl.setVisible(True)
        self.tableTabLbl.setVisible(True)
        self.loadBtn.setEnabled(False)
        self.loadBtn.clicked.connect(self.ProcessData)
        self.resetBtn.clicked.connect(self.Reset)
        self.exitBtn.clicked.connect(self.Exit)
        self.imageGLbl.setPixmap(QtGui.QPixmap("Images" + os.sep + "whitegear.png"))
        self.imageFLbl.setPixmap(QtGui.QPixmap("Images" + os.sep + "file.png"))

        self.browser = QTreeWidgetItem(self.treeWidget)
        self.browser.setFlags(self.browser.flags() | Qt.ItemIsUserCheckable)
        self.browser.setText(0, "Open Browser")
        self.browser.setCheckState(0, Qt.Unchecked)
        self.browser.setFont(0, font)

        self.sav_img = QTreeWidgetItem(self.treeWidget)
        self.sav_img.setFlags(self.sav_img.flags() | Qt.ItemIsUserCheckable)
        self.sav_img.setText(0, "Save Images")
        self.sav_img.setCheckState(0, Qt.Unchecked)
        self.sav_img.setFont(0, font)

        self.pdf = QTreeWidgetItem(self.sav_img)
        self.pdf.setFlags(self.pdf.flags() |  Qt.ItemIsUserCheckable)
        self.pdf.setText(0, "Create PDF")
        self.pdf.setCheckState(0, Qt.Unchecked)
        self.pdf.setDisabled(True)
        self.pdf.setFont(0, font)

        self.webViewTable.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.webViewTable.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.treeWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.treeWidget.setStyleSheet("""
        QTreeWidget:item:disabled {
            color: #A0A0A0;
        }
        """)
        self.tabWidget.setCurrentIndex(0)

        self.treeWidget.itemChanged.connect(self.SaveImageSignal)

    def SaveImageSignal(self):
        if self.sav_img.checkState(0) == 2:
            self.browser.setCheckState(0, QtCore.Qt.Checked)
        if self.pdf.checkState(0) == 2:
            self.sav_img.setCheckState(0, QtCore.Qt.Checked)


    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def FileChooser(self):
        logging.debug("Choosing file")
        self.CleanPlot()
        self.fileErrorLbl.setVisible(False)
        self.fname = QFileDialog.getOpenFileName(self, 'Select file', '/home', 'Temp File (8500_RCTT.json)')
        self.fileEdit.setText(self.fname[0])
        if not self.fname[0]:
            logging.error("Temp file not opened")
            return None
        self.loadBtn.setEnabled(True)
        logging.info("Filename: {0}".format(self.fname[0]))
        return self.fname[0]

    def ProcessData(self):
        logging.debug("Processing data")

        days, high, low, meta, temps, info = self.ReadData()

        if not all([days, high, low, meta, temps, info]):
            logging.error("Could not process data")
            return None

        # self.UpdateTable(days, temps)

        self.CreatePlot(days, meta, temps, high, low, info)

    def ReadData(self):
        logging.debug("Read data")
        temps = []
        days = []
        meta = []
        times = []
        status = []
        sn = []
        high = []
        low = []
        # info = [["DATE"], ["TEMP"], ["TIME"], ["STATUS"], ["SN"]]
        info = []
        try:
            with open(self.fname[0]) as file:
                data = json.load(file)
            for item in data["Readings"]:
                temps.append(item["AvgTemp"])
                days.append("{0}-{1}-{2}".format(item["Date"][5:7], item["Date"][8:], item["Date"][0:4]))
                meta.append("SN: {0}<br>Status: {1}<br>Time: {2}".format(item["SN"], item["Status"], item["Time"]))
                high.append(item["HighRange"])
                low.append(item["LowRange"])
                times.append(item["Time"])
                status.append(item["Status"])
                sn.append(item["SN"])
                # info.append([item["Date"], item["AvgTemp"], item["Time"], item["Status"], item["SN"]])
            info.extend([days] + [temps] + [times] + [status] + [sn])
            return days, high, low, meta, temps, info
        except Exception as ex:
            self.fileErrorLbl.setVisible(True)
            logging.error("Exception occurred: {0}".format(ex))
            return None, None, None, None, None, None


    def CleanPlot(self):
        logging.debug("clean plots")
        self.webView.setVisible(False)
        self.webViewTable.setVisible(False)
        self.webView.setEnabled(False)
        self.webViewTable.setEnabled(False)
        self.plotTabLbl.setVisible(True)
        self.tableTabLbl.setVisible(True)


    def CreatePlot(self, days, meta, temps, high, low, info):
        logging.debug("Creating plot")
        degree = u"\u00b0"
        upper = [high[0]] * len(days)
        lower = [low[0]] * len(days)

        self.openbrowser = True if self.browser.checkState(0) == 2 else False
        if self.sav_img.checkState(0) == 2:
            image = 'png'
            img_plot_filename = 'img_TempReadingsPlot'
            img_table_filename = 'img_TempReadingsTable'
        else:
            image = img_plot_filename = img_table_filename = None


        outOfLimit = []
        for i, item in enumerate(temps):
            if item > upper[0] or item < lower[0]:
                outOfLimit.append(
                        go.Annotation(text="<b>Out Of Range</b>", yshift=12, x=i, y=item, font=dict(family='Arial',
                                                                                                    size=7,
                                                                                                    color='red'),
                                      showarrow=False))
        logging.info("Number out of limit: {0}".format(len(outOfLimit)))
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
        plotly.offline.plot(figure, filename=htmlPlot, auto_open=self.openbrowser, image=image,
                            image_filename=img_plot_filename, show_link=False,
                            config={'displaylogo': False, 'modeBarButtonsToRemove': itemsToRemove})
        # plotly.offline.plot(figure, filename=htmlPlot, auto_open=False, show_link=False,
        #                     config={"displayModeBar": True})



        data_matrix = info
        headers = [["DATE"], ["TEMP"], ["TIME"], ["STATUS"], ["SN"]]
        # # colorscale = [[0, '#4d004c'], [.5, '#f2e5ff'], [1, '#ffffff']]
        # table = ff.create_table(data_matrix)
        # table.layout.width = 485
        #
        tablePlot = os.path.join("Plots" + os.sep + 'TempReadingsTable.html')
        #
        # plotly.offline.plot(table, filename=tablePlot, auto_open=self.openbrowser, show_link=False,
        #                     config={"displayModeBar": False})

        trace = go.Table(

                header=dict(values=headers,

                            line=dict(color='rgb(50,50,50)', width=1),
                            align=['center'] * 5,
                            font=dict(color=['white'] * 5, size=14),
                            fill=dict(color='rgb(0,51,102)')
                            ),
                cells=dict(values=info,
                           align=['center'] * len(days),
                           line=dict(color='rgb(50,50,50)', width=1),
                           )
                )

        layout = dict(width=1100, height=721, margin=dict(b=0, t=0, r=60, l=0), paper_bgcolor='#EFEFEF', dragmode=None)
        data = [trace]
        fig = dict(data=data, layout=layout)

        plotly.offline.plot(fig, filename=tablePlot,auto_open=self.openbrowser, show_link=False, image=image,
                            image_filename=img_table_filename,
                            config={'displaylogo': False, 'modeBarButtonsToRemove': itemsToRemove})


        self.ShowPlots(htmlPlot, tablePlot)

        # TODO
        # if self.pdf.checkState(0) == 2:
        #     self.convert_html_to_pdf(tablePlot, "Reports" + os.sep + 'TempReadingsPlot.pdf')

    def ShowPlots(self, html, table):
        logging.debug("Showing plot")
        self.webView.load(QUrl(os.path.join("file:///" + os.path.abspath(html))))
        self.webViewTable.load(QUrl(os.path.join("file:///" + os.path.abspath(table))))
        self.webView.setEnabled(True)
        self.webViewTable.setEnabled(True)
        self.plotTabLbl.setVisible(False)
        self.tableTabLbl.setVisible(False)
        self.webViewTable.show()
        self.webView.show()


    def convert_html_to_pdf(self, source_html, output_filename):
        doc = QTextDocument()
        location = source_html
        print(location)
        html = open(location).read()
        doc.setHtml(html)
        printer = QPrinter()
        printer.setOutputFileName(output_filename)
        printer.setOutputFormat(QPrinter.PdfFormat)
        # printer.setPageSize(QPrinter.A4)
        # printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)
        doc.print(printer)

        # pdf = weasyprint.HTML('http://www.google.com').write_pdf()
        # file('google.pdf', 'w').write(pdf)

        # config = pdfkit.configuration(wkhtmltopdf='/opt/bin/wkhtmltopdf')
        # pdfkit.from_file(source_html, output_filename, configuration=config)
        # # open output file for writing (truncated binary)
        # result_file = open(output_filename, "w+b")
        #
        # # convert HTML to PDF
        # pisa_status = pisa.CreatePDF(
        #         source_html,  # the HTML to convert
        #         dest=result_file)  # file handle to recieve result
        #
        # # close output file
        # result_file.close()  # close output file
        #
        # # return True on success and False on errors
        # return pisa_status.err


    def Reset(self):
        self.CleanPlot()
        self.fileEdit.setText('')
        self.loadBtn.setEnabled(False)


    def Exit(self):
        sys.exit(0)

app = QApplication(sys.argv)
app.setStyle("fusion")
splash_image = QPixmap("Images" + os.sep + "ThermometerR.png").scaled(200, 200, QtCore.Qt.KeepAspectRatio)
splash = QSplashScreen(splash_image)
splash.show()
time.sleep(1)
myApp = TempReaderApp()
myApp.show()
splash.finish(myApp)
app.exec_()
