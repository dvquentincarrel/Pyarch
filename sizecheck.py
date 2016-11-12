import os
import time
           
def WaitForDownload(fileName,timer=150):
    counter = 0
    oldFileSize = -1
    while counter < timer:
        fileSize = int(os.stat(fileName).st_size)
        if fileSize == oldFileSize and oldFileSize != 0:
            counter += 1
        else:
            counter = 0
        oldFileSize = fileSize
        time.sleep(0.01)
    return True
