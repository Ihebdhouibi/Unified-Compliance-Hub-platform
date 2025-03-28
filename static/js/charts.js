/**
 * Chart implementations for Unified Compliance Hub
 * Uses Chart.js for visualization
 */

// Stores chart instances for potential updates
let complianceStatusChartInstance = null;
let riskBreakdownChartInstance = null;

// Render compliance status doughnut chart
function renderComplianceStatusChart(statusCounts) {
    const ctx = document.getElementById('complianceStatusChart');
    
    // If chart already exists, destroy it
    if (complianceStatusChartInstance) {
        complianceStatusChartInstance.destroy();
    }
    
    // Prepare data
    const data = {
        labels: ['Compliant', 'Partially Compliant', 'Non-Compliant'],
        datasets: [{
            data: [
                statusCounts.compliant || 0,
                statusCounts.partially_compliant || 0,
                statusCounts.non_compliant || 0
            ],
            backgroundColor: [
                '#198754', // success green
                '#fd7e14', // warning orange
                '#dc3545'  // danger red
            ],
            borderWidth: 0,
            hoverOffset: 10
        }]
    };
    
    // Chart configuration
    const config = {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        boxWidth: 12,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const value = context.raw;
                            const percentage = Math.round((value / total) * 100) + '%';
                            return `${value} controls (${percentage})`;
                        }
                    }
                }
            }
        }
    };
    
    // Create chart
    complianceStatusChartInstance = new Chart(ctx, config);
}

// Render risk level distribution chart
function renderRiskBreakdownChart(riskCounts) {
    const ctx = document.getElementById('riskBreakdownChart');
    
    // If chart already exists, destroy it
    if (riskBreakdownChartInstance) {
        riskBreakdownChartInstance.destroy();
    }
    
    // Prepare data
    const data = {
        labels: ['High', 'Medium', 'Low'],
        datasets: [{
            data: [
                riskCounts.high || 0,
                riskCounts.medium || 0,
                riskCounts.low || 0
            ],
            backgroundColor: [
                '#dc3545', // danger red
                '#fd7e14', // warning orange
                '#198754'  // success green
            ],
            borderWidth: 0
        }]
    };
    
    // Chart configuration
    const config = {
        type: 'pie',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        boxWidth: 12,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const value = context.raw;
                            const percentage = Math.round((value / total) * 100) + '%';
                            return `${value} controls (${percentage})`;
                        }
                    }
                }
            }
        }
    };
    
    // Create chart
    riskBreakdownChartInstance = new Chart(ctx, config);
}

// Format status for display
function formatStatus(status) {
    switch (status) {
        case 'compliant':
            return 'Compliant';
        case 'partially_compliant':
            return 'Partially Compliant';
        case 'non_compliant':
            return 'Non-Compliant';
        default:
            return status;
    }
}

// Format risk for display
function formatRisk(risk) {
    switch (risk) {
        case 'high':
            return 'High';
        case 'medium':
            return 'Medium';
        case 'low':
            return 'Low';
        default:
            return risk;
    }
}