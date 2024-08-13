function applyTheme() {
    var theme = localStorage.getItem('theme') || 'light';
    document.body.className = theme;
    adjustTextColor();
}

function adjustTextColor() {
    var backgroundColor = window.getComputedStyle(document.body).backgroundColor;
    var rgb = backgroundColor.match(/\d+/g);
    var brightness = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255;

    if (brightness < 0.5) {
        document.body.style.color = 'white';
    } else {
        document.body.style.color = 'black';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    applyTheme();
});

function saveTheme() {
    var theme = document.getElementById('theme').value;
    localStorage.setItem('theme', theme);
    applyTheme();
}
