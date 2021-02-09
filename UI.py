#!python3
#===TODO===
#options in client UI
#change to xml dom minidom ?
#Add set tagging refinment
#Commands
import os
import pyperclip #ONLY TO SUPPORT ADVANCED XML BROWSING
import sys
import traceback
import tkinter as tk
import functions as tag_mod
from tkinter import ttk
from PIL import Image, ImageTk
from sys import exit
from xml.etree import ElementTree as ET


"""Handles passed command line arguments"""
if len(sys.argv) == 2:
    XML_FILE = str(sys.argv[1])
    tag_mod.change_global(XML_FILE)
else:
    XML_FILE = tag_mod.XML_FILE

def get_tags(id):
    """Returns as a list all of the xml elements in which the $id is found"""
    xml_root = ET.parse(XML_FILE).getroot()
    tag_list = ['']+[elem.tag for elem in xml_root.iter() if elem.text is not None and id in elem.text]
    return tag_list

def get_ids(tag_str):
    """Returns as a list all of ids in the $tag xml element"""
    xml_root = ET.parse(XML_FILE).getroot()
    if ' ' not in tag_str: #single tag processing
        id_list = xml_root.find(tag_str).text.split('\n')
    else: #multiple tag processing
        id_list = []
        if ' and ' in tag_str: #Returns only the ids matching with all the tags
            temp_list = []
            tag_list = tag_str.split(' and ')
            for i in tag_list:
                if xml_root.find(i) != None:
                    temp_list += xml_root.find(i).text.split('\n')
            for i in temp_list:
                if temp_list.count(i) == len(tag_list):
                    id_list.append(i)
        else: #Return all ids matching with at least one tag
            tag_list = tag_str.split(' ')
            for i in tag_list:
                if xml_root.find(i) != None:
                    id_list += xml_root.find(i).text.split('\n')
        id_list = list(set(id_list))
    return id_list[1:] #First element is always empty because of xml formatting
        

def pop_up(label_text,mainWin):
    """Creates a popup window displaying $label_text and returns it"""
    popup = tk.Toplevel()
    popup_label = tk.Label(popup,text=label_text)
    popup_button = tk.Button(popup,text="Ok",command=lambda:[popup.destroy(),mainWin.deiconify()])
    popup_label.grid(row=0,column=0)
    popup_button.grid(row=1,column=0)
    return popup


class index():
    """Behaves like an int, with added securities to avoid out of range errors"""
    def __init__(self,max_var=0,min_var=0):
        self.min = min_var
        self.max = max_var
        self.cur = 0
    def __call__(self,value):
        self.cur += int(value)
        if self.cur < self.min:
            self.cur = self.max
        elif self.cur > self.max:
            self.cur = self.min
        return self.cur
    def __repr__(self):
        return str(self.cur)
    def __index__(self):
        return self.cur
    def __add__(self,var):
        return self.cur+var
    def __sub__(self,var):
        return self.cur-var
    def set_max(self,max_var):
        self.max = max_var
    def mod_max(self,var):
        self.max += var
    def reset(self):
        self.cur = 0
        

