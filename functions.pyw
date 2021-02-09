#!python3
import os
import random
import time
import re
from PIL import Image, ImageTk
from os.path import splitext,join
from xml.etree import ElementTree as ET

XML_FILE = "pyteg.xml"

def get_gif_frames(file_name):
    frame_list = []
    gif_file = Image.open(file_name)
    i=0
    try:
        while 1:
            frame_list.append(ImageTk.PhotoImage(gif_file))
            i += 1
            gif_file.seek(i)
    except EOFError:
        print(i,"frames found")
        return frame_list

def index_check(index,list_length,index_mod):
    """Check if index stays within range"""
    index += index_mod
    if index == -1: #underflow
        index = list_length-1
    elif index == list_length: #overflow
        index = 0
    return index

def build_IF_txt_list(name_list,target_dir,mode="str"):
    """Formats the list of tags to be pastable in a text file for Irfanview"""
    #file_list = [target_dir+i+'.jpg' for i in name_list]
    file_list = []
    for i in name_list:
        cur_file_path = target_dir+i+'.jpg'
        if os.path.isfile(cur_file_path):
            file_list.append(cur_file_path)
        elif os.path.isdir(target_dir+i):
            for j in os.listdir(target_dir+i):
                file_list.append(target_dir+i+"/"+j)

    if mode=='str':
        return '\n'.join(file_list)
    elif mode=='list':
        return file_list

def pic_processing(file_name,new_id,tag_list,edit_tag,SOURCE_DIR):
    if edit_tag in tag_list:
        os.rename(SOURCE_DIR+file_name,SOURCE_DIR+edit_tag+'/'+file_name)
    else:
        move_file(file_name,new_id)
        add_tags(tag_list,new_id)
        update_log(new_id)

def set_processing(folder_name,new_id,tag_list,elem_list):
    move_folder(folder_name,new_id)
    if len(elem_list) == 1:  #automatically tags single-element sets as incomplete
        tag_list += '\nincomplete'
    tag_list += '\nset'
    add_tags(tag_list,new_id)
    update_log(new_id)

def add_name(XML_FILE,reference_tag):
    """Adds a random unique id to the $XML_FILE and returns it as a string"""
    xml_parsed = ET.parse(XML_FILE)
    xml_root = xml_parsed.getroot()
    all_ids_list = xml_root.find(reference_tag).text
    new_id = rand_name()
    while new_id in all_ids_list:
        new_id = rand_name()
    xml_root.find(reference_tag).text += '\n'+new_id
    xml_parsed.write(XML_FILE)
    print("name" ,new_id," added")
    return new_id

def get_dirs(XML_FILE,verbose=False,element="config",source_dir="source",target_dir="target",sets_dir="sets",convert_bool="convert",ext="extensions",convert_ext = "convert_ext",disp_size="max_size"):
    """Parses through %XML_FILE% to get the settings, returned as a list"""
    settings_list = []
    conf_root = ET.parse(XML_FILE).getroot().find(element)
    settings_list.append(conf_root.get(source_dir)) #Source
    settings_list.append(conf_root.get(target_dir)) #Target
    settings_list.append(conf_root.get(sets_dir)) #Sets (Toshop)
    settings_list.append(conf_root.get(ext)) #Extensions
    settings_list.append(bool(int(conf_root.get(convert_bool)))) #Convert bool
    settings_list.append(conf_root.get(convert_ext))#Convert extension
    settings_list[3] = tuple(settings_list[3].split(','))
    settings_list.append(tuple(int(i)for i in conf_root.get(disp_size).split(','))) #Display size
    if verbose == True:
        verbose_list = [source_dir,target_dir,sets_dir,ext,convert_bool,convert_ext,disp_size]
        for i in range(0,len(settings_list)):
            verbose_list[i]+= ": "+str(settings_list[i])
        return verbose_list
    return settings_list

os.chdir(os.path.dirname(__file__)) #Useful for relative paths
LOG_FILE = "log.txt"
SOURCE_DIR,TARGET_DIR,SETS_DIR,EXTENSIONS,CONVERT,CONV_EXT,DISPLAY_SIZE = get_dirs(XML_FILE)
def change_global(new_xml):
    global XML_FILE,SOURCE_DIR,TARGET_DIR,SETS_DIR,EXTENSIONS,CONVERT,CONV_EXT,DISPLAY_SIZE
    XML_FILE = new_xml
    SOURCE_DIR,TARGET_DIR,SETS_DIR,EXTENSIONS,CONVERT,CONV_EXT,DISPLAY_SIZE = get_dirs(new_xml)

