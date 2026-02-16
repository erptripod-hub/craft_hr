# Salary Increment Feature

## Overview
The Salary Increment DocType allows you to manage employee salary increments with a clear comparison between current and new salary details. When submitted, it automatically creates a new Salary Structure Assignment for the employee.

## Features
- ✅ Display current salary structure and components (read-only reference)
- ✅ Editable table for new salary components
- ✅ Automatic calculation of increment amount and percentage for each component
- ✅ Total salary comparison with overall increment percentage
- ✅ Auto-create Salary Structure Assignment on submit
- ✅ Cancel linked assignment when increment is cancelled
- ✅ Validation to prevent backdated increments
- ✅ Support for different increment reasons

## Installation
The doctype files are already in the repository. Run the following commands:

```bash
# From your bench directory
bench --site [your-site-name] migrate
bench --site [your-site-name] clear-cache
```

## Usage

### Creating a Salary Increment

1. Navigate to: **HR > Salary Increment > New**

2. Fill in the basic details:
   - **Employee**: Select employee (system will auto-fetch current salary details)
   - **Company**: Select company
   - **Company License No**: Enter company license number
   - **Effective Date**: Date when increment takes effect
   - **Reason**: Select reason for increment

3. System automatically populates:
   - Current Salary Structure
   - Current Base Salary
   - Current Components (read-only table for reference)
   - New Components (editable table with current amounts pre-filled)

4. Edit the **New Components** table:
   - Modify the "New Amount" for components you want to change
   - System automatically calculates:
     - Increment amount (difference)
     - Percentage change
     - Total new salary
     - Overall increment

5. Review the summary:
   - Total Current Salary
   - Total New Salary
   - Total Increment
   - Total Increment Percentage

6. **Save** and **Submit**

### On Submission
The system will:
- Create a new Salary Structure Assignment
- Use the same Salary Structure
- Set effective date as "From Date"
- Apply the new salary components
- Link back to the Salary Increment document

### Cancellation
When you cancel a Salary Increment:
- The linked Salary Structure Assignment is also cancelled
- Data integrity is maintained

## Fields

| Field | Description |
|-------|-------------|
| Employee | Employee receiving increment |
| Emirates ID / Passport Number | Auto-fetched from employee |
| Company | Company |
| Company License No | Company trade license number |
| Effective Date | Date when increment becomes effective |
| Reason | Reason for increment |
| Current Salary Structure | Auto-fetched current structure |
| Current Base | Auto-fetched current base salary |
| Current Components | Read-only table showing current salary breakdown |
| New Components | Editable table for new salary amounts |
| Total Current Salary | Calculated total |
| Total New Salary | Calculated total |
| Total Increment | Difference between new and current |
| Total Increment % | Percentage increase |

## Print Format
A custom print format matching the UAE government amendment format is available. It includes:
- Employee details
- Company details with license number
- Designation
- Salary breakdown (Basic, Accommodation, Transport, Other Allowance)
- Signature sections for company and employee

## Permissions
- **HR Manager**: Full access (Create, Submit, Cancel, Delete)
- **HR User**: Create and view only
- **System Manager**: Full access

## Important Notes

1. **Effective Date**: Cannot be in the past
2. **Employee Must Have Active Assignment**: Employee must have at least one submitted Salary Structure Assignment
3. **Same Salary Structure**: The new assignment uses the same salary structure, only amounts change
4. **Component-wise Changes**: You can change any component individually
5. **Print Format**: Ensure company license number is filled for government compliance

## Troubleshooting

### Issue: Current salary not loading
**Solution**: Verify employee has a submitted Salary Structure Assignment

### Issue: Cannot submit increment
**Solution**: Check that:
- All required fields are filled
- Effective date is not in the past
- New component amounts are entered

### Issue: Assignment not created
**Solution**: Check if:
- Increment is submitted (not just saved)
- User has permission to create Salary Structure Assignment
- No duplicate assignment exists for the same date

## Customization

### Adding More Reasons
Edit the `reason` field options in `salary_increment.json`:
```json
{
    "fieldname": "reason",
    "options": "\nAnnual Increment\nPromotion\nPerformance Based\nMarket Adjustment\nRetention Bonus\nOther"
}
```

### Changing Naming Series
Modify in `salary_increment.json`:
```json
{
    "fieldname": "naming_series",
    "options": "HR-SAL-INC-.YYYY.-\nSAL-INC-.####"
}
```

## Integration
This DocType integrates with:
- Employee (fetches employee details)
- Salary Structure (links to structures)
- Salary Structure Assignment (creates new assignments)
- Salary Component (displays component breakdown)
- Company (company details)

## Support
For issues or questions, please check:
1. ERPNext documentation for Salary Structure Assignment
2. The Python controller for business logic
3. Browser console for JavaScript errors

## License
MIT License - Same as Craft HR
