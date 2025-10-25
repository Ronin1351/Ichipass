// Ichipass Scanner - Frontend Application Logic

// State Management
const state = {
    currentScan: null,
    scanResults: [],
    settings: {
        threads: 8,
        cacheDir: './cache',
        logLevel: 'INFO'
    }
};

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Set default dates
    const today = new Date();
    const sixMonthsAgo = new Date(today);
    sixMonthsAgo.setMonth(today.getMonth() - 6);

    document.getElementById('startDate').valueAsDate = sixMonthsAgo;
    document.getElementById('endDate').valueAsDate = today;

    // Load settings from localStorage
    loadSettings();

    // Load stats
    updateStats();

    // Setup form submission
    document.getElementById('scanForm').addEventListener('submit', handleScanSubmit);

    console.log('Ichipass Scanner initialized');
}

// Section Navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });

    // Remove active class from all nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected section
    const sectionMap = {
        'scanner': 'scannerSection',
        'results': 'resultsSection',
        'settings': 'settingsSection',
        'docs': 'docsSection'
    };

    const sectionId = sectionMap[sectionName];
    if (sectionId) {
        document.getElementById(sectionId).style.display = 'block';

        // Add active class to clicked button
        event.target.classList.add('active');
    }
}

// Handle Scan Form Submission
async function handleScanSubmit(event) {
    event.preventDefault();

    // Gather form data
    const scanConfig = {
        tickers: document.getElementById('tickers').value.split(',').map(t => t.trim()),
        start: document.getElementById('startDate').value,
        end: document.getElementById('endDate').value,
        tenkan: parseInt(document.getElementById('tenkan').value),
        kijun: parseInt(document.getElementById('kijun').value),
        senkou: parseInt(document.getElementById('senkou').value),
        lookback: parseInt(document.getElementById('lookback').value),
        minPrice: parseFloat(document.getElementById('minPrice').value),
        minVolume: parseFloat(document.getElementById('minVolume').value),
        strictCross: document.getElementById('strictCross').checked,
        threads: parseInt(document.getElementById('threads').value)
    };

    // Validate
    if (scanConfig.tickers.length === 0 || scanConfig.tickers[0] === '') {
        showNotification('Please enter at least one ticker symbol', 'error');
        return;
    }

    // Start scan
    await startScan(scanConfig);
}

// Start Scan
async function startScan(config) {
    try {
        // Update UI
        updateProgress(0, 'Initializing scan...');
        document.getElementById('scanActions').style.display = 'block';

        // Call API
        const response = await fetch('/api/scans', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        state.currentScan = data.scan_id;

        // Poll for results
        pollScanStatus(data.scan_id);

    } catch (error) {
        console.error('Scan failed:', error);
        showNotification('Scan failed: ' + error.message, 'error');
        updateProgress(0, 'Scan failed');
    }
}

// Poll Scan Status
async function pollScanStatus(scanId) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/scans/${scanId}`);
            const data = await response.json();

            // Update progress
            const progress = data.progress || 0;
            updateProgress(progress, data.status || 'Processing...');

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                handleScanComplete(data);
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                showNotification('Scan failed', 'error');
                updateProgress(0, 'Scan failed');
            }

            // Update details
            if (data.details) {
                document.getElementById('scanDetails').textContent = data.details;
            }

        } catch (error) {
            console.error('Error polling scan status:', error);
            clearInterval(pollInterval);
        }
    }, 1000);
}

// Handle Scan Complete
function handleScanComplete(data) {
    updateProgress(100, 'Scan completed!');
    state.scanResults = data.results || [];

    // Display results
    displayResults(state.scanResults);

    // Update stats
    updateStats();

    // Show notification
    showNotification(`Scan completed! Found ${state.scanResults.length} matches`, 'success');

    // Automatically switch to results tab
    setTimeout(() => {
        showSection('results');
    }, 1500);
}

// Display Results
function displayResults(results) {
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsTable = document.getElementById('resultsTable');
    const resultsBody = document.getElementById('resultsBody');

    if (!results || results.length === 0) {
        resultsContainer.style.display = 'block';
        resultsTable.style.display = 'none';
        return;
    }

    resultsContainer.style.display = 'none';
    resultsTable.style.display = 'block';

    // Clear existing rows
    resultsBody.innerHTML = '';

    // Add rows
    results.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${result.symbol}</strong></td>
            <td>${result.date_yesterday}</td>
            <td>$${result.close_y.toFixed(2)}</td>
            <td>$${result.cloud_top_y.toFixed(2)}</td>
            <td><span class="badge badge-success">${result.distance_pct.toFixed(2)}%</span></td>
            <td>$${formatNumber(result.avg_dollar_vol_20)}</td>
            <td>
                <button class="btn" onclick="viewDetails('${result.symbol}')" style="padding: 0.25rem 0.75rem;">
                    View
                </button>
            </td>
        `;
        resultsBody.appendChild(row);
    });
}

