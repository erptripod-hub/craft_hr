"""
CRAFT HR - ONE-TIME LEAVE ALLOCATION FIX
=========================================
Run this ONCE in bench console to fix all 69 affected leave allocations.

Usage:
    bench --site your-site console
    exec(open('/path/to/fix_all_leave_allocations.py').read())

What this script does:
1. Finds all leave allocations using distribution templates
2. Calculates correct total leaves as of today (Apr 23, 2026)
3. Updates ERPNext standard fields (total_leaves_allocated, new_leaves_allocated)
4. Disables the craft_hr distribution checkbox (custom_is_earned_leave)
5. Clears craft_hr custom fields to avoid confusion

After running this:
- ERPNext native earned leave will take over
- craft_hr leave distribution is disabled permanently
"""

import frappe
from frappe.utils import getdate, date_diff, today, flt
from datetime import date

# Configuration
DRY_RUN = True  # Set to False to actually make changes
REFERENCE_DATE = getdate(today())  # Uses current system date

# Monthly accrual rates
ACCRUAL_RATES = {
    "UAE Annual Leave Distribution Staff": 1.833,  # 22 days / 12 months
    "Annual Leave KSA Office": 2.5,  # 30 days / 12 months
}

def calculate_months_since_jan(from_date, to_date):
    """Calculate fractional months between two dates"""
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    
    # Full months
    months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)
    
    # Add fractional part for days
    days_in_month = 30  # Approximate
    day_fraction = (to_date.day - from_date.day) / days_in_month
    
    return months + day_fraction

def fix_all_allocations():
    """Main function to fix all leave allocations"""
    
    print("=" * 70)
    print("CRAFT HR LEAVE ALLOCATION FIX")
    print("=" * 70)
    print(f"Reference Date: {REFERENCE_DATE}")
    print(f"DRY RUN: {DRY_RUN}")
    print("=" * 70)
    
    # Get all affected allocations
    allocations = frappe.db.sql("""
        SELECT 
            la.name,
            la.employee,
            e.employee_name,
            e.date_of_joining,
            e.company,
            la.leave_type,
            la.from_date,
            la.to_date,
            la.total_leaves_allocated,
            la.new_leaves_allocated,
            la.custom_opening_leaves,
            la.custom_leave_distribution_template,
            la.custom_is_earned_leave,
            COALESCE((
                SELECT SUM(total_leave_days) 
                FROM `tabLeave Application` 
                WHERE employee = la.employee 
                AND leave_type = la.leave_type 
                AND docstatus = 1 
                AND from_date >= '2026-01-01'
            ), 0) as leaves_taken_2026
        FROM `tabLeave Allocation` la
        JOIN `tabEmployee` e ON la.employee = e.name
        WHERE la.docstatus = 1 
        AND la.custom_leave_distribution_template IS NOT NULL
        AND la.custom_leave_distribution_template != ''
        AND la.from_date >= '2026-01-01'
        ORDER BY e.company, la.leave_type, e.employee_name
    """, as_dict=True)
    
    print(f"\nFound {len(allocations)} allocations to fix\n")
    
    # Group by company for reporting
    by_company = {}
    for alloc in allocations:
        company = alloc.company
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(alloc)
    
    fixed_count = 0
    error_count = 0
    
    for company, company_allocs in by_company.items():
        print(f"\n{'='*70}")
        print(f"COMPANY: {company}")
        print(f"{'='*70}")
        
        for alloc in company_allocs:
            try:
                template = alloc.custom_leave_distribution_template
                monthly_rate = ACCRUAL_RATES.get(template)
                
                if not monthly_rate:
                    print(f"  ⚠ SKIP {alloc.employee}: Unknown template '{template}'")
                    continue
                
                # Get opening balance (what they had on Jan 1, 2026)
                opening = flt(alloc.custom_opening_leaves) or 0
                
                # Calculate months from allocation start to reference date
                alloc_start = getdate(alloc.from_date)
                
                # If allocation started after Jan 1, calculate from that date
                if alloc_start > getdate("2026-01-01"):
                    months_earned = calculate_months_since_jan(alloc_start, REFERENCE_DATE)
                else:
                    months_earned = calculate_months_since_jan("2026-01-01", REFERENCE_DATE)
                
                # Cap at reasonable maximum (avoid negative)
                months_earned = max(0, months_earned)
                
                # Calculate new accrual since Jan 1 (or allocation start)
                new_accrual = round(months_earned * monthly_rate, 3)
                
                # Total should be = opening + new accrual
                correct_total = round(opening + new_accrual, 3)
                
                # Leaves taken
                leaves_taken = flt(alloc.leaves_taken_2026) or 0
                
                # Available balance
                correct_available = round(correct_total - leaves_taken, 3)
                
                # Current values
                current_total = flt(alloc.total_leaves_allocated) or 0
                
                # Difference
                diff = round(correct_total - current_total, 3)
                
                print(f"\n  {alloc.employee}: {alloc.employee_name}")
                print(f"    Template: {template} ({monthly_rate}/mo)")
                print(f"    Opening (Jan 1): {opening}")
                print(f"    Months since: {round(months_earned, 2)}")
                print(f"    New accrual: +{new_accrual}")
                print(f"    Correct total: {correct_total}")
                print(f"    Leaves taken: -{leaves_taken}")
                print(f"    Correct available: {correct_available}")
                print(f"    Current total: {current_total}")
                print(f"    Adjustment needed: {'+' if diff >= 0 else ''}{diff}")
                
                if not DRY_RUN:
                    # Update the allocation
                    frappe.db.set_value("Leave Allocation", alloc.name, {
                        "new_leaves_allocated": correct_total,
                        "total_leaves_allocated": correct_total,
                        # Disable craft_hr distribution
                        "custom_is_earned_leave": 0,
                        # Clear craft_hr fields to avoid confusion
                        "custom_available_leaves": correct_available,
                        "custom_used_leaves": leaves_taken,
                    }, update_modified=False)
                    
                    print(f"    ✅ FIXED")
                else:
                    print(f"    🔍 DRY RUN - No changes made")
                
                fixed_count += 1
                
            except Exception as e:
                print(f"  ❌ ERROR {alloc.employee}: {str(e)}")
                error_count += 1
    
    if not DRY_RUN:
        frappe.db.commit()
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total allocations processed: {fixed_count}")
    print(f"Errors: {error_count}")
    
    if DRY_RUN:
        print(f"\n⚠️  DRY RUN MODE - No changes were made!")
        print(f"    To apply changes, set DRY_RUN = False and run again")
    else:
        print(f"\n✅ All changes committed to database")
        print(f"\nNEXT STEPS:")
        print(f"1. Verify a few employees in ERPNext UI")
        print(f"2. Apply the craft_hr code patch to prevent this from happening again")
    
    return {"fixed": fixed_count, "errors": error_count}


# Run the fix
if __name__ == "__main__" or True:
    fix_all_allocations()
