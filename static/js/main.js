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

// Upload click
uploadArea.onclick = () => fileInput.click();

// File select
fileInput.onchange = e => handleFile(e.target.files[0]);

removeImage.onclick = () => {
    selectedFile = null;
    fileInput.value = '';
    uploadArea.classList.remove('d-none');
    imagePreview.classList.add('d-none');
    extractBtn.disabled = true;
    resultsCard.classList.add('d-none');
};

// Handle file
function handleFile(file) {
    selectedFile = file;
    previewImg.src = URL.createObjectURL(file);
    uploadArea.classList.add('d-none');
    imagePreview.classList.remove('d-none');
    extractBtn.disabled = false;
}

// Extract
extractBtn.onclick = async () => {
    loadingSpinner.classList.remove('d-none');
    extractBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const res = await fetch('/api/extract', { method: 'POST', body: formData });
        const data = await res.json();
        displayResults(data);
    } catch {
        showError("Server error");
    }

    loadingSpinner.classList.add('d-none');
    extractBtn.disabled = false;
};

// Display results
function displayResults(data) {
    errorCard.classList.add('d-none');
    resultsCard.classList.remove('d-none');

    // Best match
    document.getElementById('medicineName').innerText =
        data.best_match ? data.best_match.name : 'Not detected';

    const conf = data.best_match?.confidence || 0;
    document.getElementById('confidenceBar').style.width = conf + '%';
    document.getElementById('confidenceText').innerText = conf + '%';

    // Safety details
    if (data.safety && data.safety.found) {
        document.getElementById('safetySection').classList.remove('d-none');
        document.getElementById('safeMedicineName').innerText = data.safety.medicine_name;
        document.getElementById('medicineLabel').innerText = data.safety.label.toUpperCase();
        document.getElementById('medicineIngredients').innerText = data.safety.ingredients;
    } else {
        document.getElementById('safetySection').classList.add('d-none');
    }

    // Candidates
    const cl = document.getElementById('candidatesList');
    cl.innerHTML = '';
    (data.all_candidates || []).slice(1, 5).forEach(c => {
        cl.innerHTML += `<div class="list-group-item">${c.name} (${c.confidence}%)</div>`;
    });

    // All text
    const tl = document.getElementById('allTextList');
    tl.innerHTML = '';
    (data.all_text || []).forEach(t => {
        tl.innerHTML += `<div>${t.text} (${t.confidence}%)</div>`;
    });
}

function showError(msg) {
    errorCard.classList.remove('d-none');
    resultsCard.classList.add('d-none');
    document.getElementById('errorMessage').innerText = msg;
}

