const toggleButton = document.getElementById('dark-mode-toggle');
const bodyElement = document.body;

// Check dark mode preference on page load
if (sessionStorage.getItem('darkMode') === 'true') {
    bodyElement.classList.add('dark-mode');
}

toggleButton.addEventListener('click', () => {
    $.ajax({
        type: "POST",
        url: "/toggle_dark_mode",
        contentType: "application/json",
        success: function(response) {
            // Update the dark mode based on the response
            if (response.dark_mode) {
                bodyElement.classList.add('dark-mode');
                sessionStorage.setItem('darkMode', 'true'); // Use sessionStorage for the current session only
            } else {
                bodyElement.classList.remove('dark-mode');
                sessionStorage.setItem('darkMode', 'false');
            }
        },
        error: function(xhr, status, error) {
            console.error("Error toggling dark mode:", error);
        }
    });
});