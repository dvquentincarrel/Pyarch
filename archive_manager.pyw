from PyQt4 import QtCore,QtGui
import transfer
import mark
import sys
from os import path
from time import sleep
from threading import Thread
from xml.etree import ElementTree as ET

autoBuildList = True
markDict = {}
Activated = False
stop_thread = False
dir = path.dirname(__file__)

#TBA
dirRoot = ET.parse(path.join(dir,"data.xml")).getroot().find('directories')
dictPos = {}
for i in dirRoot:
	dictPos[i.get('type')] = i.text
 

try: #Checks for the file containing the list of all the marks and their associated directory
    markFile = open(path.join(dir,'mark_file.txt'),'r')
except IOError:
    print("Mark list not found\nCreating mark list")
    markFile = open(path.join(dir,'mark_file.txt'),'w')
    markDict = mark.build_dict(dictPos['target'])
    for i in markDict:
        markFile.write(i+'#'+markDict[i])
    markFile.close()



class TransferThread(Thread): #Thread made switch on/off the file transfer

    def run(self):
        global Activated
        global markDict
        global stop_thread
        while 1:
            if Activated:
                try:
                    moveFeedback = transfer.move_file(dictPos['queue'],markDict)
                    MainApp.transfer_state.setText(moveFeedback['state'])
                    if moveFeedback['log'] != None:
                        MainApp.log_display.append(moveFeedback['log'])
                except Exception as caughtException:
                    errLog = open(path.join(dir,'Error_Log.txt'),'a').write("ERROR: "+str(caughtException)+"\n")
                    MainApp.transfer_state.setText("ERRROR. Check log file for details")
                    sys.exc_clear()
                sleep(1)
            elif not Activated:
                sleep(0.25)
                
            if stop_thread:
                break

                        
class MainWin(QtGui.QMainWindow):

    def __init__(self):
        super(MainWin, self).__init__()
        self.init_archive_tab()
        self.update_dict()
        
    def closeEvent(self,event):
        global stop_thread
        stop_thread = True
    def init_archive_tab(self):
        global archHandler
        self.button_state = False
        self.tabs = QtGui.QTabWidget()
        
        self.switch_button = QtGui.QPushButton('Start',self) #Button used to enable/disable archiving        
        self.update_button = QtGui.QPushButton('Update',self) #Button used to update the mark list
        self.search_button = QtGui.QPushButton('Search',self) #Button used to search for specific marks
        self.search_button.clicked.connect(self.search_mark)
        self.update_button.clicked.connect(self.update_dict)
        self.switch_button.clicked.connect(self.button_update)

        self.mark_display = QtGui.QTextEdit(self) #Block used to display all the marks
        self.log_display = QtGui.QTextEdit(self) #Block used to display the transfer logs
        self.mark_display.setReadOnly(True)
        self.log_display.setReadOnly(True)
        
        self.search_bar = QtGui.QLineEdit('') #Line used to search content in the mark block
        self.search_bar.setPlaceholderText('Type a mark to search')
        self.search_bar.returnPressed.connect(self.search_mark)
        
        self.count_label = QtGui.QLabel('',self) #Label used to display the mark count        
        self.transfer_state = QtGui.QLabel('',self) #Label used to display informations about the transfer state
               
        self.setWindowTitle('Archive Manager')

        self.search_layout = QtGui.QHBoxLayout()
        self.search_layout.addWidget(self.search_bar)
        self.search_layout.addWidget(self.search_button)
        
        self.mark_bottom_layout = QtGui.QVBoxLayout()
        self.mark_bottom_layout.addLayout(self.search_layout)
        self.mark_bottom_layout.addWidget(self.mark_display)

        self.mark_top_layout = QtGui.QHBoxLayout()
        self.mark_top_layout.addWidget(self.update_button)
        self.mark_top_layout.setAlignment(self.update_button,QtCore.Qt.AlignLeft)
        self.mark_top_layout.addWidget(self.count_label)
        self.mark_top_layout.setAlignment(self.count_label,QtCore.Qt.AlignRight)

        self.arch_layout = QtGui.QHBoxLayout()
        self.arch_layout.addWidget(self.switch_button)
        self.arch_layout.setAlignment(self.switch_button,QtCore.Qt.AlignLeft)
        self.arch_layout.addWidget(self.transfer_state)
        self.arch_layout.setAlignment(self.transfer_state,QtCore.Qt.AlignRight)

        self.archive_tab_grid = QtGui.QGridLayout()        
        self.archive_tab_grid.addWidget(self.log_display,1,0,1,1)
        self.archive_tab_grid.addLayout(self.mark_top_layout,0,1,1,1)
        self.archive_tab_grid.addLayout(self.mark_bottom_layout,1,1,1,1)
        self.archive_tab_grid.addLayout(self.arch_layout,0,0,1,1)
        
        self.archive_tab = QtGui.QWidget()
        self.url_tab = QtGui.QWidget()

        self.group_list_label = QtGui.QLabel('Category',self)
        self.group_list_widget = QtGui.QListWidget()
        self.list_test = QtGui.QVBoxLayout()

        category_file = open(path.join(dir,'url_groups.txt'),'r')
        for line in category_file:
            self.group_list_widget.addItem(line[:-1])

        self.list_test.addWidget(self.group_list_label)    
        self.list_test.addWidget(self.group_list_widget)        
        self.url_tab.setLayout(self.list_test)
       
        
        self.archive_tab.setLayout(self.archive_tab_grid)
        self.tabs.addTab(self.archive_tab,"Archive")
        self.tabs.addTab(self.url_tab,"Browse")
        self.setGeometry(300,300,640,520)
        self.setCentralWidget(self.tabs)
        
    def button_update(self): #Trigger between both states of the arch_button to enable/disable archiving
        global Activated
        if Activated:
            self.switch_button.setText("Start")
            self.transfer_state.setText('')
            Activated = False
        elif not Activated:
            self.switch_button.setText("Stop")
            Activated = True
            

    def update_dict(self):
        global markDict
        markDict = mark.build_dict(dictPos['target'])
        self.mark_display.clear()
        self.count_label.setText(str(markDict['count'])+" marks")
        for i in markDict:
            self.mark_display.append(str(i)+' - '+str(markDict[i])+'\n')       
                
    def search_mark(self):
        global markDict
        self.mark_display.clear()
        for i in markDict:
            if str(self.search_bar.text()) in i:
                self.mark_display.append(i+' - '+str(markDict[i])+'\n')
        
if __name__ == '__main__':

        threadExec = [0]
        app = QtGui.QApplication(sys.argv)
        archThread = TransferThread()
        MainApp = MainWin()
        archThread.start()
        MainApp.show()
        sys.exit(app.exec_())
