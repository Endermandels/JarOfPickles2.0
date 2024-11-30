// Prevent form submission when 'Enter' key is pressed in the input field
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-bar');
    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();  // Prevent form submission on Enter key press
        }
    });
});

// Reset elements on loading the window
window.onload = function() {
    document.getElementById('search-bar').value = '';
    document.getElementById('bm25').checked = true;
    document.getElementById('pagerank').checked = true;
    document.getElementById('related_results').checked = false;
};

// Handle checkbox clicked event
document.addEventListener('DOMContentLoaded', function () {
    let checkboxes = document.querySelectorAll('.checkbox-container input[type="checkbox"]');
    let delayTimeout; // Variable to store the timeout ID

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            // Clear any existing timeout to prevent multiple triggers
            clearTimeout(delayTimeout);

            // Set a new timeout for 500ms
            delayTimeout = setTimeout(() => {
                let checkedBoxes = Array.from(checkboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);

                // Send checkbox data to the backend
                fetch('/update-checkboxes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ checked: checkedBoxes }),
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Update checkbox states based on response
                    checkboxes.forEach(cb => {
                        if (cb.value === 'pagerank') {
                            cb.checked = data.checked.pagerank;
                        } else if (cb.value === 'bm25') {
                            cb.checked = data.checked.bm25;
                        } else if (cb.value === 'related_results') {
                            cb.checked = data.checked.related_results;
                        }
                    });
                })
                .catch(error => console.error('Error:', error));

                // Send search request with updated checkbox data
                fetch('/search', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'text/html',
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.text();
                })
                .then(html => {
                    document.getElementById('results').innerHTML = html;
                })
                .catch(error => {
                    console.error('Error during fetch:', error);
                });
            }, 500); // Delay of 500ms
        });
    });
});
