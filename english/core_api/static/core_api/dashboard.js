const API_BASE = "/api"; // Use relative path since it's now on the same host

// --- STATE MANAGEMENT ---
const state = {
    token: localStorage.getItem('admin_token'),
    currentPage: 'home',
    currentPageNum: 1,
    currentSearch: '',
    stats: {}
};

// --- DOM ELEMENTS ---
const elements = {
    loginModal: document.getElementById('login-modal'),
    loginForm: document.getElementById('login-form'),
    dashboardUI: document.getElementById('dashboard-ui'),
    mainView: document.getElementById('main-view'),
    pageTitle: document.getElementById('page-title'),
    pageSubtitle: document.getElementById('page-subtitle'),
    menuItems: document.querySelectorAll('.menu-item'),
    logoutBtn: document.getElementById('logout-btn'),
    searchContainer: document.getElementById('search-container'),
    searchInput: document.getElementById('admin-search'),
    paginationControls: document.getElementById('pagination-controls')
};

// --- CORE FUNCTIONS ---
const api = {
    async fetch(endpoint, options = {}) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const headers = {
            'Content-Type': 'application/json',
            ...(state.token && { 'Authorization': `Bearer ${state.token}` }),
            ...(csrfToken && { 'X-CSRFToken': csrfToken }),
            ...options.headers
        };

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
            if (response.status === 401) logout();
            return {
                ok: response.ok,
                status: response.status,
                data: await response.json().catch(() => ({}))
            };
        } catch (err) {
            console.error("Fetch Error:", err);
            return { ok: false, error: err };
        }
    }
};

async function login(username, password) {
    const res = await api.fetch('/login/', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });

    if (res.ok && res.data.access) {
        state.token = res.data.access;
        localStorage.setItem('admin_token', state.token);

        // Verify if superuser
        const profile = await api.fetch('/students/');
        if (profile.status === 403) {
            showError("Access Denied: You are not a superuser.");
            logout();
            return;
        }

        initDashboard();
    } else {
        showError("Invalid username or password.");
    }
}

function logout() {
    state.token = null;
    localStorage.removeItem('admin_token');
    elements.dashboardUI.style.display = 'none';
    elements.loginModal.classList.add('active');
}

function showError(msg) {
    const errEl = document.getElementById('login-error');
    errEl.innerText = msg;
    errEl.style.display = 'block';
}

function initDashboard() {
    elements.loginModal.classList.remove('active');
    elements.dashboardUI.style.display = 'flex';
    loadPage('home');
}

// --- NAVIGATION ---
window.toggleSidebar = function () {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
};

async function loadPage(pageId, pageNum = 1, searchQuery = state.currentSearch) {
    // Close sidebar on mobile after choosing a page
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (window.innerWidth <= 768) {
        sidebar?.classList.remove('active');
        overlay?.classList.remove('active');
    }

    state.currentPage = pageId;
    state.currentPageNum = pageNum;
    state.currentSearch = searchQuery;

    elements.menuItems.forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageId);
    });

    // Toggle search UI
    elements.searchContainer.style.display = pageId === 'home' ? 'none' : 'block';
    elements.paginationControls.style.display = 'none'; // Hide by default, renderers will show if needed

    elements.mainView.innerHTML = `<div class="animate-in" style="display:flex; justify-content:center; align-items:center; height:200px;">
        <span style="color:var(--primary); font-size:1.5rem;">Loading...</span>
    </div>`;

    switch (pageId) {
        case 'home': renderHome(); break;
        case 'students': renderStudents(); break;
        case 'listening': renderCRUD('listening', 'Listening Lessons'); break;
        case 'reading': renderCRUD('reading', 'Reading Stories'); break;
        case 'writing': renderCRUD('writing', 'Writing Tasks'); break;
        case 'speaking-topics': renderCRUD('social/topics', 'Speaking Topics'); break;
        case 'learning': renderLearning(); break;
        case 'xp-manage': renderXPManagement(); break;
    }
}

function changePage(pageNum) {
    loadPage(state.currentPage, pageNum, state.currentSearch);
}

let searchTimeout;
elements.searchInput?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadPage(state.currentPage, 1, e.target.value);
    }, 500);
});

function renderPagination(data) {
    // If backend is not paginating correctly, data.count will be undefined
    if (data.count === undefined) {
        elements.paginationControls.style.display = 'none';
        return;
    }

    elements.paginationControls.style.display = 'flex';
    const totalPages = Math.ceil(data.count / 10) || 1;

    let html = `
        <button class="btn btn-sm" ${!data.previous ? 'disabled' : ''} onclick="changePage(${state.currentPageNum - 1})" 
                style="background: ${data.previous ? 'var(--primary)' : 'rgba(255,255,255,0.05)'}; 
                       color: ${data.previous ? 'white' : 'var(--text-muted)'};
                       opacity: ${!data.previous ? '0.5' : '1'}; 
                       cursor: ${!data.previous ? 'not-allowed' : 'pointer'};">
            Previous
        </button>
        <span style="font-size:0.875rem; color:var(--text-muted); font-weight: 500;">
            Page ${state.currentPageNum} of ${totalPages} 
            <small style="opacity: 0.5; margin-left: 0.5rem;">(${data.count} items total)</small>
        </span>
        <button class="btn btn-sm" ${!data.next ? 'disabled' : ''} onclick="changePage(${state.currentPageNum + 1})" 
                style="background: ${data.next ? 'var(--primary)' : 'rgba(255,255,255,0.05)'}; 
                       color: ${data.next ? 'white' : 'var(--text-muted)'};
                       opacity: ${!data.next ? '0.5' : '1'}; 
                       cursor: ${!data.next ? 'not-allowed' : 'pointer'};">
            Next
        </button>
    `;
    elements.paginationControls.innerHTML = html;
}

