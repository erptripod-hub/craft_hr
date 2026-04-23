"""
CRAFT HR - Leave Allocation Events (SIMPLIFIED)
================================================
Stripped-down version that removes the broken distribution logic.
ERPNext native earned leave handles monthly accrual.
"""

import frappe


def validate(doc, method):
    """
    Validate leave allocation.
    
    REMOVED: Distribution template calculations (now using ERPNext native earned leave)
    """
    # The old code that calculated leaves based on distribution template
    # has been removed. ERPNext handles this natively via Leave Type settings.
    pass


def before_submit(doc, method):
    """
    Before submit hook for leave allocation.
    
    REMOVED: get_earned_leave call (now using ERPNext native earned leave)
    """
    # The old code that called get_earned_leave has been removed.
    # ERPNext handles accrual natively via Leave Type > Is Earned Leave
    pass


@frappe.whitelist()
def close_allocation(docname):
    """
    Close a leave allocation.
    
    SIMPLIFIED: Just sets status to Closed without recalculating
    """
    doc = frappe.get_doc("Leave Allocation", docname)
    doc.db_set("custom_status", "Closed")
    doc.db_set("to_date", frappe.utils.nowdate())
    frappe.msgprint(f"Leave Allocation {docname} has been closed.")
