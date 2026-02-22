// API Configuration
const API_BASE = "http://localhost:5000/api";

/**
 * Generic API request wrapper
 * @param {string} endpoint - API endpoint path
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {object} body - Request body (for POST, PUT)
 * @returns {object} Response data
 */
async function apiRequest(endpoint, method = "GET", body = null) {
    try {
        const token = localStorage.getItem("token");
        const headers = {
            "Content-Type": "application/json"
        };
        
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        
        const options = {
            method,
            headers
        };
        
        if (body && (method === "POST" || method === "PUT")) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(API_BASE + endpoint, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || "API request failed");
        }
        
        return data;
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}

/**
 * Check if user is authenticated
 * @returns {boolean} True if token exists
 */
function isAuthenticated() {
    return !!localStorage.getItem("token");
}

/**
 * Get stored user data
 * @returns {object} User data from localStorage
 */
function getCurrentUser() {
    const userStr = localStorage.getItem("user");
    return userStr ? JSON.parse(userStr) : null;
}

/**
 * Logout user
 */
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("school_id");
    window.location.href = "/auth/login.html";
}
