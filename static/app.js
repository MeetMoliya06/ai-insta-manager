// AI SOCIAL MEDIA MANAGER — Multi-Company Front-End Orchestrator

document.addEventListener("DOMContentLoaded", () => {

    const PLATFORM_ICONS = {
        instagram: "fa-brands fa-instagram",
        facebook: "fa-brands fa-facebook",
        linkedin: "fa-brands fa-linkedin",
        google_business: "fa-solid fa-location-dot",
    };

    const PLATFORM_SETUP_HINTS = {
        facebook: "Needs a Meta developer app approved for pages_manage_posts / pages_read_engagement (Graph API).",
        linkedin: "Needs LinkedIn Community Management API access, which requires LinkedIn's approval.",
        google_business: "Needs a Google Cloud project with Business Profile API production access approved by Google.",
    };

    // STATE VARIABLES
    let state = {
        config: { has_api_key: false, default_pillars: [], platforms: [], platform_labels: {}, has_supabase: false },
        companies: [],
        activeCompanyId: localStorage.getItem("activeCompanyId") || null,
        activePlatform: localStorage.getItem("activePlatform") || "instagram",
        connections: [],

        history: { posts: [] },
        calendar: [], // full company calendar, spans all platforms
        calendarFilterPlatform: "all",
        activePostIndex: null,
        hasUnsavedChanges: false,

        editingCompanyId: null, // set when company-modal is in "edit" mode

        trends: null, // cached trends payload for the active company/platform
        trendsLoading: false,
    };

    // DOM ELEMENTS
    const elements = {
        appContainer: document.getElementById("app-container"),

        companySelect: document.getElementById("company-select"),
        editCompanyBtn: document.getElementById("edit-company-btn"),
        newCompanyBtn: document.getElementById("new-company-btn"),
        platformSelect: document.getElementById("platform-select"),
        openConnectionsBtn: document.getElementById("open-connections-btn"),

        historyValue: document.querySelector("#metric-history .metric-value"),
        scheduledValue: document.querySelector("#metric-scheduled .metric-value"),
        openSettingsBtn: document.getElementById("open-settings-btn"),
        closeSettingsBtn: document.getElementById("close-settings-btn"),
        cancelSettingsBtn: document.getElementById("cancel-settings-btn"),
        saveSettingsBtn: document.getElementById("save-settings-btn"),
        settingsModal: document.getElementById("settings-modal"),
        settingsApiKey: document.getElementById("settings-api-key"),
        toggleKeyVisibility: document.getElementById("toggle-key-visibility"),
        keyStatusBox: document.getElementById("key-status-box"),
        keyStatusIndicator: document.getElementById("key-status-indicator"),
        keyStatusText: document.getElementById("key-status-text"),

        settingsSupabaseUrl: document.getElementById("settings-supabase-url"),
        settingsSupabaseKey: document.getElementById("settings-supabase-key"),
        supabaseStatusBox: document.getElementById("supabase-status-box"),
        supabaseStatusIndicator: document.getElementById("supabase-status-indicator"),
        supabaseStatusText: document.getElementById("supabase-status-text"),

        brandHandleBadge: document.getElementById("brand-handle-badge"),
        brandHandleIcon: document.getElementById("brand-handle-icon"),
        brandHandleText: document.getElementById("brand-handle-text"),
        metricFollowers: document.querySelector("#metric-followers .metric-value"),
        metricFollowing: document.querySelector("#metric-following .metric-value"),
        metricViews: document.querySelector("#metric-views .metric-value"),

        planWeeks: document.getElementById("plan-weeks"),
        postsPerWeek: document.getElementById("posts-per-week"),
        generatorModel: document.getElementById("generator-model"),
        generatePlatformHint: document.getElementById("generate-platform-hint"),
        pillarsToggle: document.getElementById("pillars-toggle"),
        pillarsContainer: document.getElementById("pillars-container"),
        pillarsChecklist: document.getElementById("pillars-checklist"),

        generateBtn: document.getElementById("generate-btn"),
        ideaInput: document.getElementById("idea-input"),
        ideaGenerateBtn: document.getElementById("idea-generate-btn"),
        ideaPlatformHint: document.getElementById("idea-platform-hint"),
        saveBtn: document.getElementById("save-btn"),
        exportBtn: document.getElementById("export-btn"),

        genLoader: document.getElementById("gen-loader"),
        progressBar: document.getElementById("progress-bar"),
        loaderStatusText: document.getElementById("loader-status-text"),

        calendarPlatformFilter: document.getElementById("calendar-platform-filter"),
        activeCalendarBadge: document.getElementById("active-calendar-badge"),
        calendarTimelineList: document.getElementById("calendar-timeline-list"),
        calendarEmptyState: document.getElementById("calendar-empty-state"),

        studioPanel: document.getElementById("studio-panel"),
        studioEmptyState: document.getElementById("studio-empty-state"),
        studioEditorContent: document.getElementById("studio-editor-content"),

        studioPostNumber: document.getElementById("studio-post-number"),
        studioPostType: document.getElementById("studio-post-type"),
        studioDatetime: document.getElementById("studio-datetime"),
        studioPlatformBadge: document.getElementById("studio-platform-badge"),
        studioFormatBadge: document.getElementById("studio-format-badge"),
        studioHookInput: document.getElementById("studio-hook-input"),
        studioCaptionInput: document.getElementById("studio-caption-input"),
        studioPromptInput: document.getElementById("studio-prompt-input"),
        studioHashtagsInput: document.getElementById("studio-hashtags-input"),
        studioNotesInput: document.getElementById("studio-notes-input"),
        studioToolRec: document.getElementById("studio-tool-recommendation"),
        studioDoneBtn: document.getElementById("studio-done-btn"),
        generateImageBtn: document.getElementById("generate-image-btn"),
        generatedImagePreview: document.getElementById("generated-image-preview"),
        generatedImagePreviewImg: document.getElementById("generated-image-preview-img"),

        copyHookBtn: document.getElementById("copy-hook-btn"),
        copyCaptionBtn: document.getElementById("copy-caption-btn"),
        copyPromptBtn: document.getElementById("copy-prompt-btn"),
        copyHashtagsBtn: document.getElementById("copy-hashtags-btn"),

        historyHeaderBtn: document.getElementById("history-header-btn"),
        historyContentArea: document.getElementById("history-content-area"),
        historyToggleBtn: document.getElementById("history-toggle-btn"),
        historySearch: document.getElementById("history-search"),
        historyTableBody: document.getElementById("history-table-body"),
        historySubtitle: document.getElementById("history-subtitle"),

        companyModal: document.getElementById("company-modal"),
        companyModalTitle: document.getElementById("company-modal-title"),
        companyName: document.getElementById("company-name"),
        companyIndustry: document.getElementById("company-industry"),
        companyContext: document.getElementById("company-context"),
        companyAudience: document.getElementById("company-audience"),
        companyVoice: document.getElementById("company-voice"),
        companyCta: document.getElementById("company-cta"),
        companyPillars: document.getElementById("company-pillars"),
        companyWebsite: document.getElementById("company-website"),
        companyAutoResearch: document.getElementById("company-auto-research"),
        autoResearchField: document.getElementById("auto-research-field"),
        researchStatusBox: document.getElementById("research-status-box"),
        researchStatusText: document.getElementById("research-status-text"),
        researchSummaryText: document.getElementById("research-summary-text"),
        researchSources: document.getElementById("research-sources"),
        researchLoading: document.getElementById("research-loading"),
        rerunResearchBtn: document.getElementById("rerun-research-btn"),
        saveCompanyBtn: document.getElementById("save-company-btn"),
        cancelCompanyBtn: document.getElementById("cancel-company-btn"),
        closeCompanyBtn: document.getElementById("close-company-btn"),
        deleteCompanyBtn: document.getElementById("delete-company-btn"),

        trendsPanel: document.getElementById("trends-panel"),
        trendsCardsRow: document.getElementById("trends-cards-row"),
        trendsEmptyHint: document.getElementById("trends-empty-hint"),
        trendsPlatformLabel: document.getElementById("trends-platform-label"),
        trendsUpdatedAt: document.getElementById("trends-updated-at"),
        refreshTrendsBtn: document.getElementById("refresh-trends-btn"),
        useTrendsCheckbox: document.getElementById("use-trends-checkbox"),

        studioScriptInput: document.getElementById("studio-script-input"),
        studioEditingStyleInput: document.getElementById("studio-editing-style-input"),
        copyScriptBtn: document.getElementById("copy-script-btn"),
        copyEditingStyleBtn: document.getElementById("copy-editing-style-btn"),

        connectionsModal: document.getElementById("connections-modal"),
        connectionsBody: document.getElementById("connections-body"),
        closeConnectionsBtn: document.getElementById("close-connections-btn"),
        closeConnectionsFooterBtn: document.getElementById("close-connections-footer-btn"),

        toastNotif: document.getElementById("toast-notif"),
        toastText: document.getElementById("toast-text"),
    };

    async function apiFetch(url, options = {}) {
        return fetch(url, options);
    }

    // ══════════════════════════════════════════════════════
    // INITIALIZATION
    // ══════════════════════════════════════════════════════

    let initialized = false;

    async function init() {
        if (!initialized) {
            setupEventListeners();
            initialized = true;
        }

        try {
            await loadConfig();
            await loadCompanies();
        } catch (err) {
            console.error("⚠️ Initialization failed:", err);
        }
    }

    function activeCompany() {
        return state.companies.find(c => String(c.id) === String(state.activeCompanyId));
    }

    // ══════════════════════════════════════════════════════
    // CONFIG
    // ══════════════════════════════════════════════════════

    async function loadConfig() {
        try {
            const res = await apiFetch("/api/config");
            if (!res.ok) throw new Error("Failed to load configuration");
            state.config = await res.json();
            updateConfigUI();
        } catch (err) {
            console.error(err);
            showToast("Error loading config: " + err.message, "error");
        }
    }

    function updateConfigUI() {
        if (state.config.has_api_key) {
            elements.keyStatusIndicator.className = "status-indicator success";
            elements.keyStatusText.textContent = "Gemini API Key is active & configured.";
        } else {
            elements.keyStatusIndicator.className = "status-indicator error";
            elements.keyStatusText.textContent = "No Gemini API Key found. Configure key to start.";
        }

        if (state.config.has_supabase) {
            elements.supabaseStatusIndicator.className = "status-indicator success";
            elements.supabaseStatusText.textContent = "Supabase cloud sync is active — companies are stored centrally.";
            elements.settingsSupabaseUrl.value = state.config.supabase_url || "";
        } else {
            elements.supabaseStatusIndicator.className = "status-indicator";
            elements.supabaseStatusText.textContent = "Supabase is offline — companies are stored in local files only.";
        }
    }

    // ══════════════════════════════════════════════════════
    // COMPANIES
    // ══════════════════════════════════════════════════════

    async function loadCompanies() {
        try {
            const res = await apiFetch("/api/companies");
            if (!res.ok) throw new Error("Failed to load companies");
            state.companies = await res.json();

            if (state.companies.length === 0) {
                renderCompanySelect();
                openCompanyModal(null);
                showToast("Create your first company to get started.");
                return;
            }

            if (!activeCompany()) {
                state.activeCompanyId = state.companies[0].id;
            }
            localStorage.setItem("activeCompanyId", state.activeCompanyId);

            renderCompanySelect();
            renderPillarsChecklist();
            await onCompanyOrPlatformChange();
        } catch (err) {
            console.error(err);
            showToast("Error loading companies: " + err.message, "error");
        }
    }

    function renderCompanySelect() {
        elements.companySelect.innerHTML = "";
        state.companies.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.name;
            if (String(c.id) === String(state.activeCompanyId)) opt.selected = true;
            elements.companySelect.appendChild(opt);
        });
    }

    async function onCompanyOrPlatformChange() {
        state.activePostIndex = null;
        renderPillarsChecklist();
        updateGenerateHint();
        updateTrendsPlatformLabel();
        state.trends = null;
        renderTrendCards();
        await Promise.all([loadConnectionsAndStats(), loadHistory(), loadCalendar(), loadTrends(false)]);
    }

    function renderPillarsChecklist() {
        const company = activeCompany();
        const pillars = (company && company.content_pillars && company.content_pillars.length)
            ? company.content_pillars
            : state.config.default_pillars;

        elements.pillarsChecklist.innerHTML = "";
        pillars.forEach((pillar) => {
            const label = document.createElement("label");
            label.className = "pillar-checkbox-label";
            label.innerHTML = `
                <input type="checkbox" value="${escapeHtml(pillar)}" checked>
                <span>${escapeHtml(pillar)}</span>
            `;
            elements.pillarsChecklist.appendChild(label);
        });
    }

    function updateGenerateHint() {
        const label = state.config.platform_labels[state.activePlatform] || state.activePlatform;
        elements.generatePlatformHint.innerHTML = `Generating content for <strong>${escapeHtml(label)}</strong> — switch platform using the selector in the header.`;
        if (elements.ideaPlatformHint) elements.ideaPlatformHint.textContent = label;
    }

    // ══════════════════════════════════════════════════════
    // LIVE TREND MONITORING
    // ══════════════════════════════════════════════════════

    function updateTrendsPlatformLabel() {
        const label = state.config.platform_labels[state.activePlatform] || state.activePlatform;
        elements.trendsPlatformLabel.textContent = label;
    }

    async function loadTrends(refresh = false) {
        if (!state.activeCompanyId) return;
        if (!state.config.has_api_key) return;

        state.trendsLoading = true;
        renderTrendCards();

        try {
            const url = `/api/companies/${state.activeCompanyId}/trends?platform=${encodeURIComponent(state.activePlatform)}${refresh ? "&refresh=true" : ""}`;
            const res = await apiFetch(url);
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Failed to load trends");
            }
            state.trends = await res.json();
            if (refresh) showToast("Trends refreshed.");
        } catch (err) {
            console.error(err);
            if (refresh) showToast("Couldn't refresh trends: " + err.message, "error");
        } finally {
            state.trendsLoading = false;
            renderTrendCards();
        }
    }

    function renderTrendCards() {
        elements.trendsCardsRow.innerHTML = "";

        if (state.trendsLoading) {
            elements.trendsUpdatedAt.textContent = "";
            const loadingEl = document.createElement("div");
            loadingEl.className = "trends-empty-hint";
            loadingEl.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Checking what's trending...`;
            elements.trendsCardsRow.appendChild(loadingEl);
            return;
        }

        const trends = (state.trends && state.trends.trends) || [];

        if (trends.length === 0) {
            elements.trendsUpdatedAt.textContent = "";
            const hint = document.createElement("div");
            hint.className = "trends-empty-hint";
            const label = state.config.platform_labels[state.activePlatform] || state.activePlatform;
            hint.innerHTML = `<i class="fa-solid fa-fire"></i> Check what's trending on <strong>${escapeHtml(label)}</strong> right now.`;
            elements.trendsCardsRow.appendChild(hint);
            return;
        }

        if (state.trends.fetched_at) {
            const date = new Date(state.trends.fetched_at);
            const timeStr = isNaN(date.getTime()) ? "" : date.toLocaleString();
            elements.trendsUpdatedAt.textContent = state.trends.stale
                ? `Showing cached trends from ${timeStr}`
                : `Updated ${timeStr}`;
        }

        trends.forEach(trend => {
            const card = document.createElement("div");
            card.className = "trend-card";
            card.innerHTML = `
                <div class="trend-card-header">
                    <span class="trend-format-tag">${escapeHtml(trend.format || "")}</span>
                    <h5>${escapeHtml(trend.title || "")}</h5>
                </div>
                <p class="trend-description">${escapeHtml(trend.description || "")}</p>
                <p class="trend-brand-angle"><i class="fa-solid fa-arrow-turn-up"></i> ${escapeHtml(trend.brand_angle || "")}</p>
            `;
            elements.trendsCardsRow.appendChild(card);
        });
    }

    // COMPANY MODAL

    function openCompanyModal(company) {
        state.editingCompanyId = company ? company.id : null;
        elements.researchLoading.classList.add("hidden");

        if (company) {
            elements.companyModalTitle.textContent = "Edit Company";
            elements.companyName.value = company.name || "";
            elements.companyIndustry.value = company.industry || "";
            elements.companyContext.value = company.business_context || "";
            elements.companyAudience.value = company.target_audience || "";
            elements.companyVoice.value = company.brand_voice || "";
            elements.companyCta.value = company.cta_text || "";
            elements.companyPillars.value = (company.content_pillars || []).join("\n");
            elements.companyWebsite.value = company.website_url || "";
            elements.companyAutoResearch.checked = false;
            elements.deleteCompanyBtn.classList.remove("hidden");

            // In edit mode, auto-research toggle is irrelevant (that only applies on create) —
            // show the re-run research status block instead.
            elements.autoResearchField.classList.add("hidden");
            elements.researchStatusBox.classList.remove("hidden");
            renderResearchStatus(company);
        } else {
            elements.companyModalTitle.textContent = "New Company";
            elements.companyName.value = "";
            elements.companyIndustry.value = "";
            elements.companyContext.value = "";
            elements.companyAudience.value = "";
            elements.companyVoice.value = "";
            elements.companyCta.value = "";
            elements.companyPillars.value = "";
            elements.companyWebsite.value = "";
            elements.companyAutoResearch.checked = true;
            elements.deleteCompanyBtn.classList.add("hidden");

            // In create mode, show the auto-research toggle; there's no company yet to re-research.
            elements.autoResearchField.classList.remove("hidden");
            elements.researchStatusBox.classList.add("hidden");
        }

        elements.companyModal.classList.remove("hidden");
        elements.companyName.focus();
    }

    function renderResearchStatus(company) {
        if (company.last_researched_at) {
            const date = new Date(company.last_researched_at);
            const dateStr = isNaN(date.getTime()) ? company.last_researched_at : date.toLocaleString();
            elements.researchStatusText.textContent = `Last researched ${dateStr}`;
        } else {
            elements.researchStatusText.textContent = "Not yet researched";
        }

        elements.researchSummaryText.textContent = company.research_summary || "";

        const sources = company.research_sources || [];
        if (sources.length > 0) {
            elements.researchSources.innerHTML = sources.map(s =>
                `<a href="${escapeHtml(s.url)}" target="_blank" class="research-source-link"><i class="fa-solid fa-link"></i> ${escapeHtml(s.title || s.url)}</a>`
            ).join("");
            elements.researchSources.classList.remove("hidden");
        } else {
            elements.researchSources.innerHTML = "";
            elements.researchSources.classList.add("hidden");
        }
    }

    function closeCompanyModal() {
        elements.companyModal.classList.add("hidden");
    }

    async function saveCompany() {
        const name = elements.companyName.value.trim();
        if (!name) {
            showToast("Company name is required", "error");
            return;
        }

        const payload = {
            name,
            industry: elements.companyIndustry.value.trim(),
            business_context: elements.companyContext.value.trim(),
            target_audience: elements.companyAudience.value.trim(),
            brand_voice: elements.companyVoice.value.trim(),
            cta_text: elements.companyCta.value.trim(),
            content_pillars: elements.companyPillars.value.split("\n").map(s => s.trim()).filter(Boolean),
            best_times: [],
            website_url: elements.companyWebsite.value.trim(),
            auto_research: state.editingCompanyId ? false : elements.companyAutoResearch.checked,
        };

        elements.saveCompanyBtn.disabled = true;
        try {
            let res;
            if (state.editingCompanyId) {
                res = await apiFetch(`/api/companies/${state.editingCompanyId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
            } else {
                res = await apiFetch("/api/companies", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
            }
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Failed to save company");
            }
            const saved = await res.json();

            closeCompanyModal();
            showToast(`Company "${saved.name}" saved successfully.`);

            state.activeCompanyId = saved.id;
            await loadCompanies();
        } catch (err) {
            console.error(err);
            showToast("Error saving company: " + err.message, "error");
        } finally {
            elements.saveCompanyBtn.disabled = false;
        }
    }

    async function runResearch() {
        if (!state.editingCompanyId) {
            showToast("Save the company first, then re-run research.", "error");
            return;
        }
        const websiteUrl = elements.companyWebsite.value.trim();
        if (!websiteUrl) {
            showToast("Add a website URL first.", "error");
            return;
        }
        if (!state.config.has_api_key) {
            showToast("Please configure your Gemini API Key in Settings first!", "error");
            return;
        }

        elements.researchLoading.classList.remove("hidden");
        elements.rerunResearchBtn.disabled = true;

        try {
            const res = await apiFetch(`/api/companies/${state.editingCompanyId}/research`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ website_url: websiteUrl }),
            });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Research failed");
            }
            const updated = await res.json();

            elements.companyIndustry.value = updated.industry || "";
            elements.companyContext.value = updated.business_context || "";
            elements.companyAudience.value = updated.target_audience || "";
            elements.companyVoice.value = updated.brand_voice || "";
            elements.companyCta.value = updated.cta_text || "";
            elements.companyPillars.value = (updated.content_pillars || []).join("\n");
            renderResearchStatus(updated);

            showToast("Research complete — fields updated below.");
            await loadCompanies();
        } catch (err) {
            console.error(err);
            showToast("Research failed: " + err.message, "error");
        } finally {
            elements.researchLoading.classList.add("hidden");
            elements.rerunResearchBtn.disabled = false;
        }
    }

    async function deleteCompanyConfirm() {
        if (!state.editingCompanyId) return;
        const company = state.companies.find(c => String(c.id) === String(state.editingCompanyId));
        if (!confirm(`Delete "${company ? company.name : "this company"}" and all of its calendar/history data? This cannot be undone.`)) return;

        try {
            const res = await apiFetch(`/api/companies/${state.editingCompanyId}`, { method: "DELETE" });
            if (!res.ok) throw new Error("Failed to delete company");

            closeCompanyModal();
            showToast("Company deleted.");

            if (String(state.activeCompanyId) === String(state.editingCompanyId)) {
                state.activeCompanyId = null;
            }
            await loadCompanies();
        } catch (err) {
            console.error(err);
            showToast("Error deleting company: " + err.message, "error");
        }
    }

    // ══════════════════════════════════════════════════════
    // PLATFORM CONNECTIONS
    // ══════════════════════════════════════════════════════

    async function loadConnectionsAndStats() {
        if (!state.activeCompanyId) return;
        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/connections`);
            if (!res.ok) throw new Error("Failed to load connections");
            state.connections = await res.json();
        } catch (err) {
            console.error(err);
            state.connections = [];
        }
        await loadPlatformStats();
    }

    async function loadPlatformStats() {
        if (!state.activeCompanyId) return;
        updateBrandBadge({ status: "loading" });
        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/connections/${state.activePlatform}/stats`);
            const result = await res.json();
            updateBrandBadge(result);
        } catch (err) {
            console.error(err);
            updateBrandBadge({ status: "error", message: err.message });
        }
    }

    function updateBrandBadge(result) {
        const badge = elements.brandHandleBadge;
        const icon = elements.brandHandleIcon;
        const text = elements.brandHandleText;
        icon.className = PLATFORM_ICONS[state.activePlatform] || "fa-solid fa-globe";

        if (result.status === "online") {
            const data = result.data;
            badge.className = "status-badge brand-handle online";
            text.textContent = data.username ? `@${data.username}` : (data.full_name || "Connected");
            elements.metricFollowers.textContent = formatCompactNumber(data.followers);
            elements.metricFollowing.textContent = formatCompactNumber(data.following);
            elements.metricViews.textContent = data.views !== undefined ? data.views : "-";
        } else if (result.status === "loading") {
            badge.className = "status-badge brand-handle";
            text.textContent = "Connecting...";
            elements.metricFollowers.textContent = "...";
            elements.metricFollowing.textContent = "...";
            elements.metricViews.textContent = "...";
        } else if (result.status === "not_implemented") {
            badge.className = "status-badge brand-handle offline";
            text.textContent = "Not Connected Yet";
            elements.metricFollowers.textContent = "-";
            elements.metricFollowing.textContent = "-";
            elements.metricViews.textContent = "-";
        } else if (result.status === "offline") {
            badge.className = "status-badge brand-handle offline";
            text.textContent = "Offline Mode";
            elements.metricFollowers.textContent = "-";
            elements.metricFollowing.textContent = "-";
            elements.metricViews.textContent = "-";
        } else {
            badge.className = "status-badge brand-handle error";
            text.textContent = "Sync Error";
            elements.metricFollowers.textContent = "Error";
            elements.metricFollowing.textContent = "Error";
            elements.metricViews.textContent = "Error";
        }
    }

    function formatCompactNumber(num) {
        if (num === undefined || num === null || isNaN(num)) return "-";
        if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
        if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, "") + "K";
        return num.toString();
    }

    // CONNECTIONS MODAL

    function openConnectionsModal() {
        renderConnectionsModal();
        elements.connectionsModal.classList.remove("hidden");
    }

    function closeConnectionsModal() {
        elements.connectionsModal.classList.add("hidden");
    }

    function renderConnectionsModal() {
        const platforms = state.config.platforms.length ? state.config.platforms : ["instagram", "facebook", "linkedin", "google_business"];
        elements.connectionsBody.innerHTML = "";

        platforms.forEach(platform => {
            const conn = state.connections.find(c => c.platform === platform);
            const label = state.config.platform_labels[platform] || platform;
            const icon = PLATFORM_ICONS[platform] || "fa-solid fa-globe";
            const row = document.createElement("div");
            row.className = "connection-row";

            if (platform === "instagram") {
                if (conn && conn.status === "connected") {
                    const modeLabel = conn.auth_type === "public" ? " (public read-only)" : "";
                    row.innerHTML = `
                        <div class="connection-row-header">
                            <span class="connection-title"><i class="${icon}"></i> ${label}</span>
                            <span class="status-badge brand-handle online" style="padding: 0.2rem 0.6rem;">Connected as @${escapeHtml(conn.username || "")}${modeLabel}</span>
                        </div>
                        <button class="btn btn-secondary connection-disconnect-btn" data-platform="${platform}">Disconnect</button>
                    `;
                } else {
                    row.innerHTML = `
                        <div class="connection-row-header">
                            <span class="connection-title"><i class="${icon}"></i> ${label}</span>
                            <span class="status-badge brand-handle offline" style="padding: 0.2rem 0.6rem;">Not connected</span>
                        </div>
                        <p class="field-hint">Leave password blank to only read stats & recent posts of a public username (no account access needed). Add the password too if you own the account and want full login. Automated publishing needs the official Graph API — see project docs.</p>
                        <div class="form-row">
                            <div class="form-group"><input type="text" class="connection-username-input" data-platform="${platform}" placeholder="Instagram username"></div>
                            <div class="form-group"><input type="password" class="connection-password-input" data-platform="${platform}" placeholder="Password (optional — public profiles only)"></div>
                        </div>
                        <button class="btn btn-primary connection-connect-btn" data-platform="${platform}">Connect Instagram</button>
                    `;
                }
            } else {
                row.innerHTML = `
                    <div class="connection-row-header">
                        <span class="connection-title"><i class="${icon}"></i> ${label}</span>
                        <span class="status-badge brand-handle offline" style="padding: 0.2rem 0.6rem;">Not available yet</span>
                    </div>
                    <p class="field-hint">${PLATFORM_SETUP_HINTS[platform] || "Not implemented yet."}</p>
                    <button class="btn btn-secondary" disabled>Connect (Coming Soon)</button>
                `;
            }

            elements.connectionsBody.appendChild(row);
        });

        elements.connectionsBody.querySelectorAll(".connection-connect-btn").forEach(btn => {
            btn.addEventListener("click", () => connectPlatform(btn.dataset.platform));
        });
        elements.connectionsBody.querySelectorAll(".connection-disconnect-btn").forEach(btn => {
            btn.addEventListener("click", () => disconnectPlatform(btn.dataset.platform));
        });
    }

    async function connectPlatform(platform) {
        const usernameInput = elements.connectionsBody.querySelector(`.connection-username-input[data-platform="${platform}"]`);
        const passwordInput = elements.connectionsBody.querySelector(`.connection-password-input[data-platform="${platform}"]`);
        const username = usernameInput ? usernameInput.value.trim() : "";
        const password = passwordInput ? passwordInput.value : "";

        if (!username) {
            showToast("Username is required", "error");
            return;
        }

        try {
            const credentials = password ? { username, password } : { username };
            const authType = password ? "password" : "public";
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/connections/${platform}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ credentials, auth_type: authType }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Failed to connect");

            showToast(data.message || "Connected successfully!");
            await loadConnectionsAndStats();
            renderConnectionsModal();
            if (state.activePlatform === platform) await loadHistory();
        } catch (err) {
            console.error(err);
            showToast("Connection failed: " + err.message, "error");
        }
    }

    async function disconnectPlatform(platform) {
        if (!confirm(`Disconnect ${state.config.platform_labels[platform] || platform}?`)) return;
        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/connections/${platform}`, { method: "DELETE" });
            if (!res.ok) throw new Error("Failed to disconnect");
            showToast("Disconnected.");
            await loadConnectionsAndStats();
            renderConnectionsModal();
        } catch (err) {
            console.error(err);
            showToast("Error: " + err.message, "error");
        }
    }

    // ══════════════════════════════════════════════════════
    // HISTORY
    // ══════════════════════════════════════════════════════

    async function loadHistory() {
        if (!state.activeCompanyId) return;
        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/history?platform=${encodeURIComponent(state.activePlatform)}`);
            if (!res.ok) throw new Error("Failed to load history");
            state.history = await res.json();

            const label = state.config.platform_labels[state.activePlatform] || state.activePlatform;
            elements.historySubtitle.textContent = `${label} history — tracked to ensure 100% unique topics every generation cycle.`;

            updateHistoryCountUI();
            renderHistoryTable(state.history.posts);
        } catch (err) {
            console.error(err);
            state.history = { posts: [] };
            updateHistoryCountUI();
            showToast("Error loading history: " + err.message, "error");
        }
    }

    function updateHistoryCountUI() {
        elements.historyValue.textContent = (state.history && state.history.posts) ? state.history.posts.length : 0;
    }

    function renderHistoryTable(posts) {
        elements.historyTableBody.innerHTML = "";
        if (posts.length === 0) {
            elements.historyTableBody.innerHTML = `<tr><td colspan="4" class="table-loading">No past posts found for this platform yet.</td></tr>`;
            return;
        }

        posts.forEach(post => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(post.date)}</strong></td>
                <td><span class="format-badge" style="padding: 0.15rem 0.4rem; font-size: 0.65rem;"><i class="${post.reel_or_static === 'Reel' ? 'fa-solid fa-video' : 'fa-solid fa-image'}"></i> ${escapeHtml(post.reel_or_static)}</span></td>
                <td>${escapeHtml(post.post_type)}</td>
                <td>${escapeHtml(post.idea_summary)}</td>
            `;
            elements.historyTableBody.appendChild(tr);
        });
    }

    // ══════════════════════════════════════════════════════
    // CALENDAR / TIMELINE
    // ══════════════════════════════════════════════════════

    async function loadCalendar() {
        if (!state.activeCompanyId) return;
        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/calendar`);
            if (!res.ok) throw new Error("Failed to load calendar");
            state.calendar = await res.json();
            renderCalendarTimeline();
        } catch (err) {
            console.error(err);
            showToast("Error loading calendar: " + err.message, "error");
        }
    }

    function visiblePairs() {
        return state.calendar
            .map((post, index) => ({ post, index }))
            .filter(({ post }) => state.calendarFilterPlatform === "all" || post.platform === state.calendarFilterPlatform);
    }

    function renderCalendarTimeline() {
        const cardElements = elements.calendarTimelineList.querySelectorAll(".timeline-card");
        cardElements.forEach(el => el.remove());
        const dividerElements = elements.calendarTimelineList.querySelectorAll(".timeline-divider, .completed-posts-container");
        dividerElements.forEach(el => el.remove());

        const totalPending = state.calendar.filter(p => !p.is_done).length;
        elements.scheduledValue.textContent = state.calendar.length ? totalPending : "-";

        if (state.calendar.length === 0) {
            elements.calendarEmptyState.classList.remove("hidden");
            elements.activeCalendarBadge.textContent = "No active calendar loaded";
            elements.saveBtn.classList.add("hidden");
            elements.exportBtn.classList.add("hidden");
            closeStudio();
            return;
        }

        elements.saveBtn.classList.remove("hidden");
        elements.exportBtn.classList.remove("hidden");

        const pairs = visiblePairs();
        if (pairs.length === 0) {
            elements.calendarEmptyState.classList.remove("hidden");
            elements.calendarEmptyState.querySelector("h4").textContent = "No Posts For This Platform";
            elements.calendarEmptyState.querySelector("p").textContent = "Generate content for this platform, or switch the filter above.";
            elements.activeCalendarBadge.textContent = "0 posts for this filter";
            closeStudio();
            return;
        }
        elements.calendarEmptyState.classList.add("hidden");

        const pendingPairs = pairs.filter(p => !p.post.is_done);
        const completedPairs = pairs.filter(p => p.post.is_done);

        elements.activeCalendarBadge.textContent = `${pendingPairs.length} pending / ${pairs.length} total`;

        function createTimelineCard(post, index) {
            const company = activeCompany();
            const pillars = (company && company.content_pillars && company.content_pillars.length) ? company.content_pillars : state.config.default_pillars;
            const pillarIndex = pillars.indexOf(post.post_type);
            const pillarClass = pillarIndex !== -1 ? `pillar-${pillarIndex % 10}` : "";

            let dayNum = "??";
            let monthStr = "";
            try {
                const parts = post.date.split(" ");
                dayNum = parts[0];
                monthStr = parts[1].substring(0, 3).toUpperCase();
            } catch (e) {}

            const activeClass = state.activePostIndex === index ? "active" : "";
            const uploadedClass = post.is_done ? "uploaded" : "";
            const checkIcon = post.is_done ? '<i class="fa-solid fa-circle-check uploaded-check-icon" title="Uploaded"></i>' : '';
            const platformIcon = PLATFORM_ICONS[post.platform] || "fa-solid fa-globe";

            const card = document.createElement("div");
            card.className = `timeline-card ${pillarClass} ${activeClass} ${uploadedClass}`;
            card.dataset.index = index;
            card.innerHTML = `
                <div class="card-date-badge">
                    <span class="day-num">${dayNum}</span>
                    <span class="month">${monthStr}</span>
                </div>
                <div class="card-main-content">
                    <div class="card-meta-line">
                        <span class="time"><i class="fa-regular fa-clock"></i> ${escapeHtml(post.day)} ${escapeHtml((post.time || "").split(" ")[0] || "")}</span>
                        <span class="format-tag"><i class="${platformIcon}"></i> ${escapeHtml(post.reel_or_static)}</span>
                        ${checkIcon}
                    </div>
                    <h4>${escapeHtml(post.post_type)}</h4>
                    <span class="hook-preview">"${escapeHtml(post.hook)}"</span>
                </div>
            `;
            card.addEventListener("click", () => selectPost(index));
            return card;
        }

        pendingPairs.forEach(({ post, index }) => {
            elements.calendarTimelineList.appendChild(createTimelineCard(post, index));
        });

        if (completedPairs.length > 0) {
            const divider = document.createElement("div");
            divider.className = "timeline-divider";
            if (state.completedCollapsed === undefined) state.completedCollapsed = false;

            const caretIconClass = state.completedCollapsed ? "fa-chevron-right" : "fa-chevron-down";
            divider.innerHTML = `
                <span><i class="fa-solid fa-circle-check" style="color: var(--teal);"></i> Completed (${completedPairs.length})</span>
                <button class="icon-btn-toggle" style="font-size: 0.75rem; width: 24px; height: 24px;"><i class="fa-solid ${caretIconClass}"></i></button>
            `;
            elements.calendarTimelineList.appendChild(divider);

            const completedContainer = document.createElement("div");
            completedContainer.className = "completed-posts-container";
            completedContainer.style.display = state.completedCollapsed ? "none" : "flex";
            completedContainer.style.flexDirection = "column";
            completedContainer.style.gap = "0.75rem";

            completedPairs.forEach(({ post, index }) => {
                completedContainer.appendChild(createTimelineCard(post, index));
            });
            elements.calendarTimelineList.appendChild(completedContainer);

            divider.style.cursor = "pointer";
            divider.addEventListener("click", () => {
                state.completedCollapsed = !state.completedCollapsed;
                const icon = divider.querySelector("button i");
                if (state.completedCollapsed) {
                    completedContainer.style.display = "none";
                    icon.className = "fa-solid fa-chevron-right";
                } else {
                    completedContainer.style.display = "flex";
                    completedContainer.style.flexDirection = "column";
                    completedContainer.style.gap = "0.75rem";
                    icon.className = "fa-solid fa-chevron-down";
                }
            });
        }

        if (state.activePostIndex !== null && state.activePostIndex < state.calendar.length) {
            selectPost(state.activePostIndex);
        } else {
            closeStudio();
        }
    }

    // STUDIO ACTIONS
    function selectPost(index) {
        state.activePostIndex = index;
        const post = state.calendar[index];
        if (!post) return;

        const cards = elements.calendarTimelineList.querySelectorAll(".timeline-card");
        cards.forEach((card) => {
            if (parseInt(card.dataset.index) === index) card.classList.add("active");
            else card.classList.remove("active");
        });

        elements.studioEmptyState.classList.add("hidden");
        elements.studioEditorContent.classList.remove("hidden");

        elements.studioPostNumber.textContent = `#${post.post_number}`;
        elements.studioPostType.textContent = post.post_type;
        elements.studioDatetime.textContent = `${post.date} (${post.day}) @ ${post.time}`;

        const platformLabel = state.config.platform_labels[post.platform] || post.platform;
        elements.studioPlatformBadge.innerHTML = `<i class="${PLATFORM_ICONS[post.platform] || 'fa-solid fa-globe'}"></i> ${escapeHtml(platformLabel)}`;

        const isReel = post.reel_or_static === "Reel";
        elements.studioFormatBadge.innerHTML = `<i class="${isReel ? 'fa-solid fa-video' : 'fa-solid fa-image'}"></i> ${escapeHtml(post.reel_or_static)}`;

        elements.studioHookInput.value = post.hook;
        elements.studioCaptionInput.value = post.caption;
        elements.studioPromptInput.value = post.image_prompt;
        elements.studioHashtagsInput.value = post.hashtags;
        elements.studioNotesInput.value = post.notes_for_creator;
        elements.studioScriptInput.value = post.script || "";
        elements.studioEditingStyleInput.value = post.editing_style || "";

        if (post.image_url) {
            elements.generatedImagePreviewImg.src = post.image_url;
            elements.generatedImagePreview.classList.remove("hidden");
        } else {
            elements.generatedImagePreviewImg.src = "";
            elements.generatedImagePreview.classList.add("hidden");
        }
        elements.generateImageBtn.disabled = false;
        elements.generateImageBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Generate Image with AI</span>';

        if (post.is_done) {
            elements.studioDoneBtn.classList.add("done");
            elements.studioDoneBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> <span>Uploaded</span>';
        } else {
            elements.studioDoneBtn.classList.remove("done");
            elements.studioDoneBtn.innerHTML = '<i class="fa-regular fa-circle-check"></i> <span>Mark Done</span>';
        }

        if (isReel) {
            elements.studioToolRec.textContent = "RunwayML / Kling Suggestion";
            elements.studioToolRec.style.background = "var(--purple-glow)";
            elements.studioToolRec.style.color = "var(--purple)";
            elements.studioToolRec.style.borderColor = "rgba(127, 119, 221, 0.2)";
        } else {
            elements.studioToolRec.textContent = "Midjourney / Leonardo Suggestion";
            elements.studioToolRec.style.background = "var(--teal-glow)";
            elements.studioToolRec.style.color = "#3cdba4";
            elements.studioToolRec.style.borderColor = "rgba(60, 219, 164, 0.2)";
        }

        if (window.innerWidth <= 1024) {
            elements.studioPanel.scrollIntoView({ behavior: "smooth" });
        }
    }

    async function generatePostImage() {
        if (state.activePostIndex === null) return;
        const index = state.activePostIndex;
        const post = state.calendar[index];
        if (!post) return;

        elements.generateImageBtn.disabled = true;
        elements.generateImageBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Generating...</span>';

        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/calendar/generate-image`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ post_index: index }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Image generation failed");

            post.image_url = data.image_url;
            elements.generatedImagePreviewImg.src = data.image_url;
            elements.generatedImagePreview.classList.remove("hidden");
            showToast("Image generated!");
        } catch (err) {
            console.error(err);
            showToast("Image generation failed: " + err.message, "error");
        } finally {
            elements.generateImageBtn.disabled = false;
            elements.generateImageBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Generate Image with AI</span>';
        }
    }

    function closeStudio() {
        state.activePostIndex = null;
        elements.studioEmptyState.classList.remove("hidden");
        elements.studioEditorContent.classList.add("hidden");
    }

    function handleStudioInputChange() {
        if (state.activePostIndex === null) return;
        const post = state.calendar[state.activePostIndex];

        post.hook = elements.studioHookInput.value;
        post.caption = elements.studioCaptionInput.value;
        post.image_prompt = elements.studioPromptInput.value;
        post.hashtags = elements.studioHashtagsInput.value;
        post.notes_for_creator = elements.studioNotesInput.value;
        post.script = elements.studioScriptInput.value;
        post.editing_style = elements.studioEditingStyleInput.value;

        state.hasUnsavedChanges = true;
        elements.saveBtn.classList.remove("btn-secondary");
        elements.saveBtn.classList.add("btn-primary");

        const activeCard = elements.calendarTimelineList.querySelector(`.timeline-card.active`);
        if (activeCard) {
            const hookPreview = activeCard.querySelector(".hook-preview");
            if (hookPreview) hookPreview.textContent = `"${post.hook}"`;
        }
    }

    // ══════════════════════════════════════════════════════
    // SAVE / EXPORT
    // ══════════════════════════════════════════════════════

    async function saveCalendarEdits() {
        if (state.calendar.length === 0 || !state.activeCompanyId) return;

        elements.saveBtn.disabled = true;
        const text = elements.saveBtn.querySelector(".btn-text") || elements.saveBtn;
        const origContent = text.innerHTML;
        text.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/save`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ posts: state.calendar }),
            });
            if (!res.ok) throw new Error("Failed to save changes");

            showToast("Calendar saved successfully.");
            state.hasUnsavedChanges = false;
            elements.saveBtn.classList.remove("btn-primary");
            elements.saveBtn.classList.add("btn-secondary");
        } catch (err) {
            console.error(err);
            showToast("Error saving edits: " + err.message, "error");
        } finally {
            text.innerHTML = origContent;
            elements.saveBtn.disabled = false;
        }
    }

    async function commitAndExportExcel() {
        if (state.calendar.length === 0 || !state.activeCompanyId) return;

        elements.exportBtn.disabled = true;
        const origContent = elements.exportBtn.innerHTML;
        elements.exportBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Exporting...';

        try {
            const saveRes = await apiFetch(`/api/companies/${state.activeCompanyId}/export`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ posts: state.calendar }),
            });
            if (!saveRes.ok) throw new Error("Export generation request failed");

            const blob = await saveRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            const company = activeCompany();
            a.download = `${(company ? company.slug : "content")}_content_calendar.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            showToast("Calendar exported & history committed successfully!");
            state.hasUnsavedChanges = false;
            elements.saveBtn.classList.remove("btn-primary");
            elements.saveBtn.classList.add("btn-secondary");

            await loadHistory();
        } catch (err) {
            console.error(err);
            showToast("Export failed: " + err.message, "error");
        } finally {
            elements.exportBtn.innerHTML = origContent;
            elements.exportBtn.disabled = false;
        }
    }

    // ══════════════════════════════════════════════════════
    // GENERATION
    // ══════════════════════════════════════════════════════

    async function triggerGeneration() {
        if (!state.activeCompanyId) {
            showToast("Create or select a company first!", "error");
            return;
        }
        if (!state.config.has_api_key) {
            showToast("Please configure your Gemini API Key in Settings first!", "error");
            openSettings();
            return;
        }

        const weeks = parseInt(elements.planWeeks.value);
        const postsPerWeek = parseInt(elements.postsPerWeek.value);
        const modelName = elements.generatorModel.value;

        const checkedPillars = [];
        elements.pillarsChecklist.querySelectorAll("input[type='checkbox']").forEach(cb => {
            if (cb.checked) checkedPillars.push(cb.value);
        });

        if (checkedPillars.length === 0) {
            showToast("Please select at least one active Content Pillar!", "error");
            return;
        }

        elements.genLoader.classList.remove("hidden");
        elements.generateBtn.disabled = true;

        const platformLabel = state.config.platform_labels[state.activePlatform] || state.activePlatform;
        let statuses = [
            "Connecting to Gemini API...",
            "Loading past post history to verify unique topics...",
            `Creating high-converting ${platformLabel} hooks...`,
            "Formulating high-converting Call-to-Actions...",
            `Optimizing ${platformLabel} captions & creator notes...`,
            "Reviewing AI visual generation prompts...",
            "Applying target audience optimization...",
        ];

        let statusIndex = 0;
        const statusInterval = setInterval(() => {
            if (statusIndex < statuses.length - 1) {
                statusIndex++;
                elements.loaderStatusText.textContent = statuses[statusIndex];
            }
        }, 3500);

        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    platform: state.activePlatform,
                    weeks,
                    posts_per_week: postsPerWeek,
                    pillars: checkedPillars,
                    model_name: modelName,
                    append_to_existing: true,
                    use_trends: elements.useTrendsCheckbox.checked,
                }),
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Generation failed");
            }

            const data = await res.json();
            state.calendar = data;
            state.calendarFilterPlatform = state.activePlatform;
            elements.calendarPlatformFilter.value = state.activePlatform;
            state.hasUnsavedChanges = false;

            const newlyGenerated = data.filter(p => p.platform === state.activePlatform).length;
            showToast(`Generated posts successfully! (${newlyGenerated} total for ${platformLabel})`);

            renderCalendarTimeline();
        } catch (err) {
            console.error(err);
            showToast(err.message, "error");
        } finally {
            clearInterval(statusInterval);
            elements.genLoader.classList.add("hidden");
            elements.generateBtn.disabled = false;
            elements.loaderStatusText.textContent = "Thinking...";
        }
    }

    async function triggerIdeaGeneration() {
        if (!state.activeCompanyId) {
            showToast("Create or select a company first!", "error");
            return;
        }
        if (!state.config.has_api_key) {
            showToast("Please configure your Gemini API Key in Settings first!", "error");
            openSettings();
            return;
        }

        const idea = elements.ideaInput.value.trim();
        if (!idea) {
            showToast("Describe your idea first!", "error");
            return;
        }

        const btnText = elements.ideaGenerateBtn.querySelector(".btn-text");
        const spinner = elements.ideaGenerateBtn.querySelector(".spinner");
        elements.ideaGenerateBtn.disabled = true;
        btnText.classList.add("hidden");
        spinner.classList.remove("hidden");

        try {
            const res = await apiFetch(`/api/companies/${state.activeCompanyId}/generate-from-idea`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    idea,
                    platform: state.activePlatform,
                    model_name: elements.generatorModel.value,
                    use_trends: elements.useTrendsCheckbox.checked,
                }),
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Generation failed");
            }

            const data = await res.json();
            state.calendar = data;
            state.calendarFilterPlatform = state.activePlatform;
            elements.calendarPlatformFilter.value = state.activePlatform;
            state.hasUnsavedChanges = false;

            elements.ideaInput.value = "";
            const platformLabel = state.config.platform_labels[state.activePlatform] || state.activePlatform;
            showToast(`Post generated from your idea and added to the ${platformLabel} calendar!`);

            renderCalendarTimeline();
        } catch (err) {
            console.error(err);
            showToast(err.message, "error");
        } finally {
            elements.ideaGenerateBtn.disabled = false;
            btnText.classList.remove("hidden");
            spinner.classList.add("hidden");
        }
    }

    // ══════════════════════════════════════════════════════
    // SETTINGS MODAL
    // ══════════════════════════════════════════════════════

    function openSettings() {
        elements.settingsApiKey.value = "";
        elements.settingsSupabaseKey.value = "";
        elements.settingsModal.classList.remove("hidden");
        elements.settingsApiKey.focus();
    }

    function closeSettings() {
        elements.settingsModal.classList.add("hidden");
    }

    async function saveSettings() {
        const apiKey = elements.settingsApiKey.value.trim();
        const supabaseUrl = elements.settingsSupabaseUrl.value.trim();
        const supabaseKey = elements.settingsSupabaseKey.value.trim();

        if (!apiKey && !state.config.has_api_key) {
            showToast("Gemini API Key is required to plan content", "error");
            return;
        }

        elements.saveSettingsBtn.disabled = true;
        elements.saveSettingsBtn.textContent = "Saving...";

        try {
            if (apiKey) {
                const res = await apiFetch("/api/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ api_key: apiKey }),
                });
                if (!res.ok) throw new Error("Failed to save Gemini API Key");
            }

            if (supabaseUrl && supabaseKey) {
                const res = await apiFetch("/api/supabase/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: supabaseUrl, key: supabaseKey }),
                });
                if (!res.ok) throw new Error("Failed to connect Supabase");
                showToast("Supabase connected!");
            }

            showToast("Settings updated successfully!");
            await loadConfig();
            await loadCompanies();
            closeSettings();
        } catch (err) {
            console.error(err);
            showToast("Error updating settings: " + err.message, "error");
        } finally {
            elements.saveSettingsBtn.disabled = false;
            elements.saveSettingsBtn.textContent = "Save Settings";
        }
    }

    // ══════════════════════════════════════════════════════
    // UTILITIES
    // ══════════════════════════════════════════════════════

    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function copyTextToClipboard(text, badgeType) {
        if (!text) return;
        navigator.clipboard.writeText(text).then(() => {
            showToast(`${badgeType} copied to clipboard!`);
        }).catch(err => {
            console.error(err);
            showToast("Failed to copy", "error");
        });
    }

    function showToast(message, type = "success") {
        elements.toastText.textContent = message;
        if (type === "error") {
            elements.toastNotif.classList.add("error");
            elements.toastNotif.querySelector("i").className = "fa-solid fa-circle-exclamation";
        } else {
            elements.toastNotif.classList.remove("error");
            elements.toastNotif.querySelector("i").className = "fa-solid fa-check-circle";
        }

        elements.toastNotif.classList.remove("hidden");
        elements.toastNotif.style.transform = "translateY(0)";
        elements.toastNotif.style.opacity = "1";

        setTimeout(() => {
            elements.toastNotif.style.transform = "translateY(50px)";
            elements.toastNotif.style.opacity = "0";
            setTimeout(() => {
                elements.toastNotif.classList.add("hidden");
            }, 300);
        }, 3000);
    }

    // ══════════════════════════════════════════════════════
    // EVENT LISTENERS
    // ══════════════════════════════════════════════════════

    function setupEventListeners() {
        elements.companySelect.addEventListener("change", async () => {
            state.activeCompanyId = elements.companySelect.value;
            localStorage.setItem("activeCompanyId", state.activeCompanyId);
            await onCompanyOrPlatformChange();
        });
        elements.newCompanyBtn.addEventListener("click", () => openCompanyModal(null));
        elements.editCompanyBtn.addEventListener("click", () => {
            const company = activeCompany();
            if (company) openCompanyModal(company);
        });
        elements.saveCompanyBtn.addEventListener("click", saveCompany);
        elements.cancelCompanyBtn.addEventListener("click", closeCompanyModal);
        elements.closeCompanyBtn.addEventListener("click", closeCompanyModal);
        elements.deleteCompanyBtn.addEventListener("click", deleteCompanyConfirm);
        elements.rerunResearchBtn.addEventListener("click", runResearch);

        elements.refreshTrendsBtn.addEventListener("click", () => loadTrends(true));

        elements.platformSelect.addEventListener("change", async () => {
            state.activePlatform = elements.platformSelect.value;
            localStorage.setItem("activePlatform", state.activePlatform);
            await onCompanyOrPlatformChange();
        });
        elements.platformSelect.value = state.activePlatform;

        elements.calendarPlatformFilter.addEventListener("change", () => {
            state.calendarFilterPlatform = elements.calendarPlatformFilter.value;
            renderCalendarTimeline();
        });

        elements.openConnectionsBtn.addEventListener("click", openConnectionsModal);
        elements.closeConnectionsBtn.addEventListener("click", closeConnectionsModal);
        elements.closeConnectionsFooterBtn.addEventListener("click", closeConnectionsModal);

        elements.openSettingsBtn.addEventListener("click", openSettings);
        elements.closeSettingsBtn.addEventListener("click", closeSettings);
        elements.cancelSettingsBtn.addEventListener("click", closeSettings);
        elements.saveSettingsBtn.addEventListener("click", saveSettings);

        elements.toggleKeyVisibility.addEventListener("click", () => {
            const type = elements.settingsApiKey.type === "password" ? "text" : "password";
            elements.settingsApiKey.type = type;
            elements.toggleKeyVisibility.querySelector("i").className = type === "password" ? "fa-regular fa-eye" : "fa-regular fa-eye-slash";
        });

        elements.pillarsToggle.addEventListener("click", () => {
            elements.pillarsContainer.classList.toggle("expanded");
            const icon = elements.pillarsToggle.querySelector("i");
            icon.className = elements.pillarsContainer.classList.contains("expanded") ? "fa-solid fa-chevron-up" : "fa-solid fa-chevron-down";
        });

        elements.studioHookInput.addEventListener("input", handleStudioInputChange);
        elements.studioCaptionInput.addEventListener("input", handleStudioInputChange);
        elements.studioPromptInput.addEventListener("input", handleStudioInputChange);
        elements.studioHashtagsInput.addEventListener("input", handleStudioInputChange);
        elements.studioNotesInput.addEventListener("input", handleStudioInputChange);
        elements.studioScriptInput.addEventListener("input", handleStudioInputChange);
        elements.studioEditingStyleInput.addEventListener("input", handleStudioInputChange);

        elements.copyHookBtn.addEventListener("click", () => copyTextToClipboard(elements.studioHookInput.value, "Hook"));
        elements.copyCaptionBtn.addEventListener("click", () => copyTextToClipboard(elements.studioCaptionInput.value, "Caption"));
        elements.copyPromptBtn.addEventListener("click", () => copyTextToClipboard(elements.studioPromptInput.value, "AI prompt"));
        elements.copyHashtagsBtn.addEventListener("click", () => copyTextToClipboard(elements.studioHashtagsInput.value, "Hashtags"));
        elements.copyScriptBtn.addEventListener("click", () => copyTextToClipboard(elements.studioScriptInput.value, "Script"));
        elements.copyEditingStyleBtn.addEventListener("click", () => copyTextToClipboard(elements.studioEditingStyleInput.value, "Editing style"));

        elements.generateImageBtn.addEventListener("click", generatePostImage);

        elements.studioDoneBtn.addEventListener("click", () => {
            if (state.activePostIndex === null) return;
            const post = state.calendar[state.activePostIndex];
            post.is_done = !post.is_done;

            state.hasUnsavedChanges = true;
            elements.saveBtn.classList.remove("btn-secondary");
            elements.saveBtn.classList.add("btn-primary");

            selectPost(state.activePostIndex);
            renderCalendarTimeline();
        });

        elements.generateBtn.addEventListener("click", triggerGeneration);
        elements.ideaGenerateBtn.addEventListener("click", triggerIdeaGeneration);
        elements.saveBtn.addEventListener("click", saveCalendarEdits);
        elements.exportBtn.addEventListener("click", commitAndExportExcel);

        elements.historyHeaderBtn.addEventListener("click", () => {
            elements.historyContentArea.classList.toggle("expanded");
            const icon = elements.historyToggleBtn.querySelector("i");
            if (elements.historyContentArea.classList.contains("expanded")) {
                icon.className = "fa-solid fa-chevron-down";
                setTimeout(() => {
                    elements.historyContentArea.scrollIntoView({ behavior: "smooth", block: "end" });
                }, 200);
            } else {
                icon.className = "fa-solid fa-chevron-up";
            }
        });

        elements.historySearch.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = elements.historyTableBody.querySelectorAll("tr");
            if (state.history.posts.length === 0) return;
            rows.forEach(row => {
                row.style.display = row.innerText.toLowerCase().includes(query) ? "" : "none";
            });
        });

        window.addEventListener("beforeunload", (e) => {
            if (state.hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = "You have unsaved changes in your content calendar. Are you sure you want to leave?";
            }
        });
    }

    // START
    init();
});
