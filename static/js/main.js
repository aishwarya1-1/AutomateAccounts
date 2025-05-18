// Global variables
let currentFileId = null;
let currentReceiptId = null;

// Initialize Toast component
const toastElement = document.getElementById('alertToast');
const toast = toastElement ? new bootstrap.Toast(toastElement) : null;

// Show notification toast
function showNotification(title, message, type = 'info') {
    if (!toast) return;
    
    const alertTitle = document.getElementById('alertTitle');
    const alertMessage = document.getElementById('alertMessage');
    
    alertTitle.textContent = title;
    alertMessage.textContent = message;
    
    // Remove existing classes
    toastElement.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    
    // Add appropriate class based on type
    switch (type) {
        case 'success':
            toastElement.classList.add('bg-success', 'text-white');
            break;
        case 'error':
            toastElement.classList.add('bg-danger', 'text-white');
            break;
        case 'warning':
            toastElement.classList.add('bg-warning');
            break;
        default:
            toastElement.classList.add('bg-info', 'text-white');
    }
    
    toast.show();
}

// Update step status
function updateStepStatus(stepNumber, status) {
    const stepElement = document.getElementById(`step${stepNumber}`);
    const statusElement = document.getElementById(`step${stepNumber}-status`);
    
    if (!stepElement || !statusElement) return;
    
    // Reset classes
    stepElement.classList.remove('text-success', 'text-danger', 'text-warning');
    statusElement.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-secondary', 'bg-primary');
    
    switch (status) {
        case 'success':
            statusElement.textContent = 'Complete';
            statusElement.classList.add('bg-success');
            stepElement.classList.add('text-success');
            break;
        case 'error':
            statusElement.textContent = 'Failed';
            statusElement.classList.add('bg-danger');
            stepElement.classList.add('text-danger');
            break;
        case 'processing':
            statusElement.textContent = 'Processing';
            statusElement.classList.add('bg-primary');
            break;
        case 'waiting':
            statusElement.textContent = 'Waiting';
            statusElement.classList.add('bg-secondary');
            break;
        default:
            statusElement.textContent = status;
            statusElement.classList.add('bg-warning');
    }
}

// Reset all steps to waiting
function resetSteps() {
    updateStepStatus(1, 'waiting');
    updateStepStatus(2, 'waiting');
    updateStepStatus(3, 'waiting');
  
}

// Handle form submission
const uploadForm = document.getElementById('uploadForm');
if (uploadForm) {
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset steps
        resetSteps();
        
        const fileInput = document.getElementById('receiptFile');
        const file = fileInput.files[0];
        
        if (!file) {
            showNotification('Error', 'Please select a file to upload.', 'error');
            return;
        }
        
        if (file.type !== 'application/pdf') {
            showNotification('Invalid File', 'Please upload a PDF file.', 'error');
            return;
        }
        
        // Show processing spinner
        const spinner = document.getElementById('processingSpinner');
        spinner.classList.remove('d-none');
        document.getElementById('uploadBtn').disabled = true;
        
        // Step 1: Upload file
        updateStepStatus(1, 'processing');
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            let uploadResult;
            try {
                const uploadResponse = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                uploadResult = await uploadResponse.json();
                
                if (!uploadResponse.ok || !uploadResult.success) {
                    throw new Error(uploadResult.error || 'Failed to upload file');
                }
                
                updateStepStatus(1, 'success');
                showNotification('Upload Complete', 'File uploaded successfully', 'success');
                
                // Save the file ID for subsequent steps
                currentFileId = uploadResult.file_id;
            } catch (uploadError) {
                console.error('Error uploading file:', uploadError);
                showNotification('Upload Error', 'There was an error uploading the file. Please try again.', 'error');
                throw uploadError;
            }
            
            // Step 2: Validate PDF
            updateStepStatus(2, 'processing');
            
            const validateResponse = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_id: currentFileId })
            });
            
            const validateResult = await validateResponse.json();
            
            if (!validateResponse.ok || !validateResult.success) {
                throw new Error(validateResult.error || 'Failed to validate PDF');
            }
            
            if (!validateResult.is_valid) {
                updateStepStatus(2, 'error');
                showNotification('Invalid PDF', validateResult.error || 'The uploaded file is not a valid PDF', 'error');
                return;
            }
            
            updateStepStatus(2, 'success');
            showNotification('Validation Complete', 'PDF validation successful', 'success');
            
            // Step 3: Process receipt
            updateStepStatus(3, 'processing');
            
          
            
        } catch (error) {
            console.error('Processing error:', error);
            showNotification('Error', error.message || 'An error occurred during processing', 'error');
        } finally {
            // Hide spinner and re-enable button
            spinner.classList.add('d-none');
            document.getElementById('uploadBtn').disabled = false;
        }
    });
}



// Document ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the page
    resetSteps();
    

});