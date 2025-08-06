// Continuation of OrdersManager class methods

    // UI Helper Methods
    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const applyButton = document.getElementById('applyFilters');
        
        this.isLoading = show;
        
        if (show) {
            loadingIndicator.classList.remove('hidden');
            applyButton.disabled = true;
            applyButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Applying...';
        } else {
            loadingIndicator.classList.add('hidden');
            applyButton.disabled = false;
            applyButton.innerHTML = '<i class="fas fa-search mr-2"></i>Apply Filters';
        }
    }
    
    showNoOrdersMessage() {
        document.getElementById('ordersTableContainer').classList.add('hidden');
        document.getElementById('noOrdersMessage').classList.remove('hidden');
    }
    
    hideNoOrdersMessage() {
        document.getElementById('ordersTableContainer').classList.remove('hidden');
        document.getElementById('noOrdersMessage').classList.add('hidden');
    }
    
    updateStats(stats) {
        // Update table title
        const title = document.getElementById('ordersTableTitle');
        title.innerHTML = `
            <i class="fas fa-list text-energy-primary mr-2"></i>
            Orders (${stats.total})
        `;
        
        // Update filter results stats
        const totalRevenue = document.querySelector('#totalRevenue span');
        const avgOrderValue = document.querySelector('#avgOrderValue span');
        const resultsStats = document.getElementById('filterResultsStats');
        
        if (stats.total > 0) {
            const avgValue = stats.total_revenue / stats.total;
            totalRevenue.textContent = `$${stats.total_revenue.toFixed(2)}`;
            avgOrderValue.textContent = `$${avgValue.toFixed(2)} avg`;
            resultsStats.classList.remove('hidden');
        } else {
            resultsStats.classList.add('hidden');
        }
        
        // Update stats cards if they exist
        this.updateStatsCards(stats);
    }
    
    updateStatsCards(stats) {
        // Update the stats cards at the top
        const statsSelectors = [
            '.grid .bg-white:nth-child(1) .text-2xl', // Total orders
            '.grid .bg-white:nth-child(2) .text-2xl', // Pending
            '.grid .bg-white:nth-child(3) .text-2xl', // Shipped  
            '.grid .bg-white:nth-child(4) .text-2xl'  // Delivered
        ];
        
        const statsValues = [stats.total, stats.pending, stats.shipped, stats.delivered];
        
        statsSelectors.forEach((selector, index) => {
            const element = document.querySelector(selector);
            if (element && statsValues[index] !== undefined) {
                element.textContent = statsValues[index].toLocaleString();
            }
        });
    }
    
    updateFilterSummary(stats) {
        const hasFilters = this.hasActiveFilters();
        const filterSummary = document.getElementById('filterSummary');
        const activeFiltersText = document.getElementById('activeFiltersText');
        
        if (hasFilters) {
            filterSummary.classList.remove('hidden');
            activeFiltersText.textContent = this.buildFilterSummaryText(stats);
        } else {
            filterSummary.classList.add('hidden');
        }
    }
    
    buildFilterSummaryText(stats) {
        const filters = [];
        
        if (this.currentFilters.status !== 'all') {
            filters.push(`Status: ${this.currentFilters.status}`);
        }
        
        if (this.currentFilters.date_from || this.currentFilters.date_to) {
            if (this.currentFilters.date_from && this.currentFilters.date_to) {
                filters.push(`Date: ${this.currentFilters.date_from} to ${this.currentFilters.date_to}`);
            } else if (this.currentFilters.date_from) {
                filters.push(`From: ${this.currentFilters.date_from}`);
            } else {
                filters.push(`Until: ${this.currentFilters.date_to}`);
            }
        }
        
        if (this.currentFilters.search) {
            filters.push(`Search: "${this.currentFilters.search}"`);
        }
        
        return `Active filters: ${filters.join(', ')} • ${stats.total} orders found`;
    }
    
    hasActiveFilters() {
        return this.currentFilters.status !== 'all' || 
               this.currentFilters.date_from || 
               this.currentFilters.date_to || 
               this.currentFilters.search.trim();
    }
    
    updateFilterStatus() {
        const filterStatus = document.getElementById('filterStatus');
        const statusText = filterStatus.querySelector('span');
        
        if (this.hasActiveFilters()) {
            statusText.textContent = 'Applying filters...';
        } else {
            statusText.textContent = 'Showing all orders';
        }
    }
    
    updateSearchClearButton(value) {
        const clearButton = document.getElementById('clearSearch');
        if (value.trim()) {
            clearButton.classList.remove('hidden');
        } else {
            clearButton.classList.add('hidden');
        }
    }
    
    animateNewContent() {
        // Add entrance animations to new rows
        const rows = document.querySelectorAll('.animate-fadeIn, .animate-slideUp');
        rows.forEach((row, index) => {
            row.style.opacity = '0';
            row.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                row.style.transition = 'all 0.3s ease-out';
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }
    
    showSuccessMessage(message) {
        // You could implement a toast notification system here
        console.log('Success:', message);
    }
    
    showErrorMessage(message) {
        // You could implement error notification here
        console.error('Error:', message);
        
        // For now, show a simple alert
        if (message !== 'Failed to filter orders. Please try again.') {
            alert(`Error: ${message}`);
        }
    }
}

// Global functions for backward compatibility and event handlers
let ordersManager;

// Initialize the orders manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    ordersManager = new OrdersManager();
});

