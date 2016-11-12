import os

def build_dict(markRoot, archName='arch.txt'):
    markFile = open('mark_file.txt','w')
    markDict = {}
    count = 0
    for root,subdir,filelist in os.walk(markRoot):
        archPath = os.path.join(root,archName)
        if os.path.isfile(archPath):
            mark = open(archPath,'r').read()
            markFile.write(mark+'#'+root+'\n')
            markDict[mark]=root
            count += 1
    markDict['count']=count
    markFile.close()
    return markDict
            

    
                