// --- VIEW RENDERS ---
async function renderHome() {
    elements.pageTitle.innerText = "Admin Overview";
    elements.pageSubtitle.innerText = "Monitor student growth and curriculum health.";

    const res = await api.fetch('/students/admin_stats/');
    if (!res.ok) return;

    const { users, curriculum, activity } = res.data;
    state.activityData = activity; // Store for switching

    elements.mainView.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card glass animate-in">
                <span class="stat-label">Total Students</span>
                <span class="stat-value">${users.total}</span>
                <div class="stat-trend trend-up">Registered Learners</div>
            </div>
            <div class="stat-card glass animate-in" style="animation-delay: 0.1s">
                <span class="stat-label">Active (Approved)</span>
                <span class="stat-value">${users.approved}</span>
                <div class="stat-trend trend-up">Verified Accounts</div>
            </div>
            <div class="stat-card glass animate-in" style="animation-delay: 0.2s">
                <span class="stat-label">Pending Approval</span>
                <span class="stat-value" style="color:var(--warning);">${users.pending}</span>
                <div class="stat-trend">Needs Attention</div>
            </div>
            <div class="stat-card glass animate-in" style="animation-delay: 0.3s">
                <span class="stat-label">Curriculum Total</span>
                <span class="stat-value">${curriculum.listening + curriculum.reading + curriculum.writing + curriculum.chapters}</span>
                <div class="stat-trend">Content Modules</div>
            </div>
        </div>

        <div class="glass animate-in" style="padding: 1.5rem; animation-delay: 0.4s; margin-bottom: 1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1.5rem;">
                <h3>Students Activity Trend</h3>
                <div class="btn-group" style="display:flex; gap:0.5rem; background:rgba(255,255,255,0.05); padding:0.25rem; border-radius:0.5rem;">
                    <button class="btn btn-sm" onclick="switchActivityChart('daily')" id="btn-daily">Daily</button>
                    <button class="btn btn-sm" onclick="switchActivityChart('weekly')" id="btn-weekly">Weekly</button>
                    <button class="btn btn-sm" onclick="switchActivityChart('monthly')" id="btn-monthly">Monthly</button>
                    <button class="btn btn-sm" onclick="switchActivityChart('yearly')" id="btn-yearly">Yearly</button>
                </div>
            </div>
            <div id="activity-chart-container" class="chart-container">
                <!-- Bars will be injected here -->
            </div>
        </div>

        <div class="glass animate-in" style="padding: 1.5rem; animation-delay: 0.5s">
            <h3 style="margin-bottom: 1.5rem;">Curriculum Distribution</h3>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem;">
                <div style="text-align:center;">
                    <div style="font-size: 2rem;">🎙️</div>
                    <div style="font-weight:600; margin-top:0.5rem;">${curriculum.listening} Listening</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">Video Lessons</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size: 2rem;">📖</div>
                    <div style="font-weight:600; margin-top:0.5rem;">${curriculum.reading} Reading</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">Short Stories</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size: 2rem;">✍️</div>
                    <div style="font-weight:600; margin-top:0.5rem;">${curriculum.writing} Writing</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">Grammar Exercises</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size: 2rem;">📚</div>
                    <div style="font-weight:600; margin-top:0.5rem;">${curriculum.chapters} Grammar</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">Thematic Chapters</div>
                </div>
            </div>
        </div>
    `;

    // Default to daily
    switchActivityChart('daily');
}

window.switchActivityChart = function (type) {
    const data = state.activityData[type] || [];
    const container = document.getElementById('activity-chart-container');
    if (!container) return;

    // Update buttons
    ['daily', 'weekly', 'monthly', 'yearly'].forEach(t => {
        const btn = document.getElementById(`btn-${t}`);
        if (btn) btn.style.background = (t === type) ? 'var(--primary)' : 'transparent';
    });

    if (data.length === 0) {
        container.innerHTML = `<div style="height:100%; display:flex; align-items:center; justify-content:center; color:var(--text-muted);">No activity data yet.</div>`;
        return;
    }

    const maxCount = Math.max(...data.map(d => d.count), 1);

    // Reverse data to show chronological order if needed, but let's show most recent first as per array
    // Actually, usually charts are L to R (Oldest to Newest).
    const displayData = [...data].reverse();

    container.innerHTML = displayData.map(d => {
        const date = new Date(d.period);
        let label = '';
        if (type === 'daily') label = date.toLocaleDateString(undefined, { weekday: 'short' });
        else if (type === 'weekly') label = 'W' + Math.ceil(date.getDate() / 7);
        else if (type === 'monthly') label = date.toLocaleDateString(undefined, { month: 'short' });
        else label = date.getFullYear();

        return `
            <div class="chart-bar" style="height: ${(d.count / maxCount) * 100}%">
                <div class="chart-tooltip">${d.count} actions</div>
                <span class="chart-label">${label}</span>
            </div>
        `;
    }).join('');
};

async function renderStudents() {
    elements.pageTitle.innerText = "Student Management";
    elements.pageSubtitle.innerText = "Approve accounts and track learner progress.";

    const res = await api.fetch(`/students/?page=${state.currentPageNum}&search=${state.currentSearch}`);
    if (!res.ok) return;

    const students = res.data.results || [];
    renderPagination(res.data);

    elements.mainView.innerHTML = `
        <div class="glass animate-in" style="padding: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>Active & Pending Learners</h3>
                <div style="display:flex; gap:0.75rem;">
                    <input type="file" id="bulk-student-input" accept=".csv" style="display:none;" onchange="handleBulkUpload(event)">
                    <button class="btn" style="background:rgba(255,255,255,0.05);" onclick="document.getElementById('bulk-student-input').click()">
                        📤 Bulk Import (CSV)
                    </button>
                    <button class="btn btn-primary" onclick="openEntityModal('register', null)">
                        + Add New Student
                    </button>
                </div>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px;">S.No</th>
                            <th>Student ID</th>
                            <th>Username</th>
                            <th>Points (XP)</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${students.map((student, index) => `
                            <tr>
                                <td style="color: var(--text-muted); font-size: 0.8rem;">${(state.currentPageNum - 1) * 10 + index + 1}</td>
                                <td style="font-family: monospace; font-size: 0.8rem;">${student.student_id}</td>
                                <td style="font-weight: 600;">${student.username}</td>
                                <td>${student.total_xp} XP</td>
                                <td>
                                    <span class="badge ${student.is_approved ? 'badge-approved' : 'badge-pending'}">
                                        ${student.is_approved ? 'Approved' : 'Pending'}
                                    </span>
                                </td>
                                <td>
                                    <div style="display:flex; gap:0.5rem;">
                                        <label class="switch" title="${student.is_approved ? 'Suspend Student' : 'Approve Student'}">
                                            <input type="checkbox" ${student.is_approved ? 'checked' : ''} 
                                                   onchange="toggleApproval('${student.id}', ${student.is_approved})">
                                            <span class="slider round"></span>
                                        </label>
                                        <button class="btn" onclick="openEntityModal('students', ${student.id})" 
                                                style="background:rgba(255, 255, 255, 0.05); padding: 0.4rem 0.6rem;" title="Edit Profile">
                                            ✏️
                                        </button>
                                        <button class="btn" onclick="viewStudentReport(${student.id})" 
                                                style="background:rgba(99, 102, 241, 0.1); color:var(--primary); padding: 0.4rem 0.6rem;" title="View Detailed Report">
                                            📊
                                        </button>
                                        <button class="btn" onclick="deleteEntry('students', ${student.id})" 
                                                style="background:rgba(239, 68, 68, 0.1); color:var(--danger); padding: 0.4rem 0.6rem;" title="Delete Student">
                                            🗑️
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

window.toggleApproval = async function (studentId, currentStatus) {
    const res = await api.fetch(`/students/${studentId}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_approved: !currentStatus })
    });

    if (res.ok) {
        renderStudents();
    } else {
        alert("Failed to update student status.");
    }
};

