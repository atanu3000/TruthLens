// Image upload handling
const dropZone = document.getElementById('dropZone');
const imageFile = document.getElementById('imageFile');
const imagePreview = document.getElementById('imagePreview');
const preview = document.getElementById('preview');
const removeImage = document.getElementById('removeImage');

// Handle drag and drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Handle file selection
dropZone.addEventListener('click', () => imageFile.click());

// Handle drop
dropZone.addEventListener('drop', handleDrop);
imageFile.addEventListener('change', handleFiles);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles({ target: { files } });
}

function handleFiles(e) {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            dropZone.classList.add('hidden');
            imagePreview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}

// Remove image
removeImage.addEventListener('click', () => {
    imageFile.value = '';
    preview.src = '';
    imagePreview.classList.add('hidden');
    dropZone.classList.remove('hidden');
});

// Mode switching
const textBtn = document.getElementById('textBtn');
const urlBtn = document.getElementById('urlBtn');
const imageBtn = document.getElementById('imageBtn');
const textInput = document.getElementById('textInput');
const urlInput = document.getElementById('urlInput');
const imageInput = document.getElementById('imageInput');
const modeField = document.getElementById('modeField');
const modeBtns = [textBtn, urlBtn, imageBtn];
const modeInputs = [textInput, urlInput, imageInput];

function switchMode(modeIdx) {
    modeInputs.forEach((el, i) => {
        const isActive = i === modeIdx;
        // Toggle visibility
        el.classList.toggle('hidden', !isActive);

        // Handle input elements
        const input = el.querySelector("input, textarea");
        if (input) {
            if (isActive) {
                // Active input should be required and enabled
                input.setAttribute("required", "");
                input.removeAttribute("disabled");
            } else {
                // Inactive inputs should not be required and should be disabled
                input.removeAttribute("required");
                input.setAttribute("disabled", "");
                // Clear the value when switching modes
                input.value = '';
            }
        }
    });

    // Update button styles
    modeBtns.forEach((btn, i) => {
        const isActive = i === modeIdx;
        btn.classList.toggle('bg-blue-500', isActive);
        btn.classList.toggle('text-white', isActive);
        btn.classList.toggle('bg-gray-200', !isActive);
        btn.classList.toggle('text-blue-700', !isActive);
        btn.classList.toggle('dark:bg-gray-700', !isActive);
        btn.classList.toggle('dark:text-blue-400', !isActive);
    });

    // Update mode field
    modeField.value = ['text', 'url', 'image'][modeIdx];
}

textBtn.onclick = () => switchMode(0);
urlBtn.onclick = () => switchMode(1);
imageBtn.onclick = () => switchMode(2);

// Form submission
document.getElementById('inputForm').onsubmit = async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    console.log(formData.get('image'));

    // Show loading spinner in button and disable
    const submitBtn = document.getElementById('submitBtn');
    const submitBtnText = document.getElementById('submitBtnText');
    const submitBtnSpinner = document.getElementById('submitBtnSpinner');
    submitBtn.disabled = true;
    submitBtnSpinner.classList.remove('hidden');
    submitBtnText.textContent = 'Thinking...';

    document.getElementById('result').classList.add('hidden');

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        document.getElementById('result').classList.remove('hidden');
        // verdict styling
        const verdictEl = document.getElementById('verdict');
        verdictEl.textContent = data.result || 'No verdict';
        verdictEl.className = "text-lg font-bold p-2 rounded " +
            (data.result === 'Credible' ? "bg-green-100 text-green-700" :
                data.result === 'Suspicious' ? "bg-red-100 text-red-700" :
                    "bg-yellow-100 text-yellow-700");
        // Render markdown safely
        const explanationEl = document.getElementById('explanation');
        const raw = data.explanation || 'No explanation';
        try {
            const html = marked.parse(raw);
            explanationEl.innerHTML = DOMPurify.sanitize(html);
        } catch (err) {
            explanationEl.textContent = raw;
        }
    } catch (err) {
        document.getElementById('result').classList.remove('hidden');
        document.getElementById('verdict').textContent = 'Error';
        document.getElementById('verdict').className = "text-lg font-bold p-2 rounded bg-yellow-100 text-yellow-700";
        document.getElementById('explanation').textContent = 'An error occurred.';
    } finally {
        submitBtn.disabled = false;
        submitBtnSpinner.classList.add('hidden');
        submitBtnText.textContent = 'Analyze';
    }
};