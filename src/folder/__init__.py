from folder.list_folders import register as register_list_folders
from folder.create_folder import register as register_create_folder
from folder.move_emails import register as register_move_emails


def register_tools(mcp):
    register_list_folders(mcp)
    register_create_folder(mcp)
    register_move_emails(mcp)
