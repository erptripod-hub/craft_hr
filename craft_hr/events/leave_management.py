"""
Leave Management Automation for New Employees
Auto-allocates Leave Policy and Annual Leave based on:
- Company (Tripod Global = KSA, Tripod Media = UAE)
- Employment Type (Office Staff, Labour)
- Gender (Male, Female)
"""

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, add_years, flt, cint
from datetime import datetime

# Company mappings
COMPANY_REGION = {
    "TRIPOD GLOBAL SHOPFIT MANUFACTURING COMPANY": "KSA",
    "Tripod Media FZ LLC": "UAE"
}

# Leave Policy mappings (updated yearly)
def get_leave_policy(gender, year=None):
    """Get leave policy name based on gender and year"""
    if not year:
        year = getdate(nowdate()).year
    
    if gender == "Male":
        return f"Male Staff Policy - {year}"
    else:
        return f"Female Staff Policy - {year}"

# Annual Leave Type mappings
def get_annual_leave_type(company, employment_type):
    """Get annual leave type based on company and employment type"""
    region = COMPANY_REGION.get(company)
    
    if region == "KSA":
        # KSA: Same for all (30 days / 2.5 per month)
        return "Annual Leave KSA Office"
    elif region == "UAE":
        if employment_type == "Office Staff":
            # UAE Office Staff: 22 days / 1.833 per month
            return "Annual Leave Office UAE"
        else:
            # UAE Labour/Workers: 30 days / 2.5 per month
            return "Annual Leave UAE Workers"
    
    return None

# Leave Policy Details (days per leave type)
MALE_POLICY_LEAVES = [
    {"leave_type": "Sick Leave - Full Pay", "days": 15},
    {"leave_type": "Sick Leave - Half Pay", "days": 30},
    {"leave_type": "Paternity Leave", "days": 5},
    {"leave_type": "Compassionate leave", "days": 5},
]

FEMALE_POLICY_LEAVES = [
    {"leave_type": "Sick Leave - Full Pay", "days": 15},
    {"leave_type": "Sick Leave - Half Pay", "days": 30},
    {"leave_type": "Maternity - Full Pay", "days": 45},
    {"leave_type": "Maternity - Half Pay", "days": 15},
    {"leave_type": "Compassionate leave", "days": 5},
]


@frappe.whitelist()
def allocate_employee_leaves(employee):
    """
    Main function to allocate leaves for an employee.
    Called from Employee form button.
    """
    try:
        emp = frappe.get_doc("Employee", employee)
        
        # Validate employee
        if emp.status != "Active":
            return {"success": False, "message": _("Employee is not active")}
        
        if not emp.company:
            return {"success": False, "message": _("Company not set")}
        
        if not emp.gender:
            return {"success": False, "message": _("Gender not set")}
        
        if not emp.date_of_joining:
            return {"success": False, "message": _("Date of Joining not set")}
        
        if not emp.employment_type:
            return {"success": False, "message": _("Employment Type not set")}
        
        year = getdate(nowdate()).year
        results = []
        
        # 1. Allocate Leave Policy (Sick, Paternity/Maternity, Compassionate)
        policy_result = allocate_leave_policy(emp, year)
        results.append(policy_result)
        
        # 2. Allocate Annual Leave
        annual_result = allocate_annual_leave(emp)
        results.append(annual_result)
        
        # Check if anything was allocated
        allocated_count = sum(1 for r in results if r.get("allocated"))
        
        if allocated_count > 0:
            frappe.db.commit()
            return {
                "success": True,
                "message": _("Annual leave and leave policy allocation done")
            }
        else:
            return {
                "success": False,
                "message": _("Leaves already allocated for this employee")
            }
            
    except Exception as e:
        frappe.log_error(f"Leave Allocation Error for {employee}: {str(e)}")
        return {"success": False, "message": str(e)}


