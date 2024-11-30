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
};

// Handle checkbox clicked event
document.addEventListener('DOMContentLoaded', function () {
    let checkboxes = document.querySelectorAll('.checkbox-container input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            let checkedBoxes = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            
            // Make sure at least one checkbox is on.
            if (checkedBoxes.length === 0) {
                checkboxes[0].checked = true; // Default to the first checkbox
                checkedBoxes = [checkboxes[0].value]; // Update the checked list
            }

            // Send checkbox data to the backend
            fetch('/update-checkboxes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ checked: checkedBoxes }),
            })
            .catch(error => console.error('Error:', error));

            // Send search request with updated checkbox data
            fetch('/search', {
                method: 'GET',
                headers: {
                    'Content-Type': 'text/html'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error!  Status: ${response.status}`);
                }
                return response.text();
            })
            .then(html => {
                document.getElementById('results').innerHTML = html;
            })
            .catch(error => {
                console.error('Error during fetch:', error);
            });
        });
    });
});