// Global utility functions
function toggleFilterPanel() {
    const panel = document.getElementById('filterPanel');
    const button = document.getElementById('toggleFilters');
    const icon = button.querySelector('i');
    
    panel.classList.toggle('hidden');
    
    if (panel.classList.contains('hidden')) {
        icon.className = 'fas fa-chevron-down text-sm';
    } else {
        icon.className = 'fas fa-chevron-up text-sm';
    }
}

function applyQuickFilter(period) {
    if (!ordersManager) return;
    
    const today = new Date();
    let startDate = '';
    
    switch (period) {
        case 'today':
            startDate = today.toISOString().split('T')[0];
            ordersManager.currentFilters.date_from = startDate;
            ordersManager.currentFilters.date_to = startDate;
            break;
            
        case 'week':
            const weekAgo = new Date(today);
            weekAgo.setDate(today.getDate() - 7);
            ordersManager.currentFilters.date_from = weekAgo.toISOString().split('T')[0];
            ordersManager.currentFilters.date_to = today.toISOString().split('T')[0];
            break;
            
        case 'month':
            const monthAgo = new Date(today);
            monthAgo.setMonth(today.getMonth() - 1);
            ordersManager.currentFilters.date_from = monthAgo.toISOString().split('T')[0];
            ordersManager.currentFilters.date_to = today.toISOString().split('T')[0];
            break;
    }
    
    // Update UI inputs
    document.getElementById('dateFrom').value = ordersManager.currentFilters.date_from;
    document.getElementById('dateTo').value = ordersManager.currentFilters.date_to;
    
    // Apply filters
    ordersManager.applyFilters();
}

function clearSearch() {
    if (!ordersManager) return;
    
    document.getElementById('searchInput').value = '';
    ordersManager.currentFilters.search = '';
    ordersManager.updateSearchClearButton('');
    ordersManager.debouncedApplyFilters();
}

function clearAllFilters() {
    if (!ordersManager) return;
    
    // Reset filters
    ordersManager.currentFilters = {
        status: 'all',
        date_from: '',
        date_to: '',
        search: ''
    };
    
    // Reset UI
    document.getElementById('statusFilter').value = 'all';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('searchInput').value = '';
    ordersManager.updateSearchClearButton('');
    
    // Apply filters
    ordersManager.applyFilters();
}

function applyFilters() {
    if (ordersManager) {
        ordersManager.applyFilters();
    }
}

// Legacy functions for existing functionality
function toggleStatusMenu(orderId) {
    const menu = document.getElementById(`status-menu-${orderId}`);
    const allMenus = document.querySelectorAll('[id^="status-menu-"]');
    
    // Close all other menus
    allMenus.forEach(m => {
        if (m.id !== `status-menu-${orderId}`) {
            m.classList.add('hidden');
        }
    });
    
    // Toggle current menu
    menu.classList.toggle('hidden');
}

async function updateOrderStatus(orderId, newStatus) {
    const confirmMessage = `Are you sure you want to change this order to "${newStatus}"?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // Close the menu
    document.getElementById(`status-menu-${orderId}`).classList.add('hidden');
    
    // Show loading state
    const button = document.querySelector(`button[onclick="toggleStatusMenu(${orderId})"]`);
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin text-sm"></i>';
    button.disabled = true;
    
    try {
        const response = await fetch(`/admin/orders/update_status/${orderId}?status=${newStatus}`, {
            method: 'GET',
        });
        
        if (response.ok) {
            // Refresh the current filtered view instead of full page reload
            if (ordersManager) {
                await ordersManager.applyFilters();
            } else {
                window.location.reload();
            }
        } else {
            throw new Error('Failed to update status');
        }
    } catch (error) {
        console.error('Error updating order status:', error);
        alert('Failed to update order status. Please try again.');
        
        // Restore button
        button.innerHTML = originalContent;
        button.disabled = false;
    }
}

function viewOrder(orderId) {
    // This would typically fetch order details via AJAX
    // For now, show a placeholder modal
    const modal = document.getElementById('orderModal');
    const details = document.getElementById('orderDetails');
    
    details.innerHTML = `
        <div class="text-center py-8">
            <i class="fas fa-spinner fa-spin text-4xl text-energy-primary mb-4"></i>
            <p class="text-gray-600">Loading order details for #${orderId}...</p>
        </div>
    `;
    
    modal.classList.remove('hidden');
    
    // Simulate loading delay
    setTimeout(() => {
        details.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h3 class="text-lg font-bold text-gray-800 mb-3">Customer Information</h3>
                        <div class="space-y-2 text-sm">
                            <p><strong>Name:</strong> <span class="text-gray-600">Loading...</span></p>
                            <p><strong>Phone:</strong> <span class="text-gray-600">Loading...</span></p>
                            <p><strong>Address:</strong> <span class="text-gray-600">Loading...</span></p>
                        </div>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-gray-800 mb-3">Order Summary</h3>
                        <div class="space-y-2 text-sm">
                            <p><strong>Order ID:</strong> #${orderId}</p>
                            <p><strong>Status:</strong> <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">Pending</span></p>
                            <p><strong>Total:</strong> <span class="text-green-600 font-bold">$0.00</span></p>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-bold text-gray-800 mb-3">Order Items</h3>
                    <div class="bg-gray-50 rounded-lg p-4">
                        <p class="text-gray-600">Order details would be loaded here...</p>
                    </div>
                </div>
            </div>
        `;
    }, 1000);
}

function closeModal() {
    document.getElementById('orderModal').classList.add('hidden');
}

// Event listeners for modal and dropdowns
document.getElementById('orderModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('[onclick^="toggleStatusMenu"]')) {
        const menus = document.querySelectorAll('[id^="status-menu-"]');
        menus.forEach(menu => menu.classList.add('hidden'));
    }
});