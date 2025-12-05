const API = {
    upload: '/api/upload',
    list: '/api/files',
    stats: '/api/stats',
    download: (id) => `/api/download/${id}`,
    delete: (id) => `/api/delete/${id}`
};

document.getElementById('drop-zone').ondrop = e => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
};
document.getElementById('drop-zone').ondragover = e => e.preventDefault();
document.getElementById('file-input').onchange = e => handleFiles(e.target.files);

async function handleFiles(files) {
    for (let file of files) {
        if (file.size > 100*1024*1024) {
            alert("Max 100MB per file");
            continue;
        }
        const form = new FormData();
        form.append('file', file);
        
        const res = await fetch(API.upload, { method:'POST', body:form });
        const data = await res.json();
        if (data.success) {
            loadFiles();
            loadStats(); // refresh storage bar
        } else {
            alert("Upload failed: " + (data.error || "Unknown"));
        }
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function loadFiles() {
    const res = await fetch(API.list);
    const data = await res.json();
    const container = document.getElementById('files-table');
    container.innerHTML = '';

    if (data.files.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:60px; color:#95a5a6;">
            <i class="fas fa-cloud-upload-alt fa-4x"></i><br><br>
            <h3>No files yet</h3>
            <p>Upload your first file to get started</p>
        </div>`;
        return;
    }

    const table = document.createElement('table');
    table.innerHTML = `
        <thead>
            <tr>
                <th>File</th>
                <th>Size</th>
                <th>Uploaded</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    const tbody = table.querySelector('tbody');

    data.files.forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><i class="fas fa-file"></i> ${f.name}</td>
            <td>${formatBytes(f.size)}</td>
            <td>${new Date(f.uploaded).toLocaleString()}</td>
            <td>
                <button class="action-btn download" onclick="location.href='${API.download(f.id)}'">
                    Download
                </button>
                <button class="action-btn delete" onclick="deleteFile('${f.id}')">
                    Delete
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    container.appendChild(table);
}

async function deleteFile(id) {
    if (!confirm("Delete this file permanently?")) return;
    await fetch(API.delete(id), {method:'DELETE'});
    loadFiles();
    loadStats();
}

async function loadStats() {
    try {
        const res = await fetch(API.stats);
        const s = await res.json();
        document.getElementById('used-space').textContent = formatBytes(s.used);
        document.getElementById('total-space').textContent = formatBytes(s.total);
        document.getElementById('used-percent').textContent = s.percent + '%';
        document.getElementById('usage-bar').style.width = s.percent + '%';
    } catch(e) {
        console.log("Stats not loaded");
    }
}

async function deleteFile(id) {
    if (!confirm("Delete this file permanently?")) return;
    await fetch(API.delete(id), {method:'DELETE'});
    loadFiles();
    loadStats();
}

// Load everything when page opens
loadFiles();
loadStats();
setInterval(loadStats, 10000); // refresh every 10 sec