def allocate_leave_policy(emp, year):
    """Allocate leave policy (Sick, Paternity/Maternity, Compassionate)"""
    
    policy_name = get_leave_policy(emp.gender, year)
    
    # Check if Leave Policy exists
    if not frappe.db.exists("Leave Policy", policy_name):
        return {"allocated": False, "message": f"Leave Policy {policy_name} not found"}
    
    # Check if Leave Policy Assignment already exists
    existing = frappe.db.exists("Leave Policy Assignment", {
        "employee": emp.name,
        "leave_policy": policy_name,
        "docstatus": 1
    })
    
    if existing:
        return {"allocated": False, "message": "Leave Policy already assigned"}
    
    # Get leave types based on gender
    leave_types = MALE_POLICY_LEAVES if emp.gender == "Male" else FEMALE_POLICY_LEAVES
    
    allocated_any = False
    
    for lt in leave_types:
        leave_type = lt["leave_type"]
        days = lt["days"]
        
        # Check if allocation already exists
        existing_alloc = frappe.db.exists("Leave Allocation", {
            "employee": emp.name,
            "leave_type": leave_type,
            "from_date": [">=", f"{year}-01-01"],
            "docstatus": 1
        })
        
        if existing_alloc:
            continue
        
        # Create Leave Allocation
        alloc = frappe.get_doc({
            "doctype": "Leave Allocation",
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "leave_type": leave_type,
            "from_date": f"{year}-01-01",
            "to_date": f"{year}-12-31",
            "new_leaves_allocated": days,
            "total_leaves_allocated": days,
            "carry_forward": 0,
            "leave_policy": policy_name
        })
        alloc.insert(ignore_permissions=True)
        alloc.submit()
        
        allocated_any = True
    
    # Create Leave Policy Assignment
    if not existing:
        lpa = frappe.get_doc({
            "doctype": "Leave Policy Assignment",
            "employee": emp.name,
            "leave_policy": policy_name,
            "effective_from": f"{year}-01-01",
            "effective_to": f"{year}-12-31",
        })
        lpa.insert(ignore_permissions=True)
        lpa.submit()
        allocated_any = True
    
    return {"allocated": allocated_any, "message": "Leave Policy allocated"}


def allocate_annual_leave(emp):
    """Allocate Annual Leave based on company and employment type"""
    
    leave_type = get_annual_leave_type(emp.company, emp.employment_type)
    
    if not leave_type:
        return {"allocated": False, "message": "Could not determine Annual Leave type"}
    
    # Check if Annual Leave allocation already exists
    existing = frappe.db.exists("Leave Allocation", {
        "employee": emp.name,
        "leave_type": leave_type,
        "docstatus": 1
    })
    
    if existing:
        return {"allocated": False, "message": "Annual Leave already allocated"}
    
    # Create Annual Leave Allocation
    # From joining date to 2099-12-31
    # ERPNext earned leave will handle monthly accrual
    alloc = frappe.get_doc({
        "doctype": "Leave Allocation",
        "employee": emp.name,
        "employee_name": emp.employee_name,
        "leave_type": leave_type,
        "from_date": emp.date_of_joining,
        "to_date": "2099-12-31",
        "new_leaves_allocated": 0,  # ERPNext earned leave adds monthly
        "total_leaves_allocated": 0,
        "carry_forward": 0
    })
    alloc.insert(ignore_permissions=True)
    alloc.submit()
    
    return {"allocated": True, "message": "Annual Leave allocated"}


@frappe.whitelist()
def get_allocation_status(employee):
    """Get leave allocation status for an employee"""
    
    emp = frappe.get_doc("Employee", employee)
    year = getdate(nowdate()).year
    
    # Get expected leave types based on gender
    leave_types = MALE_POLICY_LEAVES if emp.gender == "Male" else FEMALE_POLICY_LEAVES
    
    # Add annual leave
    annual_leave_type = get_annual_leave_type(emp.company, emp.employment_type)
    
    result = []
    
    # Check policy leaves
    for lt in leave_types:
        leave_type = lt["leave_type"]
        alloc = frappe.db.get_value("Leave Allocation", {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": [">=", f"{year}-01-01"],
            "docstatus": 1
        }, ["total_leaves_allocated"], as_dict=True)
        
        result.append({
            "leave_type": leave_type,
            "allocated": bool(alloc),
            "days": alloc.total_leaves_allocated if alloc else 0
        })
    
    # Check annual leave
    if annual_leave_type:
        alloc = frappe.db.get_value("Leave Allocation", {
            "employee": employee,
            "leave_type": annual_leave_type,
            "docstatus": 1
        }, ["total_leaves_allocated"], as_dict=True)
        
        result.append({
            "leave_type": annual_leave_type,
            "allocated": bool(alloc),
            "days": alloc.total_leaves_allocated if alloc else 0
        })
    
    return result
