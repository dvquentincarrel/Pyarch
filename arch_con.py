import arch_model as model

def get_tags_of_id(id : str) -> [str]:
    return model.fetch_tags(id)

def filter_ids_by_tag(tag : str) -> [str]:
    return model.fetch_ids(tag)

def get_gif_frames(file: "Image") -> list:
    return model.get_gif_frames(file)

def build_IF_txt_list(name_list: [str],target_dir: str,mode="str") -> [str]:
    #MOST LIKELY TO RETURN NOTHING AND THE COPY/PASTE TO BE MOVED TO THE MODEL
    return build_IF_txt_list(name_list, target_dir, mode="str")

def process_set(picture_index: "Index", set_index: "Index",
        pictures_names: [str], folder_names: [str]) -> None:
    model.set_processing(picture_index, set_index, pictures_names, folder_names)

def process_pic(index: "Index",pictures_names: [str]) -> None:
    model.pic_processing(index, pictures_names)

def add_name(XML_FILE: str,reference_tag: str) -> str:
    return model.add_name(XML_FILE, reference_tag)

def get_settings(XML_FILE: str, verbose=False, element="config", source_dir="source",
        target_dir="target", sets_dir="sets", convert_bool="convert",
        ext="extensions", convert_ext = "convert_ext",disp_size="max_size") -> [str]:
    return model.get_dirs(XML_FILE)

def undo_last_transfer() -> None:
    pass
