// Cloud Storage File Manager
class CloudStorage {
    constructor() {
        this.init();
    }
    
    init() {
        // Load initial data
        this.loadStorageStats();
        this.loadNodes();
        this.loadFiles();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup drag and drop
        this.setupDragAndDrop();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.loadStorageStats();
            this.loadFiles();
        }, 30000);
    }
    
    setupEventListeners() {
        // Browse button
        document.getElementById('browse-btn')?.addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        
        // File input change
        document.getElementById('file-input')?.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                Array.from(e.target.files).forEach(file => {
                    this.uploadFile(file);
                });
            }
        });
        
        // Refresh stats button
        document.getElementById('refresh-stats')?.addEventListener('click', () => {
            this.loadStorageStats();
            this.loadNodes();
            this.loadFiles();
            this.showNotification('Data refreshed', 'success');
        });
        
        // Search input
        document.getElementById('search-input')?.addEventListener('input', (e) => {
            this.filterFiles(e.target.value.toLowerCase());
        });
    }
    
    setupDragAndDrop() {
        const dropZone = document.getElementById('drop-zone');
        if (!dropZone) return;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop zone
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            }, false);
        });
        
        // Handle dropped files
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                Array.from(files).forEach(file => {
                    this.uploadFile(file);
                });
            }
        }, false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    async uploadFile(file) {
        // Check file size (100MB limit)
        if (file.size > 100 * 1024 * 1024) {
            this.showNotification(`File "${file.name}" exceeds 100MB limit`, 'error');
            return;
        }
        
        // Show upload progress
        this.showUploadProgress(file);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            // Simulate progress (in real app, use XMLHttpRequest for progress events)
            let progress = 0;
            const progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += 10;
                    this.updateUploadProgress(progress, file);
                }
            }, 200);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            clearInterval(progressInterval);
            
            const data = await response.json();
            
            if (response.ok) {
                this.updateUploadProgress(100, file);
                this.showNotification(`"${file.name}" uploaded successfully!`, 'success');
                
                // Refresh data
                setTimeout(() => {
                    this.loadStorageStats();
                    this.loadFiles();
                    this.hideUploadProgress();
                }, 1000);
            } else {
                this.showNotification(`Upload failed: ${data.error}`, 'error');
                this.hideUploadProgress();
            }
        } catch (error) {
            this.showNotification(`Upload error: ${error.message}`, 'error');
            this.hideUploadProgress();
        }
    }
    
    showUploadProgress(file) {
        const progressDiv = document.getElementById('upload-progress');
        const filenameSpan = document.getElementById('progress-filename');
        const sizeSpan = document.getElementById('progress-size');
        
        if (progressDiv && filenameSpan && sizeSpan) {
            filenameSpan.textContent = file.name;
            sizeSpan.textContent = this.formatFileSize(file.size);
            progressDiv.style.display = 'block';
        }
    }
    
    updateUploadProgress(percent, file) {
        const progressFill = document.getElementById('progress-fill');
        const progressPercent = document.getElementById('progress-percent');
        
        if (progressFill && progressPercent) {
            progressFill.style.width = `${percent}%`;
            progressPercent.textContent = `${percent}%`;
        }
    }
    
    hideUploadProgress() {
        const progressDiv = document.getElementById('upload-progress');
        if (progressDiv) {
            setTimeout(() => {
                progressDiv.style.display = 'none';
                document.getElementById('progress-fill').style.width = '0%';
                document.getElementById('progress-percent').textContent = '0%';
            }, 500);
        }
    }
    
    async loadStorageStats() {
        try {
            const response = await fetch('/api/storage/stats');
            const data = await response.json();
            
            if (response.ok) {
                this.updateStorageUI(data);
            }
        } catch (error) {
            console.error('Error loading storage stats:', error);
        }
    }
    
    updateStorageUI(data) {
        // Update header stats
        const totalStorage = document.getElementById('total-storage');
        const usedStorage = document.getElementById('used-storage');
        
        if (totalStorage) totalStorage.textContent = data.total_gb;
        if (usedStorage) usedStorage.textContent = data.used_gb;
        
        // Update meters
        const usedPercent = data.usage_percent || 0;
        const availablePercent = 100 - usedPercent;
        
        document.getElementById('used-meter').style.width = `${usedPercent}%`;
        document.getElementById('available-meter').style.width = `${availablePercent}%`;
        
        // Update text
        document.getElementById('total-text').textContent = data.total_gb;
        document.getElementById('used-text').textContent = data.used_gb;
        document.getElementById('available-text').textContent = data.available_gb;
        
        document.getElementById('used-percent').textContent = `${Math.round(usedPercent)}%`;
        document.getElementById('available-percent').textContent = `${Math.round(availablePercent)}%`;
    }
    
    async loadNodes() {
        try {
            const response = await fetch('/api/nodes');
            const data = await response.json();
            
            if (response.ok) {
                this.renderNodes(data.nodes);
            }
        } catch (error) {
            console.error('Error loading nodes:', error);
        }
    }
    
    renderNodes(nodes) {
        const container = document.getElementById('nodes-container');
        if (!container) return;
        
        if (!nodes || nodes.length === 0) {
            container.innerHTML = '<div class="empty-state">No nodes available</div>';
            return;
        }
        
        container.innerHTML = nodes.map(node => `
            <div class="node-card ${node.is_active ? 'active' : 'inactive'}">
                <div class="node-header">
                    <div class="node-id">
                        <i class="fas fa-server"></i>
                        ${node.node_id}
                    </div>
                    <div class="node-status ${node.is_active ? 'active' : 'inactive'}">
                        ${node.is_active ? 'Active' : 'Inactive'}
                    </div>
                </div>
                <div class="node-stats">
                    <div class="node-stat">
                        <span class="stat-label">Capacity:</span>
                        <span class="stat-value">${node.capacity_gb}</span>
                    </div>
                    <div class="node-stat">
                        <span class="stat-label">Used:</span>
                        <span class="stat-value">${node.used_gb}</span>
                    </div>
                    <div class="node-stat">
                        <span class="stat-label">Available:</span>
                        <span class="stat-value">${node.available_gb}</span>
                    </div>
                    <div class="node-stat">
                        <span class="stat-label">Files:</span>
                        <span class="stat-value">${node.files_count || 0}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    async loadFiles() {
        try {
            const response = await fetch('/api/files');
            const data = await response.json();
            
            if (response.ok) {
                this.renderFiles(data.files || []);
            }
        } catch (error) {
            console.error('Error loading files:', error);
            this.renderFiles([]);
        }
    }
    
    renderFiles(files) {
        const tbody = document.getElementById('files-table-body');
        if (!tbody) return;
        
        if (!files || files.length === 0) {
            tbody.innerHTML = `
                <tr id="no-files">
                    <td colspan="5" class="empty-state">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <p>No files uploaded yet</p>
                        <p class="subtext">Upload your first file to get started</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        // Remove "no files" row if it exists
        const noFilesRow = document.getElementById('no-files');
        if (noFilesRow) noFilesRow.remove();
        
        // Calculate totals
        let totalSize = 0;
        let fileCount = 0;
        
        const rows = files.map(file => {
            totalSize += file.size || 0;
            fileCount++;
            
            const fileExt = this.getFileExtension(file.filename);
            const fileIcon = this.getFileIcon(fileExt);
            
            return `
                <tr data-filename="${file.filename.toLowerCase()}">
                    <td>
                        <div class="file-name">
                            <i class="fas ${fileIcon} file-icon"></i>
                            <span>${file.filename}</span>
                        </div>
                    </td>
                    <td>${this.formatFileSize(file.size || 0)}</td>
                    <td>${this.formatDate(file.uploaded_at)}</td>
                    <td>
                        <span class="node-badge">${file.node_id || 'Multiple'}</span>
                    </td>
                    <td>
                        <div class="file-actions">
                            <button class="file-action download" 
                                    onclick="storage.downloadFile('${file.original_filename || file.filename}')"
                                    title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="file-action delete" 
                                    onclick="storage.deleteFile('${file.original_filename || file.filename}')"
                                    title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = rows;
        
        // Update footer
        document.getElementById('files-count').textContent = fileCount;
        document.getElementById('total-size').textContent = this.formatFileSize(totalSize);
    }
    
    filterFiles(searchTerm) {
        const rows = document.querySelectorAll('#files-table-body tr');
        rows.forEach(row => {
            const filename = row.getAttribute('data-filename') || '';
            if (filename.includes(searchTerm) || searchTerm === '') {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    async downloadFile(filename) {
        try {
            this.showNotification(`Preparing download: ${filename}`, 'info');
            
            const response = await fetch(`/api/download/${encodeURIComponent(filename)}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification(`Download started: ${filename}`, 'success');
            } else {
                const data = await response.json();
                this.showNotification(`Download failed: ${data.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Download error: ${error.message}`, 'error');
        }
    }
    
    async deleteFile(filename) {
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/delete/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification(`"${filename}" deleted successfully`, 'success');
                this.loadStorageStats();
                this.loadFiles();
            } else {
                this.showNotification(`Delete failed: ${data.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Delete error: ${error.message}`, 'error');
        }
    }
    
    // Utility Methods
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    getFileExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    }
    
    getFileIcon(extension) {
        const icons = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word',
            'docx': 'fa-file-word',
            'xls': 'fa-file-excel',
            'xlsx': 'fa-file-excel',
            'ppt': 'fa-file-powerpoint',
            'pptx': 'fa-file-powerpoint',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'gif': 'fa-file-image',
            'zip': 'fa-file-archive',
            'rar': 'fa-file-archive',
            'txt': 'fa-file-alt',
            'mp3': 'fa-file-audio',
            'mp4': 'fa-file-video',
            'mov': 'fa-file-video'
        };
        
        return icons[extension] || 'fa-file';
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;
        
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas ${icons[type] || 'fa-info-circle'}"></i>
            <div class="notification-content">
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideInRight 0.3s ease reverse';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
}

// Initialize the application
const storage = new CloudStorage();

// Make storage globally available for onclick handlers
window.storage = storage;