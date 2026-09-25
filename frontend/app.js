const API_BASE_URL = "http://127.0.0.1:8000";

let authToken = localStorage.getItem("smartresearch_token");
let currentUser = null;
let allPapers = [];


/* =========================================================
   DOM HELPERS
========================================================= */

const $ = (id) => document.getElementById(id);

function showElement(element) {
    if (element) {
        element.classList.remove("hidden");
    }
}

function hideElement(element) {
    if (element) {
        element.classList.add("hidden");
    }
}

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================================
   MESSAGES
========================================================= */

function showMessage(element, message, type = "") {
    if (!element) {
        return;
    }

    element.textContent = message;
    element.className = "form-message";

    if (type) {
        element.classList.add(type);
    }
}


function showToast(message, type = "success") {
    const toast = $("toast");

    if (!toast) {
        return;
    }

    toast.textContent = message;
    toast.className = "toast show";

    if (type === "error") {
        toast.style.borderColor = "var(--danger)";
    } else {
        toast.style.borderColor = "var(--border)";
    }

    setTimeout(() => {
        toast.className = "toast";
    }, 3000);
}


/* =========================================================
   AUTHENTICATION
========================================================= */

function showLoginView() {
    showElement($("loginView"));
    hideElement($("registerView"));

    $("loginMessage").textContent = "";
    $("registerMessage").textContent = "";
}


function showRegisterView() {
    hideElement($("loginView"));
    showElement($("registerView"));

    $("loginMessage").textContent = "";
    $("registerMessage").textContent = "";
}


function showDashboard() {
    hideElement($("authScreen"));
    showElement($("appScreen"));

    if (currentUser) {
        $("currentUsername").textContent =
            currentUser.username;

        $("currentRole").textContent =
            currentUser.role;

        const avatarLetter =
            currentUser.username
                .charAt(0)
                .toUpperCase();

        document.querySelector(".user-avatar").textContent =
            avatarLetter;
    }

    const uploadNav = $("uploadNavItem");

if (uploadNav) {
    showElement(uploadNav);
}

    loadPapers();

    showPage("home");
}


function showAuthScreen() {
    showElement($("authScreen"));
    hideElement($("appScreen"));

    showLoginView();
}


async function registerUser(username, password) {
    const response = await fetch(
        `${API_BASE_URL}/register`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                password,
                role: "user"
            })
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || "Registration failed."
        );
    }

    return data;
}


async function loginUser(username, password) {
    const response = await fetch(
        `${API_BASE_URL}/login`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                password
            })
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || "Login failed."
        );
    }

    return data;
}


