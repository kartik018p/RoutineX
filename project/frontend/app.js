/**
 * RoutineX — Frontend Application
 * Vanilla JS SPA with full API integration
 */

// ═══════════════════════════════════════════════════════════
// API Helpers
// ═══════════════════════════════════════════════════════════
const API_BASE = "/api";

async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        ...options,
    };

    try {
        const res = await fetch(url, config);
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || `Request failed (${res.status})`);
        }

        return data;
    } catch (err) {
        if (err.message === "Failed to fetch") {
            throw new Error("Cannot connect to server. Is the backend running?");
        }
        throw err;
    }
}

// ═══════════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════════
const state = {
    user: null,
    habits: [],
    currentPage: "dashboard",
    theme: localStorage.getItem("routinex-theme") || "dark",
    charts: {},
};

// ═══════════════════════════════════════════════════════════
// DOM References
// ═══════════════════════════════════════════════════════════
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const authContainer = $("#auth-container");
const appContainer = $("#app-container");
const loginForm = $("#login-form");
const registerForm = $("#register-form");
const authError = $("#auth-error");
const habitModal = $("#habit-modal");

// ═══════════════════════════════════════════════════════════
// Theme
// ═══════════════════════════════════════════════════════════
function setTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("routinex-theme", theme);
}

function toggleTheme() {
    setTheme(state.theme === "dark" ? "light" : "dark");
}

// Init theme
setTheme(state.theme);

// ═══════════════════════════════════════════════════════════
// Auth
// ═══════════════════════════════════════════════════════════
function showAuthError(msg) {
    authError.textContent = msg;
    authError.hidden = false;
    setTimeout(() => (authError.hidden = true), 5000);
}

function hideAuthError() {
    authError.hidden = true;
}

// Toggle between login / register
$("#show-register").addEventListener("click", (e) => {
    e.preventDefault();
    loginForm.classList.remove("active");
    registerForm.classList.add("active");
    hideAuthError();
});

$("#show-login").addEventListener("click", (e) => {
    e.preventDefault();
    registerForm.classList.remove("active");
    loginForm.classList.add("active");
    hideAuthError();
});

// Login
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("#login-btn");
    const loader = btn.querySelector(".btn-loader");
    const span = btn.querySelector("span");

    span.textContent = "Signing in...";
    loader.hidden = false;
    btn.disabled = true;

    try {
        const data = await apiFetch("/login", {
            method: "POST",
            body: JSON.stringify({
                email: $("#login-email").value,
                password: $("#login-password").value,
            }),
        });

        state.user = data.user;
        showApp();
        toast("Welcome back, " + data.user.name + "! 👋", "success");
    } catch (err) {
        showAuthError(err.message);
    } finally {
        span.textContent = "Sign In";
        loader.hidden = true;
        btn.disabled = false;
    }
});

// Register
registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("#register-btn");
    const loader = btn.querySelector(".btn-loader");
    const span = btn.querySelector("span");

    span.textContent = "Creating account...";
    loader.hidden = false;
    btn.disabled = true;

    try {
        const data = await apiFetch("/register", {
            method: "POST",
            body: JSON.stringify({
                name: $("#reg-name").value,
                email: $("#reg-email").value,
                password: $("#reg-password").value,
            }),
        });

        state.user = data.user;
        showApp();
        toast("Account created! Let's build great habits. 🎉", "success");
    } catch (err) {
        showAuthError(err.message);
    } finally {
        span.textContent = "Create Account";
        loader.hidden = true;
        btn.disabled = false;
    }
});

// Logout
$("#logout-btn").addEventListener("click", async () => {
    try {
        await apiFetch("/logout", { method: "POST" });
    } catch (_) {}
    state.user = null;
    showAuth();
    toast("Logged out successfully", "info");
});

// Check session
async function checkSession() {
    try {
        const data = await apiFetch("/me");
        state.user = data.user;
        showApp();
    } catch (_) {
        showAuth();
    }
}

function showAuth() {
    authContainer.hidden = false;
    appContainer.hidden = true;
}

function showApp() {
    authContainer.hidden = true;
    appContainer.hidden = false;
    updateUserUI();
    updateGreeting();
    navigateTo("dashboard");
}

