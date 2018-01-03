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
import shutil
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler

import fpdf
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QSplashScreen, QTreeWidgetItem, QWidget
from bokeh.io import export_png
from bokeh.layouts import column
from bokeh.models import CDSView, ColumnDataSource, HoverTool, IndexFilter
from bokeh.plotting import figure, output_file, save
from fpdf import HTMLMixin

qtCreatorFile = "UI" + os.sep + "tempR5.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class TempReaderApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.initUI()

        logFile = "Logs" + os.sep + "TempReaderApp.log"
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(funcName)s - Line %(lineno)d - %(levelname)s: %(message)s',
                            datefmt='%m-%d-%Y %I:%M:%S %p',
                            filename=logFile,
                            filemode='a')

        handler = RotatingFileHandler(logFile, maxBytes=5 * 1024 * 1024,
                                      backupCount=1, encoding=None, delay=0)
        logging.getLogger().addHandler(handler)
        logging.debug("Temperature app initialized")


    def initUI(self):
        font = QFont()
        font.setPointSize(12)
        self.center()
        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon("Icons" + os.sep + "Thermometer.png"))
        self.webView.setEnabled(False)
        self.webViewTable.setEnabled(False)
        self.plotTabLbl.setText("Select file to load.")
        self.plotTabLbl.setVisible(True)
        self.tableTabLbl.setText("Select file to load.")
        self.tableTabLbl.setVisible(True)
        self.loadBtn.clicked.connect(self.ProcessData)
        self.resetBtn.clicked.connect(self.Reset)
        self.createPDFBtn.clicked.connect(self.CreatePDF)
        self.exitBtn.clicked.connect(self.Exit)
        self.imageGLbl.setPixmap(QtGui.QPixmap("Icons" + os.sep + "whitegear.png"))
        self.imageFLbl.setPixmap(QtGui.QPixmap("Icons" + os.sep + "file.png"))
        self.imageCLbl.setPixmap(QtGui.QPixmap("Icons" + os.sep + "scatterplot.png"))

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

        self.webViewTable.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.webViewTable.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.webViewTable.setEnabled(False)
        self.treeWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.treeWidget.setStyleSheet("""
        QTreeWidget:item:disabled {
            color: #A0A0A0;
        }
        """)
        self.tabWidget.setCurrentIndex(0)

        self.miniBtn.clicked.connect(self.miniScreen)

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def miniScreen(self):
        self.setWindowState(Qt.WindowMinimized)

    def LoadFile(self):
        logging.debug("Loading temperature file")
        self.CleanPlot()
        self.fname = QFileDialog.getOpenFileName(self, 'Select file', '/home', 'Temp File (8500_RCTT.json)')
        self.fileEdit.setText(self.fname[0])

        if not self.fname[0]:
            logging.warning("Temperature file selection cancelled")
            return None

        logging.info("Filename: {0}".format(self.fname[0]))
        return self.fname[0]


    def ProcessData(self):
        file = self.LoadFile()
        print("test")
        self.tableTabLbl.setText("Loading file, please wait.")
        self.tableTabLbl.setVisible(True)
        self.plotTabLbl.setText("Loading file, please wait.")
        self.plotTabLbl.setVisible(True)
        QApplication.processEvents()

        if not file:
            logging.debug("File not selected")
            return
        logging.debug("Processing data")

        days, high, low, temps, status, sn, times = self.ReadData()

        if not all([days, high, low, temps, status, sn, times]):
            logging.error("Could not process data from temperature file, list is None")
            return None

        self.CreatePlot(days, temps, high, low, status, sn, times)

    def ReadData(self):
        logging.debug("Begin reading temperature data")
        temps = []
        days = []
        times = []
        status = []
        sn = []
        high = []
        low = []

        try:
            with open(self.fname[0]) as file:
                data = json.load(file)
            for item in data["Readings"]:
                temps.append(item["AvgTemp"])
                days.append("{0}-{1}-{2}".format(item["Date"][5:7], item["Date"][8:], item["Date"][0:4]))
                high.append(item["HighRange"])
                low.append(item["LowRange"])
                times.append(item["Time"])
                status.append(item["Status"])
                sn.append(item["SN"])
            return days, high, low, temps, status, sn, times
        except Exception as ex:
            MessageBox("Error opening file {0}".format(ex))
            logging.error("Exception occurred reading data: {0}".format(ex))
            return None, None, None, None, None, None, None


    def CleanPlot(self):
        logging.debug("clean plots on the UI")
        self.webView.setVisible(False)
        self.webViewTable.setVisible(False)
        self.webView.setEnabled(False)
        self.webViewTable.setEnabled(False)
        self.plotTabLbl.setText("Select file to load.")
        self.plotTabLbl.setVisible(True)
        self.tableTabLbl.setText("Select file to load.")
        self.tableTabLbl.setVisible(True)


    def CreatePlot(self, days, temps, high, low, status, sn, times):
        logging.debug("Creating plot of temperature data")
        degree = u"\u00b0"
        # upper = [high[0]] * len(days)
        # lower = [low[0]] * len(days)

        self.openbrowser = True if self.browser.checkState(0) == 2 else False
        self.saveFiles = True if self.sav_img.checkState(0) == 2 else False

        # image = 'png'
        img_plot_filename = 'img_TempReadingsPlot.png'
        img_table_filename = 'img_TempReadingsTable.png'

        # output to static HTML file
        output_file("temp_plot.html")
        tools = ["box_select", "hover", "reset"]
        # create a new plot
        p = figure(plot_height=700, plot_width=1000, tools=tools, x_axis_label='Days', x_minor_ticks=len(days),
                   y_axis_label='Temperature ({0}C)'.format(degree), x_axis_type="datetime", toolbar_location="right",
                   title="All Temperature Readings")
        p_filtered = figure(plot_height=700, plot_width=1000, tools=tools, x_axis_label='Days',
                                x_minor_ticks=len(days),
                                y_axis_label='Temperature ({0}C)'.format(degree), x_axis_type="datetime",
                                toolbar_location="right",
                                title="Out of Limit Temperature Readings")

        from datetime import datetime
        daysF = None
        try:
            daysF = [datetime(int(x[6:]),int(x[0:2]),int(x[3:5])) for x in days]
        except Exception as ex:
            logging.warning("Could not convert to date time object: {0}".format(ex))
            MessageBox("Error encountered processing data: {0}".format(ex))

        source = ColumnDataSource(data={
            'Day': daysF,  # python datetime object as X axis
            'Temp': temps,
            'Day_str': days,  # string of datetime for display in tooltip
            'High': high,
            'Low': low,
            'Status': status})


        # p.line(days, upper, legend="Upper Limit", line_width=3)
        # p.line(days, lower, legend="Lower Limit", line_width=3)
        filter_points =[]
        for i, item in enumerate(temps):
            if item < low[i] or item > high[i]:
                filter_points.append(i)
        view = CDSView(source=source, filters=[IndexFilter(filter_points)])
        p_filtered.circle('Day', 'Temp', source=source, legend="Readings", line_width=3, hover_color="green", alpha=0.4,
                   size=11, view=view)
        # p.annulus(x=days, y=temps, color="#7FC97F",
        #              inner_radius=0.2, outer_radius=0.5)

        p_filtered.title.align = "center"
        p_filtered.title.text_color = "navy"
        p_filtered.title.text_font_size = "20px"
        p_filtered.title.text_font_style = "bold"
        p_filtered.xaxis[0].ticker.desired_num_ticks = len(days)
        p_filtered.legend.visible = False
        p_filtered.select_one(HoverTool).tooltips = [
            ('Date', '@Day_str'),
            ('Temp', '@Temp'),
            ('High', '@High'),
            ('Low', '@Low'),
            ('Status', '@Status')
            ]

        p.circle('Day', 'Temp', source=source, legend="Readings", line_width=3, hover_color="green", alpha=0.4,
                 size=11)
        # p.annulus(x=days, y=temps, color="#7FC97F",
        #              inner_radius=0.2, outer_radius=0.5)

        p.title.align = "center"
        p.title.text_color = "navy"
        p.title.text_font_size = "20px"
        p.title.text_font_style = "bold"
        p.xaxis[0].ticker.desired_num_ticks = len(days)
        p.legend.visible = False
        p.select_one(HoverTool).tooltips = [
            ('Date', '@Day_str'),
            ('Temp', '@Temp'),
            ('High', '@High'),
            ('Low', '@Low'),
            ('Status', '@Status')
            ]

        if filter_points:
            save(column(p, p_filtered))
        else:
            save(column(p))

        try:
            shutil.copy2(os.path.join('temp_plot.html'), os.path.join("Plots" + os.sep + "plot.html"))
        except Exception as ex:
            logging.warning("Could not move files: {0}".format(ex))
            MessageBox("Error encountered processing data: {0}".format(ex))

        self.createHTML(days, temps, high, low, times, status, sn)


        if self.openbrowser:
            import webbrowser
            webbrowser.open(os.path.join("Plots" + os.sep + "plot.html"))
            webbrowser.open(os.path.join("Plots" + os.sep + "HTMLTable.html"))

        if self.saveFiles:
            export_png(p, filename=img_plot_filename)
            try:
                shutil.move(os.path.join(img_plot_filename), os.path.join("Images" + os.sep + img_plot_filename))
            except Exception as ex:
                logging.warning("Could not move files: {0}".format(ex))
                MessageBox("Error encountered processing data: {0}".format(ex))

        self.ShowPlots(r"Plots\plot.html", r"Plots\HTMLTable.html")

    def createHTML(self, days, temps, high, low, times, status, sn):
        strTable = """
                        <html>
                        <head>
                        <style>
                        table{
                                width: 100%;
                                border-collapse: collapse;
                                font-family: Arial, serif;
                            }
                            
                            th{
                                height: 5px;
                                text-align: center;
                                background-color: #003366;;
                                color: white;
                                border: 1px solid #008CBA;
                            }
                            
                            td{
                                height: 5px;
                                text-align: center;
                                border: 1px solid #008CBA;
                                font-size: 13px;
                            }
                            </style>
                            </head>
                            <div style=overflow - x: auto;>
                            <table>
                            <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Temp</th>
                            <th>High</th>
                            <th>Low</th>
                            <th>Status</th>
                            <th>SN</th>
                            </tr>
                            
                            """
        endTable ="</table></div></html>"

        for i in range(len(days)):
            if temps[i] <= high[i] and temps[i] >= low[i]:
                strRW = "<tr><td>" + str(days[i]) + "</td><td>" + str(times[i]) + "</td><td>" + str(temps[i]) \
                        + "</td><td>" + str(high[i])+ "</td><td>" + str(low[i]) + "</td><td>" + str(status[i]) \
                        + "</td><td>" + str(sn[i]) + "</td></tr>"
            else:
                strRW = "<tr style=color:red><td>" + str(days[i]) + "</td><td>" + str(times[i]) + "</td><td>" + str(temps[i]) \
                        + "</td><td>" + str(high[i]) + "</td><td>" + str(low[i]) + "</td><td>" + str(status[i]) \
                        + "</td><td>" + str(sn[i]) + "</td></tr>"
            strTable = strTable + strRW
        strTable = strTable + endTable

        with open("Plots" + os.sep + "HTMLTable.html", 'w') as html:
            html.write(strTable)
        return html

    def ShowPlots(self, html, table):
        logging.debug("Showing plot")
        self.webView.load(QUrl(os.path.join("file:///" + os.path.abspath(html))))
        self.webViewTable.load(QUrl(os.path.join("file:///" + os.path.abspath(table))))
        self.webView.setEnabled(True)
        self.webViewTable.setEnabled(False)
        self.plotTabLbl.setVisible(False)
        self.tableTabLbl.setVisible(False)
        self.webViewTable.show()
        self.webView.show()
        logging.debug("End Showing plot")


    def CreatePDF(self):
        try:
            directory = self.directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                                          os.path.dirname(os.path.realpath(__file__)),
                                                                          QFileDialog.ShowDirsOnly)
            self.pdfEdit.setText(self.directory)

            # TODO check if files exists
            plotFilename = "img_TempReadingsPlot.png"
            if not os.path.isfile(directory + os.sep + plotFilename):
                logging.warning("Files are missing")
                msg = MessageBox("Image files are missing.")
                return
            pdf = MyPDF()
            pdf.alias_nb_pages()
            pdf.set_display_mode(zoom='real', layout='default')
            pdf.add_page("L")
            pdf.set_font('Arial', 'B', 12)
            pdf.set_title("Reagent Carousel Temperature Report")
            pdf.set_author("Rick Roll")
            # pdf.text(70.0, 5.0, "Reagent Carousel Temperature Report")
            pdf.image(directory + os.sep + plotFilename, x=45, y=None, w=0, h=160)
            pdf.set_x(60)
            h = """
            
                        <html>
                        <head>
                            <table>
                            <tr>
                            <th width="14%">Date</th>
                            <th width="14%">Time</th>
                            <th width="14%">Temp</th>
                            <th width="14%">High</th>
                            <th width="14%">Low</th>
                            <th width="14%">Status</th>
                            <th width="14%">SN</th>
                            </tr>
                            
                            <tr><td>09-12-2016</td><td>07:10:52 AM</td><td>8.7</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr style=color:red><td>09-13-2016</td><td>07:12:15 AM</td><td>1.2</td><td>15.0</td><td>2.0</td><td>Fail</td><td>16FMP00032</td></tr><tr><td>09-14-2016</td><td>08:08:02 AM</td><td>6.1</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-15-2016</td><td>08:14:23 AM</td><td>8.0</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-16-2016</td><td>01:43:56 PM</td><td>8.1</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-17-2016</td><td>01:45:04 PM</td><td>9.2</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-18-2016</td><td>03:17:04 PM</td><td>9.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-19-2016</td><td>03:40:05 PM</td><td>9.6</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-20-2016</td><td>03:40:46 PM</td><td>9.7</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-21-2016</td><td>03:42:26 PM</td><td>9.8</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-22-2016</td><td>03:43:22 PM</td><td>9.9</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-23-2016</td><td>03:45:20 PM</td><td>10.0</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-24-2016</td><td>03:47:49 PM</td><td>10.1</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-25-2016</td><td>03:48:26 PM</td><td>10.2</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-26-2016</td><td>10:13:56 AM</td><td>10.3</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-27-2016</td><td>11:40:18 AM</td><td>10.4</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-28-2016</td><td>11:41:44 AM</td><td>10.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-29-2016</td><td>11:43:48 AM</td><td>10.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>09-30-2016</td><td>01:45:21 PM</td><td>10.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr style=color:red><td>10-01-2016</td><td>02:00:36 PM</td><td>15.9</td><td>15.0</td><td>2.0</td><td>Fail</td><td>16FMP00032</td></tr><tr><td>10-02-2016</td><td>02:01:11 PM</td><td>10.6</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-03-2016</td><td>02:01:46 PM</td><td>10.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-04-2016</td><td>02:02:11 PM</td><td>10.6</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-05-2016</td><td>02:02:42 PM</td><td>10.4</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-06-2016</td><td>02:03:14 PM</td><td>10.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-07-2016</td><td>02:03:52 PM</td><td>10.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-08-2016</td><td>02:04:32 PM</td><td>10.6</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-09-2016</td><td>02:04:58 PM</td><td>13.5</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-10-2016</td><td>02:45:23 PM</td><td>10.6</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-11-2016</td><td>09:45:16 AM</td><td>11.0</td><td>15.0</td><td>2.0</td><td>Pass</td><td>16FMP00032</td></tr><tr><td>10-12-2016</td><td>09:47:09 AM</td><td>11.0</td><td>15.0</td><td>8.0</td><td>Pass</td><td>16FMP00032</td></tr></table></div></html>
            """
            pdf.write_html(h)
            outputFile = "Reports" + os.sep + 'TempReadingsReport.pdf'
            pdf.output(outputFile, "F")
            pdf.close()
            print("open file")
            subprocess.Popen([outputFile], shell=True)
        except Exception as ex:
            logging.error("Error occurred while generating PDF {0}".format(ex))
            errorMessage = MessageBox("Error encountered: {0}".format(ex))
            errorMessage.showDialog()


    def Reset(self):
        self.CleanPlot()
        self.fileEdit.setText('')
        self.pdfEdit.setText('')
        self.loadBtn.setEnabled(True)


    def Exit(self):
        sys.exit(0)


