#!python3
#===TODO===
#options in client UI
#change to xml dom minidomeee ?
#Add set tagging refinment
#Commands
#Autofill + showing how many pics for each suggested tag
#Better forbidden char test
#Warning prompt in new tags (if tag not in list, popup demanding confirmation for whole process/for the foreign tag)
#Ignorer des images jusqu'à reboot (bouton)
#Add rollback for last pic
#Separate set from picture tag by ----- (à revoir)
#Add watermarks to pics if artist doesn't do it
#Aliases to prevent redundancy
import os
import pyperclip #ONLY TO SUPPORT ADVANCED XML BROWSING
import sys
import traceback
import tkinter as tk
import arch_model as model
from tkinter import ttk
from PIL import Image, ImageTk
from sys import exit
from xml.etree import ElementTree as ET


"""Handles passed command line arguments"""
if len(sys.argv) == 2:
    XML_FILE = str(sys.argv[1])
    model.change_global(XML_FILE)
else:
    XML_FILE = model.XML_FILE

def get_tags(id: str) -> [str]: #moved to model
    """Returns as a list all of the xml elements in which the $id is found"""
    xml_root = ET.parse(XML_FILE).getroot()
    tag_list = []+[elem.tag for elem in xml_root.iter() if elem.text is not None and id in elem.text]
    return tag_list

def get_ids(tag_str: str) -> [str]: #moved to model
    """Returns as a list all of ids in the $tag xml element"""
    xml_root = ET.parse(XML_FILE).getroot()
    if ' ' not in tag_str: #single tag processing
        elem_search = xml_root.find(tag_str)
        if elem_search != None:
            print("found")
            id_list = elem_search.text.split('\n')
        else:
            print("nothing found")
            return []
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


def pop_up(label_text: str,mainWin: tk.Tk) -> tk.Toplevel:
    """Creates a popup window displaying $label_text and returns it"""
    popup = tk.Toplevel()
    popup_label = tk.Label(popup,text=label_text)
    popup_button = tk.Button(popup,text="Ok",command=lambda:[popup.destroy(),mainWin.deiconify()])
    popup_label.grid(row=0,column=0)
    popup_button.grid(row=1,column=0)
    return popup