// Update Progress
function updateProgress(percent, status) {
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');

    progressBar.style.width = percent + '%';
    progressBar.textContent = percent + '%';
    statusText.textContent = status;
}

// Update Stats
function updateStats() {
    // Get stats from localStorage or API
    const stats = JSON.parse(localStorage.getItem('scanStats') || '{}');

    document.getElementById('totalScans').textContent = stats.totalScans || 0;
    document.getElementById('matchesFound').textContent = stats.matchesFound || 0;
    document.getElementById('symbolsTracked').textContent = stats.symbolsTracked || 0;
    document.getElementById('successRate').textContent = (stats.successRate || 0) + '%';
}

// Apply Ichimoku Preset
function applyPreset(presetName) {
    const presets = {
        'default': { tenkan: 9, kijun: 26, senkou: 52 },
        'fast': { tenkan: 7, kijun: 22, senkou: 44 },
        'slow': { tenkan: 10, kijun: 30, senkou: 60 }
    };

    const preset = presets[presetName];
    if (preset) {
        document.getElementById('tenkan').value = preset.tenkan;
        document.getElementById('kijun').value = preset.kijun;
        document.getElementById('senkou').value = preset.senkou;

        showNotification(`Applied ${presetName} preset`, 'success');
    }
}

// Save Settings
function saveSettings() {
    state.settings = {
        threads: parseInt(document.getElementById('threads').value),
        cacheDir: document.getElementById('cacheDir').value,
        logLevel: document.getElementById('logLevel').value
    };

    localStorage.setItem('settings', JSON.stringify(state.settings));
    showNotification('Settings saved successfully', 'success');
}

// Load Settings
function loadSettings() {
    const savedSettings = localStorage.getItem('settings');
    if (savedSettings) {
        state.settings = JSON.parse(savedSettings);

        document.getElementById('threads').value = state.settings.threads;
        document.getElementById('cacheDir').value = state.settings.cacheDir;
        document.getElementById('logLevel').value = state.settings.logLevel;
    }
}

// Clear Cache
async function clearCache() {
    if (!confirm('Are you sure you want to clear the cache?')) {
        return;
    }

    try {
        const response = await fetch('/api/cache', {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Cache cleared successfully', 'success');
            document.getElementById('cacheSize').textContent = '0 MB';
        } else {
            throw new Error('Failed to clear cache');
        }
    } catch (error) {
        console.error('Error clearing cache:', error);
        showNotification('Error clearing cache', 'error');
    }
}

// Download Results
function downloadResults() {
    if (!state.scanResults || state.scanResults.length === 0) {
        showNotification('No results to download', 'warning');
        return;
    }

    // Convert to CSV
    const csv = convertToCSV(state.scanResults);

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ichipass_results_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    showNotification('Results downloaded', 'success');
}

// Convert to CSV
function convertToCSV(data) {
    if (!data || data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');

    const csvRows = data.map(row => {
        return headers.map(header => {
            const value = row[header];
            // Escape quotes and wrap in quotes if contains comma
            return typeof value === 'string' && value.includes(',')
                ? `"${value.replace(/"/g, '""')}"`
                : value;
        }).join(',');
    });

    return [csvHeaders, ...csvRows].join('\n');
}

// Cancel Scan
function cancelScan() {
    if (!state.currentScan) return;

    if (confirm('Are you sure you want to cancel the current scan?')) {
        fetch(`/api/scans/${state.currentScan}`, {
            method: 'DELETE'
        }).then(() => {
            showNotification('Scan cancelled', 'warning');
            updateProgress(0, 'Scan cancelled');
            state.currentScan = null;
        });
    }
}

// View Symbol Details
function viewDetails(symbol) {
    showNotification(`Viewing details for ${symbol}`, 'info');
    // TODO: Implement detailed view with charts
}

// Show Notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-primary);
        padding: var(--spacing-md);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-convex);
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
    `;

    const colors = {
        'success': 'var(--success)',
        'error': 'var(--danger)',
        'warning': 'var(--warning)',
        'info': 'var(--accent-primary)'
    };

    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
            <div style="width: 4px; height: 40px; background: ${colors[type]}; border-radius: 2px;"></div>
            <div style="flex: 1;">
                <p style="color: var(--text-primary); font-weight: 500;">${message}</p>
            </div>
        </div>
    `;

    document.body.appendChild(notification);

    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Format Number
function formatNumber(num) {
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(2) + 'B';
    } else if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