function updateUserUI() {
    if (!state.user) return;
    const initials = state.user.name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
    $("#user-avatar").textContent = initials;
    $("#user-name").textContent = state.user.name;
    $("#user-email").textContent = state.user.email;

    if (state.user.preferences?.theme) {
        setTheme(state.user.preferences.theme);
    }
}

function updateGreeting() {
    const hour = new Date().getHours();
    let greeting;
    if (hour < 12) greeting = "Good morning";
    else if (hour < 17) greeting = "Good afternoon";
    else greeting = "Good evening";

    const name = state.user?.name?.split(" ")[0] || "";
    $("#greeting").textContent = `${greeting}, ${name}! Let's build great habits.`;
}

// ═══════════════════════════════════════════════════════════
// Navigation
// ═══════════════════════════════════════════════════════════
function navigateTo(page) {
    state.currentPage = page;

    // Update nav items
    $$(".nav-item").forEach((item) => {
        item.classList.toggle("active", item.dataset.page === page);
    });

    // Update pages
    $$(".page").forEach((p) => {
        p.classList.toggle("active", p.id === `page-${page}`);
    });

    // Close mobile sidebar
    $("#sidebar").classList.remove("open");
    const overlay = $(".mobile-overlay");
    if (overlay) overlay.classList.remove("active");

    // Load page data
    switch (page) {
        case "dashboard":
            loadDashboard();
            break;
        case "habits":
            loadHabits();
            break;
        case "recommendations":
            loadRecommendations();
            break;
        case "progress":
            loadProgress();
            break;
    }
}

$$(".nav-item").forEach((item) => {
    item.addEventListener("click", () => navigateTo(item.dataset.page));
});

// Mobile sidebar
$("#mobile-menu-btn").addEventListener("click", () => {
    const sidebar = $("#sidebar");
    sidebar.classList.toggle("open");

    let overlay = $(".mobile-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "mobile-overlay";
        document.body.appendChild(overlay);
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("open");
            overlay.classList.remove("active");
        });
    }
    overlay.classList.toggle("active", sidebar.classList.contains("open"));
});

// Theme toggles
$("#theme-toggle").addEventListener("click", toggleTheme);
$("#mobile-theme-toggle").addEventListener("click", toggleTheme);

// ═══════════════════════════════════════════════════════════
// Dashboard
// ═══════════════════════════════════════════════════════════
async function loadDashboard() {
    try {
        const [habitsData, progressData] = await Promise.all([
            apiFetch("/get-habits"),
            apiFetch("/progress?period=weekly"),
        ]);

        state.habits = habitsData.habits;
        renderDashboardStats(habitsData.habits, progressData);
        renderTodayHabits(habitsData.habits);
        renderWeeklyChart(progressData);
    } catch (err) {
        toast(err.message, "error");
    }
}

function renderDashboardStats(habits, progress) {
    const completedToday = habits.filter((h) => h.completed_today).length;
    const bestStreak = progress.streaks?.overall_best || 0;
    const weeklyRate = progress.overall_completion_rate || 0;

    $("#stat-completed").textContent = completedToday;
    $("#stat-streak").textContent = bestStreak;
    $("#stat-rate").textContent = weeklyRate + "%";
    $("#stat-total").textContent = habits.length;
    $("#today-count").textContent = `${completedToday} / ${habits.length}`;
}

