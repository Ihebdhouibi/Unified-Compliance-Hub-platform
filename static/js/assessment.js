/**
 * Assessment functionality for Unified Compliance Hub
 * Handles the control assessment form and validation
 */

// Initialize assessment form
function initAssessmentForm() {
    // Get elements
    const statusSelects = document.querySelectorAll('.status-select');
    const riskSelects = document.querySelectorAll('.risk-select');
    const saveBtn = document.getElementById('save-assessment-btn');
    
    // Set up event listeners for status selects
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const controlId = this.dataset.controlId;
            const controlItem = document.querySelector(`.control-item[data-id="${controlId}"]`);
            const actionRequired = controlItem.querySelector('.action-required-container');
            const statusIndicator = document.getElementById(`status-indicator-${controlId}`);
            const statusText = document.getElementById(`status-text-${controlId}`);
            
            // Update status indicator and text
            statusIndicator.className = 'status-indicator';
            if (this.value) {
                statusIndicator.classList.add(this.value);
                controlItem.dataset.status = this.value;
                statusText.textContent = formatStatus(this.value);
                
                // Show action required field for non-compliant or partially compliant
                if (this.value === 'non_compliant' || this.value === 'partially_compliant') {
                    actionRequired.classList.remove('d-none');
                } else {
                    actionRequired.classList.add('d-none');
                }
            } else {
                controlItem.dataset.status = 'pending';
                statusText.textContent = 'Pending';
                actionRequired.classList.add('d-none');
            }
            
            // Update progress
            updateProgress();
        });
    });
    
    // Set up event listeners for risk selects
    riskSelects.forEach(select => {
        select.addEventListener('change', function() {
            // For future implementations, could visually indicate risk level changes
        });
    });
    
    // Set up save button event handler
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            document.getElementById('assessment-form').submit();
        });
    }
    
    // Count total controls
    const totalControls = document.querySelectorAll('.control-item').length;
    document.getElementById('total-controls').textContent = totalControls;
}

// Setup event handlers for filtering and batch operations
function setupFilters() {
    // Framework filter
    const frameworkFilters = document.querySelectorAll('input[name="framework-filter"]');
    frameworkFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            const framework = this.id.replace('filter-', '');
            applyFilters();
        });
    });
    
    // Search filter
    const searchInput = document.getElementById('filter-search');
    searchInput.addEventListener('input', function() {
        applyFilters();
    });
    
    // Status filter
    const statusFilters = document.querySelectorAll('.status-filter');
    statusFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update dropdown text
            const dropdownButton = document.getElementById('statusFilterDropdown');
            dropdownButton.textContent = this.textContent;
            
            // Apply filter
            applyFilters();
        });
    });
    
    // Batch update
    const batchUpdateOptions = document.querySelectorAll('.batch-update');
    batchUpdateOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            
            const status = this.dataset.status;
            const visibleControls = getVisibleControls();
            
            if (visibleControls.length > 0) {
                if (confirm(`Are you sure you want to set ${visibleControls.length} visible controls to "${formatStatus(status)}"?`)) {
                    batchUpdateControls(visibleControls, status);
                }
            } else {
                alert('No visible controls to update. Please adjust your filters.');
            }
        });
    });
}

// Apply all active filters
function applyFilters() {
    const controls = document.querySelectorAll('.control-item');
    const searchTerm = document.getElementById('filter-search').value.toLowerCase();
    const framework = document.querySelector('input[name="framework-filter"]:checked').id.replace('filter-', '');
    const statusFilter = document.getElementById('statusFilterDropdown').textContent.trim();
    
    controls.forEach(control => {
        let showByFramework = true;
        let showBySearch = true;
        let showByStatus = true;
        
        // Framework filter
        if (framework !== 'all') {
            showByFramework = control.dataset.framework === framework;
        }
        
        // Search filter
        if (searchTerm) {
            showBySearch = control.textContent.toLowerCase().includes(searchTerm);
        }
        
        // Status filter
        if (statusFilter !== 'Status') {
            const statusMap = {
                'Pending': 'pending',
                'Compliant': 'compliant',
                'Partially Compliant': 'partially_compliant',
                'Non-Compliant': 'non_compliant',
                'All': 'all'
            };
            
            const statusValue = statusMap[statusFilter] || 'all';
            if (statusValue !== 'all') {
                showByStatus = control.dataset.status === statusValue;
            }
        }
        
        // Show or hide based on combined filters
        if (showByFramework && showBySearch && showByStatus) {
            control.style.display = '';
        } else {
            control.style.display = 'none';
        }
    });
}

// Batch update controls
function batchUpdateControls(controls, status) {
    controls.forEach(control => {
        const controlId = control.dataset.id;
        
        // Update select
        const statusSelect = document.querySelector(`.status-select[data-control-id="${controlId}"]`);
        statusSelect.value = status;
        
        // Trigger change event to update UI
        const event = new Event('change');
        statusSelect.dispatchEvent(event);
    });
}

// Get visible controls
function getVisibleControls() {
    return Array.from(document.querySelectorAll('.control-item')).filter(
        control => control.style.display !== 'none'
    );
}

// Update progress indicators
function updateProgress() {
    const totalControls = document.querySelectorAll('.control-item').length;
    const completedControls = document.querySelectorAll('.control-item:not([data-status="pending"])').length;
    const progressPercent = Math.round((completedControls / totalControls) * 100) || 0;
    
    // Update progress bar
    document.getElementById('progress-bar').style.width = `${progressPercent}%`;
    document.getElementById('progress-bar').setAttribute('aria-valuenow', progressPercent);
    
    // Update text indicators
    document.getElementById('completed-controls').textContent = completedControls;
    document.querySelector('.assessment-progress + div .text-muted:first-child').textContent = `${progressPercent}% Completed`;
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
            return 'Pending';
    }
}