class MainWin(tk.Frame):
    
    def __init__(self,parent):
        tk.Frame.__init__(self,parent) #cuz our __init__ is larger than just the basic one (we define GUI)
        self.parent = parent #To modify the root's attribute or call its methods
        self.picture_list = tag_mod.build_file_list(tag_mod.SOURCE_DIR) #List of files to process
        self.file_index = index()
        self.file_index.set_max(len(self.picture_list)-1)
        self.set_list = tag_mod.build_set_list() #List of sets to process
        self.set_index = index()
        self.set_index.set_max(len(self.set_list)-1)
        self.mode = 'single' #Single picture tagging vs sets tagging
        self.i = 0
        self.anim = []
        self.prev_type = ''
        self.im = ''

        
        #--- GUI defining
        self.menu = tk.Menu(self)
        self.disp_canvas = tk.Canvas(self,background='#cccccc',offset='900,900') #Center canvas to display images to tag
        self.disp_canvas.bind('<Button-1>',self.change_picture)
        self.tag_box = tk.Text(self,height=8,width=15)        
        
        #--- GUI settings
        self.parent.config(menu=self.menu)
        self.tag_box.bind('<Escape>',lambda i:self.pic_processing(self.file_index,self.picture_list))
        self.menu.add_radiobutton(label="Prev", command=lambda index_mod = -1:self.pic_display_wrapper(index_mod))
        self.menu.add_radiobutton(label="Next", command=lambda index_mod = +1:self.pic_display_wrapper(index_mod))
        self.menu.add_radiobutton(label="Tags", command=self.tag_display)
        self.menu.add_radiobutton(label="Settings", command=self.settings)
        self.menu.add_radiobutton(label="Single", command=lambda:self.menu.entryconfig(5, label=self.switch_mode()))
        
                
        #--- GUI positioning
        self.tag_box.grid(row=1,column=0,sticky=tk.W+tk.E+tk.N+tk.S)
        self.disp_canvas.grid(row=1,column=1,columnspan=2)
        self.pic_display(self.file_index,self.picture_list)
    
    def gif_loop(self,delay,filename):
        self.disp_canvas.delete('all')
        self.disp_canvas.create_image(0,0,anchor=tk.NW,image=self.anim[self.i])
        self.display_arrows()
        if self.i<len(self.anim)-1:
            self.i += 1
        else:
            self.i = 0
        if filename == self.im.filename:
            tk.Label.after(self.disp_canvas,delay,lambda:self.display_animated(delay,filename))
    
    def display_animated(self,delay,filename):
        self.disp_canvas.config(width=self.im.width,height=self.im.height)
        if not self.anim:
            self.anim = tag_mod.get_gif_frames(tag_mod.SOURCE_DIR+self.picture_list[self.file_index])
        if len(self.anim) > 1:
            self.last_anim = 0
            self.gif_loop(delay,filename)
        else:
            self.display_static()
    
    def change_picture(self,event):
        if self.mode == 'single':
            if event.x<=self.im.width/2:
                self.pic_display_wrapper(-1)
            else:
                self.pic_display_wrapper(1)
        elif self.mode == 'sets':
            if event.x<=self.im.width/2:
                self.set_display_wrapper(-1)
            else:
                self.set_display_wrapper(1)
            
    def display_static(self):
        self.disp_canvas.delete('all')
        self.im.thumbnail(tag_mod.DISPLAY_SIZE) #Downscale picture if superior to $DISPLAY_SIZE resolution
        self.disp_canvas.config(width=self.im.width,height=self.im.height)
        self.tk_im = ImageTk.PhotoImage(self.im)
        self.disp_canvas.create_image(0,0,anchor=tk.NW,image=self.tk_im)
        #TEST ////
        self.display_arrows()
        #TEST ////
        self.parent.geometry("") #This forces the main window to resize itself according to the size of its widgets
            
    def display_arrows(self):
        height = self.im.height/2
        xmax = self.im.width
        self.disp_canvas.create_line(
        75,height-50,
        25,height,
        75,height+50,
        width=20,stipple="gray50",fill="gray",activestipple="",activefill="white")
        a= self.disp_canvas.create_line(
        xmax-75,height-50,
        xmax-25,height,
        xmax-75,height+50,
        width=20,stipple="gray50",fill="gray",activestipple="",activefill="white")
        pass
    
    def switch_mode(self):
        """Switch tagging mode"""
        if self.mode == 'single': #Single -> Sets
            self.set_index.reset()
            self.file_index.reset()
            if self.set_list:
                self.picture_list = tag_mod.build_file_list(tag_mod.SETS_DIR+self.set_list[self.set_index])
                self.file_index.set_max(len(self.picture_list)-1)
            self.mode = 'sets'
            self.tag_box.bind('<Escape>',lambda i:self.set_processing(self.file_index,self.set_index,self.picture_list,self.set_list))
            self.menu.entryconfig(1, command=lambda index_mod = -1:self.change_set(index_mod))
            self.menu.entryconfig(2, command=lambda index_mod = +1:self.change_set(index_mod))
            self.set_display_wrapper(0)
            return "Sets"
        else: #Sets -> Single
            self.file_index.reset()
            self.picture_list = tag_mod.build_file_list(tag_mod.SOURCE_DIR)
            self.file_index.set_max(len(self.picture_list)-1)
            self.mode = 'single'
            self.tag_box.bind('<Escape>',lambda i:self.pic_processing(self.file_index,self.picture_list))
            self.menu.entryconfig(1, command=lambda index_mod = -1:self.pic_display_wrapper(index_mod))
            self.menu.entryconfig(2, command=lambda index_mod = +1:self.pic_display_wrapper(index_mod))
            self.pic_display_wrapper(0)
            return "Single"
    
    def change_set(self,index_mod):
        self.set_index(index_mod)
        self.file_index.reset()
        if self.set_list:
            self.picture_list = tag_mod.build_file_list(tag_mod.SETS_DIR+self.set_list[self.set_index])
            self.file_index.set_max(len(self.picture_list)-1)
        self.set_display_wrapper(0)
    
    def notif_empty_queue(self,placeholder):
        self.im = Image.open(placeholder)
        print("No file to process")
        self.parent.iconify()
        popup_obj = pop_up("No file to process",self.parent)
        
    def pic_display_wrapper(self,index_mod):
        self.file_index(index_mod)
        self.pic_display(self.file_index,self.picture_list)
        
    def set_display_wrapper(self,index_mod):
        self.file_index(index_mod)
        self.set_display(self.file_index,self.set_index,self.set_list,self.picture_list)
        
    def pic_display(self,index,picture_list):
        """Sets the pic to display inside of the canvas widget"""
        if not picture_list: #If all pics are processed
            self.notif_empty_queue("D:/Users/Pepito/Pictures/Toshop/rt.jpg")
        else:
            if self.im:
                self.prev_type = self.im.format
            self.anim = []
            self.i = 0
            list_len = str(len(picture_list))
            self.parent.title(str(index+1)+"/"+list_len+" Tagger V2.0 - "+picture_list[index])
            self.im = Image.open(tag_mod.SOURCE_DIR+picture_list[index]) #DO NOT USE A VARIABLE, UNLIKE ATTRIBUTES, THEY GET DEALT WITH BY THE GARBAGE COLLECTOR AND FUCK UP THE DISPLAY
        if self.im.format in ('GIF','WEBP'):
            self.display_animated(33,self.im.filename)
        else:
            self.display_static()
            
    def set_display(self,file_index,set_index,set_list,picture_list):
        """Sets the set to display inside the canvas widget"""
        if not set_list : #If all sets are processed
            self.notif_empty_queue("D:/Users/Pepito/Pictures/Toshop/immigrey.jpg")
        else:
            current_set_name = set_list[set_index]
            cur_set_index = str(set_index+1)
            cur_set_size = str(len(picture_list))
            cur_picture_index = str(file_index+1)
            self.parent.title(cur_picture_index+"/"+cur_set_size+" - "+current_set_name)
            self.im = Image.open(tag_mod.SETS_DIR+current_set_name+'/'+picture_list[file_index])
        self.display_static()
         
    def pic_processing(self,index,picture_list):
        """ creates a random id and adds it to the xml file. Places the file in its target folder. Adds the tags to the xml file. Updates the display"""
        if picture_list:
            pic_id = tag_mod.add_name(XML_FILE,"name")
            tag_mod.pic_processing(picture_list[index],pic_id,self.tag_box.get(0.0,tk.END),"toshop",tag_mod.SOURCE_DIR)
            print("added file "+pic_id)
            self.tag_box.delete(0.0,tk.END)
            del picture_list[index] #Side effect. Litteral data cancer, will have to find a workaround.
            index.mod_max(-1) #pretty dirty too ngl
        self.pic_display_wrapper(0)
        
    def set_processing(self,file_index,set_index,picture_list,set_list):
        """creates a random id and adds it to the xml file. Moves the set folder to the target folder. Adds the tags to the xml file. Updates the display"""
        if file_index+1 != len(picture_list) or not self.set_list:
            self.set_display_wrapper(+1)
        else:
            #do the real processing
            folder_id = tag_mod.add_name(XML_FILE,"name")
            tag_mod.set_processing(set_list[set_index],folder_id,self.tag_box.get(0.0,tk.END),picture_list)
            print("added folder "+folder_id)
            self.tag_box.delete(0.0,tk.END)
            file_index.reset()
            del set_list[set_index]
            set_index.mod_max(-1)
            if set_list:
                picture_list.clear() #j'ai juré, gg les side effects
                picture_list += tag_mod.build_file_list(tag_mod.SETS_DIR+set_list[set_index]) #d'un autre côté, c'est vrai que c'est plus simple, m'enfin merde
                file_index.set_max(len(picture_list)-1)
            self.set_display_wrapper(0)
            
    def tag_display(self):
        """Displays tags"""
        #---UI initialization
        popup = tk.Toplevel()
        tabs = tk.ttk.Notebook(popup)
        all_tags_frame = tk.Frame(tabs)
        get_tags_frame = tk.Frame(tabs)
        get_ids_frame = tk.Frame(tabs)
        
        all_tags_scrollbar = tk.Scrollbar(all_tags_frame)
        get_tags_scrollbar = tk.Scrollbar(get_tags_frame)
        get_ids_scrollbar = tk.Scrollbar(get_ids_frame)
        
        all_tags_label = tk.Listbox(all_tags_frame,selectmode=tk.EXTENDED,yscrollcommand=all_tags_scrollbar.set,height=20)
        get_tags_label = tk.Listbox(get_tags_frame,selectmode=tk.EXTENDED,yscrollcommand=get_tags_scrollbar.set,height=20)
        get_ids_label = tk.Listbox(get_ids_frame,selectmode=tk.EXTENDED,yscrollcommand=get_ids_scrollbar.set,height=20)
        
        get_tags_entry = tk.Entry(get_tags_frame)
        get_ids_entry = tk.Entry(get_ids_frame)
        get_ids_button = tk.Button(get_ids_frame,text="copy")
        
        get_tags_entry.bind('<Return>',lambda i:self.fill_listbox(get_tags(get_tags_entry.get().lower()),get_tags_label))
        get_ids_entry.bind('<Return>',lambda i:self.fill_listbox(get_ids(get_ids_entry.get().lower()),get_ids_label))
        get_ids_button.config(command=lambda i=0:pyperclip.copy(tag_mod.build_IF_txt_list(get_ids_label.get(0,tk.END)[2:],tag_mod.TARGET_DIR)))
        
        all_tags_scrollbar.config(command=all_tags_label.yview)
        get_tags_scrollbar.config(command=get_tags_label.yview)
        get_ids_scrollbar.config(command=get_ids_label.yview)
        
        #---UI placement
        
        all_tags_label.grid(row=0,column=0)
        all_tags_scrollbar.grid(row=0,column=1,sticky=tk.S+tk.N)
        
        get_tags_entry.grid(row=0,column=0)
        get_tags_label.grid(row=1,column=0)
        get_tags_scrollbar.grid(row=0,column=1,sticky=tk.S+tk.N,rowspan=2)
        
        get_ids_entry.grid(row=0,column=0)
        get_ids_label.grid(row=1,column=0)
        get_ids_scrollbar.grid(row=0,column=1,sticky=tk.S+tk.N,rowspan=2)
        get_ids_button.grid(row=2,column=0)
        
        tabs.pack()
        tabs.add(all_tags_frame,text="general")
        tabs.add(get_tags_frame,text="get tags")
        tabs.add(get_ids_frame,text="get ids")
        
        for i in tag_mod.browse_tag():
            all_tags_label.insert(tk.END,i)

    def fill_listbox(self,elem_list,listbox,):
        listbox.delete(0,tk.END)
        for i in elem_list:
            listbox.insert(tk.END,i)
        listbox.insert(0,'')
        listbox.insert(0,str(len(elem_list)))
    
    def settings(self):
        """Displays settings"""
        popup = tk.Toplevel()
        settings_label = tk.Text(popup)
        for i in tag_mod.get_dirs(XML_FILE,verbose=True):
            settings_label.insert(tk.INSERT,str(i)+'\n')
        settings_label.grid(row=0,column=0)
        settings_label.config(state=tk.DISABLED)

try:
    os.chdir(os.path.dirname(__file__))
    tk_root = tk.Tk()
    lul = MainWin(tk_root)
    lul.grid(row=0,column=0)
    tk_root.mainloop()
except: #for debugging
    input(traceback.print_exc()) #Prints the entire traceback