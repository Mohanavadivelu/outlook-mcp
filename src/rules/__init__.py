from rules.list_rules import register as register_list_rules
from rules.create_rule import register as register_create_rule
from rules.edit_rule_sequence import register as register_edit_rule_sequence


def register_tools(mcp):
    register_list_rules(mcp)
    register_create_rule(mcp)
    register_edit_rule_sequence(mcp)