function renderTodayHabits(habits) {
    const container = $("#habits-today-list");

    if (habits.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round">
                    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                    <path d="M9 12l2 2 4-4"/>
                </svg>
                <p>No habits yet. Add your first habit to get started!</p>
            </div>`;
        return;
    }

    container.innerHTML = habits
        .map(
            (h) => `
        <div class="habit-today-item ${h.completed_today ? "completed" : ""}" data-habit-id="${h.id}">
            <div class="habit-color-dot" style="background: ${h.color}"></div>
            <div class="habit-check ${h.completed_today ? "checked" : ""}" onclick="toggleHabit('${h.id}', event)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <div class="habit-today-info">
                <div class="habit-today-name">${escapeHtml(h.name)}</div>
                <div class="habit-today-meta">
                    <span>${getCategoryEmoji(h.category)} ${capitalize(h.category)}</span>
                    ${h.target_time ? `<span>⏰ ${h.target_time}</span>` : ""}
                </div>
            </div>
            ${h.streak > 0 ? `<div class="habit-today-streak">🔥 ${h.streak}</div>` : ""}
        </div>`
        )
        .join("");
}

function renderWeeklyChart(progress) {
    const ctx = $("#weekly-chart");
    if (!ctx) return;

    // Destroy old chart
    if (state.charts.weekly) state.charts.weekly.destroy();

    const labels = progress.daily_data.map((d) => formatDateShort(d.date));
    const data = progress.daily_data.map((d) => d.rate);

    const gradient = ctx.getContext("2d").createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, "rgba(108, 99, 255, 0.3)");
    gradient.addColorStop(1, "rgba(108, 99, 255, 0.01)");

    state.charts.weekly = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Completion Rate %",
                    data,
                    borderColor: "#3B82F6",
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    pointBackgroundColor: "#3B82F6",
                    pointBorderColor: "#fff",
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(17, 20, 39, 0.9)",
                    titleColor: "#F1F1F6",
                    bodyColor: "#9B9CB8",
                    borderColor: "rgba(255,255,255,0.1)",
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "rgba(155,156,184,0.6)", font: { size: 11 } },
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: {
                        color: "rgba(155,156,184,0.6)",
                        font: { size: 11 },
                        callback: (v) => v + "%",
                    },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════
// Habits CRUD
// ═══════════════════════════════════════════════════════════
async function loadHabits() {
    try {
        const data = await apiFetch("/get-habits");
        state.habits = data.habits;
        renderHabitsGrid(data.habits);
    } catch (err) {
        toast(err.message, "error");
    }
}

function renderHabitsGrid(habits) {
    const container = $("#habits-grid");

    if (habits.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M9 12l2 2 4-4"/>
                </svg>
                <h3>No habits yet</h3>
                <p>Create your first habit to start tracking!</p>
                <button class="btn btn-primary" onclick="openAddModal()">Add First Habit</button>
            </div>`;
        return;
    }

    container.innerHTML = habits
        .map(
            (h) => `
        <div class="habit-card" style="--habit-color: ${h.color}">
            <div class="habit-card-header">
                <div>
                    <div class="habit-card-name">${escapeHtml(h.name)}</div>
                    <div class="habit-card-category">${getCategoryEmoji(h.category)} ${capitalize(h.category)} · ${capitalize(h.frequency)}</div>
                </div>
                <div class="habit-card-actions">
                    <button class="btn-icon" onclick="openEditModal('${h.id}')" title="Edit">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="btn-icon" onclick="deleteHabit('${h.id}')" title="Delete" style="color: var(--danger)">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
            ${h.target_time ? `<div class="habit-card-time"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> ${h.target_time}</div>` : ""}
            ${h.description ? `<p style="font-size:0.8125rem; color:var(--text-secondary); margin-top:var(--space-sm)">${escapeHtml(h.description)}</p>` : ""}
            <div class="habit-card-stats">
                <div class="habit-stat">
                    <span class="habit-stat-value" style="color:${h.color}">${h.streak}</span>
                    <span class="habit-stat-label">Streak</span>
                </div>
                <div class="habit-stat">
                    <span class="habit-stat-value">${h.best_streak}</span>
                    <span class="habit-stat-label">Best</span>
                </div>
                <div class="habit-stat">
                    <span class="habit-stat-value">${h.total_completions}</span>
                    <span class="habit-stat-label">Total</span>
                </div>
            </div>
        </div>`
        )
        .join("");
}

// Toggle habit completion
async function toggleHabit(habitId, event) {
    if (event) event.stopPropagation();

    try {
        const data = await apiFetch("/track-habit", {
            method: "POST",
            body: JSON.stringify({ habit_id: habitId }),
        });

        if (data.completed) {
            toast(`Habit completed! 🎉 Streak: ${data.streak}`, "success");
        } else {
            toast("Habit untracked", "info");
        }

        // Refresh dashboard
        loadDashboard();
    } catch (err) {
        toast(err.message, "error");
    }
}

// Make toggleHabit global for inline onclick
window.toggleHabit = toggleHabit;

