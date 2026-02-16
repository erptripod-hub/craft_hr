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
		if (frm.doc.employee) {
			// Fetch current salary details
			frappe.call({
				method: 'craft_hr.craft_hr.doctype.salary_increment.salary_increment.get_current_salary_details',
				args: {
					employee: frm.doc.employee
				},
				callback: function(r) {
					if (r.message && r.message.salary_structure) {
						// Set current salary structure and base
						frm.set_value('current_salary_structure', r.message.salary_structure);
						frm.set_value('current_base', r.message.base);
						frm.set_value('new_salary_structure', r.message.salary_structure);
						
						// Clear existing tables
						frm.clear_table('current_components');
						frm.clear_table('new_components');
						
						// Populate current components table (read-only)
						if (r.message.components) {
							r.message.components.forEach(function(component) {
								let current_row = frm.add_child('current_components');
								current_row.salary_component = component.salary_component;
								current_row.current_amount = component.current_amount;
								current_row.new_amount = 0;
								current_row.difference = 0;
								current_row.percentage_change = 0;
								
								// Also add to new components table (editable)
								let new_row = frm.add_child('new_components');
								new_row.salary_component = component.salary_component;
								new_row.current_amount = component.current_amount;
								new_row.new_amount = component.new_amount;
								new_row.difference = 0;
								new_row.percentage_change = 0;
							});
						}
						
						frm.refresh_fields(['current_components', 'new_components']);
						frm.refresh_fields(['current_salary_structure', 'current_base', 'new_salary_structure']);
						
						// Calculate totals
						calculate_totals(frm);
					}
				}
			});
		}
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
	// Calculate total current salary
	let total_current = flt(frm.doc.current_base);
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
