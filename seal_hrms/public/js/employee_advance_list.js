frappe.listview_settings['Employee Advance'] = {
    onload: function(listview) {
        // Add custom buttons
        add_custom_buttons(listview);
    },
    
    refresh: function(listview) {
        // Refresh buttons when list refreshes
        add_custom_buttons(listview);
    }
};

function add_custom_buttons(listview) {
    // Remove existing buttons if present
    listview.page.remove_inner_button(__('Process All Recoveries'));
    listview.page.remove_inner_button(__('Notify Overdue Advances'));
    listview.page.remove_inner_button(__('Check Recovery Status'));
    
    // Add the recovery button
    listview.page.add_inner_button(__('Process All Recoveries'), function() {
        process_all_advance_recoveries(listview);
    }, __('Actions'));
    
    // Add the notification button
    listview.page.add_inner_button(__('Notify Overdue Advances'), function() {
        notify_overdue_advances(listview);
    }, __('Actions'));
    
    // Add status check button
    listview.page.add_inner_button(__('Check Recovery Status'), function() {
        check_global_recovery_status(listview);
    }, __('Reports'));
}

function process_all_advance_recoveries(listview) {
    // Show confirmation dialog
    frappe.confirm(
        `<div>
            <h4>Process All Overdue Advance Recoveries</h4>
            <p>This will:</p>
            <ul>
                <li>Process overdue advances for <strong>ALL companies</strong></li>
                <li>Create Additional Salary records for recovery</li>
                <li>Send email notifications to HR teams</li>
                <li>Run as a background job (may take several minutes)</li>
            </ul>
            <p><strong>Do you want to continue?</strong></p>
        </div>`,
        function() {
            execute_recovery_job(listview);
        },
        function() {
            frappe.show_alert({
                message: __('Recovery process cancelled'),
                indicator: 'blue'
            });
        }
    );
}

function notify_overdue_advances(listview) {
    // Show confirmation dialog
    frappe.confirm(
        `<div>
            <h4>Send Overdue Advance Notifications</h4>
            <p>This will:</p>
            <ul>
                <li>Send notification emails to employees with expiring/overdue advances</li>
                <li>Process advances from <strong>ALL companies</strong> with notifications enabled</li>
                <li>Send both advance warnings and urgent alerts as configured</li>
                <li>Send summary email to HR teams when complete</li>
                <li>Run as a background job (may take several minutes)</li>
            </ul>
            <p><strong>Do you want to continue?</strong></p>
        </div>`,
        function() {
            execute_notification_job(listview);
        },
        function() {
            frappe.show_alert({
                message: __('Notification process cancelled'),
                indicator: 'blue'
            });
        }
    );
}

function execute_recovery_job(listview) {
    // Show loading state
    frappe.show_alert({
        message: __('Queuing advance recovery job...'),
        indicator: 'blue'
    });

    // Disable button temporarily
    const recovery_btn = listview.page.inner_toolbar.find('.btn:contains("Process All Recoveries")');
    recovery_btn.prop('disabled', true);

    // Call the server method to enqueue the job
    frappe.call({
        method: 'seal_hrms.seal_hrms.overrides.employee_advance.recover_overdue_advances',
        callback: function(response) {
            handle_recovery_job_response(response, listview);
        },
        error: function(error) {
            handle_recovery_job_error(error, listview);
        },
        always: function() {
            // Re-enable button after 30 seconds
            setTimeout(function() {
                recovery_btn.prop('disabled', false);
            }, 30000);
        }
    });
}

function execute_notification_job(listview) {
    // Show loading state
    frappe.show_alert({
        message: __('Queuing notification job...'),
        indicator: 'blue'
    });

    // Disable button temporarily
    const notify_btn = listview.page.inner_toolbar.find('.btn:contains("Notify Overdue Advances")');
    notify_btn.prop('disabled', true);

    // Call the server method to enqueue the job
    frappe.call({
        method: 'seal_hrms.seal_hrms.overrides.employee_advance.notify_overdue_advances',
        callback: function(response) {
            handle_notification_job_response(response, listview);
        },
        error: function(error) {
            handle_notification_job_error(error, listview);
        },
        always: function() {
            // Re-enable button after 30 seconds
            setTimeout(function() {
                notify_btn.prop('disabled', false);
            }, 30000);
        }
    });
}