// Delete habit
async function deleteHabit(habitId) {
    if (!confirm("Are you sure you want to delete this habit? This cannot be undone.")) return;

    try {
        await apiFetch(`/delete-habit/${habitId}`, { method: "DELETE" });
        toast("Habit deleted", "info");
        loadHabits();
    } catch (err) {
        toast(err.message, "error");
    }
}
window.deleteHabit = deleteHabit;

// ═══════════════════════════════════════════════════════════
// Habit Modal
// ═══════════════════════════════════════════════════════════
function openAddModal() {
    $("#modal-title").textContent = "Add New Habit";
    $("#modal-save span").textContent = "Save Habit";
    $("#habit-edit-id").value = "";
    $("#habit-form").reset();

    // Reset color picker
    $$(".color-swatch").forEach((s) => s.classList.remove("active"));
    $('[data-color="#3B82F6"]').classList.add("active");

    habitModal.hidden = false;
}
window.openAddModal = openAddModal;

function openEditModal(habitId) {
    const habit = state.habits.find((h) => h.id === habitId);
    if (!habit) return;

    $("#modal-title").textContent = "Edit Habit";
    $("#modal-save span").textContent = "Update Habit";
    $("#habit-edit-id").value = habitId;
    $("#habit-name").value = habit.name;
    $("#habit-category").value = habit.category;
    $("#habit-frequency").value = habit.frequency;
    $("#habit-time").value = habit.target_time || "";
    $("#habit-desc").value = habit.description || "";

    // Set color
    $$(".color-swatch").forEach((s) => {
        s.classList.toggle("active", s.dataset.color === habit.color);
    });

    habitModal.hidden = false;
}
window.openEditModal = openEditModal;

function closeModal() {
    habitModal.hidden = true;
}

$("#modal-close").addEventListener("click", closeModal);
$("#modal-cancel").addEventListener("click", closeModal);

habitModal.addEventListener("click", (e) => {
    if (e.target === habitModal) closeModal();
});

// Color picker
$$(".color-swatch").forEach((swatch) => {
    swatch.addEventListener("click", () => {
        $$(".color-swatch").forEach((s) => s.classList.remove("active"));
        swatch.classList.add("active");
    });
});

// Save habit
$("#habit-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const editId = $("#habit-edit-id").value;
    const activeColor = $(".color-swatch.active");
    const color = activeColor ? activeColor.dataset.color : "#3B82F6";

    const habitData = {
        name: $("#habit-name").value,
        category: $("#habit-category").value,
        frequency: $("#habit-frequency").value,
        target_time: $("#habit-time").value,
        description: $("#habit-desc").value,
        color: color,
    };

    const btn = $("#modal-save");
    const loader = btn.querySelector(".btn-loader");
    const span = btn.querySelector("span");

    loader.hidden = false;
    btn.disabled = true;

    try {
        if (editId) {
            await apiFetch(`/edit-habit/${editId}`, {
                method: "PUT",
                body: JSON.stringify(habitData),
            });
            toast("Habit updated! ✏️", "success");
        } else {
            await apiFetch("/add-habit", {
                method: "POST",
                body: JSON.stringify(habitData),
            });
            toast("Habit created! 🎯", "success");
        }

        closeModal();
        if (state.currentPage === "habits") loadHabits();
        if (state.currentPage === "dashboard") loadDashboard();
    } catch (err) {
        toast(err.message, "error");
    } finally {
        loader.hidden = true;
        btn.disabled = false;
        span.textContent = editId ? "Update Habit" : "Save Habit";
    }
});

// Quick add buttons
["quick-add-btn", "add-habit-btn", "add-first-habit-btn"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", openAddModal);
});

