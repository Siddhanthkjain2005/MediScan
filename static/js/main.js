// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const removeImage = document.getElementById('removeImage');
const extractBtn = document.getElementById('extractBtn');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsCard = document.getElementById('resultsCard');
const errorCard = document.getElementById('errorCard');

let selectedFile = null;

// Upload area click
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e. dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// File input change
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Remove image
removeImage.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    uploadArea.classList.remove('d-none');
    imagePreview.classList.add('d-none');
    extractBtn.disabled = true;
    resultsCard.classList.add('d-none');
    errorCard.classList.add('d-none');
});

// Extract button
extractBtn.addEventListener('click', extractMedicine);

// Handle file selection
function handleFile(file) {
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
    
    if (!allowedTypes.includes(file.type)) {
        showError('Invalid file type. Please upload an image.');
        return;
    }
    
    // Validate file size (16MB)
    if (file.size > 16 * 1024 * 1024) {
        showError('File too large. Maximum size is 16MB.');
        return;
    }
    
    selectedFile = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        uploadArea.classList.add('d-none');
        imagePreview.classList.remove('d-none');
        extractBtn. disabled = false;
    };
    reader.readAsDataURL(file);
    
    // Hide previous results
    resultsCard.classList.add('d-none');
    errorCard.classList.add('d-none');
}

// Extract medicine name
async function extractMedicine() {
    if (!selectedFile) return;
    
    // Show loading
    extractBtn.disabled = true;
    loadingSpinner.classList.remove('d-none');
    resultsCard.classList.add('d-none');
    errorCard.classList.add('d-none');
    
    // Create form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
        } else {
            showError(data.error || 'An error occurred');
        }
    } catch (error) {
        showError('Network error:  ' + error.message);
    } finally {
        loadingSpinner.classList.add('d-none');
        extractBtn.disabled = false;
    }
}

// Display results
function displayResults(data) {
    // Hide error card
    errorCard.classList. add('d-none');
    
    // Show best match
    if (data.best_match) {
        document.getElementById('medicineName').textContent = data.best_match. name;
        document.getElementById('confidenceBar').style.width = data.best_match.confidence + '%';
        document.getElementById('confidenceText').textContent = data.best_match.confidence + '%';
        
        // Color code confidence
        const confidenceBar = document.getElementById('confidenceBar');
        if (data.best_match.confidence >= 70) {
            confidenceBar. className = 'progress-bar bg-success';
        } else if (data.best_match.confidence >= 50) {
            confidenceBar. className = 'progress-bar bg-warning';
        } else {
            confidenceBar.className = 'progress-bar bg-danger';
        }
    } else {
        document.getElementById('medicineName').textContent = 'No medicine name detected';
        document.getElementById('confidenceBar').style.width = '0%';
        document.getElementById('confidenceText').textContent = '0%';
    }
    
    // Show other candidates
    const candidatesList = document.getElementById('candidatesList');
    candidatesList. innerHTML = '';
    
    if (data.all_candidates && data.all_candidates.length > 1) {
        data.all_candidates.slice(1, 5).forEach((candidate, index) => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${candidate.name}</strong>
                        <br>
                        <small class="text-muted">Position: #${candidate.position}</small>
                    </div>
                    <span class="badge bg-primary rounded-pill">${candidate.confidence}%</span>
                </div>
            `;
            candidatesList.appendChild(item);
        });
    } else {
        candidatesList.innerHTML = '<div class="list-group-item text-muted">No other candidates</div>';
    }
    
    // Show all detected text
    const allTextList = document.getElementById('allTextList');
    allTextList.innerHTML = '';
    
    if (data.all_text && data. all_text.length > 0) {
        data.all_text.forEach((item, index) => {
            const textItem = document.createElement('div');
            textItem.className = 'mb-2 pb-2 border-bottom';
            textItem.innerHTML = `
                <span class="badge bg-secondary">${index + 1}</span>
                <strong>${item.text}</strong>
                <span class="text-muted float-end">${item.confidence}%</span>
            `;
            allTextList.appendChild(textItem);
        });
    } else {
        allTextList.innerHTML = '<p class="text-muted mb-0">No text detected</p>';
    }
    
    // Show results card
    resultsCard.classList.remove('d-none');
}

// Show error
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    errorCard.classList.remove('d-none');
    resultsCard.classList.add('d-none');
}