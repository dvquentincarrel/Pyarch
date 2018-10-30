import sys
import os
import piexif
from os.path import splitext,join
from PIL import Image
from PyQt4 import QtGui,QtCore
from xml.etree import ElementTree as ET


class mainWin(QtGui.QWidget):

	def __init__(self,filepath,tags,fileDir):
		
		super(mainWin,self).__init__()

		self.count = 0
		self.selectedTags = []
		self.fileDir = fileDir
		self.rootDir = filepath
		self.tagDict = tags
		self.lenTags = len(tags)

		self.setUI()
       	
	def displayImg(self, height=770):
		self.pixmap = QtGui.QPixmap(self.rootDir+self.fileDir[0])
		self.pixmap = self.pixmap.scaledToHeight(height,QtCore.Qt.SmoothTransformation)
		self.setFixedWidth(self.pixmap.width()+20)
		self.imgDisplayLabel.setPixmap(self.pixmap)
		
		
	def setUI(self):
		self.setWindowTitle("Tagger")

		self.tagField = QtGui.QLineEdit("")
		self.fNameField = QtGui.QLineEdit("")
		self.tagTypeLabel = QtGui.QLabel(self.tagDict[0][1])
		self.tagCountLabel = QtGui.QLabel(str(self.lenTags))
		self.currentTag = QtGui.QLabel(self.tagDict[0][0])
		self.nextTag = QtGui.QLabel(self.tagDict[1][0])
		self.imgDisplayLabel = QtGui.QLabel()

		self.displayImg()
		self.fNameField.setPlaceholderText("file name")
		self.tagField.setPlaceholderText("exif tags")

		self.tagsLayout = QtGui.QHBoxLayout()
		self.tagsLayout.addWidget(self.tagCountLabel)
		self.tagsLayout.setAlignment(self.tagCountLabel,QtCore.Qt.AlignRight)
		self.tagsLayout.addWidget(self.currentTag)
		self.tagsLayout.setAlignment(self.currentTag,QtCore.Qt.AlignHCenter)
		self.tagsLayout.addWidget(self.nextTag)
		
		self.fieldLayout = QtGui.QHBoxLayout()
		self.fieldLayout.addWidget(self.tagField)
		self.fieldLayout.addWidget(self.fNameField)

		self.UIgrid = QtGui.QGridLayout()
		self.UIgrid.addLayout(self.fieldLayout,0,0)
		self.UIgrid.addWidget(self.imgDisplayLabel,1,0)
		self.UIgrid.addWidget(self.tagTypeLabel,2,0)
		self.UIgrid.setAlignment(self.tagTypeLabel,QtCore.Qt.AlignHCenter)
		self.UIgrid.addLayout(self.tagsLayout,3,0)

		self.setLayout(self.UIgrid)
		self.setGeometry(200,200,200,200)

		self.show()

	def keyPressEvent(self,event):

		if event.key() == 16777237: #Key = down arrow (tag selected)
			self.selectedTags.append(self.tagDict[self.count][0]) #Add the current tag to the selected tags list
			self.update_tag_label()

		if event.key() == 16777235: #Key = up arrow (tag not selected)
			self.update_tag_label()

		if (event.key() == 16777216 and #Key = escape (next picture)
			self.fNameField.text() != ''): #Filename field != empty
			self.count = len(self.tagDict)-1
			self.update_tag_label()

		if (event.key() in (16777220,16777221) and #Key = enter or return (adds the text in the tag field to the selected tags list)
			self.tagField.text() != ''): #Tag field != empty
			self.selectedTags.append(str(self.tagField.text()))
			self.tagField.clear()

		event.accept()


	def update_tag_label(self):

		if self.count == len(self.tagDict)-1:
			#If the current index position is the last element of the tag list
			filename = self.fNameField.text()
			fileObj = decompose_file(fileDir[0],self.rootDir)
			os.rename(fileObj["pathFull"],fileObj["target"]+filename+"!"+fileObj["counter"]+fileObj["ext"]) #Rename file for moving
			convert_to_exif(str(filename+"!"+fileObj["counter"]+fileObj["ext"]),fileObj["target"],self.selectedTags)
			self.count = 0
			self.selectedTags = []
            
			if len(self.fileDir) > 1: #If there are files left to tag
				self.fileDir.pop(0)
				self.displayImg()

				self.currentTag.setText(self.tagDict[0][0])
				self.tagTypeLabel.setText(self.tagDict[0][1])
				self.nextTag.setText(self.tagDict[1][0])
				self.tagCountLabel.setText(str(len(self.tagDict)))

				self.tagField.clear()
				self.fNameField.clear()


				self.setWindowTitle(fileDir[0])
			else: #If there are no files left to tag, quits the program
				sys.exit()
		else:
			self.count += 1
			self.tagTypeLabel.setText(self.tagDict[self.count][1])
			self.tagCountLabel.setText(str(len(self.tagDict)-self.count))	
			self.currentTag.setText(self.tagDict[self.count][0])
            
			if self.count < len(self.tagDicts)-1:
				self.nextTag.setText(self.tagDict[self.count+1][0])
			else:
				self.nextTag.setText('-')
				
#TBA
tagDict = {}
tagRoot = ET.parse('data.xml').getroot().find('tags')
for pos,elem in enumerate(tagRoot):
	tagDict[pos] = [elem.text,elem.get('category')]

#Puts all image file in a given directory, in a list
dirRoot = ET.parse('data.xml').getroot().find('directories')
for pos,elem in enumerate(dirRoot):
	if elem.get('type') == 'to_tag':
		toTagDir = elem.text
	if elem.get('type') == 'queue':
		queueDir = elem.text
                
fileDir = []
for i in os.listdir(toTagDir):
	if splitext(i)[1] in ('.jpg','.png','.jpeg'):
		fileDir.append(i)
fileDir.sort()

            
def decompose_file(file,rootPath,targetPath = queueDir):
	fileObj = {}
	fileObj["file"] = file
	fileObj["name"] = splitext(file)[0]
	fileObj["ext"] = splitext(file)[1]
	fileObj["pathNoExt"] = rootPath+fileObj["name"]
	fileObj["pathFull"] = rootPath+file
	fileObj["target"] = targetPath
	fileObj["counter"] = str(len(os.listdir(targetPath)))
	return fileObj
	
def convert_to_exif(file,filePath,tagList):

	#Converts png files to jpg, to support exif tags
	try:
		if splitext(file)[1] in ('.png','.jpeg'):
			im = Image.open(filePath+file)
			im = im.convert("RGB")
			im.save(filePath+splitext(file)[0]+'.jpg',quality=95)
			os.remove(filePath+file)
			file = splitext(file)[0]+'.jpg'
			
		chrList = []

		exifDict = {
			'Exif': {},
			'0th': {40094: {}},
			'Interop': {},
			'1st': {},
			'thumbnail': None,
			'GPS': {}
				}
		for chr in ';'.join(tagList):
			chrList.extend((ord(chr), 0))
		chrList.extend((0,0))
		exifDict['0th'][40094] = chrList
		exifBytes = piexif.dump(exifDict)
		piexif.insert(exifBytes,filePath+file)
	except Exception as caughtException:
		print caughtException


app = QtGui.QApplication(sys.argv)
lul = mainWin(toTagDir,tagDict,fileDir)
sys.exit(app.exec_())
