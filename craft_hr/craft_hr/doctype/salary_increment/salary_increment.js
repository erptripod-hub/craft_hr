// Copyright (c) 2024, Craftinteractive and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salary Increment', {
	refresh: function(frm) {
		// Set default company
		if (!frm.doc.company) {
			frm.set_value('company', frappe.defaults.get_user_default('Company'));
		}
	},

	employee: function(frm) {
		if (!frm.doc.employee) return;

		// Step 1: Fetch employee fields (company, identification_no)
		frappe.db.get_value('Employee', frm.doc.employee, 
			['company', 'identification_no'],
			function(emp) {
				if (emp) {
					if (emp.company)           frm.set_value('company', emp.company);
					if (emp.identification_no) frm.set_value('identification_no', emp.identification_no);
				} else {
					// fallback: try passport_number
					frappe.db.get_value('Employee', frm.doc.employee, 
						['company', 'passport_number'],
						function(emp2) {
							if (emp2) {
								if (emp2.company)         frm.set_value('company', emp2.company);
								if (emp2.passport_number) frm.set_value('identification_no', emp2.passport_number);
							}
						}
					);
				}
			}
		);

		// Step 2: Fetch current salary details from Salary Structure Assignment
		frappe.call({
			method: 'craft_hr.craft_hr.doctype.salary_increment.salary_increment.get_current_salary_details',
			args: { employee: frm.doc.employee },
			callback: function(r) {
				if (!r.message || !r.message.salary_structure) return;

				// Set salary structure fields
				frm.set_value('current_salary_structure', r.message.salary_structure);
				frm.set_value('current_base', r.message.base);
				frm.set_value('new_salary_structure', r.message.salary_structure);

				// Set company from assignment if not already set
				if (r.message.company && !frm.doc.company) {
					frm.set_value('company', r.message.company);
				}

				// Clear tables
				frm.clear_table('current_components');
				frm.clear_table('new_components');

				// Populate both tables
				(r.message.components || []).forEach(function(component) {
					// Current (read-only reference)
					let cur = frm.add_child('current_components');
					cur.salary_component  = component.salary_component;
					cur.current_amount    = component.current_amount;
					cur.new_amount        = component.current_amount;
					cur.difference        = 0;
					cur.percentage_change = 0;

					// New (editable)
					let nw = frm.add_child('new_components');
					nw.salary_component  = component.salary_component;
					nw.current_amount    = component.current_amount;
					nw.new_amount        = component.current_amount;
					nw.difference        = 0;
					nw.percentage_change = 0;
				});

				frm.refresh_fields(['current_components', 'new_components',
					'current_salary_structure', 'current_base', 'new_salary_structure']);

				calculate_totals(frm);
			}
		});
	}
});

frappe.ui.form.on('Salary Component Detail', {
	new_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		
		// Calculate difference and percentage
		row.difference = flt(row.new_amount) - flt(row.current_amount);
		if (flt(row.current_amount) > 0) {
			row.percentage_change = (row.difference / flt(row.current_amount)) * 100;
		}
		
		frm.refresh_field('new_components');
		
		// Calculate totals
		calculate_totals(frm);
	},
	
	new_components_remove: function(frm) {
		calculate_totals(frm);
	}
});

function calculate_totals(frm) {
	// Calculate total current salary from components only (Basic already in components)
	let total_current = 0;
	(frm.doc.current_components || []).forEach(function(row) {
		total_current += flt(row.current_amount);
	});
	frm.set_value('total_current_salary', total_current);
	
	// Calculate total new salary
	let total_new = 0;
	(frm.doc.new_components || []).forEach(function(row) {
		total_new += flt(row.new_amount);
	});
	frm.set_value('total_new_salary', total_new);
	
	// Calculate increment
	let increment = total_new - total_current;
	frm.set_value('total_increment', increment);
	
	if (total_current > 0) {
		let increment_percentage = (increment / total_current) * 100;
		frm.set_value('total_increment_percentage', increment_percentage);
	}
	
	// Show warning if negative increment
	if (increment < 0) {
		frappe.msgprint({
			title: __('Warning'),
			indicator: 'orange',
			message: __('New salary is lower than current salary. This will be a salary reduction.')
		});
	}
}
