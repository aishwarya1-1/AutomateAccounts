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
    document.getElementById('processingResults').style.display = 'none';
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
            
            const processResponse = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_id: currentFileId })
            });
            
            const processResult = await processResponse.json();
            
            if (!processResponse.ok || !processResult.success) {
                throw new Error(processResult.error || 'Failed to process receipt');
            }
            
            updateStepStatus(3, 'success');
            showNotification('Processing Complete', 'Receipt data extracted successfully', 'success');
            
            // Save the receipt ID
            currentReceiptId = processResult.receipt_id;
            
            // Display extracted data
            displayReceiptData(processResult.receipt_data);
            
            // Reload the receipts table
            loadReceipts();
            
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

// Display extracted receipt data
function displayReceiptData(receiptData) {
    const resultsSection = document.getElementById('processingResults');
    if (!resultsSection) return;
    
    // Show the results section
    resultsSection.style.display = 'block';
    
    // Populate receipt details
    document.getElementById('merchantName').textContent = receiptData.merchant_name || 'Not available';
    
    const purchaseDate = receiptData.purchased_at 
        ? new Date(receiptData.purchased_at).toLocaleDateString()
        : 'Not available';
    document.getElementById('purchaseDate').textContent = purchaseDate;
    
    document.getElementById('receiptNumber').textContent = receiptData.receipt_number || 'Not available';
    
    const formattedAmount = receiptData.total_amount 
        ? `${receiptData.currency || ''} ${receiptData.total_amount.toFixed(2)}`
        : 'Not available';
    document.getElementById('totalAmount').textContent = formattedAmount;
    
    document.getElementById('paymentMethod').textContent = receiptData.payment_method || 'Not available';
    
    const formattedTax = receiptData.tax_amount 
        ? `${receiptData.currency || ''} ${receiptData.tax_amount.toFixed(2)}`
        : 'Not available';
    document.getElementById('taxAmount').textContent = formattedTax;
    
    // Populate items table
    const itemsTableBody = document.querySelector('#itemsTable tbody');
    itemsTableBody.innerHTML = '';
    
    if (receiptData.items && receiptData.items.length > 0) {
        receiptData.items.forEach(item => {
            const row = document.createElement('tr');
            
            const descCell = document.createElement('td');
            descCell.textContent = item.description || 'N/A';
            
            const qtyCell = document.createElement('td');
            qtyCell.textContent = item.quantity || 'N/A';
            
            const unitPriceCell = document.createElement('td');
            unitPriceCell.textContent = item.unit_price 
                ? `${receiptData.currency || ''} ${item.unit_price.toFixed(2)}`
                : 'N/A';
            
            const totalPriceCell = document.createElement('td');
            totalPriceCell.textContent = item.total_price 
                ? `${receiptData.currency || ''} ${item.total_price.toFixed(2)}`
                : 'N/A';
            
            row.appendChild(descCell);
            row.appendChild(qtyCell);
            row.appendChild(unitPriceCell);
            row.appendChild(totalPriceCell);
            
            itemsTableBody.appendChild(row);
        });
    } else {
        // No items
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.textContent = 'No items found';
        cell.className = 'text-center';
        row.appendChild(cell);
        itemsTableBody.appendChild(row);
    }
    
    // Set up the view receipt button
    const viewReceiptBtn = document.getElementById('viewReceiptBtn');
    if (viewReceiptBtn) {
        viewReceiptBtn.onclick = () => {
            window.location.href = `/receipt/${currentReceiptId}`;
        };
    }
}

// Load receipts into the table
async function loadReceipts() {
    try {
        const response = await fetch('/api/receipts');
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to load receipts');
        }
        
        const receiptsTable = document.querySelector('#receiptsTable tbody');
        if (!receiptsTable) return;
        
        receiptsTable.innerHTML = '';
        
        if (data.receipts.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.textContent = 'No receipts found';
            cell.className = 'text-center';
            row.appendChild(cell);
            receiptsTable.appendChild(row);
            return;
        }
        
        data.receipts.forEach(receipt => {
            const row = document.createElement('tr');
            
            const idCell = document.createElement('td');
            idCell.textContent = receipt.id;
            
            const merchantCell = document.createElement('td');
            merchantCell.textContent = receipt.merchant_name || 'Unknown';
            
            const dateCell = document.createElement('td');
            dateCell.textContent = receipt.purchased_at 
                ? new Date(receipt.purchased_at).toLocaleDateString()
                : 'N/A';
            
            const amountCell = document.createElement('td');
            amountCell.textContent = receipt.total_amount 
                ? `${receipt.currency || ''} ${receipt.total_amount.toFixed(2)}`
                : 'N/A';
            
            const actionsCell = document.createElement('td');
            const viewButton = document.createElement('a');
            viewButton.href = `/receipt/${receipt.id}`;
            viewButton.className = 'btn btn-sm btn-outline-primary me-2';
            viewButton.innerHTML = '<i class="fas fa-eye me-1"></i> View';
            
            actionsCell.appendChild(viewButton);
            
            row.appendChild(idCell);
            row.appendChild(merchantCell);
            row.appendChild(dateCell);
            row.appendChild(amountCell);
            row.appendChild(actionsCell);
            
            receiptsTable.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading receipts:', error);
        showNotification('Error', 'Failed to load receipts', 'error');
    }
}

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the page
    resetSteps();
    
    // Load existing receipts when the page loads (already in place in the template)
});