window.handleBulkUpload = async function (event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!confirm(`Are you sure you want to import students from ${file.name}?`)) {
        event.target.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    // Manual fetch because api.fetch assumes JSON
    try {
        const response = await fetch(`${API_BASE}/students/bulk-import/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`,
                'X-CSRFToken': csrfToken
            },
            body: formData
        });

        let data;
        try {
            data = await response.json();
        } catch (e) {
            data = { error: `Server returned ${response.status} (Not JSON)` };
        }

        if (response.ok) {
            let msg = data.message;
            if (data.errors && data.errors.length > 0) {
                msg += "\n\nIssues encountered:\n" + data.errors.slice(0, 5).join('\n');
                if (data.errors.length > 5) msg += `\n...and ${data.errors.length - 5} more errors.`;
            }
            alert(msg);
            renderStudents();
        } else {
            let errorMsg = `Import failed (${response.status}): ` + (data.error || data.detail || data.message || "Check file format.");
            if (data.errors && data.errors.length > 0) {
                errorMsg += "\n\nSkipped Rows:\n" + data.errors.slice(0, 10).join('\n');
            }
            alert(errorMsg);
        }
    } catch (err) {
        console.error("Bulk Upload Error:", err);
        alert("A network error occurred: " + err.message);
    } finally {
        event.target.value = '';
    }
};

