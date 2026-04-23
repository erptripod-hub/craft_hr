# CRAFT HR - LEAVE ALLOCATION FIX
## Complete Solution for UAE & KSA Leave Balance Issues

---

## PROBLEM SUMMARY

The craft_hr app had a "Leave Distribution Template" feature that:
1. Was DISABLED in the code (function was just `pass`)
2. Conflicted with ERPNext native earned leave
3. Caused wrong balances: Two systems showing different numbers
4. Custom fields frozen and not updating

**Result:** 69 employees with incorrect leave balances

---

## SOLUTION OVERVIEW

| Step | What | Risk |
|------|------|------|
| 1 | Run fix script to correct all 69 allocations | Low - DRY RUN first |
| 2 | Replace craft_hr leave code files | Low - Only removes broken code |
| 3 | ERPNext native earned leave takes over | None - Already working |

---

## STEP 1: FIX ALL LEAVE ALLOCATIONS

### 1.1 Upload the fix script to your server

```bash
# Copy fix_all_leave_allocations.py to your server
scp fix_all_leave_allocations.py user@yourserver:/home/frappe/frappe-bench/
```

### 1.2 Run in DRY RUN mode first (NO CHANGES)

```bash
cd /home/frappe/frappe-bench
bench --site your-site.com console
```

Then in the console:
```python
exec(open('fix_all_leave_allocations.py').read())
```

**Review the output** - it will show:
- Each employee
- Current balance vs correct balance
- Adjustment needed

### 1.3 Run for REAL (MAKE CHANGES)

Edit the script and change line 21:
```python
DRY_RUN = False  # Changed from True
```

Run again:
```bash
bench --site your-site.com console
exec(open('fix_all_leave_allocations.py').read())
```

### 1.4 Verify in ERPNext UI

Check a few employees:
1. TM-EMP-0042 (UAE Staff) - Should show ~17-18 days available
2. TGK-EMP-0200 (KSA Staff) - Should show ~11-12 days available

---

## STEP 2: UPDATE CRAFT_HR CODE (PERMANENT FIX)

This prevents the broken code from coming back after `bench update`.

### 2.1 Replace these files in your craft_hr app:

```bash
cd /home/frappe/frappe-bench/apps/craft_hr/craft_hr

# Backup originals first
cp hooks.py hooks.py.bak
cp events/get_leaves.py events/get_leaves.py.bak
cp events/leave_allocation.py events/leave_allocation.py.bak

# Copy new files
cp /path/to/patches/hooks.py ./hooks.py
cp /path/to/patches/get_leaves.py ./events/get_leaves.py
cp /path/to/patches/leave_allocation.py ./events/leave_allocation.py
```

### 2.2 Clear cache and restart

```bash
cd /home/frappe/frappe-bench
bench --site your-site.com clear-cache
bench restart
```

### 2.3 Commit to your git repo (IMPORTANT!)

```bash
cd /home/frappe/frappe-bench/apps/craft_hr
git add -A
git commit -m "Remove broken leave distribution - use ERPNext native earned leave"
git push origin main
```

**This ensures the fix stays after `bench update`**

---

## STEP 3: VERIFY ERPNEXT LEAVE TYPES

Make sure your Leave Types have earned leave configured correctly:

1. Go to **HR > Leave Type**
2. For each leave type (Annual Leave Office UAE, Annual Leave KSA Office):
   - ✅ Is Earned Leave = Yes
   - ✅ Earned Leave Frequency = Monthly
   - ✅ Rounding = 0.5 (or as needed)
   - ✅ Based On DOJ = Yes (if accrual starts from joining)

---

## WHAT WAS REMOVED

| Component | Action | Reason |
|-----------|--------|--------|
| `get_earned_leave()` | Made into stub | Was disabled anyway |
| Leave Allocation hooks | Removed from hooks.py | Conflicting with ERPNext |
| Daily scheduler tasks | Already commented, kept that way | Not needed |
| Distribution template checkbox | Disabled via fix script | ERPNext handles accrual |

## WHAT WAS KEPT

| Component | Reason |
|-----------|--------|
| Leave Distribution Template doctype | Data preservation (no harm) |
| Custom fields on Leave Allocation | Historical data |
| All other craft_hr features | Not related to leave distribution |

---

## TROUBLESHOOTING

### "Leave balance still wrong after fix"

1. Check if ERPNext earned leave is configured on Leave Type
2. Run the fix script again with updated date
3. Manually adjust the allocation if needed

### "Error running fix script"

1. Check you're in the correct site: `bench use your-site.com`
2. Check the script path is correct
3. Look at the error message - usually missing field or permission

### "Changes reverted after bench update"

You didn't commit to git. Run:
```bash
cd apps/craft_hr
git add -A
git commit -m "Leave distribution fix"
git push origin main
```

---

## SUPPORT

If you need help, provide:
1. Screenshot of the error
2. Output of the fix script (DRY RUN mode)
3. Employee ID that's not working correctly

---

## FILES INCLUDED

```
fix_all_leave_allocations.py  # Run once to fix all 69 allocations
craft_hr_patches/
  ├── hooks.py                 # Replace in craft_hr/craft_hr/
  ├── get_leaves.py           # Replace in craft_hr/craft_hr/events/
  └── leave_allocation.py     # Replace in craft_hr/craft_hr/events/
```