function handle_recovery_job_response(response, listview) {
    frappe.show_alert({
        message: __('Recovery job queued successfully! Check Background Jobs for progress.'),
        indicator: 'green'
    });

    // Refresh the listview after a short delay
    setTimeout(function() {
        listview.refresh();
    }, 2000);
}

function handle_notification_job_response(response, listview) {
    frappe.show_alert({
        message: __('Notification job queued successfully! Check Background Jobs for progress.'),
        indicator: 'green'
    });

    // You could also show a more detailed message if needed
    frappe.msgprint({
        title: __('Notification Job Queued'),
        indicator: 'green',
        message: `
            <div>
                <h4>✅ Employee Notification Job Started</h4>
                <p>The notification process has been queued as a background job.</p>
                <br>
                <p><strong>What's happening:</strong></p>
                <ul>
                    <li>Employees with expiring advances will be notified</li>
                    <li>Both advance warnings and urgent alerts will be sent</li>
                    <li>HR will receive a summary email when complete</li>
                </ul>
                <br>
                <p><strong>Monitor progress via:</strong></p>
                <ul>
                    <li>Background Jobs</li>
                    <li>Error Log</li>
                    <li>Email notifications</li>
                </ul>
            </div>
        `
    });

    // Refresh the listview after a short delay
    setTimeout(function() {
        listview.refresh();
    }, 2000);
}

function handle_recovery_job_error(error, listview) {
    console.error('Recovery Job Error:', error);
    
    frappe.msgprint({
        title: __('Error Queuing Job'),
        indicator: 'red',
        message: `
            <div>
                <h4>❌ Failed to Queue Recovery Job</h4>
                <p>There was an error starting the advance recovery process.</p>
                <br>
                <p><strong>Possible causes:</strong></p>
                <ul>
                    <li>Background job queue is full</li>
                    <li>System configuration issue</li>
                    <li>Insufficient permissions</li>
                </ul>
                <br>
                <p><strong>Please:</strong></p>
                <ul>
                    <li>Check Background Jobs for any failed jobs</li>
                    <li>Review Error Log for details</li>
                    <li>Contact system administrator if issue persists</li>
                </ul>
            </div>
        `
    });

    frappe.show_alert({
        message: __('Failed to queue recovery job'),
        indicator: 'red'
    });
}

function handle_notification_job_error(error, listview) {
    console.error('Notification Job Error:', error);
    
    frappe.msgprint({
        title: __('Error Queuing Notification Job'),
        indicator: 'red',
        message: `
            <div>
                <h4>❌ Failed to Queue Notification Job</h4>
                <p>There was an error starting the notification process.</p>
                <br>
                <p><strong>Possible causes:</strong></p>
                <ul>
                    <li>Background job queue is full</li>
                    <li>Email configuration issues</li>
                    <li>System configuration problem</li>
                    <li>Insufficient permissions</li>
                </ul>
                <br>
                <p><strong>Please:</strong></p>
                <ul>
                    <li>Check Background Jobs for any failed jobs</li>
                    <li>Review Error Log for details</li>
                    <li>Verify email settings in System Settings</li>
                    <li>Contact system administrator if issue persists</li>
                </ul>
            </div>
        `
    });

    frappe.show_alert({
        message: __('Failed to queue notification job'),
        indicator: 'red'
    });
}

function check_global_recovery_status(listview) {
    frappe.show_alert({
        message: __('Loading recovery status...'),
        indicator: 'blue'
    });

    frappe.call({
        method: 'seal_hrms.seal_hrms.overrides.employee_advance.get_global_recovery_status',
        callback: function(response) {
            if (response.message) {
                show_global_status(response.message);
            }
        },
        error: function() {
            frappe.msgprint({
                title: __('Status Check Failed'),
                indicator: 'red',
                message: __('Unable to retrieve recovery status. Please check system logs.')
            });
        }
    });
}

