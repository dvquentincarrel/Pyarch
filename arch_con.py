import arch_model as model

def get_tags_of_id(id : str) -> [str]:
    return model.fetch_tags(id)

def filter_ids_by_tag(tag : str) -> [str]:
    return model.fetch_ids(tag)

def undo_last_transfer() -> None:
    pass
