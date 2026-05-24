// NEW GEN STUDIOS — AI Social Media Manager Front-End Orchestrator

document.addEventListener("DOMContentLoaded", () => {
    
    // STATE VARIABLES
    let state = {
        config: { has_api_key: false, default_pillars: [] },
        history: { posts: [] },
        calendar: [], // The current active scheduled posts
        activePostIndex: null, // The index of the post currently open in the studio
        hasUnsavedChanges: false
    };

    // DOM ELEMENTS
    const elements = {
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
        
        instaStatusBox: document.getElementById("insta-status-box"),
        instaStatusIndicator: document.getElementById("insta-status-indicator"),
        instaStatusText: document.getElementById("insta-status-text"),
        
        supabaseStatusBox: document.getElementById("supabase-status-box"),
        supabaseStatusIndicator: document.getElementById("supabase-status-indicator"),
        supabaseStatusText: document.getElementById("supabase-status-text"),

        
        brandHandleBadge: document.getElementById("brand-handle-badge"),
        brandHandleText: document.getElementById("brand-handle-text"),
        metricFollowers: document.querySelector("#metric-followers .metric-value"),
        metricFollowing: document.querySelector("#metric-following .metric-value"),
        metricViews: document.querySelector("#metric-views .metric-value"),

        
        planWeeks: document.getElementById("plan-weeks"),
        postsPerWeek: document.getElementById("posts-per-week"),
        generatorModel: document.getElementById("generator-model"),
        pillarsToggle: document.getElementById("pillars-toggle"),
        pillarsContainer: document.getElementById("pillars-container"),
        pillarsChecklist: document.getElementById("pillars-checklist"),
        
        generateBtn: document.getElementById("generate-btn"),
        saveBtn: document.getElementById("save-btn"),
        exportBtn: document.getElementById("export-btn"),
        
        genLoader: document.getElementById("gen-loader"),
        progressBar: document.getElementById("progress-bar"),
        loaderStatusText: document.getElementById("loader-status-text"),
        
        activeCalendarBadge: document.getElementById("active-calendar-badge"),
        calendarTimelineList: document.getElementById("calendar-timeline-list"),
        calendarEmptyState: document.getElementById("calendar-empty-state"),
        
        studioPanel: document.getElementById("studio-panel"),
        studioEmptyState: document.getElementById("studio-empty-state"),
        studioEditorContent: document.getElementById("studio-editor-content"),
        
        studioPostNumber: document.getElementById("studio-post-number"),
        studioPostType: document.getElementById("studio-post-type"),
        studioDatetime: document.getElementById("studio-datetime"),
        studioFormatBadge: document.getElementById("studio-format-badge"),
        studioHookInput: document.getElementById("studio-hook-input"),
        studioCaptionInput: document.getElementById("studio-caption-input"),
        studioPromptInput: document.getElementById("studio-prompt-input"),
        studioHashtagsInput: document.getElementById("studio-hashtags-input"),
        studioNotesInput: document.getElementById("studio-notes-input"),
        studioToolRec: document.getElementById("studio-tool-recommendation"),
        studioDoneBtn: document.getElementById("studio-done-btn"),
        
        copyHookBtn: document.getElementById("copy-hook-btn"),
        copyCaptionBtn: document.getElementById("copy-caption-btn"),
        copyPromptBtn: document.getElementById("copy-prompt-btn"),
        copyHashtagsBtn: document.getElementById("copy-hashtags-btn"),
        
        historyHeaderBtn: document.getElementById("history-header-btn"),
        historyContentArea: document.getElementById("history-content-area"),
        historyToggleBtn: document.getElementById("history-toggle-btn"),
        historySearch: document.getElementById("history-search"),
        historyTableBody: document.getElementById("history-table-body"),
        
        toastNotif: document.getElementById("toast-notif"),
        toastText: document.getElementById("toast-text")
    };

    // INITIALIZATION
    async function init() {
        // Register event listeners immediately so the UI is fully responsive (close/cancel modal buttons work instantly)
        setupEventListeners();
        
        showToast("System initialized. Loading configuration...");
        try {
            // Load configuration first to check active cloud/Insta integrations
            await loadConfig();
            
            // Fetch history, calendar, and Instagram profiles concurrently in the background.
            // This prevents a slow Instagram login connection from blocking the page thread or indicators.
            loadHistory();
            loadCalendar();
            loadInstagramProfile();
        } catch (err) {
            console.error("⚠️ Initialization failed:", err);
        }
    }

    async function loadInstagramProfile() {
        if (!state.config.has_instagram) {
            updateInstagramUI({ status: "offline", message: "Instagram connection not configured." });
            return;
        }

        updateInstagramUI({ status: "loading", message: "Connecting to Instagram..." });

        try {
            const res = await fetch("/api/instagram/profile");
            if (!res.ok) throw new Error("Server communication error");
            const result = await res.json();
            
            updateInstagramUI(result);
        } catch (err) {
            console.error(err);
            updateInstagramUI({ status: "error", message: "Failed to connect: " + err.message });
        }
    }

    function updateInstagramUI(result) {
        const badge = elements.brandHandleBadge;
        const text = elements.brandHandleText;
        const followers = elements.metricFollowers;
        const following = elements.metricFollowing;
        const views = elements.metricViews;

        if (result.status === "online") {
            const data = result.data;
            badge.className = "status-badge brand-handle online";
            text.textContent = `@${data.username}`;
            followers.textContent = formatCompactNumber(data.followers);
            following.textContent = formatCompactNumber(data.following);
            views.textContent = data.views;
            
            // Dynamically show actual live posts count in header
            elements.historyValue.textContent = data.posts_count;
            
            elements.instaStatusIndicator.className = "status-indicator success";
            elements.instaStatusText.textContent = `Connected as @${data.username}`;
        } else if (result.status === "offline") {
            badge.className = "status-badge brand-handle offline";
            text.textContent = "Offline Mode";
            followers.textContent = "-";
            following.textContent = "-";
            views.textContent = "-";
            
            // Restore local history post count
            elements.historyValue.textContent = state.history.posts ? state.history.posts.length : "0";
            
            elements.instaStatusIndicator.className = "status-indicator";
            elements.instaStatusText.textContent = "Instagram connection is not active.";
        } else if (result.status === "loading") {
            badge.className = "status-badge brand-handle";
            text.textContent = "Connecting...";
            followers.textContent = "...";
            following.textContent = "...";
            views.textContent = "...";
            
            elements.instaStatusIndicator.className = "status-indicator warning";
            elements.instaStatusText.textContent = result.message || "Connecting...";
        } else {
            // error
            badge.className = "status-badge brand-handle error";
            text.textContent = "Sync Error";
            followers.textContent = "Error";
            following.textContent = "Error";
            views.textContent = "Error";
            
            // Restore local history post count
            elements.historyValue.textContent = state.history.posts ? state.history.posts.length : "0";
            
            elements.instaStatusIndicator.className = "status-indicator error";
            elements.instaStatusText.textContent = result.message || "Connection failed.";
        }
    }

    function formatCompactNumber(num) {
        if (num === undefined || num === null || isNaN(num)) return "-";
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1).replace(/\.0$/, "") + "K";
        }
        return num.toString();
    }


    // API CALLS
    async function loadConfig() {
        try {
            const res = await fetch("/api/config");
            if (!res.ok) throw new Error("Failed to load configuration");
            state.config = await res.json();
            
            updateConfigUI();
            renderPillarsChecklist();
        } catch (err) {
            console.error(err);
            showToast("Error loading config: " + err.message, "error");
        }
    }

    async function loadHistory() {
        try {
            const res = await fetch("/api/history");
            if (!res.ok) throw new Error("Failed to load history");
            state.history = await res.json();
            
            elements.historyValue.textContent = state.history.posts.length;
            renderHistoryTable(state.history.posts);
        } catch (err) {
            console.error(err);
            elements.historyValue.textContent = "0";
            showToast("Error loading history: " + err.message, "error");
        }
    }

    async function loadCalendar() {
        try {
            const res = await fetch("/api/calendar");
            if (!res.ok) throw new Error("Failed to load calendar");
            const data = await res.json();
            state.calendar = data;
            
            renderCalendarTimeline();
        } catch (err) {
            console.error(err);
            showToast("Error loading calendar: " + err.message, "error");
        }
    }

    // UI RENDERERS
    function updateConfigUI() {
        if (state.config.has_api_key) {
            elements.keyStatusIndicator.className = "status-indicator success";
            elements.keyStatusText.textContent = "Gemini API Key is active & configured.";
            elements.openSettingsBtn.style.color = "var(--purple)";
        } else {
            elements.keyStatusIndicator.className = "status-indicator error";
            elements.keyStatusText.textContent = "No Gemini API Key found. Configure key to start.";
            elements.openSettingsBtn.style.color = "var(--red)";
        }

        // Render Supabase Sync Indicator
        if (state.config.has_supabase) {
            elements.supabaseStatusIndicator.className = "status-indicator success";
            elements.supabaseStatusText.textContent = "Supabase cloud sync is active.";
        } else {
            elements.supabaseStatusIndicator.className = "status-indicator";
            elements.supabaseStatusText.textContent = "Supabase is offline (local JSON backup active).";
        }
    }


    function renderPillarsChecklist() {
        elements.pillarsChecklist.innerHTML = "";
        state.config.default_pillars.forEach((pillar, i) => {
            const label = document.createElement("label");
            label.className = "pillar-checkbox-label";
            label.innerHTML = `
                <input type="checkbox" value="${pillar}" checked>
                <span>${pillar}</span>
            `;
            elements.pillarsChecklist.appendChild(label);
        });
    }

    function renderCalendarTimeline() {
        // Clear previous list, leaving only the empty state placeholder
        const cardElements = elements.calendarTimelineList.querySelectorAll(".timeline-card");
        cardElements.forEach(el => el.remove());

        if (state.calendar.length === 0) {
            elements.calendarEmptyState.classList.remove("hidden");
            elements.activeCalendarBadge.textContent = "No active calendar loaded";
            elements.scheduledValue.textContent = "-";
            elements.saveBtn.classList.add("hidden");
            elements.exportBtn.classList.add("hidden");
            closeStudio();
            return;
        }

        elements.calendarEmptyState.classList.add("hidden");
        elements.activeCalendarBadge.textContent = `${state.calendar.length} posts scheduled`;
        elements.scheduledValue.textContent = state.calendar.length;
        elements.saveBtn.classList.remove("hidden");
        elements.exportBtn.classList.remove("hidden");

        // Parse date for building calendar cards
        state.calendar.forEach((post, index) => {
            // Find index of pillar to assign matching color code
            const pillarIndex = state.config.default_pillars.indexOf(post.post_type);
            const pillarClass = pillarIndex !== -1 ? `pillar-${pillarIndex}` : "";

            // Parse Date string (e.g. "27 May 2025")
            let dayNum = "??";
            let monthStr = "MAY";
            try {
                const parts = post.date.split(" ");
                dayNum = parts[0];
                monthStr = parts[1].substring(0, 3).toUpperCase();
            } catch (e) {}

            const activeClass = state.activePostIndex === index ? "active" : "";
            const uploadedClass = post.is_done ? "uploaded" : "";
            const checkIcon = post.is_done ? '<i class="fa-solid fa-circle-check uploaded-check-icon" title="Uploaded"></i>' : '';

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
                        <span class="time"><i class="fa-regular fa-clock"></i> ${post.day} ${post.time.split(" ")[0]}</span>
                        <span class="format-tag">${post.reel_or_static}</span>
                        ${checkIcon}
                    </div>
                    <h4>${post.post_type}</h4>
                    <span class="hook-preview">"${post.hook}"</span>
                </div>
            `;

            card.addEventListener("click", () => selectPost(index));
            elements.calendarTimelineList.appendChild(card);
        });

        // Maintain selection after reload if index is valid
        if (state.activePostIndex !== null && state.activePostIndex < state.calendar.length) {
            selectPost(state.activePostIndex);
        } else {
            closeStudio();
        }
    }

    function renderHistoryTable(posts) {
        elements.historyTableBody.innerHTML = "";
        if (posts.length === 0) {
            elements.historyTableBody.innerHTML = `<tr><td colspan="4" class="table-loading">No past posts found in history. This will be the first generation run.</td></tr>`;
            return;
        }

        posts.forEach(post => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${post.date}</strong></td>
                <td><span class="format-badge" style="padding: 0.15rem 0.4rem; font-size: 0.65rem;"><i class="${post.reel_or_static === 'Reel' ? 'fa-solid fa-video' : 'fa-solid fa-image'}"></i> ${post.reel_or_static}</span></td>
                <td>${post.post_type}</td>
                <td>${post.idea_summary}</td>
            `;
            elements.historyTableBody.appendChild(tr);
        });
    }

    // STUDIO ACTIONS
    function selectPost(index) {
        state.activePostIndex = index;
        const post = state.calendar[index];

        // Toggle active card CSS
        const cards = elements.calendarTimelineList.querySelectorAll(".timeline-card");
        cards.forEach((card, i) => {
            if (i === index) card.classList.add("active");
            else card.classList.remove("active");
        });

        // Load studio data
        elements.studioEmptyState.classList.add("hidden");
        elements.studioEditorContent.classList.remove("hidden");

        elements.studioPostNumber.textContent = `#${post.post_number}`;
        elements.studioPostType.textContent = post.post_type;
        elements.studioDatetime.textContent = `${post.date} (${post.day}) @ ${post.time}`;
        
        // Format Icon & Badge
        const isReel = post.reel_or_static === "Reel";
        elements.studioFormatBadge.innerHTML = `<i class="${isReel ? 'fa-solid fa-video' : 'fa-solid fa-image'}"></i> ${post.reel_or_static}`;
        
        // Populate inputs
        elements.studioHookInput.value = post.hook;
        elements.studioCaptionInput.value = post.caption;
        elements.studioPromptInput.value = post.image_prompt;
        elements.studioHashtagsInput.value = post.hashtags;
        elements.studioNotesInput.value = post.notes_for_creator;

        // Toggle Done Button Style
        if (post.is_done) {
            elements.studioDoneBtn.classList.add("done");
            elements.studioDoneBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> <span>Uploaded</span>';
        } else {
            elements.studioDoneBtn.classList.remove("done");
            elements.studioDoneBtn.innerHTML = '<i class="fa-regular fa-circle-check"></i> <span>Mark Done</span>';
        }

        // Tool Recommendations & Links
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

        // Scroll to editor on mobile
        if (window.innerWidth <= 1024) {
            elements.studioPanel.scrollIntoView({ behavior: "smooth" });
        }
    }

    function closeStudio() {
        state.activePostIndex = null;
        elements.studioEmptyState.classList.remove("hidden");
        elements.studioEditorContent.classList.add("hidden");
    }

    function handleStudioInputChange() {
        if (state.activePostIndex === null) return;
        
        const index = state.activePostIndex;
        const post = state.calendar[index];

        // Detect edits
        post.hook = elements.studioHookInput.value;
        post.caption = elements.studioCaptionInput.value;
        post.image_prompt = elements.studioPromptInput.value;
        post.hashtags = elements.studioHashtagsInput.value;
        post.notes_for_creator = elements.studioNotesInput.value;

        // Mark unsaved and trigger button glows
        state.hasUnsavedChanges = true;
        elements.saveBtn.classList.remove("btn-secondary");
        elements.saveBtn.classList.add("btn-primary");
        
        // Update Hook in the Timeline Card dynamically
        const activeCard = elements.calendarTimelineList.querySelector(`.timeline-card.active`);
        if (activeCard) {
            const hookPreview = activeCard.querySelector(".hook-preview");
            if (hookPreview) hookPreview.textContent = `"${post.hook}"`;
        }
    }

    // ACTIONS: SAVE & EXPORT
    async function saveCalendarEdits() {
        if (state.calendar.length === 0) return;
        
        elements.saveBtn.disabled = true;
        const text = elements.saveBtn.querySelector(".btn-text") || elements.saveBtn;
        const origContent = text.innerHTML;
        text.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        try {
            const res = await fetch("/api/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ posts: state.calendar })
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
        if (state.calendar.length === 0) return;

        elements.exportBtn.disabled = true;
        const origContent = elements.exportBtn.innerHTML;
        elements.exportBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Exporting...';

        try {
            // Save state first
            const saveRes = await fetch("/api/export", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ posts: state.calendar })
            });

            if (!saveRes.ok) throw new Error("Export generation request failed");
            
            // Handle binary Excel response
            const blob = await saveRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.download = "content_calendar.xlsx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            showToast("Calendar exported & history committed successfully!");
            state.hasUnsavedChanges = false;
            elements.saveBtn.classList.remove("btn-primary");
            elements.saveBtn.classList.add("btn-secondary");

            // Reload history to show updated post count
            await loadHistory();
        } catch (err) {
            console.error(err);
            showToast("Export failed: " + err.message, "error");
        } finally {
            elements.exportBtn.innerHTML = origContent;
            elements.exportBtn.disabled = false;
        }
    }

    // ACTIONS: GENERATION
    async function triggerGeneration() {
        if (!state.config.has_api_key) {
            showToast("Please configure your Gemini API Key in Settings first!", "error");
            openSettings();
            return;
        }

        const weeks = parseInt(elements.planWeeks.value);
        const postsPerWeek = parseInt(elements.postsPerWeek.value);
        const modelName = elements.generatorModel.value;

        // Get checked pillars
        const checkedPillars = [];
        const checkboxes = elements.pillarsChecklist.querySelectorAll("input[type='checkbox']");
        checkboxes.forEach(cb => {
            if (cb.checked) checkedPillars.push(cb.value);
        });

        if (checkedPillars.length === 0) {
            showToast("Please select at least one active Content Pillar!", "error");
            return;
        }

        // Show full page loader and start progress animations
        elements.genLoader.classList.remove("hidden");
        elements.generateBtn.disabled = true;
        
        let statuses = [
            "Connecting to Gemini API...",
            "Loading past posts history to verify unique topics...",
            "Creating luxury Jewellry & Saree hooks...",
            "Formulating high-converting Call-to-Actions...",
            "Optimizing Instagram captions & creator notes...",
            "Reviewing Midjourney and Runway AI visual prompts...",
            "Applying target audience optimization (UK/US/Australia/UAE)..."
        ];
        
        let statusIndex = 0;
        const statusInterval = setInterval(() => {
            if (statusIndex < statuses.length - 1) {
                statusIndex++;
                elements.loaderStatusText.textContent = statuses[statusIndex];
            }
        }, 3500);

        try {
            const res = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    weeks: weeks,
                    posts_per_week: postsPerWeek,
                    pillars: checkedPillars,
                    model_name: modelName
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Generation failed");
            }

            const data = await res.json();
            state.calendar = data;
            state.activePostIndex = 0; // Automatically open first post
            state.hasUnsavedChanges = false;
            
            showToast(`Generated ${data.length} posts successfully!`);
            
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

    // SETTINGS MODAL
    function openSettings() {
        elements.settingsApiKey.value = "";
        elements.settingsModal.classList.remove("hidden");
        elements.settingsApiKey.focus();
    }

    function closeSettings() {
        elements.settingsModal.classList.add("hidden");
    }

    async function saveSettings() {
        const apiKey = elements.settingsApiKey.value.trim();

        if (!apiKey && !state.config.has_api_key) {
            showToast("Gemini API Key is required to plan content", "error");
            return;
        }

        elements.saveSettingsBtn.disabled = true;
        elements.saveSettingsBtn.textContent = "Saving...";

        try {
            // Save Gemini API Key if entered
            if (apiKey) {
                const res = await fetch("/api/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ api_key: apiKey })
                });
                if (!res.ok) throw new Error("Failed to save Gemini API Key");
                showToast("Gemini API Key updated successfully!");
            }
            
            await loadConfig();
            await loadInstagramProfile();
            await loadHistory();
            await loadCalendar();
            closeSettings();
        } catch (err) {
            console.error(err);
            showToast("Error updating settings: " + err.message, "error");
        } finally {
            elements.saveSettingsBtn.disabled = false;
            elements.saveSettingsBtn.textContent = "Save Key Settings";
        }
    }



    // CLIPBOARD ACTIONS
    function copyTextToClipboard(text, badgeType) {
        if (!text) return;
        navigator.clipboard.writeText(text).then(() => {
            showToast(`${badgeType} copied to clipboard!`);
        }).catch(err => {
            console.error(err);
            showToast("Failed to copy", "error");
        });
    }

    // DYNAMIC TOAST UTILITIES
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
        
        // CSS bounce in
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

    // EVENT LISTENERS
    function setupEventListeners() {
        // Settings Toggles
        elements.openSettingsBtn.addEventListener("click", openSettings);
        elements.closeSettingsBtn.addEventListener("click", closeSettings);
        elements.cancelSettingsBtn.addEventListener("click", closeSettings);
        elements.saveSettingsBtn.addEventListener("click", saveSettings);
        
        elements.toggleKeyVisibility.addEventListener("click", () => {
            const type = elements.settingsApiKey.type === "password" ? "text" : "password";
            elements.settingsApiKey.type = type;
            elements.toggleKeyVisibility.querySelector("i").className = type === "password" ? "fa-regular fa-eye" : "fa-regular fa-eye-slash";
        });


        // Collapsible Content Pillars
        elements.pillarsToggle.addEventListener("click", () => {
            elements.pillarsContainer.classList.toggle("expanded");
            const icon = elements.pillarsToggle.querySelector("i");
            if (elements.pillarsContainer.classList.contains("expanded")) {
                icon.className = "fa-solid fa-chevron-up";
            } else {
                icon.className = "fa-solid fa-chevron-down";
            }
        });

        // Studio Live Editors
        elements.studioHookInput.addEventListener("input", handleStudioInputChange);
        elements.studioCaptionInput.addEventListener("input", handleStudioInputChange);
        elements.studioPromptInput.addEventListener("input", handleStudioInputChange);
        elements.studioHashtagsInput.addEventListener("input", handleStudioInputChange);
        elements.studioNotesInput.addEventListener("input", handleStudioInputChange);

        // Copy Actions
        elements.copyHookBtn.addEventListener("click", () => copyTextToClipboard(elements.studioHookInput.value, "Hook"));
        elements.copyCaptionBtn.addEventListener("click", () => copyTextToClipboard(elements.studioCaptionInput.value, "Caption"));
        elements.copyPromptBtn.addEventListener("click", () => copyTextToClipboard(elements.studioPromptInput.value, "AI prompt"));
        elements.copyHashtagsBtn.addEventListener("click", () => copyTextToClipboard(elements.studioHashtagsInput.value, "Hashtags"));

        // Mark Done Status Action
        elements.studioDoneBtn.addEventListener("click", () => {
            if (state.activePostIndex === null) return;
            const index = state.activePostIndex;
            const post = state.calendar[index];
            
            // Toggle status
            post.is_done = !post.is_done;
            
            // Update Save button styling to show there are unsaved changes
            state.hasUnsavedChanges = true;
            elements.saveBtn.classList.remove("btn-secondary");
            elements.saveBtn.classList.add("btn-primary");
            
            // Refresh UI
            selectPost(index);
            renderCalendarTimeline();
        });

        // Global Action Buttons
        elements.generateBtn.addEventListener("click", triggerGeneration);
        elements.saveBtn.addEventListener("click", saveCalendarEdits);
        elements.exportBtn.addEventListener("click", commitAndExportExcel);

        // History Drawer Toggle
        elements.historyHeaderBtn.addEventListener("click", () => {
            elements.historyContentArea.classList.toggle("expanded");
            const icon = elements.historyToggleBtn.querySelector("i");
            if (elements.historyContentArea.classList.contains("expanded")) {
                icon.className = "fa-solid fa-chevron-down";
                // Scroll down to see full table
                setTimeout(() => {
                    elements.historyContentArea.scrollIntoView({ behavior: "smooth", block: "end" });
                }, 200);
            } else {
                icon.className = "fa-solid fa-chevron-up";
            }
        });

        // Live Search Filter on History
        elements.historySearch.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = elements.historyTableBody.querySelectorAll("tr");
            
            if (state.history.posts.length === 0) return;

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });

        // Prompt Unsaved Changes Warning on tab close
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
