document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('editProfileForm');

    form.addEventListener('submit', function (event) {
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        
        const email = emailInput.value;
        const password = passwordInput.value;

        if (!validateEmail(email)) {
            alert('Invalid email address.');
            event.preventDefault();
            return;
        }

        if (password && !validatePassword(password)) {
            alert('Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, and one number.');
            event.preventDefault();
            return;
        }
    });

    function validateEmail(email) {
        // Basic email regex pattern
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailPattern.test(email);
    }

    function validatePassword(password) {
        // Password must be at least 8 characters long, contain uppercase, lowercase, and numbers
        const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/;
        return passwordPattern.test(password);
    }
});
