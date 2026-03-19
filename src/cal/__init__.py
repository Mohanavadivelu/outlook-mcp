from cal.list_events import register as register_list_events
from cal.create_event import register as register_create_event
from cal.accept_event import register as register_accept_event
from cal.decline_event import register as register_decline_event
from cal.cancel_event import register as register_cancel_event
from cal.delete_event import register as register_delete_event


def register_tools(mcp):
    register_list_events(mcp)
    register_create_event(mcp)
    register_accept_event(mcp)
    register_decline_event(mcp)
    register_cancel_event(mcp)
    register_delete_event(mcp)
