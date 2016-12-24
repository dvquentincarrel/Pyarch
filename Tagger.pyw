import sys
import os
import piexif
from os.path import splitext
from PIL import Image
from PyQt4 import QtGui,QtCore
from xml.etree import ElementTree as ET



class mainWin(QtGui.QWidget):

    def __init__(self,filepath,tags,fileDir):
        super(mainWin,self).__init__()

        self.count = 0
        self.selecTags = []
        self.fileDir = fileDir
        self.filePath = filepath
        self.tags = tags
        self.lenTags = len(tags)

        self.setUI()
        
    def displayImg(self,width = 750, height = 750):
        self.pixmap = QtGui.QPixmap(self.filePath+self.fileDir[0])
        self.pixmap = self.pixmap.scaled(width,height,QtCore.Qt.KeepAspectRatio)
        self.imgDisplay.setPixmap(self.pixmap)

    def setUI(self):
        self.setWindowTitle("Tagger")

        self.fieldTag = QtGui.QLineEdit("")
        self.pastTag = QtGui.QLabel(str(self.lenTags))
        self.curTag = QtGui.QLabel(self.tags[0])
        self.futureTag = QtGui.QLabel(self.tags[1])
        self.imgDisplay = QtGui.QLabel()
        
        self.displayImg()
        
        self.tagsLayout = QtGui.QHBoxLayout()
        self.tagsLayout.addWidget(self.pastTag)
        self.tagsLayout.setAlignment(self.pastTag,QtCore.Qt.AlignRight)
        self.tagsLayout.addWidget(self.curTag)
        self.tagsLayout.setAlignment(self.curTag,QtCore.Qt.AlignHCenter)
        self.tagsLayout.addWidget(self.futureTag)

        self.UIgrid = QtGui.QGridLayout()
        self.UIgrid.addWidget(self.fieldTag,0,0)
        self.UIgrid.addWidget(self.imgDisplay,1,0)
        self.UIgrid.addLayout(self.tagsLayout,2,0)
        
        self.setLayout(self.UIgrid)
        
        self.show()

    def keyPressEvent(self,event):

        if event.key() == 16777237: #Key = down arrow
            self.selecTags.append(self.tags[self.count])
            self.updateLabel()

        if event.key() == 16777235: #Key = up arrow
            self.updateLabel()

        if event.key() == 16777216: #Key = escape
            self.fieldTag.setReadOnly(True)
            self.fieldTag.setText("This field is now read-only")

        if (event.key() in (16777220,16777221) and 
            self.fieldTag.text() != '' and 
            not self.fieldTag.isReadOnly()):
            #Key = enter or return + field not empty + != readonly
            self.selecTags.append(str(self.fieldTag.text()))
            self.fieldTag.clear()

        event.accept()


    def updateLabel(self):

        if self.count == len(self.tags)-1:
            #If the current index position is the last element of the tag list
            convertToExif(self.fileDir[0],self.filePath,self.selecTags)
            self.count = 0
            self.selecTags = []
            
            if len(self.fileDir) > 1:
                self.fileDir.pop(0)
                self.displayImg()

                self.curTag.setText(self.tags[0])
                self.futureTag.setText(self.tags[1])
                self.pastTag.setText(str(len(self.tags)))


                self.fieldTag.setReadOnly(False)
                self.fieldTag.clear()


                self.setWindowTitle(fileDir[0])
            else:
                self.imgDisplay.setText('No picture found')

        else:
            self.count += 1
            self.curTag.setText(self.tags[self.count])
            self.pastTag.setText(str(len(self.tags)-self.count))
            
            if self.count < len(self.tags)-1:
                self.futureTag.setText(self.tags[self.count+1])
            else:
                self.futureTag.setText('-')
            

def convertToExif(file,filePath,tagList):

    #Converts png files to jpg, to support exif tags
    try:
        if splitext(file)[1] in ('.png','.jpeg'):
            im = Image.open(filePath+file)
            file = splitext(file)[0]+'.jpg'
            im.save(filePath+file)
        chrList = []

        exifDict = {
            'Exif': {},
            '0th': {40094: {}},
            'Interop': {},
            '1st': {},
            'thumbnail': None,
            'GPS': {}
                }

        """Converts every char in the tag string to its ASCII code
        adds a zero after every character, this is necessary to
        properly convert it to an EXIF tag"""
        for chr in ';'.join(tagList):
            chrList.extend((ord(chr), 0))

        chrList.extend((0,0))
        exifDict['0th'][40094] = chrList
        exifBytes = piexif.dump(exifDict)
        piexif.insert(exifBytes,filePath+file)
    except Exception as caughtException:
        print caughtException

#TBA
tagDict = {}
tagRoot = ET.parse('data.xml').getroot().find('tags')
for pos,elem in enumerate(tagRoot):
    tagDict[pos] = [elem.text,elem.get('category')]
tags = []
with open('tags.txt','r') as f:
    for line in f:
        tags.append(line.rstrip())

#Puts all image file in a given directory, in a list
fileDir = []
for i in os.listdir('C:\Users\Quentin\Desktop\Downloads\To_archive\\'):
    if splitext(i)[1] in ('.jpg','.png','.jpeg'):
        fileDir.append(i)
fileDir.sort()

app = QtGui.QApplication(sys.argv)
lul = mainWin('C:\Users\Quentin\Desktop\Downloads\To_archive\\',tags,fileDir)
sys.exit(app.exec_())