def xml_cleanup():
    """Hacky pretty-print of xml"""
    with open(XML_FILE,'r') as file:
        content = file.read()
    if os.path.isfile(XML_FILE+".bak"):
        os.remove(XML_FILE+".bak")
    os.rename(XML_FILE,XML_FILE+".bak")
    content = re.sub("><",">\n<",content)
    content = re.sub("(?<!>)\n<","<",content)
    with open(XML_FILE,'a') as file:
        file.write(content)

def add_tags(tag_str,pic_id):
    """register %pic_id%'s %tag_str% in %XML_FILE%"""
    xml_parsed = ET.parse(XML_FILE)
    tag_root = xml_parsed.getroot()
    tag_list = list(set(tag_str.split('\n')))
    for i in tag_list:
        if i == '':
            continue
        i = i.replace(' ','_')
        if i[0].isdigit():
            i = "_"+i
        if tag_root.find(i) == None:
            tag_root.append(ET.Element(i))
            tag_root.find(i).text="" #To avoid NoneType below
        tag_root.find(i).text+='\n'+pic_id
    xml_parsed.write(XML_FILE)
    xml_cleanup()
    return True

def build_file_list(source_dir): #$path is $to_tag_dir
    """Returns as a list, all the files with a given %EXTENSIONS% within %source_dir%"""
    file_list = []
    for i in os.listdir(source_dir):
        if splitext(i)[1] != '' and (splitext(i)[1] in EXTENSIONS or splitext(i)[1] in CONV_EXT):         file_list.append(i)
    return file_list

def build_set_list():
    set_list = []
    for i in os.listdir(SETS_DIR):
        if splitext(i)[1] == '':
            set_list.append(i)
    return set_list

def move_file(pic_file,pic_id,qual_int=95):
    """Converts %EXTENSIONS% to jpg, renames file with its %pic_id% and moves it to %TARGET%"""
    pic_name,pic_ext = splitext(pic_file)
    if CONVERT == True and pic_ext in EXTENSIONS:
        image = Image.open(SOURCE_DIR+'/'+pic_file)
        image = image.convert('RGB')
        image.save(SOURCE_DIR+'/'+pic_name+'.jpg',quality=qual_int)
        os.remove(SOURCE_DIR+'/'+pic_file)
    os.rename(SOURCE_DIR+'/'+pic_name+'.jpg',TARGET_DIR+'/'+pic_id+'.jpg')
    return True

def move_folder(folder,folder_id,qual_int=95):
    """Rename and move %folder% to %TARGET%. Then, converts its files to jpg and rename them as subelements of %folder_id%"""
    os.rename(SETS_DIR+'/'+folder,TARGET_DIR+'/'+folder_id)
    for i in enumerate(os.listdir(TARGET_DIR+'/'+folder_id)):
        split = splitext(i[1])
        if CONVERT == True and split[1] in EXTENSIONS:
            image = Image.open(TARGET_DIR+'/'+folder_id+'/'+i[1])
            image = image.convert('RGB')
            image.save(TARGET_DIR+'/'+folder_id+'/'+folder_id+'_'+str(i[0]+1)+'.jpg',quality=qual_int)
            os.remove(TARGET_DIR+'/'+folder_id+'/'+i[1])
        else:
            os.rename(TARGET_DIR+'/'+folder_id+'/'+i[1],TARGET_DIR+'/'+folder_id+'/'+folder_id+'_'+str(i[0]+1)+'.jpg')
    return True


def rand_name(name_length=4,char_list="1234567890abcdefghijklmnopqrstuvwxyz"): # Don't use any of these : $%@-#()[]{}+=£µ*¤!§?,;.:²°<>^&
    """Returns a string of $name_length chars choosen at random from $char_list"""
    final_name = [random.choice(char_list) for i in range(0,name_length)]
    return ''.join(final_name)

def update_log(pic_id):
    """Writes the moved file's name with current time in the log file"""
    log = open(LOG_FILE, 'a')
    log.write('\n'+pic_id+' -> '+time.strftime("%d/%m/%y - %H:%M"))
    log.close()
    return True

def browse_tag():
    """Fetches the list of existing tags and returns it as a list, sorted with most frequent tags on top"""
    xml_parsed = ET.parse(XML_FILE)
    root = xml_parsed.getroot()
    tag_list = [[len(str(i.text)),i.tag] for i in root.iter()]
    tag_list.sort()
    tag_list.reverse()
    tag_list = [i[1] for i in tag_list.copy()]
    return tag_list

if __name__ == '__main__':
    print('you launched the function module again you dumb fuck')

"""
LOG : 19/05/20 - changed $var notation to %var% notation
    added SETS_DIR system for tagging image sets pic by pic instead of photoshopping a mosaic
    : 03/06/20 - added function to move folder and files.
    : 06/06/20 - added parameter for build_file_list
"""
