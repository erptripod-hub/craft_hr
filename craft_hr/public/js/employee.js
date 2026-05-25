// Employee Leave Management Automation
// Adds "Leave Management" section with "Allocate Leaves" button

frappe.ui.form.on("Employee", {
    refresh: function(frm) {
        // Only show for saved, active employees
        if (!frm.is_new() && frm.doc.status === "Active") {
            // Add Allocate Leaves button in primary actions
            frm.add_custom_button(__('Allocate Leaves'), function() {
                allocate_leaves(frm);
            }, __('Leave Management'));
            
            // Add Check Allocation Status button
            frm.add_custom_button(__('Check Allocation Status'), function() {
                check_allocation_status(frm);
            }, __('Leave Management'));
        }
    }
});

function allocate_leaves(frm) {
    // Validate required fields
    if (!frm.doc.company) {
        frappe.msgprint(__('Please set Company first'));
        return;
    }
    if (!frm.doc.gender) {
        frappe.msgprint(__('Please set Gender first'));
        return;
    }
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set Date of Joining first'));
        return;
    }
    if (!frm.doc.employment_type) {
        frappe.msgprint(__('Please set Employment Type first'));
        return;
    }
    
    frappe.confirm(
        __('This will allocate Leave Policy and Annual Leave for this employee. Continue?'),
        function() {
            frappe.call({
                method: 'craft_hr.events.leave_management.allocate_employee_leaves',
                args: {
                    employee: frm.doc.name
                },
                freeze: true,
                freeze_message: __('Allocating Leaves...'),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.success) {
                            frappe.msgprint({
                                title: __('Success'),
                                indicator: 'green',
                                message: r.message.message
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: __('Info'),
                                indicator: 'blue',
                                message: r.message.message
                            });
                        }
                    }
                }
            });
        }
    );
}

function check_allocation_status(frm) {
    frappe.call({
        method: 'craft_hr.events.leave_management.get_allocation_status',
        args: {
            employee: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let html = '<table class="table table-bordered">';
                html += '<thead><tr><th>Leave Type</th><th>Allocated</th><th>Status</th></tr></thead><tbody>';
                
                r.message.forEach(function(row) {
                    let status_color = row.allocated ? 'green' : 'red';
                    let status_text = row.allocated ? 'Allocated' : 'Not Allocated';
                    html += `<tr>
                        <td>${row.leave_type}</td>
                        <td>${row.days || '-'}</td>
                        <td><span class="indicator ${status_color}">${status_text}</span></td>
                    </tr>`;
                });
                
                html += '</tbody></table>';
                
                frappe.msgprint({
                    title: __('Leave Allocation Status'),
                    indicator: 'blue',
                    message: html
                });
            }
        }
    });
}
