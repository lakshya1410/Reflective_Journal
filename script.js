document.addEventListener('DOMContentLoaded', function() {
    const journalForm = document.getElementById('journalForm');
    const journalEntry = document.getElementById('journalEntry');
    const responseContainer = document.getElementById('responseContainer');
    const responseContent = document.getElementById('responseContent');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const sentimentIndicator = document.getElementById('sentimentIndicator');
    const sentimentScore = document.getElementById('sentimentScore');
    
    journalForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Input validation
        const entryText = journalEntry.value.trim();
        if (!entryText) {
            showError('Please write something in your journal entry.');
            return;
        }
        
        // Show loading spinner
        loadingSpinner.classList.remove('hidden');
        responseContainer.classList.add('hidden');
        errorMessage.classList.add('hidden');
        
        try {
            const response = await fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ entry: entryText }),
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Display the response
                displayResponse(data);
            } else {
                showError(data.error || 'An error occurred while processing your entry.');
            }
        } catch (error) {
            showError('Network error. Please try again later.');
            console.error('Error:', error);
        } finally {
            loadingSpinner.classList.add('hidden');
        }
    });
    
    function displayResponse(data) {
        // Update sentiment indicator
        const sentiment = data.sentiment.toLowerCase();
        const score = data.score;
        
        sentimentIndicator.className = 'w-12 h-12 rounded-full mr-4 flex items-center justify-center text-white font-bold';
        
        // Handle different sentiment labels from the multilingual model
        if (sentiment === 'positive') {
            sentimentIndicator.classList.add('sentiment-positive');
            sentimentIndicator.innerText = '😊';
            sentimentScore.innerText = `${score}% positive sentiment`;
        } else if (sentiment === 'neutral') {
            sentimentIndicator.classList.add('sentiment-neutral');
            sentimentIndicator.innerText = '😐';
            sentimentScore.innerText = `${score}% neutral sentiment`;
        } else {
            sentimentIndicator.classList.add('sentiment-negative');
            sentimentIndicator.innerText = '😔';
            sentimentScore.innerText = `${score}% negative sentiment`;
        }
        
        // Set the response content
        responseContent.innerHTML = data.response;
        
        // Show the response container
        responseContainer.classList.remove('hidden');
        
        // Scroll to response
        responseContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    function showError(message) {
        errorText.innerText = message;
        errorMessage.classList.remove('hidden');
        loadingSpinner.classList.add('hidden');
    }
});