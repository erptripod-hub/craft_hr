# Copyright (c) 2024, Craftinteractive and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class SalaryIncrement(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_totals()
	
	def validate_dates(self):
		"""Validate effective date exists"""
		if not self.effective_date:
			frappe.throw(_("Please set an Effective Date"))
	
	def calculate_totals(self):
		"""Calculate total current and new salaries"""
		# Calculate total current salary
		self.total_current_salary = flt(self.current_base)
		for row in self.current_components:
			self.total_current_salary += flt(row.current_amount)
		
		# Calculate total new salary
		self.total_new_salary = 0
		for row in self.new_components:
			self.total_new_salary += flt(row.new_amount)
			
			# Calculate difference and percentage for each component
			row.difference = flt(row.new_amount) - flt(row.current_amount)
			if flt(row.current_amount) > 0:
				row.percentage_change = (row.difference / flt(row.current_amount)) * 100
		
		# Calculate total increment
		self.total_increment = flt(self.total_new_salary) - flt(self.total_current_salary)
		if flt(self.total_current_salary) > 0:
			self.total_increment_percentage = (self.total_increment / flt(self.total_current_salary)) * 100
	
	def on_submit(self):
		"""Create new Salary Structure Assignment when increment is submitted"""
		self.create_salary_structure_assignment()
	
	def on_cancel(self):
		"""Cancel the linked salary structure assignment"""
		self.cancel_salary_structure_assignment()
	
	def create_salary_structure_assignment(self):
		"""Create a new Salary Structure Assignment from the effective date"""
		
		# Check if assignment already exists
		existing = frappe.db.exists(
			"Salary Structure Assignment",
			{
				"employee": self.employee,
				"from_date": self.effective_date,
				"docstatus": ["!=", 2]
			}
		)
		
		if existing:
			frappe.msgprint(
				_("Salary Structure Assignment {0} already exists for this date").format(
					frappe.bold(existing)
				)
			)
			return
		
		# Get the salary structure details to create the assignment properly
		salary_structure = frappe.get_doc("Salary Structure", self.new_salary_structure)
		
		# Create component amount mapping from new_components
		component_amounts = {}
		for component in self.new_components:
			component_amounts[component.salary_component] = component.new_amount
		
		# Create new salary structure assignment
		assignment = frappe.new_doc("Salary Structure Assignment")
		assignment.employee = self.employee
		assignment.salary_structure = self.new_salary_structure
		assignment.from_date = self.effective_date
		assignment.company = self.company
		
		# Set base salary (first component with "Basic" in name)
		for component in self.new_components:
			component_name = frappe.db.get_value("Salary Component", component.salary_component, "salary_component_abbr")
			if component_name and "basic" in component_name.lower():
				assignment.base = component.new_amount
				break
		
		# If no basic found, use first component
		if not assignment.base and self.new_components:
			assignment.base = self.new_components[0].new_amount
		
		# Add custom field to track salary increment if it exists
		if hasattr(assignment, 'custom_salary_increment'):
			assignment.custom_salary_increment = self.name
		
		assignment.flags.ignore_permissions = True
		assignment.insert()
		
		# Update the salary structure assignment with new component amounts
		# This is done by modifying the salary slip generation to use these amounts
		# Store the increment reference in the assignment
		frappe.db.set_value("Salary Structure Assignment", assignment.name, {
			"custom_salary_increment": self.name if frappe.db.has_column("Salary Structure Assignment", "custom_salary_increment") else None
		})
		
		assignment.submit()
		
		frappe.msgprint(
			_("Salary Structure Assignment {0} created successfully").format(
				frappe.bold(assignment.name)
			),
			alert=True,
			indicator="green"
		)
		
		# Add comment to link documents
		assignment.add_comment(
			"Info",
			_("Created from Salary Increment: {0}").format(
				frappe.utils.get_link_to_form("Salary Increment", self.name)
			)
		)
	
	def cancel_salary_structure_assignment(self):
		"""Cancel the linked Salary Structure Assignment"""
		
		# Find the salary structure assignment created from this increment
		assignments = frappe.get_all(
			"Salary Structure Assignment",
			filters={
				"employee": self.employee,
				"from_date": self.effective_date,
				"docstatus": 1
			},
			pluck="name"
		)
		
		for assignment_name in assignments:
			assignment = frappe.get_doc("Salary Structure Assignment", assignment_name)
			assignment.flags.ignore_permissions = True
			assignment.cancel()
			
			frappe.msgprint(
				_("Salary Structure Assignment {0} has been cancelled").format(
					frappe.bold(assignment_name)
				),
				alert=True,
				indicator="orange"
			)


@frappe.whitelist()
def get_current_salary_details(employee):
	"""Get current salary structure assignment and components for an employee"""
	
	if not employee:
		return {}
	
	# Get the latest submitted salary structure assignment
	current_assignment = frappe.db.get_value(
		"Salary Structure Assignment",
		filters={
			"employee": employee,
			"docstatus": 1
		},
		fieldname=["name", "salary_structure", "base", "from_date"],
		order_by="from_date desc",
		as_dict=1
	)
	
	if not current_assignment:
		frappe.msgprint(_("No active Salary Structure Assignment found for this employee"))
		return {}
	
	components = []
	component_amounts = {}

	# Step 1: Try to get amounts from the latest submitted Salary Slip
	latest_slip = frappe.db.get_value(
		"Salary Slip",
		filters={
			"employee": employee,
			"docstatus": 1
		},
		fieldname="name",
		order_by="end_date desc"
	)

	if latest_slip:
		slip_earnings = frappe.get_all(
			"Salary Detail",
			filters={
				"parent": latest_slip,
				"parentfield": "earnings"
			},
			fields=["salary_component", "amount"],
			order_by="idx"
		)
		component_amounts = {e.salary_component: flt(e.amount) for e in slip_earnings}

	# Step 2: Get all earnings components from the salary structure
	earnings = frappe.get_all(
		"Salary Detail",
		filters={
			"parent": current_assignment.salary_structure,
			"parentfield": "earnings"
		},
		fields=["salary_component", "amount", "formula", "amount_based_on_formula"],
		order_by="idx"
	)

	for earning in earnings:
		# Get amount - priority: salary slip > structure amount
		amount = component_amounts.get(earning.salary_component, 0)
		
		# If amount is 0 and structure has a fixed amount (not formula), use it
		if flt(amount) == 0 and not earning.amount_based_on_formula:
			amount = flt(earning.amount)

		# If amount is still 0, try formula with base salary
		if flt(amount) == 0 and earning.amount_based_on_formula and earning.formula:
			if "base" in (earning.formula or "").lower():
				try:
					base = flt(current_assignment.base)
					amount = flt(eval(earning.formula.replace("base", str(base))))
				except Exception:
					amount = 0

		components.append({
			"salary_component": earning.salary_component,
			"current_amount": flt(amount),
			"new_amount": flt(amount)
		})

	return {
		"salary_structure": current_assignment.salary_structure,
		"base": flt(current_assignment.base),
		"components": components
	}
