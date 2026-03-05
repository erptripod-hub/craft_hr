import frappe

try:
    from hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool import (
        EmployeeAttendanceTool,
    )

    class CustomEmployeeAttendanceTool(EmployeeAttendanceTool):
        """Custom Employee Attendance Tool with employment_type filter support"""

        @frappe.whitelist()
        def get_employees(self):
            filters = {
                "status": "Active",
                "company": self.company,
            }

            if self.department:
                filters["department"] = self.department
            if self.branch:
                filters["branch"] = self.branch
            if self.employment_type:
                filters["employment_type"] = self.employment_type

            employees = frappe.get_list(
                "Employee",
                filters=filters,
                fields=["name", "employee_name"],
                order_by="employee_name",
            )

            self.employees = []
            for emp in employees:
                self.append(
                    "employees",
                    {
                        "employee": emp.name,
                        "employee_name": emp.employee_name,
                    },
                )

            return self.employees

except ImportError:
    pass
