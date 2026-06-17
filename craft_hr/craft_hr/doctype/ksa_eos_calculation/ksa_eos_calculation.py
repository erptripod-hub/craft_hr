# Copyright (c) 2026, Craft HR
# For license information, please see license.txt
#
# KSA End of Service Benefit Calculation
# As per Saudi Labor Law (Royal Decree No. M/51)
#
# Key differences from UAE:
# - Gratuity based on FULL salary (not basic only)
# - First 5 years: 15 days per year (half month)
# - After 5 years: 30 days per year (full month)
# - Resignation percentages differ by service length

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, cint, getdate
from calendar import monthrange


class KSAEOSCalculation(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_service_period()
        self.calculate_daily_wage()
        self.calculate_gratuity()
        self.calculate_leave_salary()
        self.calculate_overtime()
        self.calculate_pending_salary()
        self.calculate_recovery()
        self.calculate_summary()
        self.set_default_status()

    def before_submit(self):
        """Block submit unless status is Cleared."""
        if self.status != "Cleared":
            frappe.throw(
                _("Cannot submit. Please click <b>Mark as Cleared</b> first to confirm all calculations are reviewed and final.")
            )

    def on_submit(self):
        """When submitted, mark as Completed."""
        self.db_set("status", "Completed")

    def on_cancel(self):
        """When cancelled, mark as Cancelled."""
        self.db_set("status", "Cancelled")

    # ------------------------------------------------------------------
    # Default status
    # ------------------------------------------------------------------
    def set_default_status(self):
        """New records start as In Process."""
        if self.is_new() and not self.status:
            self.status = "In Process"

    # ------------------------------------------------------------------
    # Validations
    # ------------------------------------------------------------------
    def validate_dates(self):
        if self.date_of_joining and self.date_of_settlement:
            if getdate(self.date_of_settlement) < getdate(self.date_of_joining):
                frappe.throw(_("Date of Settlement cannot be earlier than Date of Joining"))

    # ------------------------------------------------------------------
    # Service period (years and days)
    # ------------------------------------------------------------------
    def calculate_service_period(self):
        if self.date_of_joining and self.date_of_settlement:
            days = date_diff(self.date_of_settlement, self.date_of_joining)
            self.total_service_days = days
            self.employment_years = flt(days / 365.25, 4)
            # Days eligible = total days minus unpaid leaves
            unpaid = cint(self.unpaid_leaves_taken) if self.unpaid_leaves_taken else 0
            self.days_eligible_for_gratuity = days - unpaid
        else:
            self.total_service_days = 0
            self.employment_years = 0
            self.days_eligible_for_gratuity = 0

    # ------------------------------------------------------------------
    # Daily wage calculation
    # ------------------------------------------------------------------
    def calculate_daily_wage(self):
        if self.gross_salary:
            self.daily_wage = flt(self.gross_salary / 30, 2)
        else:
            self.daily_wage = 0

    # ------------------------------------------------------------------
    # Gratuity (Saudi Labor Law)
    # ------------------------------------------------------------------
    def calculate_gratuity(self):
        """
        Saudi Labor Law Gratuity Rules:
        - Based on FULL salary (not basic)
        - First 5 years: 15 days per year (half month)
        - After 5 years: 30 days per year (full month)
        
        Resignation Percentages:
        - < 2 years: 0%
        - 2-5 years: 33.33%
        - 5-10 years: 66.67%
        - 10+ years: 100%
        
        Termination/End of Contract: 100%
        Article 80 (Gross Misconduct): 0%
        """
        if self.override_gratuity or self.calculation_mode == "Manual":
            return

        days = cint(self.days_eligible_for_gratuity)
        years = flt(self.employment_years)
        daily = flt(self.daily_wage)

        # Calculate gratuity days
        if days < 365:
            # Less than 1 year - still calculate pro-rata for KSA
            # (Unlike UAE which requires minimum 1 year)
            days_first_five = (days / 365.25) * 15
            days_after_five = 0
        elif years <= 5:
            # First 5 years: 15 days per year
            days_first_five = years * 15
            days_after_five = 0
        else:
            # First 5 years at 15 days + remaining at 30 days
            days_first_five = 5 * 15  # 75 days for first 5 years
            remaining_years = years - 5
            days_after_five = remaining_years * 30

        total_gratuity_days = days_first_five + days_after_five
        
        self.gratuity_days_first_five_years = flt(days_first_five, 2)
        self.gratuity_days_after_five_years = flt(days_after_five, 2)
        self.total_gratuity_days = flt(total_gratuity_days, 2)

        # Calculate gratuity amount before percentage
        gratuity_before = daily * total_gratuity_days
        self.gratuity_before_percentage = flt(gratuity_before, 2)

        # Determine percentage based on separation type and years
        percentage = self.get_gratuity_percentage(years)
        self.gratuity_percentage = percentage

        # Final gratuity
        self.gratuity_payable = flt(gratuity_before * (percentage / 100), 2)

    def get_gratuity_percentage(self, years):
        """
        Returns gratuity percentage based on separation type and years of service.
        """
        separation = self.separation_type or ""
        
        # Article 80 - Gross Misconduct = 0%
        if separation == "Termination by Employer" and self.termination_reason == "Article 80 (Gross Misconduct)":
            return 0
        
        # Termination, End of Contract, Mutual Consent, Death, Retirement = 100%
        if separation in ("Termination by Employer", "End of Contract", "Mutual Consent", "Death", "Retirement"):
            return 100
        
        # Resignation - percentage based on years
        if separation == "Resignation":
            if years < 2:
                return 0
            elif years < 5:
                return 33.33
            elif years < 10:
                return 66.67
            else:
                return 100
        
        # Default to 100% if separation type not set
        return 100

    # ------------------------------------------------------------------
    # Leave Salary
    # ------------------------------------------------------------------
    def calculate_leave_salary(self):
        if self.leave_calculation_basis == "Basic Salary Only":
            # Would need basic salary field, but KSA typically uses full salary
            daily = flt(self.daily_wage)
        else:
            daily = flt(self.daily_wage)

        self.leave_daily_rate = flt(daily, 2)

        # Auto calculate balance
        if self.leaves_accrued and self.leaves_utilized and not self.leaves_balance:
            self.leaves_balance = flt(self.leaves_accrued) - flt(self.leaves_utilized)

        if self.override_leave or self.calculation_mode == "Manual":
            return

        balance = flt(self.leaves_balance)
        self.leave_salary_payable = flt(daily * balance, 2)

    # ------------------------------------------------------------------
    # Overtime
    # ------------------------------------------------------------------
    def calculate_overtime(self):
        if self.override_overtime or self.calculation_mode == "Manual":
            return

        hours = flt(self.pending_overtime_hours)
        rate = flt(self.overtime_rate_per_hour)
        self.overtime_payable = flt(hours * rate, 2)

    # ------------------------------------------------------------------
    # Pending Salary
    # ------------------------------------------------------------------
    def calculate_pending_salary(self):
        if self.calculation_mode == "Manual":
            return

        gross = flt(self.gross_salary)
        days = cint(self.days_worked_pending)

        # Calculate current month payment
        days_in_month = 30
        if self.date_of_settlement:
            settlement_date = getdate(self.date_of_settlement)
            days_in_month = monthrange(settlement_date.year, settlement_date.month)[1]

        if gross and days:
            self.current_month_payment = flt((gross / days_in_month) * days, 2)
        else:
            self.current_month_payment = 0

        if self.override_salary_payable:
            return

        self.salary_payable = flt(
            flt(self.current_month_payment)
            + flt(self.pending_salary_last_month)
            + flt(self.air_ticket_allowance)
            + flt(self.other_dues),
            2,
        )

    # ------------------------------------------------------------------
    # Recovery / Deductions
    # ------------------------------------------------------------------
    def calculate_recovery(self):
        self.total_recovery = flt(
            flt(self.visa_iqama_expense)
            + flt(self.loan_advance_recovery)
            + flt(self.notice_period_shortfall)
            + flt(self.other_recovery),
            2,
        )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    def calculate_summary(self):
        self.total_gratuity = flt(self.gratuity_payable)
        self.total_leave_salary = flt(self.leave_salary_payable)
        self.total_overtime = flt(self.overtime_payable)
        self.total_salary_payable = flt(self.salary_payable)

        self.gross_total = flt(
            self.total_gratuity
            + self.total_leave_salary
            + self.total_overtime
            + self.total_salary_payable,
            2,
        )
        self.total_deductions = flt(self.total_recovery)
        self.net_payable = flt(self.gross_total - self.total_deductions, 2)


# ----------------------------------------------------------------------
# Whitelisted methods callable from client script
# ----------------------------------------------------------------------
@frappe.whitelist()
def mark_as_cleared(docname):
    """Mark the EOS record as Cleared. Called from the form button."""
    doc = frappe.get_doc("KSA EOS Calculation", docname)

    if doc.docstatus == 1:
        frappe.throw(_("Document is already submitted."))

    if doc.status == "Cleared":
        frappe.throw(_("Document is already marked as Cleared."))

    if doc.status not in ("In Process", None, ""):
        frappe.throw(_("Document status must be 'In Process' to mark as Cleared."))

    if not doc.net_payable or doc.net_payable <= 0:
        frappe.throw(_("Cannot mark as Cleared. Net Payable amount is zero or invalid."))

    doc.db_set("status", "Cleared")
    doc.db_set("cleared_by", frappe.session.user)
    doc.db_set("cleared_on", frappe.utils.now())

    frappe.msgprint(
        _("Marked as Cleared. You can now Submit the document."),
        alert=True,
        indicator="green"
    )
    return doc


@frappe.whitelist()
def get_employee_details(employee):
    """Fetch employee details + latest salary structure assignment."""
    if not employee:
        return {}

    if not frappe.db.exists("Employee", employee):
        frappe.throw(_("Employee {0} not found").format(employee))

    emp = frappe.get_doc("Employee", employee)

    data = {
        "employee_name": emp.employee_name,
        "designation": emp.designation,
        "department": emp.department,
        "branch": emp.branch,
        "company": emp.company,
        "date_of_joining": emp.date_of_joining,
        "nationality": getattr(emp, "custom_nationality", None) or getattr(emp, "country", None) or getattr(emp, "nationality", None),
        "iqama_no": getattr(emp, "custom_iqama_no", None) or getattr(emp, "iqama_no", None) or getattr(emp, "identification_no", None),
        "gosi_no": getattr(emp, "custom_gosi_no", None) or getattr(emp, "gosi_no", None),
        "passport_number": emp.passport_number,
        "bank_name": getattr(emp, "bank_name", None),
        "bank_account": getattr(emp, "bank_ac_no", None),
        "iban": getattr(emp, "iban", None),
    }

    # Fetch gross salary from SSA (custom_total_salary or total_salary)
    gross_salary = 0
    try:
        ssa_name = frappe.db.get_value(
            "Salary Structure Assignment",
            {"employee": employee, "docstatus": 1},
            "name",
            order_by="from_date desc",
        )
        if ssa_name:
            ssa = frappe.get_doc("Salary Structure Assignment", ssa_name)
            gross_salary = (
                flt(getattr(ssa, "custom_total_salary", 0))
                or flt(getattr(ssa, "total_salary", 0))
                or flt(getattr(ssa, "base", 0))
            )
    except Exception as ex:
        frappe.log_error(f"KSA EOS SSA fetch error: {ex}", "KSA EOS Calculation")

    data["gross_salary"] = gross_salary

    # Get leave balance
    leave_balance = 0
    try:
        leaves = frappe.db.sql("""
            SELECT SUM(la.total_leaves_allocated)
            FROM `tabLeave Allocation` la
            WHERE la.employee = %s
            AND la.docstatus = 1
            AND la.from_date <= CURDATE()
            AND la.to_date >= CURDATE()
        """, employee)
        if leaves and leaves[0][0]:
            leave_balance = flt(leaves[0][0])

        leaves_taken = frappe.db.sql("""
            SELECT SUM(la.total_leave_days)
            FROM `tabLeave Application` la
            WHERE la.employee = %s
            AND la.docstatus = 1
            AND la.status = 'Approved'
        """, employee)
        if leaves_taken and leaves_taken[0][0]:
            leave_balance -= flt(leaves_taken[0][0])
    except Exception:
        leave_balance = 0

    data["leaves_balance"] = leave_balance if leave_balance > 0 else 0

    # Active loan recovery
    try:
        if frappe.db.exists("DocType", "Loan"):
            active_loan = frappe.db.sql("""
                SELECT SUM(l.outstanding_amount)
                FROM `tabLoan` l
                WHERE l.applicant = %s
                AND l.docstatus = 1
                AND l.status NOT IN ('Closed', 'Settled')
            """, employee)
            if active_loan and active_loan[0][0]:
                data["loan_advance_recovery"] = flt(active_loan[0][0])
    except Exception:
        pass

    return data
