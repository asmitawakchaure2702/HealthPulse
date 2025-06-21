// Form Toggle with Smooth Transition
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    if (localStorage.getItem('userEmail')) {
        window.location.href = 'dashboard.html';
        return;
    }

    // Get form elements
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registrationForm');
    const showLoginLink = document.getElementById('showLogin');
    const showRegisterLink = document.getElementById('showRegister');

    // Toggle between forms if the links exist
    if (showLoginLink) {
        showLoginLink.addEventListener('click', function(event) {
            event.preventDefault();
            toggleForms(registerForm, loginForm);
        });
    }

    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', function(event) {
            event.preventDefault();
            toggleForms(loginForm, registerForm);
        });
    }

    // Handle login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;

            if (!email || !password) {
                showError("Both email and password are required!");
                return;
            }

            try {
                const response = await fetch('http://localhost:5000/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Login failed');
                }

                localStorage.setItem('userEmail', email);
                showSuccess("Login Successful! Redirecting to chat...");
                
                // Redirect to dashboard/chatbot
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1500);
            } catch (error) {
                showError(error.message);
            }
        });
    }

    // Handle registration form submission
    if (registerForm) {
        registerForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const fullName = document.getElementById('fullname').value.trim();
            const age = document.getElementById('age').value;
            const gender = document.getElementById('gender').value;
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

            if (!fullName || !age || !gender || !email || !password || !confirmPassword) {
                showError("All fields are required!");
                return;
            }

            if (!validateEmail(email)) {
                showError("Invalid email format!");
                return;
            }

            if (password.length < 6) {
                showError("Password must be at least 6 characters long!");
                return;
            }

            if (password !== confirmPassword) {
                showError("Passwords do not match. Please try again.");
                return;
            }

            try {
                const response = await fetch('http://localhost:5000/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        fullname: fullName,
                        age: parseInt(age),
                        gender: gender,
                        email: email,
                        password: password
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Registration failed');
                }

                localStorage.setItem('userEmail', email);
                showSuccess(`Registration Successful! Welcome, ${fullName}!`);
                
                // Redirect to dashboard/chatbot
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1500);
            } catch (error) {
                showError(error.message);
            }
        });
    }
});

// Helper Functions
function toggleForms(hideForm, showForm) {
    if (hideForm && showForm) {
        hideForm.style.opacity = '0';
        setTimeout(() => {
            hideForm.style.display = 'none';
            showForm.style.display = 'block';
            setTimeout(() => showForm.style.opacity = '1', 50);
        }, 300);
    }
}

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showError(message) {
    alert(`❌ Error: ${message}`);
}

function showSuccess(message) {
    alert(`✅ Success: ${message}`);
}
