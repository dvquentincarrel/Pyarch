import os
import time
from os.path import join
from os.path import splitext
from shutil import move
from threading import Thread

import piexif
from PIL import Image
from win32api import SetFileAttributes
from win32con import FILE_ATTRIBUTE_HIDDEN

import sizecheck

class Decompose_file():

        def __init__(self,basePath,filename,separator='!'):
                self.sep = separator
                self.pathOnly = basePath
                self.pathFull = join(basePath,filename)
                self.nameFull = filename
                self.nametagOnly = splitext(filename)[0]
                self.extOnly = splitext(filename)[1]
                self.tagOnly = filename.split(separator)[1:]
                self.nameOnly = splitext(filename.split(separator)[0])[0]

        def changeExt(self,newExt):
                filenameNew = splitext(self.nameFull)[0]+newExt
                self.__init__(self.pathOnly,filenameNew)
                

def insertTag(fileObj): #Function used to extract EXIF:XPKeywords from filename and add it as EXIF tag

        try:
                chrList = []        

                exifDict = {
                        'Exif': {},
                        '0th': {40094: {}},
                        'Interop': {},
                        '1st': {},
                        'thumbnail': None,
                        'GPS': {}
                            }
                
                for chr in ';'.join(fileObj.tagOnly):
                        chrList.extend((ord(chr), 0)) #Convert every char in the exif string to its ASCII counterpart
                        
                chrList.extend((0,0))
                exifDict['0th'][40094] = chrList
                exifBytes = piexif.dump(exifDict)
                piexif.insert(exifBytes,fileObj.pathFull)
                cleanName = join(fileObj.pathOnly,fileObj.nameOnly+fileObj.extOnly)
                os.rename(fileObj.pathFull, cleanName)
                return fileObj.nameOnly+fileObj.extOnly
        except Exception as caughtException:
                print caughtException


def move_file(basePath,markDict,logPath=('arch_log.txt'),fileExt = ['.bmp','.gif','.jpg','.jpeg','.png','.webm','.mp4','.avi']):
        
        fileQueue = os.listdir(basePath)
        fileCount = 1
        
        if fileQueue: #Put in a list all elements in the root directory, remove all file whose extension isn't contained in fileExt
                
                for file in fileQueue:
                        if not splitext(file)[1] in fileExt:
                                fileQueue.remove(file)
                fileObj = Decompose_file(basePath,fileQueue[0])
                
                sizecheck.WaitForDownload(fileObj.pathFull) #Waits for the file to be fully downloaded
                if fileObj.extOnly == '.png':
                        try:
                                im = Image.open(fileObj.pathFull)
                                im.save(join(basePath,fileObj.nametagOnly+'.jpg'))
                                os.remove(fileObj.pathFull)
                                fileObj.changeExt('.jpg')
                        except Exception as caughtException:
                                print "Error during converstion :",caughtException

                if fileObj.sep in fileObj.nametagOnly:
                        fileObj.nameFull = insertTag(fileObj)
                for i in markDict: #Test if name of first element in the list is a mark
                        if fileObj.nameOnly == i:
                                for file in os.listdir(markDict[i]): #Counts the number of file in the target directory
                                        if splitext(file)[1] in fileExt:
                                                fileCount += 1
                                curFileExt = '.'+fileQueue[0].split('.')[1]
                                try:
                                        fileObj.pathFull = join(markDict[i], str(fileCount)+fileObj.extOnly)
                                        move( join(basePath,fileObj.nameFull), fileObj.pathFull)
                                        SetFileAttributes(fileObj.pathFull,FILE_ATTRIBUTE_HIDDEN)
                                        logFile = open(logPath,'a').write('added '+str(fileCount)+' to: '+markDict[i]+' - '+time.strftime('%HH of %d/%m/%Y')+'\n')
                                        return {'state':'Transfer complete', 'log':str(fileCount)+' -> '+markDict[i]}
                                except EnvironmentError as error:
                                        print error
                                return {'state':'Error during transfer', 'log':error}
                return {'state':'No corresponding mark found', 'log':None}
        else:
                return {'state':'No file found', 'log':None}
