/**
 * Dashboard functionality for Unified Compliance Hub
 * Handles data loading and visualization for the dashboard
 */

// Load dashboard data from API
function loadDashboardData(assessmentId) {
     // If no assessment ID is provided, show a message
    if (!assessmentId) {
        console.log("No assessment ID provided");
        showEmptyState("No assessments found. Please create one first.");
        return;
    }
    
    fetch(`/api/assessment/${assessmentId}`)
        .then(response => response.json())
        .then(data => {
            updateDashboardMetrics(data);
            populateRiskTable(data.detailed_results);
            
            // Initialize charts
            renderComplianceStatusChart(data.status_counts);
            renderRiskBreakdownChart(data.risk_counts);
            
            // Set up filter functionality
            setupFilters();
        })
        .catch(error => {
            console.error('Error loading dashboard data:', error);
            showErrorState();
        });
}

// Update dashboard metrics with assessment data
function updateDashboardMetrics(data) {
    // Update compliance percentages
    document.querySelector('.compliance-percentage').textContent = `${Math.round(data.overall_compliance)}%`;
    document.querySelector('.iso-percentage').textContent = `${Math.round(data.framework_compliance.iso27001)}%`;
    document.querySelector('.pci-percentage').textContent = `${Math.round(data.framework_compliance.pcidss)}%`;
    
    // Update progress bars
    document.querySelector('.overall-progress-bar').style.width = `${data.overall_compliance}%`;
    document.querySelector('.iso-progress-bar').style.width = `${data.framework_compliance.iso27001}%`;
    document.querySelector('.pci-progress-bar').style.width = `${data.framework_compliance.pcidss}%`;
    
    // Update status counts
    document.querySelector('.compliant-count').textContent = data.status_counts.compliant || 0;
    document.querySelector('.partially-count').textContent = data.status_counts.partially_compliant || 0;
    document.querySelector('.non-compliant-count').textContent = data.status_counts.non_compliant || 0;
}

// Populate risk table with assessment results
function populateRiskTable(detailedResults) {
    const tableBody = document.getElementById('risk-table-body');
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Sort by risk level (high first)
    const sortedResults = [...detailedResults].sort((a, b) => {
        const riskOrder = { 'high': 0, 'medium': 1, 'low': 2 };
        return riskOrder[a.risk_level] - riskOrder[b.risk_level];
    });
    
    // Only show high and medium risk items
    const highRiskItems = sortedResults.filter(item => 
        item.risk_level === 'high' || 
        (item.risk_level === 'medium' && item.status !== 'compliant')
    );
    
    if (highRiskItems.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="fas fa-check-circle text-success mb-3" style="font-size: 2rem;"></i>
                    <p class="mb-0">No high risk issues found.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    // Add rows for high risk items
    highRiskItems.forEach(item => {
        const row = document.createElement('tr');
        row.dataset.framework = item.framework.toLowerCase().replace(/\s+/g, '');
        
        // Format status badge
        const statusBadge = formatStatus(item.status);
        
        // Format risk badge
        const riskBadge = formatRisk(item.risk_level);
        
        row.innerHTML = `
            <td>${item.control_id}</td>
            <td>${item.title}</td>
            <td>
                <span class="badge ${item.framework.includes('ISO') ? 'bg-info' : 'bg-warning'}">
                    ${item.framework}
                </span>
            </td>
            <td>${statusBadge}</td>
            <td>${riskBadge}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-eye me-1"></i>View
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Set up filter functionality for risk table
function setupFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Apply filter
            filterTable(this.dataset.filter);
        });
    });
}

// Filter table rows based on framework
function filterTable(filter) {
    const rows = document.querySelectorAll('#risk-table-body tr');
    
    rows.forEach(row => {
        if (filter === 'all' || row.dataset.framework.includes(filter)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Format status for display
function formatStatus(status) {
    const statusMap = {
        'compliant': { class: 'bg-success', icon: 'fa-check', text: 'Compliant' },
        'partially_compliant': { class: 'bg-warning', icon: 'fa-exclamation', text: 'Partial' },
        'non_compliant': { class: 'bg-danger', icon: 'fa-times', text: 'Non-Compliant' }
    };
    
    const statusInfo = statusMap[status] || statusMap.non_compliant;
    
    return `
        <span class="badge ${statusInfo.class}">
            <i class="fas ${statusInfo.icon} me-1"></i>${statusInfo.text}
        </span>
    `;
}

// Format risk level for display
function formatRisk(risk) {
    const riskMap = {
        'high': { class: 'high', text: 'High' },
        'medium': { class: 'medium', text: 'Medium' },
        'low': { class: 'low', text: 'Low' }
    };
    
    const riskInfo = riskMap[risk] || riskMap.medium;
    
    return `<span class="badge risk-badge ${riskInfo.class}">${riskInfo.text}</span>`;
}

// Show error state if data can't be loaded
function showErrorState() {
    // Reset metrics to zero
    document.querySelector('.compliance-percentage').textContent = '0%';
    document.querySelector('.iso-percentage').textContent = '0%';
    document.querySelector('.pci-percentage').textContent = '0%';
    
    // Show error message in table
    const tableBody = document.getElementById('risk-table-body');
    tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-4">
                <i class="fas fa-exclamation-triangle text-warning mb-3" style="font-size: 2rem;"></i>
                <p class="mb-0">Could not load dashboard data. Please try again later.</p>
            </td>
        </tr>
    `;
}