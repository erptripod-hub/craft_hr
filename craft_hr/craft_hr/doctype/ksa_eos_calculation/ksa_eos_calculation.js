// Copyright (c) 2026, Craft HR
// KSA End of Service Calculation - Client Script

frappe.ui.form.on('KSA EOS Calculation', {
    refresh: function(frm) {
        // Mark as Cleared button
        if (frm.doc.docstatus === 0 && frm.doc.status === 'In Process') {
            frm.add_custom_button(__('Mark as Cleared'), function() {
                frappe.call({
                    method: 'craft_hr.craft_hr.doctype.ksa_eos_calculation.ksa_eos_calculation.mark_as_cleared',
                    args: { docname: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Actions'));
        }

        // Set currency for display
        frm.set_currency_labels(['gross_salary', 'daily_wage', 'gratuity_payable', 
            'leave_salary_payable', 'overtime_payable', 'salary_payable',
            'net_payable', 'total_recovery', 'gross_total'], 'SAR');
    },

    employee: function(frm) {
        if (frm.doc.employee) {
            frappe.call({
                method: 'craft_hr.craft_hr.doctype.ksa_eos_calculation.ksa_eos_calculation.get_employee_details',
                args: { employee: frm.doc.employee },
                callback: function(r) {
                    if (r.message) {
                        let data = r.message;
                        frm.set_value('employee_name', data.employee_name);
                        frm.set_value('designation', data.designation);
                        frm.set_value('department', data.department);
                        frm.set_value('branch', data.branch);
                        frm.set_value('company', data.company);
                        frm.set_value('date_of_joining', data.date_of_joining);
                        frm.set_value('nationality', data.nationality);
                        frm.set_value('iqama_no', data.iqama_no);
                        frm.set_value('gosi_no', data.gosi_no);
                        frm.set_value('passport_number', data.passport_number);
                        frm.set_value('bank_name', data.bank_name);
                        frm.set_value('bank_account', data.bank_account);
                        frm.set_value('iban', data.iban);
                        frm.set_value('gross_salary', data.gross_salary);
                        frm.set_value('leaves_balance', data.leaves_balance);
                        if (data.loan_advance_recovery) {
                            frm.set_value('loan_advance_recovery', data.loan_advance_recovery);
                        }
                    }
                }
            });
        }
    },

    separation_type: function(frm) {
        // Clear termination reason if not termination
        if (frm.doc.separation_type !== 'Termination by Employer') {
            frm.set_value('termination_reason', '');
        }
        // Trigger recalculation
        frm.trigger('calculate_gratuity_preview');
    },

    termination_reason: function(frm) {
        frm.trigger('calculate_gratuity_preview');
    },

    calculate_gratuity_preview: function(frm) {
        // Show a preview of the gratuity percentage based on separation type
        let separation = frm.doc.separation_type;
        let years = frm.doc.employment_years || 0;
        let percentage = 100;

        if (separation === 'Termination by Employer' && 
            frm.doc.termination_reason === 'Article 80 (Gross Misconduct)') {
            percentage = 0;
        } else if (separation === 'Resignation') {
            if (years < 2) percentage = 0;
            else if (years < 5) percentage = 33.33;
            else if (years < 10) percentage = 66.67;
            else percentage = 100;
        }

        frm.set_value('gratuity_percentage', percentage);
    },

    date_of_settlement: function(frm) {
        frm.trigger('calculate_gratuity_preview');
    },

    gross_salary: function(frm) {
        if (frm.doc.gross_salary) {
            frm.set_value('daily_wage', flt(frm.doc.gross_salary / 30, 2));
        }
    },

    days_worked_pending: function(frm) {
        if (frm.doc.gross_salary && frm.doc.days_worked_pending) {
            let daily = flt(frm.doc.gross_salary / 30);
            frm.set_value('current_month_payment', flt(daily * frm.doc.days_worked_pending, 2));
        }
    }
});
