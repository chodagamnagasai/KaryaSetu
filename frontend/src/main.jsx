import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
    LayoutDashboard,
    FolderKanban,
    Mic,
    Activity,
    AlertTriangle,
    Users,
    LogOut,
    Upload,
    RefreshCw,
    CheckCircle2,
    BrainCircuit,
    TrendingDown,
    Plus,
    Sparkles,
    FileSpreadsheet,
    PencilLine,
    ShieldCheck,
    Clock3,
    ChevronRight,
    Menu,
    X,
    Radio,
    BarChart3,
    Zap,
    MapPin,
    CalendarDays,
    Target,
    CircleDot,
} from "lucide-react";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
} from "recharts";

import "./styles.css";

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const demo = {
    admin: ["admin@karyasetu.demo", "Admin@123"],
    manager: ["manager@karyasetu.demo", "Manager@123"],
    supervisor: ["supervisor@karyasetu.demo", "Supervisor@123"],
};

async function api(path, options = {}) {
    const token = localStorage.getItem("karyasetu_token");

    const headers = {
        ...(options.body instanceof FormData
            ? {}
            : { "Content-Type": "application/json" }),
        ...(options.headers || {}),
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(API + path, {
        ...options,
        headers,
    });

    const text = await response.text();

    let data = {};

    try {
        data = JSON.parse(text);
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.detail || text || `Request failed with HTTP ${response.status}`
        );
    }

    return data;
}

/* =========================================================
   LOGIN
========================================================= */