class MyPDF(fpdf.FPDF, HTMLMixin):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation='P', unit='mm', format='A4')


    def header(self):
        """
        Header on each page
        """
        # set the font for the header, B=Bold
        self.set_font("Arial", style="B", size=15)

        # insert my logo
        self.image("Icons" + os.sep + "Thermometer.png", x=90, y=5, w=15)
        # position logo on the right
        self.cell(w=80)

        # page title
        self.cell(120.0, 5.0, "Reagent Carousel Temperature Report", ln=0, align="C")

        # insert a line break of 20 pixels
        self.ln(15)

    def footer(self):
        """
        Footer on each page
        """
        # set the font, I=italic
        self.set_font("Arial", style="B", size=9)

        # position footer at 15mm from the bottom
        self.set_y(-15)

        # display the page number and center it
        pageNum = "Page %s of {nb}" % self.page_no()
        self.cell(0, 10, pageNum, align="C")




class MessageBox(QWidget):

    def __init__(self, message):
        super().__init__()
        self.title = 'MessageBox'
        self.message = message
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("""  QMessageBox {
                                    background-color: #008CBA;
                                }

                                QMessageBox QLabel {
                                    color: white;
                                }
                                QMessageBox QPushButton {
                                    color: white;
                                    background-color: #003366;
                                }
                            """
                )
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        button = QMessageBox.warning(self, self.title, self.message, QMessageBox.Ok)

    def showDialog(self):
        self.show()


app = QApplication(sys.argv)
app.setStyle("fusion")
splash_image = QPixmap("Icons" + os.sep + "ThermometerR.png").scaled(200, 200, QtCore.Qt.KeepAspectRatio)
splash = QSplashScreen(splash_image)
splash.show()
time.sleep(1)
myApp = TempReaderApp()
myApp.show()
splash.finish(myApp)
app.exec_()