// ═══════════════════════════════════════════════════════════
// Recommendations
// ═══════════════════════════════════════════════════════════
async function loadRecommendations() {
    const container = $("#recommendations-container");
    container.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Analyzing your habits with AI...</p>
        </div>`;

    try {
        const data = await apiFetch("/get-recommendations");
        renderRecommendations(data);
    } catch (err) {
        container.innerHTML = `
            <div class="empty-state">
                <p>⚠️ ${escapeHtml(err.message)}</p>
            </div>`;
    }
}

function renderRecommendations(data) {
    const container = $("#recommendations-container");

    let html = "";

    // Model status
    html += `<div style="margin-bottom: var(--space-md); font-size: 0.8125rem; color: var(--text-muted)">
        ${data.model_trained ? "🤖 ML model trained and active" : "📊 Collecting data for ML model training"}
    </div>`;

    // General tips
    if (data.general_tips?.length) {
        html += `<div class="reco-general">`;
        data.general_tips.forEach((tip) => {
            html += `<div class="reco-general-tip">${escapeHtml(tip)}</div>`;
        });
        html += `</div>`;
    }

    // Individual recommendations
    if (data.recommendations?.length) {
        html += `<div class="reco-grid">`;
        data.recommendations.forEach((rec) => {
            const probClass = rec.success_probability >= 60 ? "high" : rec.success_probability >= 30 ? "medium" : "low";

            html += `
            <div class="reco-card priority-${rec.priority}">
                <div class="reco-card-header">
                    <span class="reco-habit-name">${escapeHtml(rec.habit_name)}</span>
                    <span class="reco-probability ${probClass}">${rec.success_probability}%</span>
                </div>
                <div class="reco-meta">
                    <span class="reco-meta-item">⏰ Best: ${rec.best_time}</span>
                    <span class="reco-meta-item">📍 ${capitalize(rec.time_period)}</span>
                    <span class="reco-meta-item">${rec.priority === "high" ? "🔴" : rec.priority === "medium" ? "🟡" : "🟢"} ${capitalize(rec.priority)}</span>
                </div>
                <div class="reco-suggestions">
                    ${rec.suggestions.map((s) => `<div class="reco-suggestion">${escapeHtml(s)}</div>`).join("")}
                </div>
            </div>`;
        });
        html += `</div>`;
    } else {
        html += `<div class="empty-state"><p>No specific recommendations yet. Keep tracking your habits!</p></div>`;
    }

    container.innerHTML = html;
}

// Retrain button
$("#retrain-btn").addEventListener("click", async () => {
    try {
        const data = await apiFetch("/retrain-model", { method: "POST" });
        toast(data.message, data.success ? "success" : "info");
        loadRecommendations();
    } catch (err) {
        toast(err.message, "error");
    }
});

// ═══════════════════════════════════════════════════════════
// Progress
// ═══════════════════════════════════════════════════════════
let currentPeriod = "weekly";

async function loadProgress() {
    try {
        const data = await apiFetch(`/progress?period=${currentPeriod}`);
        renderProgressStats(data);
        renderProgressLineChart(data);
        renderProgressDoughnut(data);
        renderProgressTable(data);
    } catch (err) {
        toast(err.message, "error");
    }
}

function renderProgressStats(data) {
    $("#prog-rate").textContent = data.overall_completion_rate + "%";
    $("#prog-streak").textContent = data.streaks?.current_best || 0;
    $("#prog-best").textContent = data.streaks?.overall_best || 0;
}

function renderProgressLineChart(data) {
    const ctx = $("#progress-line-chart");
    if (state.charts.progressLine) state.charts.progressLine.destroy();

    const labels = data.daily_data.map((d) => formatDateShort(d.date));
    const rates = data.daily_data.map((d) => d.rate);
    const counts = data.daily_data.map((d) => d.completed);

    const gradient = ctx.getContext("2d").createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, "rgba(16, 185, 129, 0.25)");
    gradient.addColorStop(1, "rgba(16, 185, 129, 0.01)");

    state.charts.progressLine = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Completion Rate %",
                    data: rates,
                    borderColor: "#10B981",
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    pointBackgroundColor: "#10B981",
                    pointBorderColor: "#fff",
                    pointBorderWidth: 2,
                    pointRadius: 3,
                    fill: true,
                    tension: 0.4,
                    yAxisID: "y",
                },
                {
                    label: "Habits Completed",
                    data: counts,
                    borderColor: "#3B82F6",
                    borderWidth: 2,
                    pointRadius: 0,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    yAxisID: "y1",
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    labels: { color: "rgba(155,156,184,0.8)", font: { size: 11 } },
                },
                tooltip: {
                    backgroundColor: "rgba(17, 20, 39, 0.9)",
                    titleColor: "#F1F1F6",
                    bodyColor: "#9B9CB8",
                    cornerRadius: 8,
                    padding: 12,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "rgba(155,156,184,0.6)", font: { size: 11 } },
                },
                y: {
                    position: "left",
                    min: 0,
                    max: 100,
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: {
                        color: "rgba(155,156,184,0.6)",
                        font: { size: 11 },
                        callback: (v) => v + "%",
                    },
                },
                y1: {
                    position: "right",
                    min: 0,
                    grid: { display: false },
                    ticks: {
                        color: "rgba(155,156,184,0.4)",
                        font: { size: 11 },
                        stepSize: 1,
                    },
                },
            },
        },
    });
}

function renderProgressDoughnut(data) {
    const ctx = $("#progress-doughnut-chart");
    if (state.charts.progressDoughnut) state.charts.progressDoughnut.destroy();

    if (!data.habit_stats?.length) {
        state.charts.progressDoughnut = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["No data"],
                datasets: [{ data: [1], backgroundColor: ["rgba(155,156,184,0.2)"] }],
            },
            options: { responsive: true, maintainAspectRatio: false },
        });
        return;
    }

    state.charts.progressDoughnut = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: data.habit_stats.map((h) => h.name),
            datasets: [
                {
                    data: data.habit_stats.map((h) => h.completions),
                    backgroundColor: data.habit_stats.map((h) => h.color),
                    borderWidth: 0,
                    hoverOffset: 8,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "65%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "rgba(155,156,184,0.8)",
                        font: { size: 11 },
                        padding: 12,
                        usePointStyle: true,
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(17, 20, 39, 0.9)",
                    cornerRadius: 8,
                    padding: 12,
                },
            },
        },
    });
}

function renderProgressTable(data) {
    const tbody = $("#progress-table-body");

    if (!data.habit_stats?.length) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:var(--space-xl)">No habit data yet</td></tr>`;
        return;
    }

    tbody.innerHTML = data.habit_stats
        .map(
            (h) => `
        <tr>
            <td>
                <div style="display:flex; align-items:center; gap:var(--space-sm)">
                    <div style="width:8px; height:8px; border-radius:50%; background:${h.color}; flex-shrink:0"></div>
                    ${escapeHtml(h.name)}
                </div>
            </td>
            <td>${h.completions} / ${h.possible}</td>
            <td>
                ${h.rate}%
                <div class="progress-bar-mini">
                    <div class="progress-bar-fill" style="width:${h.rate}%; background:${h.color}"></div>
                </div>
            </td>
            <td>${h.streak > 0 ? "🔥 " + h.streak : "—"}</td>
            <td>${h.best_streak > 0 ? "🏆 " + h.best_streak : "—"}</td>
        </tr>`
        )
        .join("");
}

