"""
CRAFT HR - Leave Distribution (DEPRECATED)
==========================================
This module is deprecated. ERPNext native Earned Leave is used instead.

The Leave Distribution Template feature has been disabled because:
1. ERPNext has built-in earned leave functionality that works correctly
2. Having two systems caused conflicts and wrong balances
3. The custom fields were not syncing with ERPNext standard fields

DO NOT RE-ENABLE this code. Use ERPNext Leave Type > Is Earned Leave instead.
"""

import frappe

def get_leaves(date_of_joining, allocation_start_date, leave_distribution_template=None):
    """
    DEPRECATED: This function is no longer used.
    ERPNext native earned leave handles monthly accrual.
    
    Keeping this function stub to prevent import errors in existing code.
    """
    frappe.log_error(
        "get_leaves() is deprecated. Use ERPNext native earned leave instead.",
        "Craft HR Deprecation Warning"
    )
    return 0


def get_earned_leave(employee=None):
    """
    DEPRECATED: This function is no longer used.
    ERPNext native earned leave handles monthly accrual.
    
    Keeping this function stub to prevent import errors in existing code.
    """
    # DO NOT UNCOMMENT OR MODIFY THIS FUNCTION
    # The craft_hr leave distribution system has been replaced by ERPNext native earned leave
    pass