class MainWin(tk.Frame):

    def __init__(self,parent: tk.Tk):
        tk.Frame.__init__(self,parent)
        self.parent = parent #To modify the root's attribute or call its methods
        self.pictures_names = model.build_file_list(model.SOURCE_DIR) #List of files to process
        self.picture_index = model.Index(max=len(self.pictures_names)-1)
        self.folders_names = model.build_set_list() #List of sets to process
        self.set_index = model.Index(max=len(self.folders_names)-1)
        self.gif_frames = [ImageTk]
        self.frame_index = model.Index(0)
        self.mode = 'single' #Single picture tagging vs sets tagging
        self.im: Image = None


        #--- GUI defining
        self.menu = tk.Menu(self)
        self.pic_display_canvas = tk.Canvas(self,background='#cccccc',offset='900,900') #Center canvas to display images to tag
        self.tagging_boxes = tk.Frame(self,background='blue',width=20)
        self.main_tag_box = tk.Text(self.tagging_boxes,width=20,height=0) #To input tags
        self.aux_tag_box = tk.Text(self.tagging_boxes,width=20,height=0) #To input image-specific tags in a set


        #--- GUI settings
        self.parent.config(menu=self.menu)
        self.parent.bind('<F1>',lambda i:pop_up('Aide',self.parent)) #Instructions (NIY)
        self.parent.bind('<Control-z>',lambda i:pop_up('Rulbeck',self.parent)) #Rollback (NIY)
        self.pic_display_canvas.bind('<Button-1>',self.clicked_arrow)
        self.main_tag_box.bind('<Escape>',lambda i:self.processing_wrapper())
        self.menu.add_radiobutton(label="Prev", command=lambda index_mod = -1:self.display_wrapper(index_mod))
        self.menu.add_radiobutton(label="Next", command=lambda index_mod = +1:self.display_wrapper(index_mod))
        self.menu.add_radiobutton(label="Tags", command=self.tag_display)
        self.menu.add_radiobutton(label="Settings", command=self.settings)
        self.menu.add_radiobutton(label="Single", command=lambda:self.switch_mode())

        #--- GUI positioning
        self.tagging_boxes.rowconfigure(0,weight=2)
        self.tagging_boxes.rowconfigure(1,weight=1)
        self.main_tag_box.grid(row=0,rowspan=2,sticky=tk.N+tk.S) #,sticky=tk.N+tk.S

        self.tagging_boxes.grid(row=0,column=0,sticky=tk.N+tk.S)
        self.pic_display_canvas.grid(row=0,column=1)
        self.display_wrapper(0)


    def gif_loop(self,delay: "milliseconds: int",file: Image) -> None:
        self.pic_display_canvas.delete('all')
        self.pic_display_canvas.create_image(0,0,anchor=tk.NW,image=self.gif_frames[self.frame_index])
        self.display_arrows()
        self.frame_index(1)
        if file.filename == self.im.filename: # Prevents conflict when switching to another gif
            tk.Label.after(self.pic_display_canvas,delay,lambda:self.display_animated(delay,file))

    def display_animated(self,delay: "milliseconds: int",file: Image) -> None:
        self.pic_display_canvas.config(width=self.im.width,height=self.im.height)
        if not self.gif_frames:
            self.gif_frames = model.get_gif_frames(self.im)
            self.frame_index.set_max(len(self.gif_frames)-1)
        if len(self.gif_frames) > 1:
            self.gif_loop(delay,file)
        else:
            self.display_static()

    def clicked_arrow(self,event: tk.Event) -> None:
        if self.mode == 'single':
            if event.x<=self.im.width/2:
                self.display_wrapper(-1)
            else:
                self.display_wrapper(1)
        elif self.mode == 'sets':
            if event.x<=self.im.width/2:
                self.display_wrapper(-1)
            else:
                self.display_wrapper(1)

    def display_static(self) -> None:
        """Updates the display for a static image"""
        self.pic_display_canvas.delete('all')
        self.im.thumbnail(model.DISPLAY_SIZE) #Downscale picture if superior to $DISPLAY_SIZE resolution
        self.pic_display_canvas.config(width=self.im.width,height=self.im.height)
        self.tk_im = ImageTk.PhotoImage(self.im)
        self.pic_display_canvas.create_image(0,0,anchor=tk.NW,image=self.tk_im)
        #TEST ////
        self.display_arrows()
        #TEST ////
        self.parent.geometry("") #This forces the main window to resize itself according to the size of its widgets

    def display_arrows(self) -> None:
        """Draws the arrows on the canvas"""
        height = self.im.height/2
        xmax = self.im.width
        self.pic_display_canvas.create_line(
        75,height-50,
        25,height,
        75,height+50,
        width=20,stipple="gray50",fill="gray",activestipple="",activefill="white")
        a= self.pic_display_canvas.create_line(
        xmax-75,height-50,
        xmax-25,height,
        xmax-75,height+50,
        width=20,stipple="gray50",fill="gray",activestipple="",activefill="white")
        pass

    def switch_mode(self) -> str:
        """Switch tagging mode"""
        if self.mode == 'single': #Single to Sets
            self.set_index.reset()
            self.picture_index.reset()
            if self.folders_names:
                self.pictures_names = model.build_file_list(model.SETS_DIR+self.folders_names[self.set_index])
                self.picture_index.set_max(len(self.pictures_names)-1)
            self.mode = 'sets'
            self.aux_tag_box.grid(row=1,sticky=tk.N+tk.S)
            self.main_tag_box.grid(row=0,sticky=tk.N+tk.S)
            self.menu.entryconfig(5, label="Sets")
            self.menu.insert_radiobutton(1,label="Next set", command=lambda index_mod = +1:self.change_set(index_mod))
            self.menu.insert_radiobutton(1,label="Prev set", command=lambda index_mod = -1:self.change_set(index_mod))
            self.display_wrapper(0)
            return "Sets"
        else: #Sets to Single
            self.picture_index.reset()
            self.aux_tag_box.grid_remove()
            self.main_tag_box.grid(row=0,rowspan=2,sticky=tk.N+tk.S)
            self.pictures_names = model.build_file_list(model.SOURCE_DIR)
            self.picture_index.set_max(len(self.pictures_names)-1)
            self.mode = 'single'
            self.menu.delete(1,2)
            self.menu.entryconfig(5, label="Single")
            self.display_wrapper(0)
            return "Single"

    def change_set(self,index_mod: int) -> None:
        """Changes the current set (if there are sets to proces)"""
        self.set_index += index_mod
        self.picture_index.reset()
        if self.folders_names:
            self.pictures_names = model.build_file_list(model.SETS_DIR+self.folders_names[self.set_index])
            self.picture_index.set_max(len(self.pictures_names)-1)
        self.display_wrapper(0)

    def display_wrapper(self,index_mod: int) -> None:
        self.picture_index += index_mod
        self.update_title()
        self.gif_frames = []
        self.frame_index.reset()

        if self.mode == 'single' and self.pictures_names:
            self.im = Image.open(model.SOURCE_DIR+self.pictures_names[self.picture_index]) #DO NOT USE A VARIABLE, UNLIKE ATTRIBUTES, THEY GET DEALT WITH BY THE GARBAGE COLLECTOR AND FUCK UP THE DISPLAY
        elif self.mode == 'sets' and self.folders_names:
            current_set = self.folders_names[self.set_index]
            current_pic = self.pictures_names[self.picture_index]
            self.im = Image.open(model.SETS_DIR+current_set+'/'+current_pic) #Same as above
        else: #If all pics are processed
            self.im = Image.open("D:/Users/Pepito/Pictures/Toshop/rt.jpg")
            print("No file to process")
            self.parent.iconify()
            popup_obj = pop_up("No file to process",self.parent)

        if self.im.format in ('GIF','WEBP'):
            self.display_animated(33,self.im)
        else:
            self.display_static()

    def update_title(self) -> None:
        if self.mode == 'single':
            pass
            self.parent.title(str(self.picture_index+1)
                             +"/"
                             +str(len(self.pictures_names))
                             +" Tagger V2.0 - "
                             +self.pictures_names[self.picture_index])
        elif self.mode == 'sets':
            self.parent.title(str(self.picture_index+1)
                             +"/"
                             +str(len(self.pictures_names))
                             +" [" + str(self.set_index+1)
                             +"/" + str(len(self.folders_names))
                             +"] Tagger V2.0 - "
                             +self.folders_names[self.set_index])

    def pic_processing(self,index: model.Index,pictures_names: [str]) -> None: #moved to model
        """ creates a random id and adds it to the xml file. Places the file in its target folder. Adds the tags to the xml file. Updates the display"""
        if pictures_names:
            pic_id = model.add_name(XML_FILE,"name")
            model.pic_processing(pictures_names[index],pic_id,self.main_tag_box.get(0.0,tk.END),"toshop",model.SOURCE_DIR)
            print("added file "+pic_id)
            self.main_tag_box.delete(0.0,tk.END)
            del pictures_names[index] #Side effect. Litteral data cancer, will have to find a workaround.
            index.mod_max(-1) #pretty dirty too ngl
        self.display_wrapper(0)

    def processing_wrapper(self) -> None:
        pass
        if self.mode == 'single':
            self.pic_processing(self.picture_index,self.pictures_names)
        elif self.mode =='sets':
            self.set_processing(self.picture_index,self.set_index,self.pictures_names,self.folders_names)

    def set_processing(self,picture_index: model.Index,set_index: model.Index,pictures_names: [str],folders_names: [str]) -> None: #moved to model
        """creates a random id and adds it to the xml file. Moves the set folder to the target folder. Adds the tags to the xml file. Updates the display"""
        if picture_index+1 != len(pictures_names) or not self.folders_names:
            self.display_wrapper(+1)
        else:
            #do the real processing
            folder_id = model.add_name(XML_FILE,"name")
            model.set_processing(folders_names[set_index],folder_id,self.main_tag_box.get(0.0,tk.END),pictures_names)
            print("added folder "+folder_id)
            self.main_tag_box.delete(0.0,tk.END)
            picture_index.reset()
            del folders_names[set_index]
            set_index.mod_max(-1)
            if folders_names:
                pictures_names.clear() #j'ai juré, gg les side effects
                pictures_names += model.build_file_list(model.SETS_DIR+folders_names[set_index]) #d'un autre côté, c'est vrai que c'est plus simple, m'enfin merde
                picture_index.set_max(len(pictures_names)-1)
            self.display_wrapper(0)

    def tag_display(self) -> None:
        """Displays tags"""
        #---UI initialization
        popup = tk.Toplevel()
        tabs = tk.ttk.Notebook(popup,width=250)
        all_tags_frame = tk.Frame(tabs)
        all_tags_frame.grid_columnconfigure(0,weight=1)
        get_tags_frame = tk.Frame(tabs)
        get_tags_frame.grid_columnconfigure(0,weight=1)
        get_ids_frame = tk.Frame(tabs)
        get_ids_frame.grid_columnconfigure(0,weight=1)

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
        get_ids_button.config(command=lambda i=0:pyperclip.copy(model.build_IF_txt_list(get_ids_label.get(0,tk.END)[2:],model.TARGET_DIR)))

        all_tags_scrollbar.config(command=all_tags_label.yview)
        get_tags_scrollbar.config(command=get_tags_label.yview)
        get_ids_scrollbar.config(command=get_ids_label.yview)

        #---UI placement

        all_tags_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        all_tags_scrollbar.grid(row=0,column=1,sticky=tk.S+tk.N)

        get_tags_entry.grid(row=0,column=0,sticky=tk.E+tk.W)
        get_tags_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        get_tags_scrollbar.grid(row=0,column=1,sticky=tk.S+tk.N,rowspan=2)

        get_ids_entry.grid(row=0,column=0,sticky=tk.E+tk.W)
        get_ids_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        get_ids_scrollbar.grid(row=0,column=1,sticky=tk.S+tk.N,rowspan=2)
        get_ids_button.grid(row=2,column=0)

        tabs.pack(fill = tk.BOTH)
        tabs.add(all_tags_frame,text="general")
        tabs.add(get_tags_frame,text="get tags")
        tabs.add(get_ids_frame,text="get ids")

        for i in model.browse_tag():
            all_tags_label.insert(tk.END,i)

    def fill_listbox(self,elem_list: [str], listbox: tk.Listbox) -> None:
        listbox.delete(0,tk.END)
        if len(elem_list) == 0:
            listbox.insert(0,"No result found")
        else :
            for i in elem_list:
                listbox.insert(tk.END,i)
            listbox.insert(0,"")
            listbox.insert(0,str(len(elem_list)))

    def settings(self) -> None:
        """Displays settings"""
        popup = tk.Toplevel()
        settings_label = tk.Text(popup)
        for i in model.get_dirs(XML_FILE,verbose=True):
            settings_label.insert(tk.INSERT,str(i)+'\n')
        settings_label.grid(row=0,column=0)
        settings_label.config(state=tk.DISABLED)

try:
    os.chdir(os.path.dirname(__file__))
    tk_root = tk.Tk()
    lul = MainWin(tk_root)
    lul.pack()
    tk_root.mainloop()
except: #for debugging
    input(traceback.print_exc()) #Prints the entire traceback