async function renderCRUD(type, label) {
    elements.pageTitle.innerText = label;
    elements.pageSubtitle.innerText = `Manage all ${label.toLowerCase()} in the curriculum.`;

    const endpoint = type === 'learning' ? '/learning/chapters/' : `/${type}/`;
    const res = await api.fetch(`${endpoint}?page=${state.currentPageNum}&search=${state.currentSearch}`);
    if (!res.ok) return;

    const items = res.data.results || [];
    renderPagination(res.data);

    elements.mainView.innerHTML = `
        <div class="glass animate-in" style="padding: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>Curriculum Library</h3>
                <button class="btn btn-primary" onclick="openEntityModal('${type}', null)">
                    + Add New ${label.split(' ')[0]}
                </button>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Title/Hint</th>
                            <th>Level</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map(item => `
                            <tr>
                                <td style="font-weight: 600;">${item.title || item.malayalam_meaning || 'Untitled'}</td>
                                <td><span class="badge" style="background:rgba(255,255,255,0.05);">${item.level || 'Standard'}</span></td>
                                <td>
                                    <div style="display:flex; gap:0.5rem;">
                                        <button class="btn" onclick="openEntityModal('${type}', ${item.id})" style="background:rgba(255,255,255,0.05); padding: 0.4rem 0.6rem;">✏️</button>
                                        <button class="btn" onclick="deleteEntry('${type}', ${item.id})" style="background:rgba(239, 68, 68, 0.1); color:var(--danger); padding: 0.4rem 0.6rem;">🗑️</button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// --- MODAL & FORM LOGIC ---
const modal = {
    overlay: document.getElementById('entity-modal'),
    title: document.getElementById('modal-title'),
    form: document.getElementById('entity-form'),
    fields: document.getElementById('form-fields')
};

window.openEntityModal = async function (type, id) {
    let data = {};
    if (id && type !== 'register') {
        const res = await api.fetch(`/${type}/${id}/`);
        if (res.ok) data = res.data;
    }

    modal.title.innerText = type === 'register' ? 'Register New Student' : (id ? `Edit ${type}` : `Add New ${type}`);
    modal.overlay.classList.add('active');

    // Generate Fields based on type
    let fieldsHtml = '';
    const config = {
        register: ['username', 'password', 'email'],
        students: ['username', 'email', 'password', 'student_id', 'is_approved'],
        listening: ['title', 'youtube_url', 'level'],
        reading: ['title', 'level', 'story_content', 'background_image_url'],
        writing: ['level', 'malayalam_meaning', 'correct_sentence', 'extra_words'],
        'learning/chapters': ['order', 'title', 'grammar_rule_malayalam', 'level'],
        'social/topics': ['text', 'level']
    };

    config[type].forEach(key => {
        const value = data[key] || '';
        const isLevel = key === 'level';
        const isCorrect = key.includes('correct') && !key.includes('sentence');
        const isApproved = key === 'is_approved';
        const isPassword = key === 'password';

        let inputHtml = '';
        if (isLevel) {
            const levels = ['BEGINNER', 'INTERMEDIATE', 'PROFESSIONAL'];
            inputHtml = `
                <select class="form-input" name="${key}">
                    ${levels.map(lvl => `<option value="${lvl}" ${value === lvl ? 'selected' : ''}>${lvl}</option>`).join('')}
                </select>
            `;
        } else if (isApproved) {
            inputHtml = `
                <select class="form-input" name="${key}">
                    <option value="true" ${value === true ? 'selected' : ''}>Approved</option>
                    <option value="false" ${value === false ? 'selected' : ''}>Pending</option>
                </select>
            `;
        } else if (isCorrect) {
            const options = [1, 2, 3, 4];
            inputHtml = `
                <select class="form-input" name="${key}">
                    ${options.map(opt => `<option value="${opt}" ${value == opt ? 'selected' : ''}>Option ${opt}</option>`).join('')}
                </select>
            `;
        } else if (key === 'story_content' || key === 'grammar_rule_malayalam') {
            inputHtml = `<textarea class="form-input" name="${key}" rows="4">${value}</textarea>`;
        } else if (isPassword) {
            inputHtml = `<input type="password" class="form-input" name="${key}" value="" placeholder="Enter new password to change">`;
        } else {
            inputHtml = `<input type="text" class="form-input" name="${key}" value="${value}">`;
        }

        fieldsHtml += `
            <div class="form-group">
                <label>${key.replace(/_/g, ' ').toUpperCase()}</label>
                ${inputHtml}
            </div>
        `;
    });

    // Add dynamic questions section for listening and reading
    if (type === 'listening' || type === 'reading') {
        fieldsHtml += `
            <div style="border-top: 1px solid var(--glass-border); padding-top: 1.5rem; margin-top: 1.5rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <h3>Questions Quiz</h3>
                    <button type="button" class="btn btn-sm" style="background:var(--primary);" onclick="addQuestionRow()">+ Add Question</button>
                </div>
                <div id="questions-container">
                    ${(data.questions || []).map((q, i) => getQuestionHtml(i, q)).join('')}
                    ${(data.questions || []).length === 0 ? getQuestionHtml(0) + getQuestionHtml(1) + getQuestionHtml(2) : ''}
                </div>
            </div>
        `;
    }

    // Add Grammar Examples and Quizzes sections
    if (type === 'learning/chapters') {
        fieldsHtml += `
            <div style="border-top: 1px solid var(--glass-border); padding-top: 1.5rem; margin-top: 1.5rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <h3>Grammar Examples</h3>
                    <button type="button" class="btn btn-sm" style="background:var(--primary);" onclick="addExampleRow()">+ Add Example</button>
                </div>
                <div id="examples-container">
                    ${(data.examples || []).map((ex, i) => getExampleHtml(i, ex)).join('')}
                    ${(data.examples || []).length === 0 ? getExampleHtml(0) : ''}
                </div>
            </div>
            <div style="border-top: 1px solid var(--glass-border); padding-top: 1.5rem; margin-top: 1.5rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <h3>Chapter Quizzes</h3>
                    <button type="button" class="btn btn-sm" style="background:var(--primary);" onclick="addGrammarQuizRow()">+ Add Quiz</button>
                </div>
                <div id="quizzes-container">
                    ${(data.quizzes || []).map((qz, i) => getGrammarQuizHtml(i, qz)).join('')}
                    ${(data.quizzes || []).length === 0 ? getGrammarQuizHtml(0) : ''}
                </div>
            </div>
        `;
    }

    modal.fields.innerHTML = fieldsHtml;
    modal.form.onsubmit = (e) => saveEntry(e, type, id);
};

window.getQuestionHtml = function (index, data = {}) {
    return `
        <div class="question-row glass" style="padding: 1rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.05);">
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.5rem;">
                <label style="font-weight:600; font-size:0.75rem; color:var(--primary);">QUESTION #${index + 1}</label>
                <button type="button" onclick="this.parentElement.parentElement.remove()" style="background:transparent; color:var(--danger); border:none; cursor:pointer;">Remove</button>
            </div>
            <div class="form-group">
                <input type="text" class="form-input q-text" value="${data.text || ''}" placeholder="Question text">
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem;">
                <input type="text" class="form-input q-opt1" value="${data.option_1 || ''}" placeholder="Option 1">
                <input type="text" class="form-input q-opt2" value="${data.option_2 || ''}" placeholder="Option 2">
                <input type="text" class="form-input q-opt3" value="${data.option_3 || ''}" placeholder="Option 3">
            </div>
            <div class="form-group" style="margin-top:0.5rem;">
                <label style="font-size:0.75rem;">Correct Option</label>
                <select class="form-input q-correct">
                    <option value="0" ${data.correct == 0 ? 'selected' : ''}>Option A</option>
                    <option value="1" ${data.correct == 1 ? 'selected' : ''}>Option B</option>
                    <option value="2" ${data.correct == 2 ? 'selected' : ''}>Option C</option>
                </select>
            </div>
            ${data.id ? `<input type="hidden" class="q-id" value="${data.id}">` : ''}
        </div>
    `;
};

window.addQuestionRow = function () {
    const container = document.getElementById('questions-container');
    const index = container.querySelectorAll('.question-row').length;
    const div = document.createElement('div');
    div.innerHTML = getQuestionHtml(index);
    container.appendChild(div.firstElementChild);
};

// --- GRAMMAR HELPERS ---
window.getExampleHtml = function (index, data = {}) {
    return `
        <div class="example-row glass" style="padding: 1rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.05);">
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.5rem;">
                <label style="font-weight:600; font-size:0.75rem; color:var(--primary);">EXAMPLE #${index + 1}</label>
                <button type="button" onclick="this.parentElement.parentElement.remove()" style="background:transparent; color:var(--danger); border:none; cursor:pointer;">Remove</button>
            </div>
            <div class="form-group">
                <input type="text" class="form-input ex-en" value="${data.english_text || ''}" placeholder="English Text">
            </div>
            <div class="form-group">
                <input type="text" class="form-input ex-ml" value="${data.malayalam_explanation || ''}" placeholder="Malayalam Explanation">
            </div>
            <div class="form-group" style="display:flex; align-items:center; gap:0.5rem;">
                <input type="checkbox" class="ex-backup" ${data.is_backup ? 'checked' : ''}>
                <label style="font-size:0.8rem;">Is Backup Example?</label>
            </div>
            ${data.id ? `<input type="hidden" class="ex-id" value="${data.id}">` : ''}
        </div>
    `;
};

window.addExampleRow = function () {
    const container = document.getElementById('examples-container');
    if (!container) return;
    const index = container.querySelectorAll('.example-row').length;
    const div = document.createElement('div');
    div.innerHTML = getExampleHtml(index);
    container.appendChild(div.firstElementChild);
};

window.getGrammarQuizHtml = function (index, data = {}) {
    return `
        <div class="quiz-row glass" style="padding: 1rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.05);">
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.5rem;">
                <label style="font-weight:600; font-size:0.75rem; color:var(--primary);">QUIZ #${index + 1}</label>
                <button type="button" onclick="this.parentElement.parentElement.remove()" style="background:transparent; color:var(--danger); border:none; cursor:pointer;">Remove</button>
            </div>
            <div class="form-group">
                <input type="text" class="form-input qz-text" value="${data.question_text || ''}" placeholder="Question text">
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom:0.5rem;">
                <input type="text" class="form-input qz-a" value="${data.option_a || ''}" placeholder="Option A">
                <input type="text" class="form-input qz-b" value="${data.option_b || ''}" placeholder="Option B">
                <input type="text" class="form-input qz-c" value="${data.option_c || ''}" placeholder="Option C">
                <input type="text" class="form-input qz-d" value="${data.option_d || ''}" placeholder="Option D">
            </div>
            <div class="form-group">
                <label style="font-size:0.75rem;">Correct Option</label>
                <select class="form-input qz-correct">
                    <option value="0" ${data.correct_option == 0 ? 'selected' : ''}>Option A</option>
                    <option value="1" ${data.correct_option == 1 ? 'selected' : ''}>Option B</option>
                    <option value="2" ${data.correct_option == 2 ? 'selected' : ''}>Option C</option>
                    <option value="3" ${data.correct_option == 3 ? 'selected' : ''}>Option D</option>
                </select>
            </div>
            ${data.id ? `<input type="hidden" class="qz-id" value="${data.id}">` : ''}
        </div>
    `;
};

window.addGrammarQuizRow = function () {
    const container = document.getElementById('quizzes-container');
    if (!container) return;
    const index = container.querySelectorAll('.quiz-row').length;
    const div = document.createElement('div');
    div.innerHTML = getGrammarQuizHtml(index);
    container.appendChild(div.firstElementChild);
};

window.closeModal = () => modal.overlay.classList.remove('active');

async function saveEntry(e, type, id) {
    e.preventDefault();
    const formData = new FormData(modal.form);
    const body = Object.fromEntries(formData.entries());

    let endpoint = `/${type}/${id ? id + '/' : ''}`;
    let method = id ? 'PUT' : 'POST';

    if (type === 'register') {
        endpoint = '/admin/register-student/';
        method = 'POST';
    }

    // Convert is_approved string to boolean for students
    if (type === 'students') {
        if (body.is_approved === 'true') body.is_approved = true;
        if (body.is_approved === 'false') body.is_approved = false;
        // Remove empty password to avoid accidental resets
        if (!body.password) delete body.password;
    }

    // Handle nested questions for listening and reading
    if (type === 'listening' || type === 'reading') {
        body.questions = Array.from(document.querySelectorAll('.question-row')).map(row => ({
            id: row.querySelector('.q-id')?.value,
            text: row.querySelector('.q-text').value,
            option_1: row.querySelector('.q-opt1').value,
            option_2: row.querySelector('.q-opt2').value,
            option_3: row.querySelector('.q-opt3').value,
            correct: parseInt(row.querySelector('.q-correct').value)
        }));
    } else if (type === 'learning/chapters') {
        body.examples = Array.from(document.querySelectorAll('.example-row')).map(row => ({
            id: row.querySelector('.ex-id')?.value,
            english_text: row.querySelector('.ex-en').value,
            malayalam_explanation: row.querySelector('.ex-ml').value,
            is_backup: row.querySelector('.ex-backup').checked
        }));
        body.quizzes = Array.from(document.querySelectorAll('.quiz-row')).map(row => ({
            id: row.querySelector('.qz-id')?.value,
            question_text: row.querySelector('.qz-text').value,
            option_a: row.querySelector('.qz-a').value,
            option_b: row.querySelector('.qz-b').value,
            option_c: row.querySelector('.qz-c').value,
            option_d: row.querySelector('.qz-d').value,
            correct_option: parseInt(row.querySelector('.qz-correct').value)
        }));
    }

    const res = await api.fetch(endpoint, {
        method: method,
        body: JSON.stringify(body)
    });

    if (res.ok) {
        closeModal();
        if (type === 'register') renderStudents();
        else loadPage(type);
    } else {
        // Human-readable error reporting
        let errorMsg = "Update failed:\n";
        if (res.data) {
            for (const [key, value] of Object.entries(res.data)) {
                let detail = value;
                if (typeof value === 'object' && value !== null) {
                    detail = JSON.stringify(value);
                } else if (Array.isArray(value)) {
                    detail = value.join(', ');
                }
                errorMsg += `- ${key}: ${detail}\n`;
            }
        } else {
            errorMsg += res.error || "Unknown error occurred.";
        }
        alert(errorMsg);
    }
}

window.deleteEntry = async function (type, id) {
    if (!confirm("Are you sure you want to delete this?")) return;
    const res = await api.fetch(`/${type}/${id}/`, { method: 'DELETE' });
    if (res.ok) loadPage(type);
};

async function renderLearning() {
    elements.pageTitle.innerText = "Grammar Chapters";
    elements.pageSubtitle.innerText = "Manage nested chapters, examples, and quizzes.";

    const res = await api.fetch(`/learning/chapters/?page=${state.currentPageNum}&search=${state.currentSearch}`);
    if (!res.ok) return;

    const chapters = res.data.results || [];
    renderPagination(res.data);

    elements.mainView.innerHTML = `
        <div class="glass animate-in" style="padding: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>Chapters Hierarchy</h3>
                <button class="btn btn-primary" onclick="openEntityModal('learning/chapters', null)">
                    + Add New Chapter
                </button>
            </div>
            
            <div class="chapter-list" style="display:flex; flex-direction:column; gap:1.5rem;">
                ${chapters.map(chapter => `
                    <div class="glass" style="padding: 1.5rem; border-color: rgba(99, 102, 241, 0.2);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="color:var(--primary); font-weight:700;">Chapter ${chapter.order}</span>
                                <h4 style="font-size:1.25rem;">${chapter.title}</h4>
                            </div>
                            <div style="display:flex; gap:0.5rem;">
                                <button class="btn" onclick="openEntityModal('learning/chapters', ${chapter.id})" style="background:rgba(255,255,255,0.05); padding: 0.4rem 0.6rem;">✏️ Edit</button>
                                <button class="btn" onclick="deleteEntry('learning/chapters', ${chapter.id})" style="background:rgba(239, 68, 68, 0.1); color:var(--danger); padding: 0.4rem 0.6rem;">🗑️ Delete</button>
                            </div>
                        </div>
                        
                        <div style="margin-top: 1rem; display:grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div class="inner-stat glass" style="background:rgba(0,0,0,0.1); padding:0.75rem;">
                                <span style="font-size:0.75rem; color:var(--text-muted);">Examples</span>
                                <div style="font-weight:600;">${chapter.examples ? chapter.examples.length : 0} Items</div>
                            </div>
                            <div class="inner-stat glass" style="background:rgba(0,0,0,0.1); padding:0.75rem;">
                                <span style="font-size:0.75rem; color:var(--text-muted);">Quiz Questions</span>
                                <div style="font-weight:600;">${chapter.quizzes ? chapter.quizzes.length : 0} Items</div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// --- EVENT LISTENERS ---
elements.loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    login(document.getElementById('username').value, document.getElementById('password').value);
});

