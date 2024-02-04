const toggleButton = document.getElementById('dark-mode-toggle');
const bodyElement = document.body;

if (localStorage.getItem('darkMode') === 'enabled') {
    bodyElement.classList.add('dark-mode');
}

toggleButton.addEventListener('click', () => {
    bodyElement.classList.toggle('dark-mode');
    if (bodyElement.classList.contains('dark-mode')) {
        localStorage.setItem('darkMode', 'enabled');
    } else {
        localStorage.removeItem('darkMode');
    }
});