// Period selector
$$(".period-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        $$(".period-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentPeriod = btn.dataset.period;
        loadProgress();
    });
});

// ═══════════════════════════════════════════════════════════
// Toast
// ═══════════════════════════════════════════════════════════
function toast(message, type = "info") {
    const container = $("#toast-container");
    const el = document.createElement("div");
    el.className = `toast ${type}`;

    const icons = {
        success: "✅",
        error: "❌",
        info: "ℹ️",
    };

    el.innerHTML = `<span>${icons[type] || ""}</span> ${escapeHtml(message)}`;
    container.appendChild(el);

    setTimeout(() => {
        el.remove();
    }, 3200);
}

// ═══════════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════════
function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function capitalize(str) {
    return str ? str.charAt(0).toUpperCase() + str.slice(1) : "";
}

function getCategoryEmoji(cat) {
    const emojis = {
        health: "🏃",
        fitness: "💪",
        mindfulness: "🧘",
        learning: "📚",
        productivity: "⚡",
        social: "🤝",
        creativity: "🎨",
        general: "📌",
    };
    return emojis[cat] || "📌";
}

function formatDateShort(dateStr) {
    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString("en", { month: "short", day: "numeric" });
}

// ═══════════════════════════════════════════════════════════
// Init
// ═══════════════════════════════════════════════════════════
checkSession();