elements.menuItems.forEach(item => {
    item.addEventListener('click', () => loadPage(item.dataset.page));
});

elements.logoutBtn.addEventListener('click', logout);

// Auto-init if token exists
if (state.token) initDashboard();

// --- STUDENT REPORT LOGIC ---
window.viewStudentReport = async function (studentId) {
    const reportModal = document.getElementById('report-modal');
    const content = document.getElementById('report-content');

    reportModal.classList.add('active');
    content.innerHTML = `<div style="text-align:center; padding: 3rem; color:var(--primary);">Loading comprehensive report...</div>`;

    const res = await api.fetch(`/students/${studentId}/student_report/`);
    if (!res.ok) {
        content.innerHTML = `<div style="color:var(--danger); text-align:center; padding:3rem;">Failed to load report data.</div>`;
        return;
    }

    const { profile, section_summary, recent_activity, wellbeing_trend, call_history } = res.data;

    let activityHtml = recent_activity.length > 0 ?
        recent_activity.map(log => `
            <tr>
                <td>${new Date(log.timestamp).toLocaleDateString()}</td>
                <td style="font-weight:600; color:var(--primary);">${log.activity_type}</td>
                <td>${log.duration_minutes}m</td>
                <td style="font-weight:700;">${log.quiz_score !== null ? log.quiz_score + '%' : '-'}</td>
            </tr>
        `).join('') : `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:2rem;">No recent activities logged.</td></tr>`;

    let callHistoryHtml = call_history && call_history.length > 0 ?
        call_history.map(call => `
            <tr>
                <td>${new Date(call.timestamp).toLocaleString()}</td>
                <td style="font-weight:600; color:var(--primary);">${call.call_type} (${call.contact_name || 'Gemini'})</td>
                <td>${Math.floor(call.duration_seconds / 60)}m ${call.duration_seconds % 60}s</td>
                <td>
                    ${call.recording_file ? `
                        <audio controls style="height: 30px; width: 180px;">
                            <source src="${call.recording_file}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    ` : '<span style="color:var(--text-muted);">No recording</span>'}
                </td>
            </tr>
        `).join('') : `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:2rem;">No call history found.</td></tr>`;

    content.innerHTML = `
        <div style="display:flex; align-items:center; gap:1.5rem; margin-bottom: 2rem; border-bottom: 1px solid var(--glass-border); padding-bottom: 1.5rem;">
            <div style="width:64px; height:64px; border-radius:50%; background:var(--primary); display:flex; align-items:center; justify-content:center; font-size:1.5rem;">🎓</div>
            <div>
                <h2 style="margin:0;">${profile.username} <span style="font-size: 0.9rem; color:var(--text-muted); font-weight:400;">(${profile.student_id})</span></h2>
                <p style="margin:0.25rem 0 0; color:var(--text-muted);">${profile.email} • Level: ${profile.current_level} • ${profile.total_xp} Total XP</p>
            </div>
        </div>

        <h3>Section Analytics</h3>
        <div class="report-grid">
            ${Object.entries(section_summary).map(([section, stats]) => `
                <div class="report-section-card">
                    <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:0.5rem;">${section}</div>
                    <div style="font-size:1.25rem; font-weight:700;">${stats.total_time}m</div>
                    <div style="font-size:0.7rem; color:var(--text-muted);">${stats.sessions} sessions • Avg: ${stats.avg_score}%</div>
                </div>
            `).join('')}
        </div>

        <div style="margin: 2.5rem 0;">
            <h3 style="margin-bottom:1rem;">7-Day Activity Trend (Minutes)</h3>
            <div id="report-chart" class="chart-container" style="height: 120px;">
                ${Object.entries(wellbeing_trend).map(([date, mins]) => {
        const max = Math.max(...Object.values(wellbeing_trend), 1);
        return `
                        <div class="chart-bar" style="height:${(mins / max) * 100}%">
                            <div class="chart-tooltip">${mins} mins</div>
                            <span class="chart-label" style="font-size:0.6rem;">${date.split('-').slice(1).join('/')}</span>
                        </div>
                    `;
    }).join('')}
            </div>
        </div>

        <h3 style="margin-top:2.5rem;">Recent Activity Logs</h3>
        <div class="table-container" style="margin-bottom: 2.5rem;">
            <table class="report-log-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Activity</th>
                        <th>Duration</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    ${activityHtml}
                </tbody>
            </table>
        </div>

        <h3>History & Call Recordings</h3>
        <div class="table-container">
            <table class="report-log-table">
                <thead>
                    <tr>
                        <th>Date & Time</th>
                        <th>Contact</th>
                        <th>Duration</th>
                        <th>Playback</th>
                    </tr>
                </thead>
                <tbody>
                    ${callHistoryHtml}
                </tbody>
            </table>
        </div>
    `;
};

window.closeReportModal = function () {
    document.getElementById('report-modal').classList.remove('active');
};

// --- XP MANAGEMENT ---
async function renderXPManagement() {
    elements.pageTitle.innerText = "XP Management";
    elements.pageSubtitle.innerText = "Configure global level logic and override student progress.";

    const [configRes, studentsRes] = await Promise.all([
        api.fetch('/xp-config/'),
        api.fetch(`/students/`)
    ]);

    if (!configRes.ok || !studentsRes.ok) return;

    const config = configRes.data;

    // Helper to render a compact section card
    const renderSectionCard = (title, icon, type) => `
        <div class="xp-dashboard-card">
            <header>
                <i class="fas ${icon}"></i>
                <h4>${title} Progression</h4>
            </header>
            <form onsubmit="window.saveXPConfig(event)">
                <div class="xp-track mini">
                    <div class="lvl-card">
                        <label style="font-size: 0.65rem; color: var(--text-muted); display: block; margin-bottom: 0.3rem;">REWARD FOR BEG</label>
                        <input type="number" name="${type.toLowerCase()}_beginner_xp" class="xp-arrow-input" value="${config[type.toLowerCase() + '_beginner_xp']}">
                    </div>
                    <div class="xp-arrow-container">
                        <div class="xp-arrow"></div>
                    </div>
                    <div class="lvl-card">
                        <label style="font-size: 0.65rem; color: var(--text-muted); display: block; margin-bottom: 0.3rem;">REWARD FOR INT</label>
                        <input type="number" name="${type.toLowerCase()}_intermediate_xp" class="xp-arrow-input" value="${config[type.toLowerCase() + '_intermediate_xp']}">
                    </div>
                    <div class="xp-arrow-container">
                        <div class="xp-arrow"></div>
                    </div>
                    <div class="lvl-card">
                        <label style="font-size: 0.65rem; color: var(--text-muted); display: block; margin-bottom: 0.3rem;">REWARD FOR PRO</label>
                        <input type="number" name="${type.toLowerCase()}_professional_xp" class="xp-arrow-input" value="${config[type.toLowerCase() + '_professional_xp']}">
                    </div>
                </div>
                <div style="display: flex; justify-content: flex-end; margin-top: 1.5rem;">
                    <button type="submit" class="btn btn-primary btn-sm" style="padding: 0.4rem 1rem;">Save ${title}</button>
                </div>
            </form>
        </div>
    `;

    elements.mainView.innerHTML = `
        <div class="animate-in">
            <!-- Top Section: System Thresholds -->
            <div class="glass" style="padding: 1.5rem; margin-bottom: 1.5rem;">
                <h3 style="margin-bottom: 1.5rem; color: var(--accent); font-size: 1.1rem; display: flex; align-items: center; gap: 0.75rem;">
                    <i class="fas fa-project-diagram"></i> Global XP Engine
                </h3>
                <form onsubmit="window.saveXPConfig(event)" style="display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;">
                    <div class="xp-track mini" style="flex: 1; min-width: 400px;">
                        <div class="lvl-card">
                            <h4>BEGINNER</h4>
                            <span>0 XP (Start)</span>
                        </div>
                        <div class="xp-arrow-container">
                            <div class="xp-arrow-label" style="top: -25px;"><label style="font-size: 0.65rem; color: var(--accent);">PROMOTES TO INT @</label></div>
                            <div class="xp-arrow-label"><input type="number" name="overall_intermediate" class="xp-arrow-input" value="${config.overall_intermediate}"></div>
                            <div class="xp-arrow"></div>
                        </div>
                        <div class="lvl-card">
                            <h4>INTERMEDIATE</h4>
                            <span>Min: ${config.overall_intermediate} XP</span>
                        </div>
                        <div class="xp-arrow-container">
                            <div class="xp-arrow-label" style="top: -25px;"><label style="font-size: 0.65rem; color: var(--accent);">PROMOTES TO PRO @</label></div>
                            <div class="xp-arrow-label"><input type="number" name="overall_professional" class="xp-arrow-input" value="${config.overall_professional}"></div>
                            <div class="xp-arrow"></div>
                        </div>
                        <div class="lvl-card">
                            <h4>PROFESSIONAL</h4>
                            <span>Min: ${config.overall_professional} XP</span>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary" style="height: 40px; padding: 0 1.5rem;">Save Engine</button>
                </form>
            </div>

            <!-- Main Grid: Section Rewards -->
            <div class="xp-dashboard-grid">
                ${renderSectionCard('Listening', 'fa-headphones', 'Listening')}
                ${renderSectionCard('Speaking', 'fa-microphone', 'Speaking')}
                ${renderSectionCard('Reading', 'fa-book-open', 'Reading')}
                ${renderSectionCard('Writing', 'fa-pen-fancy', 'Writing')}
                ${renderSectionCard('Grammar', 'fa-graduation-cap', 'Learning')}
            </div>

            <!-- Bottom Row: Note -->
            <div style="margin-top: 1.5rem;">
                <div class="glass" style="padding: 1rem; border-style: dashed; border-color: var(--accent); display: flex; align-items: center; gap: 0.75rem;">
                    <i class="fas fa-info-circle" style="color: var(--accent); font-size: 1rem;"></i>
                    <p style="font-size: 0.75rem; color: var(--text-muted); line-height: 1.3;">
                        <strong>Note:</strong> All sections now follow a level-based automated reward system.
                    </p>
                </div>
            </div>
        </div>
    `;
}

window.saveXPConfig = async function (e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const body = Object.fromEntries(formData.entries());

    // Convert to numbers
    for (let key in body) body[key] = parseInt(body[key]);

    const res = await api.fetch('/xp-config/', {
        method: 'PATCH',
        body: JSON.stringify(body)
    });

    if (res.ok) {
        alert("Global XP Logic Updated Successfully!");
        renderXPManagement();
    } else {
        alert("Failed to update global config.");
    }
};


// Removed window.saveStudentXP as per manual override removal