async function verifyExistingToken() {
    if (!authToken) {
        showAuthScreen();
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/me`,
            {
                headers: {
                    Authorization:
                        `Bearer ${authToken}`
                }
            }
        );

        if (!response.ok) {
            throw new Error("Session expired.");
        }

        const data = await response.json();

        currentUser = data.user;

        showDashboard();

    } catch (error) {
        localStorage.removeItem(
            "smartresearch_token"
        );

        authToken = null;
        currentUser = null;

        showAuthScreen();
    }
}


/* =========================================================
   PAGE NAVIGATION
========================================================= */

function showPage(pageName) {

    document.querySelectorAll(".page").forEach(
        (page) => {
            page.classList.remove("active-page");
        }
    );

    const selectedPage =
        $(`page-${pageName}`);

    if (selectedPage) {
        selectedPage.classList.add("active-page");
    }

    document.querySelectorAll(".nav-item").forEach(
        (button) => {
            button.classList.remove("active");

            if (
                button.dataset.page === pageName
            ) {
                button.classList.add("active");
            }
        }
    );

    const navigation =
        $("mainNavigation");

    if (navigation) {
        navigation.classList.remove(
            "mobile-open"
        );
    }

    if (pageName === "repository") {
        renderRepository();
    }

    if (pageName === "home") {
        updateHomeStats();
    }
}


/* =========================================================
   PAPER REPOSITORY
========================================================= */

async function loadPapers() {
    try {

        const response = await fetch(
            `${API_BASE_URL}/papers`
        );

        if (!response.ok) {
            throw new Error(
                "Unable to load papers."
            );
        }

        const data = await response.json();

        allPapers = data.papers || [];

        updateHomeStats();

        renderRepository();

    } catch (error) {

        console.error(error);

        allPapers = [];

        renderRepository();

        showToast(
            "Unable to load the paper repository.",
            "error"
        );
    }
}


function updateHomeStats() {

    const totalPapers =
        $("totalPapers");

    const repositoryCount =
        $("repositoryCount");

    if (totalPapers) {
        totalPapers.textContent =
            allPapers.length;
    }

    if (repositoryCount) {
        repositoryCount.textContent =
            allPapers.length;
    }
}


function renderRepository() {

    const grid =
        $("repositoryGrid");

    if (!grid) {
        return;
    }

    const searchInput =
        $("repositorySearch");

    const domainFilter =
        $("domainFilter");

    const searchTerm =
        searchInput
            ? searchInput.value
                .trim()
                .toLowerCase()
            : "";

    const selectedDomain =
        domainFilter
            ? domainFilter.value
            : "";

    const filteredPapers =
        allPapers.filter((paper) => {

            const title =
                String(
                    paper.title || ""
                ).toLowerCase();

            const authors =
                String(
                    paper.authors || ""
                ).toLowerCase();

            const domain =
                String(
                    paper.domain || ""
                );

            const matchesSearch =
                !searchTerm ||
                title.includes(searchTerm) ||
                authors.includes(searchTerm);

            const matchesDomain =
                !selectedDomain ||
                domain === selectedDomain;

            return (
                matchesSearch &&
                matchesDomain
            );
        });


    if (filteredPapers.length === 0) {

        grid.innerHTML = `
            <div class="empty-state">
                <h3>No papers found</h3>
                <p>
                    Try another search or domain filter.
                </p>
            </div>
        `;

        return;
    }


    grid.innerHTML =
        filteredPapers.map((paper) => {

            const id =
                Number(paper.id);

            const title =
                escapeHtml(
                    paper.title ||
                    "Untitled Paper"
                );

            const authors =
                escapeHtml(
                    paper.authors ||
                    "Authors not available"
                );

            const domain =
                escapeHtml(
                    paper.domain ||
                    "General"
                );

            const year =
                paper.year ||
                "Year unavailable";


            return `
                <article class="paper-card">

                    <div class="paper-icon">
                        ▣
                    </div>

                    <h3>
                        ${title}
                    </h3>

                    <p>
                        ${authors}
                    </p>

                    <p>
                        ${year}
                    </p>

                    <div class="paper-card-footer">

                        <span class="domain-badge">
                            ${domain}
                        </span>

                        <button
                            class="read-button"
                            onclick="openPaper(${id})"
                        >
                            Read Paper →
                        </button>

                    </div>

                </article>
            `;

        }).join("");
}


function openPaper(paperId) {

    const pdfUrl =
        `${API_BASE_URL}/papers/${paperId}/pdf`;

    window.open(
        pdfUrl,
        "_blank"
    );
}


/* =========================================================
   SEMANTIC SEARCH
========================================================= */

async function performSearch() {

    const input =
        $("searchInput");

    const resultsContainer =
        $("searchResults");

    const status =
        $("searchStatus");

    if (!input || !resultsContainer) {
        return;
    }

    const query =
        input.value.trim();

    if (!query) {
        showMessage(
            status,
            "Please enter something to search.",
            "error"
        );

        return;
    }


    resultsContainer.innerHTML = "";

    showMessage(
        status,
        "Searching the research knowledge base..."
    );


    try {

        const response = await fetch(
            `${API_BASE_URL}/search`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    query,
                    top_k: 6
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Search failed."
            );
        }


        if (!data.results ||
            data.results.length === 0) {

            showMessage(
                status,
                "No relevant papers were found."
            );

            return;
        }


        showMessage(
            status,
            `Found ${data.results.length} relevant papers.`
        );


        resultsContainer.innerHTML =
            data.results.map(
                (result) => {

                    const title =
                        escapeHtml(
                            result.title ||
                            "Untitled Paper"
                        );

                    const domain =
                        escapeHtml(
                            result.domain ||
                            "General"
                        );

                    const year =
                        result.year ||
                        "Year unavailable";

                    const content =
                        escapeHtml(
                            result.content ||
                            "No matching passage available."
                        );

                    const similarity =
                        (
                            Number(
                                result.similarity
                            ) * 100
                        ).toFixed(1);


                    return `
                        <article
                            class="result-card"
                        >

                            <div class="result-top">

                                <span
                                    class="result-domain"
                                >
                                    ${domain}
                                </span>

                                <span
                                    class="similarity"
                                >
                                    ${similarity}%
                                    similarity
                                </span>

                            </div>

                            <h3>
                                ${title}
                            </h3>

                            <div
                                class="result-meta"
                            >
                                ${year}
                                ·
                                Matching chunk
                                ${result.best_chunk}
                            </div>

                            <p
                                class="result-content"
                            >
                                ${content}
                            </p>

                            <div
                                class="result-actions"
                            >

                                <button
                                    class="read-button"
                                    onclick="openPaper(${Number(result.paper_id)})"
                                >
                                    📄 Open Full Paper
                                </button>

                            </div>

                        </article>
                    `;

                }
            ).join("");


    } catch (error) {

        console.error(error);

        showMessage(
            status,
            error.message ||
            "Search failed.",
            "error"
        );
    }
}


/* =========================================================
   RESEARCH Q&A
========================================================= */

async function askResearchQuestion() {

    const input =
        $("questionInput");

    const resultContainer =
        $("qaResult");

    const status =
        $("qaStatus");

    const question =
        input.value.trim();

    if (!question) {

        showMessage(
            status,
            "Please enter a research question.",
            "error"
        );

        return;
    }


    hideElement(resultContainer);

    showMessage(
        status,
        "Retrieving relevant research context..."
    );


    try {

        const response = await fetch(
            `${API_BASE_URL}/ask`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    question,
                    top_k: 5
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to answer the question."
            );
        }


        let sourcesHtml = "";


        if (
            data.sources &&
            data.sources.length > 0
        ) {

            sourcesHtml = `
                <div class="source-list">

                    <h3>
                        Retrieved Sources
                    </h3>

                    ${data.sources.map(
                        (source) => {

                            return `
                                <div
                                    class="source-item"
                                >

                                    <strong>
                                        ${escapeHtml(
                                            source.title
                                        )}
                                    </strong>

                                    <span>
                                        ${escapeHtml(
                                            source.domain ||
                                            "General"
                                        )}
                                        ·
                                        similarity
                                        ${Number(
                                            source.similarity
                                        ).toFixed(4)}
                                    </span>

                                </div>
                            `;

                        }
                    ).join("")}

                </div>
            `;

        }


        resultContainer.innerHTML = `

            <h3>
                Research Answer
            </h3>

            <div
                class="answer-text"
            >
                ${escapeHtml(
                    data.answer ||
                    "No answer was generated."
                )}
            </div>

            ${sourcesHtml}

        `;


        showElement(resultContainer);

        showMessage(
            status,
            "Research context retrieved successfully."
        );


    } catch (error) {

        console.error(error);

        showMessage(
            status,
            error.message ||
            "Unable to answer the question.",
            "error"
        );
    }
}


/* =========================================================
   PAPER UPLOAD
========================================================= */

async function uploadPaper(event) {

    event.preventDefault();


    if (
        !authToken ||
        !currentUser ||
        currentUser.role !== "admin"
    ) {

        showToast(
            "Administrator access is required.",
            "error"
        );

        return;
    }


    const file =
        $("paperFile").files[0];

    const title =
        $("paperTitle").value.trim();

    const authors =
        $("paperAuthors").value.trim();

    const domain =
        $("paperDomain").value;

    const year =
        $("paperYear").value;


    if (!file) {

        showMessage(
            $("uploadMessage"),
            "Please select a PDF file.",
            "error"
        );

        return;
    }


    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    formData.append(
        "title",
        title
    );

    formData.append(
        "authors",
        authors
    );

    formData.append(
        "domain",
        domain
    );

    if (year) {

        formData.append(
            "year",
            year
        );

    }


    showMessage(
        $("uploadMessage"),
        "Uploading and processing paper..."
    );


    try {

        const response = await fetch(
            `${API_BASE_URL}/papers/upload`,
            {
                method: "POST",

                headers: {
                    Authorization:
                        `Bearer ${authToken}`
                },

                body: formData
            }
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Upload failed."
            );
        }


        showMessage(
            $("uploadMessage"),
            "Paper uploaded and processed successfully.",
            "success"
        );


        $("uploadForm").reset();

        showToast(
            "Research paper added successfully."
        );


        await loadPapers();

        showPage("repository");


    } catch (error) {

        console.error(error);

        showMessage(
            $("uploadMessage"),
            error.message ||
            "Upload failed.",
            "error"
        );
    }
}


/* =========================================================
   THEME
========================================================= */

function initializeTheme() {

    const savedTheme =
        localStorage.getItem(
            "smartresearch_theme"
        );

    const theme =
        savedTheme || "light";

    document.documentElement
        .setAttribute(
            "data-theme",
            theme
        );

    updateThemeIcon();
}


function toggleTheme() {

    const currentTheme =
        document.documentElement
            .getAttribute("data-theme") ||
        "light";

    const nextTheme =
        currentTheme === "dark"
            ? "light"
            : "dark";

    document.documentElement
        .setAttribute(
            "data-theme",
            nextTheme
        );

    localStorage.setItem(
        "smartresearch_theme",
        nextTheme
    );

    updateThemeIcon();
}


function updateThemeIcon() {

    const button =
        $("themeToggle");

    if (!button) {
        return;
    }

    const theme =
        document.documentElement
            .getAttribute("data-theme");

    button.textContent =
        theme === "dark"
            ? "☀"
            : "☾";
}


/* =========================================================
   EVENT LISTENERS
========================================================= */

function setupEventListeners() {

    /* Login */

    $("loginForm")
        .addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();

                const username =
                    $("loginUsername")
                        .value
                        .trim();

                const password =
                    $("loginPassword")
                        .value;

                showMessage(
                    $("loginMessage"),
                    "Signing in..."
                );


                try {

                    const data =
                        await loginUser(
                            username,
                            password
                        );


                    authToken =
                        data.access_token;

                    currentUser =
                        data.user;


                    localStorage.setItem(
                        "smartresearch_token",
                        authToken
                    );


                    showMessage(
                        $("loginMessage"),
                        "Login successful.",
                        "success"
                    );


                    showDashboard();


                } catch (error) {

                    showMessage(
                        $("loginMessage"),
                        error.message ||
                        "Login failed.",
                        "error"
                    );

                }

            }
        );


    /* Register */

    $("registerForm")
        .addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();

                const username =
                    $("registerUsername")
                        .value
                        .trim();

                const password =
                    $("registerPassword")
                        .value;


                showMessage(
                    $("registerMessage"),
                    "Creating your account..."
                );


                try {

                    await registerUser(
                        username,
                        password
                    );


                    showMessage(
                        $("registerMessage"),
                        "Account created successfully. You can now sign in.",
                        "success"
                    );


                    setTimeout(
                        () => {
                            showLoginView();

                            $("loginUsername")
                                .value =
                                username;

                            $("loginPassword")
                                .value = "";
                        },
                        1000
                    );


                } catch (error) {

                    showMessage(
                        $("registerMessage"),
                        error.message ||
                        "Registration failed.",
                        "error"
                    );

                }

            }
        );


    /* Auth switching */

    $("showRegisterButton")
        .addEventListener(
            "click",
            showRegisterView
        );


    $("showLoginButton")
        .addEventListener(
            "click",
            showLoginView
        );


    /* Logout */

    $("logoutButton")
        .addEventListener(
            "click",
            () => {

                localStorage.removeItem(
                    "smartresearch_token"
                );

                authToken = null;
                currentUser = null;

                showToast(
                    "You have been logged out."
                );

                setTimeout(
                    () => {
                        showAuthScreen();
                    },
                    500
                );

            }
        );


    /* Theme */

    $("themeToggle")
        .addEventListener(
            "click",
            toggleTheme
        );


    /* Navigation */

    document.querySelectorAll(
        ".nav-item"
    ).forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    const page =
                        button.dataset.page;

                    if (page) {
                        showPage(page);
                    }

                }
            );

        }
    );


    /* Home navigation buttons */

    document.querySelectorAll(
        "[data-go-page]"
    ).forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    showPage(
                        button.dataset.goPage
                    );

                }
            );

        }
    );


    /* Mobile menu */

    $("mobileMenuButton")
        .addEventListener(
            "click",
            () => {

                $("mainNavigation")
                    .classList.toggle(
                        "mobile-open"
                    );

            }
        );


    /* Search */

    $("searchButton")
        .addEventListener(
            "click",
            performSearch
        );


    $("searchInput")
        .addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Enter"
                ) {

                    event.preventDefault();

                    performSearch();

                }

            }
        );


    /* Q&A */

    $("askButton")
        .addEventListener(
            "click",
            askResearchQuestion
        );


    /* Repository */

    $("repositorySearch")
        .addEventListener(
            "input",
            renderRepository
        );


    $("domainFilter")
        .addEventListener(
            "change",
            renderRepository
        );


    /* Upload */

    $("uploadForm")
        .addEventListener(
            "submit",
            uploadPaper
        );

}


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeTheme();

        setupEventListeners();

        verifyExistingToken();

    }
);