function show_global_status(status) {
    let message = `
        <div>
            <h4>Global Advance Recovery Status</h4>
            <table class="table table-bordered" style="margin-top: 15px;">
                <tr>
                    <td><strong>Total Companies with Auto-Recovery</strong></td>
                    <td>${status.enabled_companies || 0}</td>
                </tr>
                <tr>
                    <td><strong>Total Overdue Advances</strong></td>
                    <td>${status.total_overdue_advances || 0}</td>
                </tr>
                <tr>
                    <td><strong>Total Outstanding Amount</strong></td>
                    <td>${format_currency(status.total_outstanding_amount || 0)}</td>
                </tr>
                <tr>
                    <td><strong>Pending Recovery Records</strong></td>
                    <td>${status.pending_recoveries || 0}</td>
                </tr>
                <tr>
                    <td><strong>Last Auto Recovery Run</strong></td>
                    <td>${status.last_run || 'Never'}</td>
                </tr>
                <tr>
                    <td><strong>Current Background Jobs</strong></td>
                    <td>${status.active_recovery_jobs || 0}</td>
                </tr>
            </table>
    `;

    if (status.company_breakdown && status.company_breakdown.length > 0) {
        message += `
            <br>
            <h5>Company Breakdown:</h5>
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Overdue Advances</th>
                        <th>Outstanding Amount</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        status.company_breakdown.forEach(function(company) {
            message += `
                <tr>
                    <td>${company.company}</td>
                    <td>${company.overdue_count}</td>
                    <td>${format_currency(company.outstanding_amount)}</td>
                </tr>
            `;
        });
        
        message += `
                </tbody>
            </table>
        `;
    }

    if (status.configuration_issues && status.configuration_issues.length > 0) {
        message += `
            <br>
            <div class="alert alert-warning">
                <h6>⚠️ Configuration Issues:</h6>
                <ul>
        `;
        
        status.configuration_issues.forEach(function(issue) {
            message += `<li>${issue}</li>`;
        });
        
        message += `
                </ul>
            </div>
        `;
    }

    message += '</div>';

    frappe.msgprint({
        title: __('Recovery Status Report'),
        indicator: status.total_overdue_advances > 0 ? 'orange' : 'green',
        message: message
    });
}

// Add keyboard shortcuts for quick access
$(document).on('keydown', function(e) {
    if (cur_list && cur_list.doctype === 'Employee Advance') {
        // Ctrl+Shift+R for Recovery
        if (e.ctrlKey && e.shiftKey && e.keyCode === 82) {
            e.preventDefault();
            process_all_advance_recoveries(cur_list);
        }
        // Ctrl+Shift+N for Notifications
        if (e.ctrlKey && e.shiftKey && e.keyCode === 78) {
            e.preventDefault();
            notify_overdue_advances(cur_list);
        }
    }
});

// Utility function for currency formatting
function format_currency(amount, currency = null) {
    if (!amount) return '0.00';
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || frappe.defaults.get_default('currency') || 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

// // Add refresh indicator when jobs are running
// function add_job_status_indicator(listview) {
//     // Check if recovery or notification jobs are currently running
//     frappe.call({
//         method: 'frappe.core.doctype.rq_job.rq_job.get_jobs',
//         args: {
//             start: 0,
//             limit: 20
//         },
//         callback: function(r) {
//             if (r.message) {
//                 const active_jobs = r.message.filter(job => 
//                     (job.job_name === 'Employee Advance Recovery' || 
//                      job.job_name === 'Employee Advance Notifications') && 
//                     job.status === 'started'
//                 );
                
//                 if (active_jobs.length > 0) {
//                     let job_names = active_jobs.map(job => job.job_name).join(', ');
//                     listview.page.set_indicator(`${job_names} Running`, 'blue');
                    
//                     // Auto-refresh every 30 seconds while jobs are running
//                     setTimeout(function() {
//                         if (cur_list && cur_list.doctype === 'Employee Advance') {
//                             add_job_status_indicator(listview);
//                         }
//                     }, 30000);
//                 }
//             }
//         }
//     });
// }

// // Initialize job status checking when list loads
// $(document).ready(function() {
//     if (cur_list && cur_list.doctype === 'Employee Advance') {
//         add_job_status_indicator(cur_list);
//     }
// });