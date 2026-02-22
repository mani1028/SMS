/**
 * Handle login form submission
 */
async function handleLogin() {
    const form = document.getElementById("loginForm");
    const messageDiv = document.getElementById("message");
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        const schoolId = document.getElementById("schoolId").value.trim();
        
        messageDiv.textContent = "";
        messageDiv.className = "";
        
        if (!email || !password || !schoolId) {
            showMessage("Please fill all fields", "error");
            return;
        }
        
        try {
            const response = await apiRequest("/login", "POST", {
                email,
                password,
                school_id: parseInt(schoolId)
            });
            
            if (response.status) {
                // Store token and user data
                localStorage.setItem("token", response.data.token);
                localStorage.setItem("user", JSON.stringify(response.data));
                localStorage.setItem("school_id", schoolId);
                
                showMessage("Login successful! Redirecting...", "success");
                setTimeout(() => {
                    window.location.href = "/admin/dashboard.html";
                }, 1500);
            } else {
                showMessage(response.message || "Login failed", "error");
            }
        } catch (error) {
            showMessage(error.message || "Login error", "error");
        }
    });
}

/**
 * Show message in UI
 * @param {string} message - Message text
 * @param {string} type - Message type: 'success', 'error'
 */
function showMessage(message, type) {
    const messageDiv = document.getElementById("message");
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = type === "success" ? "success-message" : "error-message";
    }
}

/**
 * Handle registration form submission
 */
async function handleRegister() {
    const form = document.getElementById("registerForm");
    if (!form) return;
    
    const messageDiv = document.getElementById("message");
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const formData = {
            school_name: document.getElementById("schoolName").value.trim(),
            school_email: document.getElementById("schoolEmail").value.trim(),
            admin_name: document.getElementById("adminName").value.trim(),
            admin_email: document.getElementById("adminEmail").value.trim(),
            admin_password: document.getElementById("adminPassword").value.trim()
        };
        
        messageDiv.textContent = "";
        messageDiv.className = "";
        
        try {
            const response = await apiRequest("/register", "POST", formData);
            
            if (response.status) {
                showMessage("Registration successful! You can now login.", "success");
                setTimeout(() => {
                    window.location.href = "/auth/login.html";
                }, 2000);
            } else {
                showMessage(response.message || "Registration failed", "error");
            }
        } catch (error) {
            showMessage(error.message || "Registration error", "error");
        }
    });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    handleLogin();
    handleRegister();
});