function Login({ onLogin }) {
    const [email, setEmail] = useState(demo.supervisor[0]);
    const [password, setPassword] = useState(demo.supervisor[1]);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    async function submit(e) {
        e.preventDefault();

        setBusy(true);
        setError("");

        try {
            const data = await api("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email,
                    password,
                }),
            });

            localStorage.setItem("karyasetu_token", data.token);
            onLogin(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="login-page">
            <div className="login-glow glow-one" />
            <div className="login-glow glow-two" />

            <div className="login-shell">
                <div className="login-visual">
                    <div className="visual-grid" />

                    <div className="visual-content">
                        <div className="brand-large">
                            <div className="brand-mark">
                                <BrainCircuit size={27} />
                            </div>

                            <div>
                                <strong>KaryaSetu</strong>
                                <span>Execution Intelligence</span>
                            </div>
                        </div>

                        <div className="visual-title">
                            <span className="gradient-label">
                                <Sparkles size={14} />
                                AI-POWERED PROJECT CONTROL
                            </span>

                            <h1>
                                Turn site updates
                                <br />
                                into <span>project intelligence.</span>
                            </h1>

                            <p>
                                Connect planning, field execution, AI analysis and project
                                control in one intelligent workspace.
                            </p>
                        </div>

                        <div className="login-features">
                            <Feature
                                icon={<Mic size={18} />}
                                title="Voice-first updates"
                                text="Speak naturally from the site."
                            />

                            <Feature
                                icon={<Target size={18} />}
                                title="Smart schedule matching"
                                text="Automatically identify the correct activity."
                            />

                            <Feature
                                icon={<ShieldCheck size={18} />}
                                title="Risk intelligence"
                                text="Detect delays before they become critical."
                            />
                        </div>
                    </div>
                </div>

                <div className="login-card">
                    <div className="mobile-brand">
                        <div className="brand-mark">
                            <BrainCircuit size={22} />
                        </div>
                        <strong>KaryaSetu</strong>
                    </div>

                    <div className="login-heading">
                        <span>WELCOME BACK</span>
                        <h2>Sign in to your workspace</h2>
                        <p>Monitor projects and turn field updates into action.</p>
                    </div>

                    <form onSubmit={submit}>
                        <label>
                            Email address
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@company.com"
                            />
                        </label>

                        <label>
                            Password
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                            />
                        </label>

                        {error && <div className="error">{error}</div>}

                        <button className="primary-btn login-btn" disabled={busy}>
                            {busy ? (
                                <>
                                    <span className="spinner" />
                                    Signing in...
                                </>
                            ) : (
                                <>
                                    Sign in
                                    <ChevronRight size={17} />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="demo-box">
                        <div>
                            <span className="demo-title">DEMO ACCESS</span>
                            <p>Choose a role to quickly fill credentials.</p>
                        </div>

                        <div className="demo-buttons">
                            {Object.entries(demo).map(([role, credentials]) => (
                                <button
                                    type="button"
                                    key={role}
                                    onClick={() => {
                                        setEmail(credentials[0]);
                                        setPassword(credentials[1]);
                                    }}
                                >
                                    {role}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function Feature({ icon, title, text }) {
    return (
        <div className="login-feature">
            <div className="feature-icon">{icon}</div>

            <div>
                <strong>{title}</strong>
                <span>{text}</span>
            </div>
        </div>
    );
}

/* =========================================================
   MAIN SHELL
========================================================= */

function Shell({ user, onLogout }) {
    const [page, setPage] = useState("dashboard");
    const [refresh, setRefresh] = useState(0);
    const [mobileMenu, setMobileMenu] = useState(false);

    const nav = [
        ["dashboard", "Dashboard", LayoutDashboard],
        ["projects", "Projects", FolderKanban],
        ["updates", "Update Center", Radio],
        ["activities", "Activities", Activity],
        ["risks", "Risks", AlertTriangle],
        ["users", "Users", Users],
    ];

    const currentPage = nav.find((item) => item[0] === page);

    function go(nextPage) {
        setPage(nextPage);
        setRefresh((x) => x + 1);
        setMobileMenu(false);
    }

    return (
        <div className="app">
            <div
                className={`mobile-overlay ${mobileMenu ? "show" : ""}`}
                onClick={() => setMobileMenu(false)}
            />

            <aside className={mobileMenu ? "sidebar mobile-open" : "sidebar"}>
                <div className="sidebar-top">
                    <div className="side-brand">
                        <div className="brand-mark small">
                            <BrainCircuit size={20} />
                        </div>

                        <div className="side-brand-text">
                            <strong>KaryaSetu</strong>
                            <span>Project Intelligence</span>
                        </div>

                        <button
                            className="mobile-close"
                            onClick={() => setMobileMenu(false)}
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="role-chip">
                        <span className="online-dot" />
                        {user.role}
                    </div>
                </div>

                <div className="nav-label">WORKSPACE</div>

                <nav>
                    {nav.map(([id, label, Icon]) => (
                        <button
                            key={id}
                            className={page === id ? "nav-item active" : "nav-item"}
                            onClick={() => go(id)}
                        >
                            <span className="nav-icon">
                                <Icon size={18} />
                            </span>

                            <span>{label}</span>

                            {id === "updates" && (
                                <span className="nav-new">LIVE</span>
                            )}
                        </button>
                    ))}
                </nav>

                <div className="sidebar-bottom">
                    <div className="sidebar-ai">
                        <div className="ai-orb">
                            <Sparkles size={17} />
                        </div>

                        <div>
                            <strong>AI Engine</strong>
                            <span>Ready to analyze</span>
                        </div>

                        <span className="status-dot" />
                    </div>

                    <button className="logout" onClick={onLogout}>
                        <LogOut size={17} />
                        Logout
                    </button>
                </div>
            </aside>

            <main className="main">
                <header className="topbar">
                    <button
                        className="mobile-menu"
                        onClick={() => setMobileMenu(true)}
                    >
                        <Menu size={22} />
                    </button>

                    <div className="page-title">
                        <span className="breadcrumb">KARYASETU / WORKSPACE</span>
                        <h2>{currentPage?.[1]}</h2>
                    </div>

                    <div className="topbar-right">
                        <div className="system-status">
                            <span className="status-dot" />
                            Systems operational
                        </div>

                        <div className="user-avatar">
                            {(user.name || user.email || "U")
                                .charAt(0)
                                .toUpperCase()}
                        </div>

                        <div className="user-info">
                            <strong>{user.name || "Project User"}</strong>
                            <span>{user.role}</span>
                        </div>
                    </div>
                </header>

                <section className="content">
                    {page === "dashboard" && <Dashboard key={refresh} />}
                    {page === "projects" && <Projects key={refresh} />}
                    {page === "updates" && <UpdateCenter key={refresh} />}
                    {page === "activities" && <Activities key={refresh} />}
                    {page === "risks" && <Risks key={refresh} />}
                    {page === "users" && <UsersPage key={refresh} />}
                </section>
            </main>
        </div>
    );
}

/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard() {
    const [data, setData] = useState(null);
    const [err, setErr] = useState("");

    const load = () =>
        api("/api/dashboard")
            .then((result) => {
                setData(result);
                setErr("");
            })
            .catch((e) => setErr(e.message));

    useEffect(() => {
        load();

        const timer = setInterval(load, 10000);

        return () => clearInterval(timer);
    }, []);

    if (err) {
        return <ErrorBox message={err} />;
    }

    if (!data) {
        return <Loading />;
    }

    const s = data.kpis || {};

    const chart = (data.activities || []).reduce((map, activity) => {
        const project =
            map[activity.project_id] ||
            {
                name: activity.project_id,
                planned: 0,
                actual: 0,
                n: 0,
            };

        project.planned += Number(activity.planned_progress) || 0;
        project.actual += Number(activity.actual_progress) || 0;
        project.n++;

        map[activity.project_id] = project;

        return map;
    }, {});

    const chartData = Object.values(chart).map((x) => ({
        name: String(x.name).slice(0, 16),
        planned: Math.round(x.planned / x.n),
        actual: Math.round(x.actual / x.n),
    }));

    return (
        <div className="dashboard">
            <div className="dashboard-hero">
                <div className="hero-content">
                    <div className="live-label">
                        <span className="pulse" />
                        LIVE PROJECT CONTROL CENTER
                    </div>

                    <h1>
                        See what is happening
                        <br />
                        <span>on site, in real time.</span>
                    </h1>

                    <p>
                        KaryaSetu connects your schedule with field execution.
                        Capture updates by voice, text or Excel and let AI identify
                        progress, delays, risks and corrective actions.
                    </p>

                    <div className="hero-actions">
                        <div className="hero-stat">
                            <Zap size={16} />
                            AI monitoring active
                        </div>

                        <div className="hero-stat">
                            <Clock3 size={16} />
                            Live refresh · 10s
                        </div>
                    </div>
                </div>

                <div className="hero-visual">
                    <div className="orbit orbit-one" />
                    <div className="orbit orbit-two" />

                    <div className="hero-ai-card">
                        <div className="ai-card-icon">
                            <BrainCircuit size={32} />
                        </div>

                        <span>AI ENGINE</span>
                        <strong>Monitoring</strong>

                        <div className="ai-progress">
                            <i />
                        </div>

                        <small>
                            Schedule intelligence active
                        </small>
                    </div>
                </div>
            </div>

            <div className="section-heading">
                <div>
                    <span>PROJECT OVERVIEW</span>
                    <h3>Execution at a glance</h3>
                </div>

                <button className="refresh-btn" onClick={load}>
                    <RefreshCw size={15} />
                    Refresh
                </button>
            </div>

            <div className="kpi-grid">
                <KpiCard
                    icon={<FolderKanban size={19} />}
                    title="Projects"
                    value={s.projects ?? 0}
                    label="Active projects"
                />

                <KpiCard
                    icon={<TrendingDown size={19} />}
                    title="Actual progress"
                    value={`${s.progress ?? 0}%`}
                    label="Average execution"
                />

                <KpiCard
                    icon={<AlertTriangle size={19} />}
                    title="Delayed"
                    value={s.delayed ?? 0}
                    label="Activities behind plan"
                    danger={true}
                />

                <KpiCard
                    icon={<ShieldCheck size={19} />}
                    title="Open risks"
                    value={s.risks ?? 0}
                    label="Needs attention"
                    warning={true}
                />

                <KpiCard
                    icon={<CircleDot size={19} />}
                    title="At risk"
                    value={s.at_risk ?? 0}
                    label="Potential deviation"
                />

                <KpiCard
                    icon={<Target size={19} />}
                    title="Critical"
                    value={s.critical ?? 0}
                    label="High priority"
                    danger={true}
                />
            </div>

            <div className="dashboard-grid">
                <div className="panel chart-panel">
                    <PanelHeader
                        eyebrow="EXECUTION ANALYTICS"
                        title="Planned vs actual progress"
                    />

                    <div className="chart-legend">
                        <span>
                            <i className="legend planned" />
                            Planned
                        </span>

                        <span>
                            <i className="legend actual" />
                            Actual
                        </span>
                    </div>

                    <div className="chart">
                        {chartData.length ? (
                            <ResponsiveContainer width="100%" height={330}>
                                <BarChart
                                    data={chartData}
                                    margin={{
                                        top: 20,
                                        right: 10,
                                        left: -15,
                                        bottom: 5,
                                    }}
                                    barGap={8}
                                >
                                    <CartesianGrid
                                        strokeDasharray="4 4"
                                        vertical={false}
                                    />

                                    <XAxis
                                        dataKey="name"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 11 }}
                                    />

                                    <YAxis
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 11 }}
                                    />

                                    <Tooltip
                                        contentStyle={{
                                            borderRadius: 12,
                                            border: "1px solid #e4e9f2",
                                            boxShadow:
                                                "0 10px 30px rgba(15,23,42,.12)",
                                        }}
                                    />

                                    <Bar
                                        dataKey="planned"
                                        name="Planned %"
                                        radius={[6, 6, 0, 0]}
                                    />

                                    <Bar
                                        dataKey="actual"
                                        name="Actual %"
                                        radius={[6, 6, 0, 0]}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <Empty
                                icon={<BarChart3 size={34} />}
                                text="Import a schedule to see execution analytics."
                            />
                        )}
                    </div>
                </div>

                <div className="panel">
                    <PanelHeader
                        eyebrow="FIELD ACTIVITY"
                        title="Latest site updates"
                    />

                    <div className="feed-list">
                        {data.updates?.length ? (
                            data.updates.slice(0, 6).map((update) => (
                                <div className="feed" key={update.id}>
                                    <div className="feed-icon">
                                        <CheckCircle2 size={16} />
                                    </div>

                                    <div className="feed-content">
                                        <strong>
                                            {update.extracted_description?.slice(
                                                0,
                                                70
                                            ) || "Site progress update"}
                                        </strong>

                                        <span>
                                            {update.progress ?? 0}% actual
                                            {" · "}
                                            {update.progress_gap > 0
                                                ? `${update.progress_gap}% behind`
                                                : "on plan"}
                                        </span>
                                    </div>

                                    <ChevronRight size={15} />
                                </div>
                            ))
                        ) : (
                            <Empty
                                icon={<Radio size={32} />}
                                text="No site updates yet."
                            />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function KpiCard({
    icon,
    title,
    value,
    label,
    danger,
    warning,
}) {
    return (
        <div
            className={`kpi-card ${danger ? "danger-card" : warning ? "warning-card" : ""
                }`}
        >
            <div className="kpi-top">
                <div className="kpi-icon">{icon}</div>
                <span>{title}</span>
            </div>

            <strong>{value}</strong>
            <small>{label}</small>
        </div>
    );
}

function PanelHeader({ eyebrow, title }) {
    return (
        <div className="panel-header">
            <div>
                <span>{eyebrow}</span>
                <h3>{title}</h3>
            </div>
        </div>
    );
}

/* =========================================================
   PROJECTS
========================================================= */

function Projects() {
    const [items, setItems] = useState([]);
    const [name, setName] = useState("");
    const [location, setLocation] = useState("");
    const [busy, setBusy] = useState(false);

    const load = () =>
        api("/api/projects")
            .then(setItems)
            .catch(() => { });

    useEffect(() => {
        load();
    }, []);

    async function add() {
        if (!name.trim()) return;

        setBusy(true);

        try {
            await api("/api/projects", {
                method: "POST",
                body: JSON.stringify({
                    name,
                    location,
                    description: "KaryaSetu live project",
                }),
            });

            setName("");
            setLocation("");

            load();
        } catch (e) {
            alert(e.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="page-stack">
            <div className="page-intro">
                <div>
                    <span>PROJECT PORTFOLIO</span>
                    <h1>Manage your projects</h1>
                    <p>
                        Create projects and connect their schedules to live
                        site execution.
                    </p>
                </div>

                <div className="intro-icon">
                    <FolderKanban size={30} />
                </div>
            </div>

            <div className="projects-layout">
                <div className="panel create-project">
                    <PanelHeader
                        eyebrow="NEW PROJECT"
                        title="Create project"
                    />

                    <div className="form-grid">
                        <label>
                            Project name
                            <input
                                placeholder="e.g. Hyderabad Metro Phase 2"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />
                        </label>

                        <label>
                            Location
                            <input
                                placeholder="e.g. Hyderabad, Telangana"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                            />
                        </label>
                    </div>

                    <button
                        className="primary-btn"
                        onClick={add}
                        disabled={busy}
                    >
                        {busy ? (
                            <>
                                <span className="spinner" />
                                Creating...
                            </>
                        ) : (
                            <>
                                <Plus size={17} />
                                Create project
                            </>
                        )}
                    </button>
                </div>

                <div className="panel">
                    <PanelHeader
                        eyebrow="YOUR PROJECTS"
                        title="Project portfolio"
                    />

                    {items.length ? (
                        <div className="project-list">
                            {items.map((project) => (
                                <div className="project-card" key={project.id}>
                                    <div className="project-symbol">
                                        <FolderKanban size={19} />
                                    </div>

                                    <div className="project-main">
                                        <strong>{project.name}</strong>

                                        <div className="project-meta">
                                            <span>
                                                <MapPin size={12} />
                                                {project.location || "Location not set"}
                                            </span>

                                            <span>
                                                <Activity size={12} />
                                                {project.activity_count || 0} activities
                                            </span>
                                        </div>
                                    </div>

                                    <div className="project-progress">
                                        <strong>
                                            {project.overall_progress || 0}%
                                        </strong>

                                        <div className="progress-track">
                                            <i
                                                style={{
                                                    width: `${Math.min(
                                                        100,
                                                        project.overall_progress || 0
                                                    )}%`,
                                                }}
                                            />
                                        </div>

                                        <small>Overall progress</small>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty
                            icon={<FolderKanban size={34} />}
                            text="No projects found. Create your first project."
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

/* =========================================================
   UNIFIED UPDATE CENTER
========================================================= */

function UpdateCenter() {
    const [tab, setTab] = useState("voice");

    return (
        <div className="page-stack">
            <div className="update-hero">
                <div>
                    <div className="live-label">
                        <span className="pulse" />
                        REAL-TIME FIELD INPUT
                    </div>

                    <h1>
                        Update your project
                        <br />
                        <span>the way work actually happens.</span>
                    </h1>

                    <p>
                        Speak from the field, type an update manually, or
                        import your project schedule. KaryaSetu turns every
                        input into structured project intelligence.
                    </p>
                </div>

                <div className="update-hero-icon">
                    <Radio size={44} />
                </div>
            </div>

            <div className="update-tabs">
                <button
                    className={tab === "voice" ? "active" : ""}
                    onClick={() => setTab("voice")}
                >
                    <Mic size={18} />
                    <div>
                        <strong>Voice Update</strong>
                        <span>Speak naturally</span>
                    </div>

                    <span className="recommended">FASTEST</span>
                </button>

                <button
                    className={tab === "manual" ? "active" : ""}
                    onClick={() => setTab("manual")}
                >
                    <PencilLine size={18} />
                    <div>
                        <strong>Manual Update</strong>
                        <span>Type an update</span>
                    </div>
                </button>

                <button
                    className={tab === "excel" ? "active" : ""}
                    onClick={() => setTab("excel")}
                >
                    <FileSpreadsheet size={18} />
                    <div>
                        <strong>Excel Schedule</strong>
                        <span>Import project plan</span>
                    </div>
                </button>
            </div>

            {tab === "voice" && <VoiceUpdate />}
            {tab === "manual" && <ManualUpdate />}
            {tab === "excel" && <ExcelUpdate />}
        </div>
    );
}

/* =========================================================
   VOICE UPDATE
========================================================= */

function VoiceUpdate() {
    const [projects, setProjects] = useState([]);
    const [projectId, setProjectId] = useState("");
    const [text, setText] = useState("");
    const [result, setResult] = useState(null);

    const [busy, setBusy] = useState(false);
    const [listening, setListening] = useState(false);

    const [language, setLanguage] = useState("en-IN");
    const [error, setError] = useState("");

    const recognitionRef = useRef(null);
    const finalTextRef = useRef("");

    useEffect(() => {
        api("/api/projects")
            .then((data) => {
                setProjects(data);

                if (data[0]) {
                    setProjectId(data[0].id);
                }
            })
            .catch((e) => setError(e.message));
    }, []);

    async function processUpdate(transcript) {
        if (!transcript.trim() || !projectId) return;

        setBusy(true);
        setError("");

        try {
            const response = await api("/api/updates", {
                method: "POST",
                body: JSON.stringify({
                    project_id: projectId,
                    transcript,
                    language,
                }),
            });

            setResult(response);
        } catch (e) {
            setError(e.message);
        } finally {
            setBusy(false);
        }
    }

    function startVoice() {
        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            setError(
                "Speech recognition is unavailable. Please use Google Chrome or Microsoft Edge."
            );
            return;
        }

        setText("");
        setResult(null);
        setError("");

        finalTextRef.current = "";

        const recognition = new SpeechRecognition();

        recognition.lang = language;
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onstart = () => {
            setListening(true);
        };

        recognition.onresult = (event) => {
            let finalTranscript = "";
            let interimTranscript = "";

            for (
                let i = event.resultIndex;
                i < event.results.length;
                i++
            ) {
                const transcript =
                    event.results[i][0].transcript;

                if (event.results[i].isFinal) {
                    finalTranscript += transcript + " ";
                } else {
                    interimTranscript += transcript;
                }
            }

            if (finalTranscript) {
                finalTextRef.current += finalTranscript;
            }

            setText(
                `${finalTextRef.current}${interimTranscript}`.trim()
            );
        };

        recognition.onerror = (event) => {
            setListening(false);

            if (event.error !== "no-speech") {
                setError(`Speech recognition: ${event.error}`);
            }
        };

        recognition.onend = async () => {
            setListening(false);

            const finalText = finalTextRef.current.trim();

            if (finalText) {
                setText(finalText);

                // AUTOMATIC AI PROCESSING
                await processUpdate(finalText);
            }
        };

        recognitionRef.current = recognition;

        recognition.start();
    }

    function stopVoice() {
        recognitionRef.current?.stop();
        setListening(false);
    }

    return (
        <div className="update-workspace">
            <div className="panel voice-panel">
                <div className="voice-panel-heading">
                    <div>
                        <span>AI VOICE ASSISTANT</span>
                        <h2>Tell KaryaSetu what happened on site.</h2>
                        <p>
                            Speak naturally. When you stop recording, KaryaSetu
                            automatically converts your speech into a project
                            update and sends it to the AI engine.
                        </p>
                    </div>

                    <div className="voice-status">
                        <span className="status-dot" />
                        AI Ready
                    </div>
                </div>

                <div className="voice-form">
                    <label>
                        Project
                        <select
                            value={projectId}
                            onChange={(e) => setProjectId(e.target.value)}
                        >
                            {projects.map((project) => (
                                <option key={project.id} value={project.id}>
                                    {project.name}
                                </option>
                            ))}
                        </select>
                    </label>

                    <label>
                        Language
                        <select
                            value={language}
                            onChange={(e) => setLanguage(e.target.value)}
                        >
                            <option value="en-IN">English · India</option>
                            <option value="hi-IN">Hindi · India</option>
                            <option value="te-IN">Telugu · India</option>
                        </select>
                    </label>
                </div>

                <div
                    className={`voice-recorder ${listening ? "recording" : ""
                        } ${busy ? "processing" : ""}`}
                >
                    <div className="voice-rings">
                        <div className="record-ring ring-one" />
                        <div className="record-ring ring-two" />

                        <button
                            className="record-button"
                            onClick={
                                listening ? stopVoice : startVoice
                            }
                            disabled={busy}
                        >
                            {busy ? (
                                <BrainCircuit size={32} />
                            ) : listening ? (
                                <span className="stop-square" />
                            ) : (
                                <Mic size={32} />
                            )}
                        </button>
                    </div>

                    <div className="recorder-text">
                        {busy ? (
                            <>
                                <strong>AI is understanding your update...</strong>
                                <span>
                                    Extracting progress, matching schedule and
                                    checking for risks.
                                </span>
                            </>
                        ) : listening ? (
                            <>
                                <strong>Listening to your site update</strong>
                                <span>
                                    Speak naturally. Press stop when you are done.
                                </span>
                            </>
                        ) : (
                            <>
                                <strong>Press to start recording</strong>
                                <span>
                                    Your voice will be automatically processed
                                    when recording ends.
                                </span>
                            </>
                        )}
                    </div>

                    {listening && (
                        <div className="sound-bars">
                            {Array.from({ length: 18 }).map((_, index) => (
                                <i key={index} />
                            ))}
                        </div>
                    )}
                </div>

                <div className="transcript-area">
                    <div className="transcript-header">
                        <div>
                            <span>LIVE TRANSCRIPT</span>
                            <strong>
                                {text ? "Captured site update" : "Waiting for voice..."}
                            </strong>
                        </div>

                        {text && (
                            <button
                                className="clear-btn"
                                onClick={() => {
                                    setText("");
                                    finalTextRef.current = "";
                                }}
                            >
                                Clear
                            </button>
                        )}
                    </div>

                    <textarea
                        value={text}
                        onChange={(e) => {
                            setText(e.target.value);
                            finalTextRef.current = e.target.value;
                        }}
                        placeholder="Your spoken update will appear here..."
                        rows="7"
                    />

                    <button
                        className="primary-btn full-btn"
                        disabled={
                            busy ||
                            !projectId ||
                            !text.trim()
                        }
                        onClick={() => processUpdate(text)}
                    >
                        <Sparkles size={17} />
                        Analyze this update
                    </button>
                </div>

                {error && <div className="error">{error}</div>}
            </div>

            <div className="panel result-panel">
                <PanelHeader
                    eyebrow="AI INTELLIGENCE"
                    title="Execution result"
                />

                {result ? (
                    <Result result={result} />
                ) : (
                    <div className="result-empty">
                        <div className="empty-ai-orb">
                            <BrainCircuit size={35} />
                        </div>

                        <strong>Waiting for a site update</strong>

                        <p>
                            Your AI analysis will appear here after you record
                            or submit an update.
                        </p>

                        <div className="result-flow">
                            <FlowStep icon={<Mic size={14} />} text="Voice" />
                            <ChevronRight size={14} />
                            <FlowStep
                                icon={<BrainCircuit size={14} />}
                                text="AI"
                            />
                            <ChevronRight size={14} />
                            <FlowStep
                                icon={<Target size={14} />}
                                text="Match"
                            />
                            <ChevronRight size={14} />
                            <FlowStep
                                icon={<Activity size={14} />}
                                text="Update"
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

/* =========================================================
   MANUAL UPDATE
========================================================= */

function ManualUpdate() {
    const [projects, setProjects] = useState([]);
    const [projectId, setProjectId] = useState("");
    const [text, setText] = useState("");
    const [language, setLanguage] = useState("en-IN");
    const [busy, setBusy] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
        api("/api/projects")
            .then((data) => {
                setProjects(data);

                if (data[0]) {
                    setProjectId(data[0].id);
                }
            })
            .catch((e) => setError(e.message));
    }, []);

    async function submit() {
        if (!text.trim() || !projectId) return;

        setBusy(true);
        setError("");

        try {
            const response = await api("/api/updates", {
                method: "POST",
                body: JSON.stringify({
                    project_id: projectId,
                    transcript: text,
                    language,
                }),
            });

            setResult(response);
        } catch (e) {
            setError(e.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="manual-layout">
            <div className="panel manual-panel">
                <div className="manual-icon">
                    <PencilLine size={25} />
                </div>

                <span className="eyebrow">MANUAL FIELD UPDATE</span>

                <h2>Describe what happened.</h2>

                <p className="panel-description">
                    Type a natural-language site update. You don't need to
                    fill individual fields. KaryaSetu's AI will extract the
                    relevant information automatically.
                </p>

                <label>
                    Project
                    <select
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                    >
                        {projects.map((project) => (
                            <option key={project.id} value={project.id}>
                                {project.name}
                            </option>
                        ))}
                    </select>
                </label>

                <label>
                    Update language
                    <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                    >
                        <option value="en-IN">English</option>
                        <option value="hi-IN">Hindi</option>
                        <option value="te-IN">Telugu</option>
                    </select>
                </label>

                <textarea
                    className="manual-textarea"
                    rows="12"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Example:

Foundation excavation is 70 percent complete. Heavy rain caused a two-day delay. The team expects to recover one day by increasing manpower tomorrow."
                />

                <button
                    className="primary-btn full-btn"
                    disabled={
                        busy ||
                        !projectId ||
                        !text.trim()
                    }
                    onClick={submit}
                >
                    {busy ? (
                        <>
                            <span className="spinner" />
                            AI is analyzing...
                        </>
                    ) : (
                        <>
                            <Sparkles size={17} />
                            Analyze & update project
                        </>
                    )}
                </button>

                {error && <div className="error">{error}</div>}
            </div>

            <div className="panel">
                <PanelHeader
                    eyebrow="AI RESULT"
                    title="Execution intelligence"
                />

                {result ? (
                    <Result result={result} />
                ) : (
                    <div className="result-empty compact">
                        <PencilLine size={32} />

                        <strong>No update processed yet</strong>

                        <p>
                            Write a site update and KaryaSetu will identify the
                            activity, progress, delay and risk automatically.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

/* =========================================================
   EXCEL
========================================================= */

function ExcelUpdate() {
    const [projects, setProjects] = useState([]);
    const [projectId, setProjectId] = useState("");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    useEffect(() => {
        api("/api/projects")
            .then((data) => {
                setProjects(data);

                if (data[0]) {
                    setProjectId(data[0].id);
                }
            })
            .catch((e) => setError(e.message));
    }, []);

    async function importFile(event) {
        const file = event.target.files[0];

        if (!file || !projectId) return;

        setBusy(true);
        setMessage("");
        setError("");

        const formData = new FormData();

        formData.append("file", file);

        try {
            const result = await api(
                `/api/import/schedule?project_id=${projectId}`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            setMessage(
                `Successfully imported ${result.imported || 0} activities.`
            );
        } catch (e) {
            setError(e.message);
        } finally {
            setBusy(false);
            event.target.value = "";
        }
    }

    return (
        <div className="excel-layout">
            <div className="panel excel-main">
                <div className="excel-icon">
                    <FileSpreadsheet size={30} />
                </div>

                <span className="eyebrow">SCHEDULE INGESTION</span>

                <h2>Bring your project schedule into KaryaSetu.</h2>

                <p>
                    Upload your Excel or CSV schedule. KaryaSetu will create
                    the L5/L6 activity structure that powers intelligent
                    voice and manual progress matching.
                </p>

                <label>
                    Project
                    <select
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                    >
                        {projects.map((project) => (
                            <option key={project.id} value={project.id}>
                                {project.name}
                            </option>
                        ))}
                    </select>
                </label>

                <label className="drop-zone">
                    <input
                        type="file"
                        accept=".xlsx,.xls,.csv"
                        onChange={importFile}
                        disabled={busy}
                    />

                    <div className="drop-icon">
                        {busy ? (
                            <RefreshCw className="spin" size={28} />
                        ) : (
                            <Upload size={28} />
                        )}
                    </div>

                    <strong>
                        {busy
                            ? "Importing schedule..."
                            : "Click to upload your schedule"}
                    </strong>

                    <span>
                        Supports Excel (.xlsx, .xls) and CSV files
                    </span>
                </label>

                {message && (
                    <div className="success">
                        <CheckCircle2 size={17} />
                        {message}
                    </div>
                )}

                {error && <div className="error">{error}</div>}
            </div>

            <div className="panel">
                <PanelHeader
                    eyebrow="WORKFLOW"
                    title="From schedule to intelligence"
                />

                <div className="workflow">
                    <WorkflowStep
                        number="01"
                        icon={<FileSpreadsheet size={18} />}
                        title="Upload schedule"
                        text="Import your Excel or CSV project plan."
                    />

                    <WorkflowStep
                        number="02"
                        icon={<Activity size={18} />}
                        title="Build L5/L6 structure"
                        text="Activities become searchable project entities."
                    />

                    <WorkflowStep
                        number="03"
                        icon={<Mic size={18} />}
                        title="Capture field updates"
                        text="Supervisors speak or type progress."
                    />

                    <WorkflowStep
                        number="04"
                        icon={<BrainCircuit size={18} />}
                        title="AI connects the dots"
                        text="Gemini matches updates to the correct activity."
                    />
                </div>
            </div>
        </div>
    );
}

function WorkflowStep({
    number,
    icon,
    title,
    text,
}) {
    return (
        <div className="workflow-step">
            <div className="workflow-number">{number}</div>

            <div className="workflow-icon">{icon}</div>

            <div>
                <strong>{title}</strong>
                <p>{text}</p>
            </div>
        </div>
    );
}

/* =========================================================
   RESULT
========================================================= */

function Result({ result }) {
    const activity =
        result.matched_activity || result.activity;

    const progress =
        result.update?.progress ??
        result.analysis?.progress ??
        0;

    const planned =
        result.update?.planned_progress ??
        activity?.planned_progress ??
        0;

    const gap =
        result.progress_gap ??
        result.update?.progress_gap ??
        0;

    const delay =
        result.analysis?.delay_days ?? 0;

    const confidence =
        Math.round((result.similarity || 0) * 100);

    return (
        <div className="result">
            <div className="result-success">
                <div>
                    <div className="success-icon">
                        <CheckCircle2 size={19} />
                    </div>

                    <div>
                        <strong>Update processed successfully</strong>
                        <span>
                            AI has updated the project execution status.
                        </span>
                    </div>
                </div>

                <span className="result-status-badge">
                    {result.status || "PROCESSED"}
                </span>
            </div>

            <div className="match-card">
                <div className="match-label">
                    <Target size={14} />
                    AI MATCHED ACTIVITY
                </div>

                <strong>
                    {activity?.activity_code || "L6"} ·{" "}
                    {activity?.activity_name || "Activity identified"}
                </strong>

                <div className="match-confidence">
                    <span>Semantic match confidence</span>

                    <strong>{confidence}%</strong>
                </div>

                <div className="confidence-bar">
                    <i style={{ width: `${confidence}%` }} />
                </div>
            </div>

            <div className="metric-grid">
                <Metric
                    icon={<Activity size={15} />}
                    label="Actual progress"
                    value={`${progress}%`}
                />

                <Metric
                    icon={<Target size={15} />}
                    label="Planned"
                    value={`${planned}%`}
                />

                <Metric
                    icon={<TrendingDown size={15} />}
                    label="Progress gap"
                    value={`${gap}%`}
                    danger={gap > 0}
                />

                <Metric
                    icon={<Clock3 size={15} />}
                    label="Delay"
                    value={`${delay} day(s)`}
                    danger={delay > 0}
                />
            </div>

            <div className="ai-insight">
                <div className="ai-insight-title">
                    <Sparkles size={16} />
                    AI INSIGHT
                </div>

                <div className="insight-block">
                    <span>Detected reason</span>
                    <p>
                        {result.analysis?.delay_reason ||
                            "No delay reason detected."}
                    </p>
                </div>

                <div className="insight-block">
                    <span>Recommended action</span>
                    <p>
                        {result.recommendation ||
                            "Continue monitoring the activity against the planned schedule."}
                    </p>
                </div>
            </div>
        </div>
    );
}

function Metric({
    icon,
    label,
    value,
    danger,
}) {
    return (
        <div className={`metric ${danger ? "metric-danger" : ""}`}>
            <div>
                {icon}
                <span>{label}</span>
            </div>

            <strong>{value}</strong>
        </div>
    );
}

function FlowStep({ icon, text }) {
    return (
        <div className="flow-step">
            {icon}
            <span>{text}</span>
        </div>
    );
}

/* =========================================================
   ACTIVITIES
========================================================= */

function Activities() {
    const [items, setItems] = useState([]);
    const [projects, setProjects] = useState([]);
    const [projectId, setProjectId] = useState("");
    const [level, setLevel] = useState("");

    const load = () =>
        api(
            `/api/activities?${projectId ? `project_id=${projectId}&` : ""}${level ? `level=${level}` : ""
            }`
        ).then(setItems);

    useEffect(() => {
        api("/api/projects")
            .then((data) => {
                setProjects(data);

                if (data[0]) {
                    setProjectId(data[0].id);
                }
            })
            .catch(() => { });
    }, []);

    useEffect(() => {
        load().catch(() => { });
    }, [projectId, level]);

    async function edit(activity) {
        const value = prompt(
            `Actual progress for ${activity.activity_name}`,
            activity.actual_progress
        );

        if (value === null) return;

        const number = Number(value);

        if (
            Number.isNaN(number) ||
            number < 0 ||
            number > 100
        ) {
            alert("Enter a value between 0 and 100.");
            return;
        }

        try {
            await api(`/api/activities/${activity.id}`, {
                method: "PATCH",
                body: JSON.stringify({
                    actual_progress: number,
                }),
            });

            load();
        } catch (e) {
            alert(e.message);
        }
    }

    return (
        <div className="page-stack">
            <div className="page-intro">
                <div>
                    <span>SCHEDULE INTELLIGENCE</span>
                    <h1>L5 / L6 Activities</h1>
                    <p>
                        Monitor actual progress against your project plan.
                    </p>
                </div>

                <div className="intro-icon">
                    <Activity size={30} />
                </div>
            </div>

            <div className="panel activities-panel">
                <div className="activities-toolbar">
                    <div>
                        <span>PROJECT SCHEDULE</span>
                        <h3>Execution activities</h3>
                    </div>

                    <div className="toolbar">
                        <select
                            value={projectId}
                            onChange={(e) => setProjectId(e.target.value)}
                        >
                            {projects.map((project) => (
                                <option key={project.id} value={project.id}>
                                    {project.name}
                                </option>
                            ))}
                        </select>

                        <select
                            value={level}
                            onChange={(e) => setLevel(e.target.value)}
                        >
                            <option value="">All levels</option>
                            <option value="L5">L5</option>
                            <option value="L6">L6</option>
                        </select>
                    </div>
                </div>

                {items.length ? (
                    <div className="activity-table">
                        <div className="activity-table-head">
                            <span>ACTIVITY</span>
                            <span>PROGRESS</span>
                            <span>STATUS</span>
                            <span>ACTION</span>
                        </div>

                        {items.map((activity) => (
                            <div
                                className="activity-row"
                                key={activity.id}
                            >
                                <div className="activity-name">
                                    <span
                                        className={`level-badge ${activity.level}`}
                                    >
                                        {activity.level}
                                    </span>

                                    <div>
                                        <strong>
                                            {activity.activity_code} ·{" "}
                                            {activity.activity_name}
                                        </strong>

                                        <span>
                                            {activity.planned_start || "—"} →{" "}
                                            {activity.planned_end || "—"}
                                        </span>
                                    </div>
                                </div>

                                <div className="activity-progress">
                                    <div className="activity-progress-top">
                                        <strong>
                                            {activity.actual_progress || 0}%
                                        </strong>

                                        <span>
                                            Plan {activity.planned_progress || 0}%
                                        </span>
                                    </div>

                                    <div className="progress-track">
                                        <i
                                            style={{
                                                width: `${Math.min(
                                                    100,
                                                    activity.actual_progress || 0
                                                )}%`,
                                            }}
                                        />
                                    </div>
                                </div>

                                <span
                                    className={`status-pill ${String(
                                        activity.status || ""
                                    )
                                        .replaceAll(" ", "-")
                                        .toLowerCase()}`}
                                >
                                    {activity.status || "On Track"}
                                </span>

                                <button
                                    className="edit-btn"
                                    onClick={() => edit(activity)}
                                >
                                    <PencilLine size={14} />
                                    Edit
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <Empty
                        icon={<Activity size={35} />}
                        text="No activities found. Import your project schedule first."
                    />
                )}
            </div>
        </div>
    );
}

/* =========================================================
   RISKS
========================================================= */

function Risks() {
    const [items, setItems] = useState([]);
    const [recommendations, setRecommendations] =
        useState([]);

    const load = () =>
        Promise.all([
            api("/api/risks"),
            api("/api/recommendations"),
        ]).then(([risks, recs]) => {
            setItems(risks);
            setRecommendations(recs);
        });

    useEffect(() => {
        load().catch(() => { });
    }, []);

    return (
        <div className="page-stack">
            <div className="page-intro">
                <div>
                    <span>PROJECT INTELLIGENCE</span>
                    <h1>Risks & recommendations</h1>
                    <p>
                        AI-generated project risks and corrective actions.
                    </p>
                </div>

                <div className="intro-icon danger">
                    <AlertTriangle size={30} />
                </div>
            </div>

            <div className="risk-layout">
                <div className="panel">
                    <PanelHeader
                        eyebrow="RISK ENGINE"
                        title="Detected risks"
                    />

                    {items.length ? (
                        <div className="risk-list">
                            {items.map((risk) => (
                                <div className="risk-card" key={risk.id}>
                                    <div className="risk-icon">
                                        <AlertTriangle size={18} />
                                    </div>

                                    <div className="risk-content">
                                        <div className="risk-title">
                                            <strong>{risk.title}</strong>

                                            <span
                                                className={`severity ${String(
                                                    risk.severity || ""
                                                ).toLowerCase()}`}
                                            >
                                                {risk.severity}
                                            </span>
                                        </div>

                                        <p>{risk.description}</p>

                                        <small>{risk.source}</small>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty
                            icon={<ShieldCheck size={35} />}
                            text="No project risks detected yet."
                        />
                    )}
                </div>

                <div className="panel">
                    <PanelHeader
                        eyebrow="AI ACTION ENGINE"
                        title="Corrective recommendations"
                    />

                    {recommendations.length ? (
                        <div className="recommend-list">
                            {recommendations.map((recommendation) => (
                                <div
                                    className="recommend-card"
                                    key={recommendation.id}
                                >
                                    <div className="recommend-icon">
                                        <Sparkles size={18} />
                                    </div>

                                    <div>
                                        <strong>
                                            {recommendation.action}
                                        </strong>

                                        <p>
                                            {recommendation.problem}
                                        </p>

                                        <span>
                                            Priority ·{" "}
                                            {recommendation.priority}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty
                            icon={<Sparkles size={35} />}
                            text="Recommendations appear automatically when risks are detected."
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

/* =========================================================
   USERS
========================================================= */

function UsersPage() {
    const [items, setItems] = useState([]);

    useEffect(() => {
        api("/api/users")
            .then(setItems)
            .catch((e) =>
                setItems([
                    {
                        name: e.message,
                        role: "Manager access required",
                    },
                ])
            );
    }, []);

    return (
        <div className="page-stack">
            <div className="page-intro">
                <div>
                    <span>TEAM MANAGEMENT</span>
                    <h1>Project users</h1>
                    <p>
                        Manage users participating in the KaryaSetu workspace.
                    </p>
                </div>

                <div className="intro-icon">
                    <Users size={30} />
                </div>
            </div>

            <div className="panel users-panel">
                <PanelHeader
                    eyebrow="WORKSPACE MEMBERS"
                    title="Users"
                />

                {items.map((user) => (
                    <div className="user-row" key={user.id || user.name}>
                        <div className="user-row-avatar">
                            {(user.name || "U").charAt(0).toUpperCase()}
                        </div>

                        <div className="user-row-info">
                            <strong>{user.name}</strong>
                            <span>{user.email}</span>
                        </div>

                        <span className="role-badge">
                            {user.role}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* =========================================================
   COMMON
========================================================= */

function Loading() {
    return (
        <div className="loading-state">
            <div className="loading-orb">
                <BrainCircuit size={27} />
            </div>

            <strong>Loading KaryaSetu intelligence...</strong>

            <span>Connecting to the project workspace.</span>
        </div>
    );
}

function Empty({ icon, text }) {
    return (
        <div className="empty-state">
            {icon && <div className="empty-icon">{icon}</div>}
            <span>{text}</span>
        </div>
    );
}

function ErrorBox({ message }) {
    return (
        <div className="error-page">
            <AlertTriangle size={28} />
            <strong>Unable to load this workspace</strong>
            <span>{message}</span>
        </div>
    );
}

/* =========================================================
   APP
========================================================= */

function App() {
    const [user, setUser] = useState(null);

    useEffect(() => {
        const raw = localStorage.getItem(
            "karyasetu_user"
        );

        if (raw) {
            try {
                setUser(JSON.parse(raw));
            } catch {
                setUser(null);
            }
        }
    }, []);

    function login(data) {
        localStorage.setItem(
            "karyasetu_user",
            JSON.stringify(data)
        );

        setUser(data);
    }

    function logout() {
        localStorage.removeItem("karyasetu_token");
        localStorage.removeItem("karyasetu_user");

        setUser(null);
    }

    return user ? (
        <Shell user={user} onLogout={logout} />
    ) : (
        <Login onLogin={login} />
    );
}

createRoot(document.getElementById("root")).render(
    <App />
);
