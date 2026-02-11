function sortTable(columnIndex, tableId) {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine if column is numeric
    let isNumeric = true;
    for (let i = 0; i < Math.min(5, rows.length); i++) {
        const cellText = rows[i].cells[columnIndex].textContent.trim();
        if (cellText && isNaN(parseFloat(cellText.replace(/[^0-9.-]/g, '')))) {
            isNumeric = false;
            break;
        }
    }
    
    // Get current sort direction
    const header = table.querySelectorAll('th')[columnIndex];
    const currentDirection = header.getAttribute('data-sort-direction') || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Clear all sort indicators
    table.querySelectorAll('th').forEach(th => {
        th.removeAttribute('data-sort-direction');
    });
    
    // Set new sort direction
    header.setAttribute('data-sort-direction', newDirection);
    
    // Sort rows
    rows.sort((a, b) => {
        let aVal = a.cells[columnIndex].textContent.trim();
        let bVal = b.cells[columnIndex].textContent.trim();
        
        if (isNumeric) {
            aVal = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
            bVal = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;
            return newDirection === 'asc' ? aVal - bVal : bVal - aVal;
        } else {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
            if (newDirection === 'asc') {
                return aVal.localeCompare(bVal);
            } else {
                return bVal.localeCompare(aVal);
            }
        }
    });
    
    // Reappend sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

function filterBySignal(signalType, tableId, button) {
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    // Update button states
    const buttons = button.parentElement.getElementsByClassName('filter-btn');
    for (let btn of buttons) {
        btn.classList.remove('active');
    }
    button.classList.add('active');
    
    // Filter rows by signal
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const signal = row.getAttribute('data-signal');
        
        if (signalType === 'all' || signal === signalType) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
    
    // Update visible count
    updateVisibleCount(tableId);
}

function filterByStockPattern(patternType, tableId, button) {
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    // Update button states
    const buttons = button.parentElement.getElementsByClassName('filter-btn');
    for (let btn of buttons) {
        btn.classList.remove('active');
    }
    button.classList.add('active');
    
    // Filter rows by stock pattern
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const stockPattern = row.getAttribute('data-stock-pattern');
        
        if (patternType === 'all' || stockPattern === patternType) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
    
    // Update visible count
    updateVisibleCount(tableId);
}

function filterTable(searchInput, tableId) {
    const filter = searchInput.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    
    // Get price slider value (if exists)
    const priceSlider = document.getElementById('priceMax');
    const maxPrice = priceSlider ? parseFloat(priceSlider.value) : Infinity;
    
    // Get wishlist slider value (if exists)
    const wishlistSlider = document.getElementById('wishlistMax');
    const maxWishlist = wishlistSlider ? parseInt(wishlistSlider.value) : Infinity;
    
    rows.forEach(row => {
        // Check search filter
        const text = row.textContent.toLowerCase();
        const searchMatch = !filter || text.includes(filter);
        
        // Check price filter (if slider exists)
        let priceMatch = true;
        if (priceSlider) {
            const priceAttr = row.getAttribute('data-price');
            const price = priceAttr ? parseFloat(priceAttr.replace('£', '').trim()) : 0;
            priceMatch = price <= maxPrice;
        }
        
        // Check wishlist filter (if slider exists)
        let wishlistMatch = true;
        if (wishlistSlider) {
            const wishlistAttr = row.getAttribute('data-wishlist');
            const wishlist = wishlistAttr ? parseInt(wishlistAttr.trim()) : 0;
            wishlistMatch = wishlist <= maxWishlist;
        }
        
        // Show row only if all filters match (AND logic)
        if (searchMatch && priceMatch && wishlistMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    // Update filter badge count
    updateFilterBadge(tableId);
    
    // Update visible count
    updateVisibleCount(tableId);
}

/**
 * Filter table rows by maximum price
 * Hides rows where price exceeds the slider value
 */
function filterByPrice(tableId) {
    const slider = document.getElementById('priceMax');
    const display = document.getElementById('priceDisplay');
    const table = document.getElementById(tableId);
    
    if (!slider || !display || !table) return;
    
    const maxPrice = parseFloat(slider.value);
    
    // Update display text
    display.textContent = `Showing: £5 - £${maxPrice}`;
    
    // Get search filter value (if exists)
    const searchBox = document.getElementById('search-' + tableId);
    const searchFilter = searchBox ? searchBox.value.toLowerCase() : '';
    
    // Get wishlist filter value (if exists)
    const wishlistSlider = document.getElementById('wishlistMax');
    const maxWishlist = wishlistSlider ? parseInt(wishlistSlider.value) : Infinity;
    
    // Filter rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const priceAttr = row.getAttribute('data-price');
        const price = priceAttr ? parseFloat(priceAttr.replace('£', '').trim()) : 0;
        
        const wishlistAttr = row.getAttribute('data-wishlist');
        const wishlist = wishlistAttr ? parseInt(wishlistAttr.trim()) : 0;
        
        // Check price filter
        const priceMatch = price <= maxPrice;
        
        // Check wishlist filter
        const wishlistMatch = wishlist <= maxWishlist;
        
        // Check search filter (if active)
        const text = row.textContent.toLowerCase();
        const searchMatch = !searchFilter || text.includes(searchFilter);
        
        // Show row only if all filters match (AND logic)
        if (priceMatch && wishlistMatch && searchMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    // Update filter badge and visible count
    updateFilterBadge(tableId);
    updateVisibleCount(tableId);
}

/**
 * Filter table rows by maximum wishlist count
 * Hides rows where wishlist count exceeds the slider value
 */
function filterByWishlist(tableId) {
    const slider = document.getElementById('wishlistMax');
    const display = document.getElementById('wishlistDisplay');
    const table = document.getElementById(tableId);
    
    if (!slider || !display || !table) return;
    
    const minWishlist = parseInt(slider.getAttribute('min'));
    const maxWishlist = parseInt(slider.value);
    
    // Update display text
    display.textContent = `Showing: ${minWishlist} - ${maxWishlist}`;
    
    // Get search filter value (if exists)
    const searchBox = document.getElementById('search-' + tableId);
    const searchFilter = searchBox ? searchBox.value.toLowerCase() : '';
    
    // Get price filter value (if exists)
    const priceSlider = document.getElementById('priceMax');
    const maxPrice = priceSlider ? parseFloat(priceSlider.value) : Infinity;
    
    // Filter rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const wishlistAttr = row.getAttribute('data-wishlist');
        const wishlist = wishlistAttr ? parseInt(wishlistAttr.trim()) : 0;
        
        const priceAttr = row.getAttribute('data-price');
        const price = priceAttr ? parseFloat(priceAttr.replace('£', '').trim()) : 0;
        
        // Check wishlist filter
        const wishlistMatch = wishlist <= maxWishlist;
        
        // Check price filter
        const priceMatch = price <= maxPrice;
        
        // Check search filter (if active)
        const text = row.textContent.toLowerCase();
        const searchMatch = !searchFilter || text.includes(searchFilter);
        
        // Show row only if all filters match (AND logic)
        if (wishlistMatch && priceMatch && searchMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    // Update filter badge and visible count
    updateFilterBadge(tableId);
    updateVisibleCount(tableId);
}

function toggleAdvancedFilters(contentId, toggleButton) {
    const content = document.getElementById(contentId);
    const isExpanded = content.classList.contains('show');
    
    if (isExpanded) {
        content.classList.remove('show');
        toggleButton.classList.remove('expanded');
    } else {
        content.classList.add('show');
        toggleButton.classList.add('expanded');
    }
}

/**
 * Update filter badge count for snapshot/history pages
 * Shows badge with count when filters are active
 */
function updateFilterBadge(tableId) {
    const badge = document.getElementById('filterBadge-' + tableId);
    if (!badge) return; // Badge might not exist on all pages
    
    // Count active filters
    let activeFilters = 0;
    
    // Check search filter
    const searchBox = document.getElementById('search-' + tableId);
    if (searchBox && searchBox.value.trim() !== '') {
        activeFilters++;
    }
    
    // Check price slider (active if value < max)
    const priceSlider = document.getElementById('priceMax');
    if (priceSlider) {
        const maxValue = parseFloat(priceSlider.getAttribute('max'));
        const currentValue = parseFloat(priceSlider.value);
        if (currentValue < maxValue) {
            activeFilters++;
        }
    }
    
    // Check wishlist slider (active if value < max)
    const wishlistSlider = document.getElementById('wishlistMax');
    if (wishlistSlider) {
        const maxValue = parseInt(wishlistSlider.getAttribute('max'));
        const currentValue = parseInt(wishlistSlider.value);
        if (currentValue < maxValue) {
            activeFilters++;
        }
    }
    
    // Update badge display
    if (activeFilters > 0) {
        badge.textContent = activeFilters;
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}

/**
 * Update visible count display for a table
 * Counts non-hidden rows and updates the stats strip
 */
function updateVisibleCount(tableId) {
    const countElement = document.getElementById('visible-count-' + tableId);
    if (!countElement) return; // Stats strip might not exist on all pages
    
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    
    let visibleCount = 0;
    rows.forEach(row => {
        // Check both hidden class and style.display for backwards compatibility
        if (!row.classList.contains('hidden') && row.style.display !== 'none') {
            visibleCount++;
        }
    });
    
    countElement.textContent = visibleCount;
}
