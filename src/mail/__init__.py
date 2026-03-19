from mail.list_emails import register as register_list_emails
from mail.search_emails import register as register_search_emails
from mail.read_email import register as register_read_email
from mail.send_email import register as register_send_email
from mail.draft_email import register as register_draft_email
from mail.mark_as_read import register as register_mark_as_read


def register_tools(mcp):
    register_list_emails(mcp)
    register_search_emails(mcp)
    register_read_email(mcp)
    register_send_email(mcp)
    register_draft_email(mcp)
    register_mark_as_read(mcp)
