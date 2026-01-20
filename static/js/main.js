const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const previewImg = document.getElementById("previewImg");
const imagePreview = document.getElementById("imagePreview");
const extractBtn = document.getElementById("extractBtn");
const loadingSpinner = document.getElementById("loadingSpinner");
const resultsCard = document.getElementById("resultsCard");
const errorCard = document.getElementById("errorCard");

let selectedFile = null;

uploadArea.onclick = () => fileInput.click();

fileInput.onchange = e => {
    selectedFile = e.target.files[0];
    previewImg.src = URL.createObjectURL(selectedFile);
    imagePreview.classList.remove("d-none");
    uploadArea.classList.add("d-none");
    extractBtn.disabled = false;
};

extractBtn.onclick = async () => {
    loadingSpinner.classList.remove("d-none");

    const fd = new FormData();
    fd.append("file", selectedFile);

    try {
        const res = await fetch("/api/extract", { method: "POST", body: fd });
        const data = await res.json();
        renderResults(data);
    } catch {
        showError("Server error");
    }

    loadingSpinner.classList.add("d-none");
};

function renderResults(data) {
    resultsCard.classList.remove("d-none");

    document.getElementById("medicineName").innerText =
        data.best_match?.name || "Not detected";

    const conf = data.best_match?.confidence || 0;
    document.getElementById("confidenceBar").style.width = conf + "%";
    document.getElementById("confidenceText").innerText = conf + "%";

    if (data.safety?.found) {
        document.getElementById("safetySection").classList.remove("d-none");

        // Existing fields (UNCHANGED)
        document.getElementById("safeMedicineName").innerText =
            data.safety.medicine_name ?? "-";

        document.getElementById("medicineLabel").innerText =
            data.safety.label ?? "-";

        document.getElementById("medicineIngredients").innerText =
            data.safety.ingredients ?? "-";

        // 🔹 NEW synthetic features (SAFE ADDITION)
        document.getElementById("avgDosage").innerText =
            data.safety.avg_daily_dosage_mg ?? "-";

        document.getElementById("sideEffectScore").innerText =
            data.safety.side_effect_score ?? "-";

        document.getElementById("toxicityIndex").innerText =
            data.safety.toxicity_index ?? "-";

        document.getElementById("interactionCount").innerText =
            data.safety.interaction_count ?? "-";

        document.getElementById("graphDegree").innerText =
            data.safety.graph_degree_centrality ?? "-";

        document.getElementById("graphClustering").innerText =
            data.safety.graph_clustering_coeff ?? "-";
    }
}



function showError(msg) {
    errorCard.classList.remove("d-none");
    document.getElementById("errorMessage").innerText = msg;
}
