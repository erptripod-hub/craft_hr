# Craft HR - Tripod Leave Allocation Fix

## Changes Made

This version of Craft HR has been modified to work with manual/custom leave allocation systems instead of the automated distribution template system.

### Modified Files

1. **craft_hr/events/get_leaves.py**
   - Disabled `get_earned_leave()` function
   - This function was recalculating leave allocations based on distribution templates
   - Now does nothing (pass) to allow manual leave management

2. **craft_hr/hooks.py**
   - Disabled daily scheduler tasks:
     - `craft_hr.tasks.daily.reset_leave_allocation`
     - `craft_hr.tasks.daily.update_leave_allocations`
   - These were running daily and overriding manual allocations

## Why These Changes Were Needed

The original Craft HR system uses:
- `custom_leave_distribution_template` field
- `custom_opening_used_leaves` field  
- `custom_date_of_joining` field
- Automatic daily recalculation of leaves

Tripod's system uses:
- Manual opening balances set as of Dec 31
- DOJ-based monthly accrual via custom Server Script
- Direct ledger entry management
- No distribution templates

The two systems were conflicting, causing:
- Wrong leave balances displayed in Leave Application forms
- Daily overwrites of manual allocations
- Calculation errors due to missing/incorrect custom field values

## How to Use

### For Manual Leave Management (Current Tripod Setup)

1. **Opening Balances**: Import via Data Import or set manually
2. **Monthly Accrual**: Use the DOJ-based Server Script (runs daily, adds on employee's DOJ day)
3. **Leave Applications**: Work normally using standard ERPNext
4. **Craft HR Features**: Still available (distribution templates just won't auto-calculate)

### To Re-enable Craft HR Auto-calculation

If you want to go back to Craft HR's automatic system:

1. Uncomment the code in `get_leaves.py` (lines 35-68)
2. Uncomment scheduler in `hooks.py` (lines 174-177)
3. Ensure all Leave Allocations have:
   - `custom_leave_distribution_template` (set to template name)
   - `custom_opening_used_leaves` (0 or actual used)
   - `custom_date_of_joining` (employee's DOJ)
   - `custom_status` ("Ongoing")

## Deployment

After pulling these changes:

```bash
cd ~/frappe-bench
bench get-app craft_hr https://github.com/erptripod-hub/craft_hr.git
bench --site [your-site] install-app craft_hr
bench build
bench restart
```

Or if already installed:
```bash
cd ~/frappe-bench/apps/craft_hr
git pull
cd ~/frappe-bench
bench build
bench restart
```

## Support

For issues or questions:
- Original Craft HR: info@craftinteractive.ae
- Tripod customizations: Contact your system administrator

---

**Modified:** March 2026  
**Modified by:** Claude (AI Assistant) for Tripod Media FZ LLC  
**Reason:** Fix leave allocation conflicts between Craft HR auto-calculation and manual DOJ-based system
