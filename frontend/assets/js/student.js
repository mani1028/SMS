let currentPage = 1;
const itemsPerPage = 10;

/**
 * Load and display students
 */
async function loadStudents(page = 1) {
    const messageDiv = document.getElementById("message");
    const tableBody = document.getElementById("studentTableBody");
    
    if (!tableBody) return;
    
    try {
        const response = await apiRequest(`/students?page=${page}&limit=${itemsPerPage}`);
        
        if (response.status) {
            renderStudentsTable(response.data.students);
            renderPagination(response.data.pages, page);
            currentPage = page;
        } else {
            showStudentMessage(response.message || "Failed to load students", "error");
        }
    } catch (error) {
        showStudentMessage(error.message || "Error loading students", "error");
    }
}

/**
 * Render students in table
 * @param {array} students - Array of student objects
 */
function renderStudentsTable(students) {
    const tableBody = document.getElementById("studentTableBody");
    
    if (!students || students.length === 0) {
        tableBody.innerHTML = "<tr><td colspan='6' class='text-center'>No students found</td></tr>";
        return;
    }
    
    tableBody.innerHTML = students.map(student => `
        <tr>
            <td>${student.id}</td>
            <td>${student.name}</td>
            <td>${student.admission_no}</td>
            <td>${student.class_name}</td>
            <td>${student.email || "-"}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-edit" onclick="editStudent(${student.id})">Edit</button>
                    <button class="btn-delete" onclick="deleteStudent(${student.id})">Delete</button>
                </div>
            </td>
        </tr>
    `).join("");
}

/**
 * Render pagination controls
 * @param {number} totalPages - Total number of pages
 * @param {number} currentPage - Current page number
 */
function renderPagination(totalPages, currentPage) {
    const paginationDiv = document.getElementById("pagination");
    if (!paginationDiv) return;
    
    let html = "";
    
    if (currentPage > 1) {
        html += `<button onclick="loadStudents(${currentPage - 1})">Previous</button>`;
    }
    
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            html += `<button class="active">${i}</button>`;
        } else {
            html += `<button onclick="loadStudents(${i})">${i}</button>`;
        }
    }
    
    if (currentPage < totalPages) {
        html += `<button onclick="loadStudents(${currentPage + 1})">Next</button>`;
    }
    
    paginationDiv.innerHTML = html;
}

/**
 * Open add/edit student modal
 * @param {number} studentId - Student ID for edit, null for add
 */
async function openStudentModal(studentId = null) {
    const modal = document.getElementById("studentModal");
    const form = document.getElementById("studentForm");
    
    if (!modal || !form) return;
    
    form.reset();
    document.getElementById("studentId").value = "";
    
    if (studentId) {
        try {
            const response = await apiRequest(`/students/${studentId}`);
            
            if (response.status) {
                const student = response.data;
                document.getElementById("studentId").value = student.id;
                document.getElementById("name").value = student.name;
                document.getElementById("admissionNo").value = student.admission_no;
                document.getElementById("className").value = student.class_name;
                document.getElementById("email").value = student.email || "";
                document.getElementById("phone").value = student.phone || "";
            }
        } catch (error) {
            showStudentMessage("Failed to load student", "error");
        }
    }
    
    modal.classList.add("active");
}

/**
 * Close student modal
 */
function closeStudentModal() {
    const modal = document.getElementById("studentModal");
    if (modal) {
        modal.classList.remove("active");
    }
}

/**
 * Handle student form submission
 */
async function handleStudentForm() {
    const form = document.getElementById("studentForm");
    if (!form) return;
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const studentId = document.getElementById("studentId").value;
        const formData = {
            name: document.getElementById("name").value.trim(),
            admission_no: document.getElementById("admissionNo").value.trim(),
            class_name: document.getElementById("className").value.trim(),
            email: document.getElementById("email").value.trim(),
            phone: document.getElementById("phone").value.trim()
        };
        
        try {
            let response;
            
            if (studentId) {
                response = await apiRequest(`/students/${studentId}`, "PUT", formData);
            } else {
                response = await apiRequest("/students", "POST", formData);
            }
            
            if (response.status) {
                showStudentMessage(response.message, "success");
                closeStudentModal();
                loadStudents(1);
            } else {
                showStudentMessage(response.message || "Operation failed", "error");
            }
        } catch (error) {
            showStudentMessage(error.message || "Error saving student", "error");
        }
    });
}

/**
 * Edit student
 * @param {number} studentId - Student ID to edit
 */
function editStudent(studentId) {
    openStudentModal(studentId);
}

/**
 * Delete student with confirmation
 * @param {number} studentId - Student ID to delete
 */
async function deleteStudent(studentId) {
    if (!confirm("Are you sure you want to delete this student?")) {
        return;
    }
    
    try {
        const response = await apiRequest(`/students/${studentId}`, "DELETE");
        
        if (response.status) {
            showStudentMessage("Student deleted successfully", "success");
            loadStudents(currentPage);
        } else {
            showStudentMessage(response.message || "Delete failed", "error");
        }
    } catch (error) {
        showStudentMessage(error.message || "Error deleting student", "error");
    }
}

/**
 * Show message in student page
 * @param {string} message - Message text
 * @param {string} type - Message type: 'success', 'error'
 */
function showStudentMessage(message, type) {
    const messageDiv = document.getElementById("message");
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = type === "success" ? "alert alert-success" : "alert alert-danger";
    }
}

/**
 * Check if user is authenticated
 */
function checkAuth() {
    if (!isAuthenticated()) {
        window.location.href = "/auth/login.html";
    }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    checkAuth();
    handleStudentForm();
    loadStudents(1);
});
