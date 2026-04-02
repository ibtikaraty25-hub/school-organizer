import base64
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
import uuid

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="My School Work Organizer",
    page_icon="📘",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "school_organizer.db"
HERO_IMAGE = BASE_DIR / "teacher_workspace.png"
UPLOADS_DIR = BASE_DIR / "uploaded_files"

SCHOOL_YEARS = ["2025/2026", "2026/2027", "2027/2028"]
SEMESTERS = ["First Semester", "Second Semester"]
ROLES = ["Teacher", "Administrator", "Supervisor", "Other"]

ADMIN_PASSWORD = "hana123"  # Change this password


def ensure_uploads_dir():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def image_to_base64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def save_uploaded_file(uploaded_file, subfolder: str) -> str:
    if uploaded_file is None:
        return ""
    ensure_uploads_dir()
    section_dir = UPLOADS_DIR / subfolder
    section_dir.mkdir(parents=True, exist_ok=True)
    safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
    final_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    final_path = section_dir / final_name
    final_path.write_bytes(uploaded_file.getbuffer())
    return str(final_path.relative_to(BASE_DIR))


def save_multiple_uploaded_files(uploaded_files, subfolder: str) -> str:
    if not uploaded_files:
        return ""
    paths = []
    for uploaded_file in uploaded_files:
        saved_path = save_uploaded_file(uploaded_file, subfolder)
        if saved_path:
            paths.append(saved_path)
    return " | ".join(paths)


def stars_text(value: int) -> str:
    value = max(1, min(5, int(value)))
    return "⭐" * value



def is_admin():
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Admin Access")
        if st.session_state.is_admin:
            st.success("Admin mode is active.")
            if st.button("Log out from Admin", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
        else:
            password = st.text_input("Admin Password", type="password")
            if password:
                if password == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.success("Admin mode activated.")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    return st.session_state.is_admin

def apply_custom_style():
    hero_bg = image_to_base64(HERO_IMAGE)
    hero_css = ""
    if hero_bg:
        hero_css = f"""
        .hero-box {{
            background-image:
                linear-gradient(90deg, rgba(15,23,42,0.95) 0%, rgba(15,23,42,0.84) 40%, rgba(15,23,42,0.38) 68%, rgba(15,23,42,0.12) 100%),
                url("data:image/png;base64,{hero_bg}");
            background-size: cover;
            background-position: center right;
            background-repeat: no-repeat;
        }}
        """

    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            direction: ltr;
            text-align: left;
        }}
        .stApp {{
            background:
                radial-gradient(circle at top right, rgba(84,120,255,0.18), transparent 28%),
                radial-gradient(circle at left bottom, rgba(0,180,216,0.12), transparent 24%),
                linear-gradient(135deg, #0f172a 0%, #111827 45%, #172554 100%);
            color: #f8fafc;
        }}
        div[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(15,23,42,0.98) 0%, rgba(30,41,59,0.96) 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }}
        div[data-testid="stSidebar"] * {{
            direction: ltr;
            text-align: left;
        }}
        .block-container {{
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }}
        .hero-box {{
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 26px;
            padding: 34px 34px 30px 34px;
            margin-bottom: 22px;
            min-height: 320px;
            box-shadow: 0 14px 46px rgba(0,0,0,0.28);
            display: flex;
            align-items: center;
        }}
        {hero_css}
        .hero-content {{
            max-width: 56%;
        }}
        .main-title {{
            font-size: 3rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.2rem;
            letter-spacing: 0.2px;
            color: #ffffff;
        }}
        .sub-title {{
            font-size: 1.05rem;
            color: #dbeafe;
            margin-bottom: 0.9rem;
            font-weight: 600;
        }}
        .hero-text {{
            font-size: 1.05rem;
            line-height: 1.9;
            color: #e2e8f0;
            margin-top: 0.7rem;
            max-width: 620px;
        }}
        .welcome-card {{
            background: rgba(255,255,255,0.94);
            color: #0f172a;
            border-radius: 24px;
            padding: 24px 26px;
            margin-top: 1rem;
            max-width: 760px;
            border: 1px solid rgba(15,23,42,0.06);
            box-shadow: 0 8px 24px rgba(15,23,42,0.14);
        }}
        .welcome-title {{
            font-size: 1.55rem;
            font-weight: 800;
            margin-bottom: 0.4rem;
            color: #0f172a;
        }}
        .welcome-text {{
            font-size: 1rem;
            line-height: 1.8;
            color: #334155;
        }}
        .section-card {{
            background: rgba(15,23,42,0.72);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 22px;
            padding: 18px 18px 10px 18px;
            margin-bottom: 18px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        }}
        .mini-card {{
            background: linear-gradient(135deg, rgba(30,41,59,0.95), rgba(51,65,85,0.85));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 18px;
            min-height: 140px;
            margin-bottom: 14px;
        }}
        .mini-card-title {{
            font-size: 1.08rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}
        .mini-card-text {{
            font-size: 0.95rem;
            line-height: 1.7;
            color: #dbeafe;
        }}
        .section-title {{
            font-size: 1.3rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 0.8rem;
        }}
        .info-strip {{
            background: rgba(59,130,246,0.16);
            border: 1px solid rgba(147,197,253,0.22);
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 12px;
            color: #dbeafe;
            font-size: 0.96rem;
        }}
        .feedback-card {{
            background: rgba(255,255,255,0.95);
            color: #0f172a;
            border-radius: 18px;
            padding: 16px 18px;
            margin-bottom: 14px;
            border: 1px solid rgba(15,23,42,0.08);
            box-shadow: 0 6px 18px rgba(0,0,0,0.10);
        }}
        .feedback-head {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
            font-weight: 700;
        }}
        .feedback-role {{
            color: #475569;
            font-size: 0.92rem;
        }}
        .feedback-text {{
            color: #1e293b;
            line-height: 1.8;
            font-size: 0.97rem;
        }}
        div[data-testid="metric-container"] {{
            background: rgba(15,23,42,0.78);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 18px;
            padding: 12px;
        }}
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stDateInput input,
        .stSelectbox div[data-baseweb="select"],
        .stRadio > div,
        .stDataFrame {{
            border-radius: 12px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_conn()) as conn:
        cursor = conn.cursor()
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS demo_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_name TEXT NOT NULL,
                implementation_date TEXT,
                class_name TEXT,
                attachment TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS supervisory_visits_en (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_name TEXT NOT NULL,
                visit_date TEXT,
                class_name TEXT,
                attachment TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS professional_development (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                implementing_teacher TEXT NOT NULL,
                title TEXT,
                activity_date TEXT,
                attachment TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS peer_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visiting_teacher TEXT NOT NULL,
                visited_teacher TEXT NOT NULL,
                visit_date TEXT,
                notes TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS educational_initiatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                initiative_title TEXT NOT NULL,
                time_period TEXT,
                results TEXT,
                attachments TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS plc_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_title TEXT NOT NULL,
                time_period TEXT,
                recommendations TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS files_archive_en (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                category TEXT,
                file_path TEXT,
                notes TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS weekly_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_item TEXT NOT NULL,
                notes TEXT,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS general_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_name TEXT NOT NULL,
                visitor_role TEXT,
                comment_text TEXT NOT NULL,
                rating INTEGER NOT NULL,
                school_year TEXT,
                semester TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ]
        for sql in tables_sql:
            cursor.execute(sql)
        conn.commit()


def run_query(query, params=()):
    with closing(get_conn()) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()


def fetch_df(query, params=()):
    with closing(get_conn()) as conn:
        return pd.read_sql_query(query, conn, params=params)


def render_hero():
    st.markdown(
        """
        <div class="hero-box">
            <div class="hero-content">
                <div class="main-title">My School Work Organizer</div>
                <div class="sub-title">Senior Teacher : Hana Al-Kindi</div>
                <div class="hero-text">
                    A well-organized teacher leads with clarity, teaches with purpose, and supports others with confidence.
                    This platform helps you document, plan, guide, and follow up your professional school work in one formal place.
                </div>
                <div class="welcome-card">
                    <div class="welcome-title">Welcome, Teacher 🌟</div>
                    <div class="welcome-text">
                        Your daily effort shapes classrooms, supports teachers, and builds stronger learning environments.
                        Record your work clearly, manage your files confidently, and keep every professional step in one organized system.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_shell(title, note=None):
    render_hero()
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="info-strip">{note}</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)


def close_page_shell():
    st.markdown("</div>", unsafe_allow_html=True)


def sidebar_navigation():
    st.sidebar.title("Navigation")
    school_year = st.sidebar.selectbox("School Year", SCHOOL_YEARS, index=0)
    semester = st.sidebar.selectbox("Semester", SEMESTERS, index=0)
    page = st.sidebar.radio(
        "Sections",
        [
            "Home",
            "Demo Lessons",
            "Supervisory Visits",
            "Professional Development",
            "Peer Visits",
            "Educational Initiatives",
            "Professional Learning Community",
            "Files",
            "Calendar",
            "General Feedback",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Use one academic year and one semester at a time for cleaner records.")
    if st.sidebar.button("Initialize Database", use_container_width=True):
        init_db()
        st.sidebar.success("Database is ready.")
    return school_year, semester, page



def render_admin_notice(admin: bool):
    if admin:
        st.success("Admin mode: data entry is enabled.")
    else:
        st.info("Viewer mode: viewing and general feedback only.")

def home_page(school_year, semester):
    render_hero()
    st.markdown(
        f'<div class="info-strip">Current selection: <b>{school_year}</b> | <b>{semester}</b></div>',
        unsafe_allow_html=True,
    )
    count_demo = fetch_df("SELECT COUNT(*) AS c FROM demo_lessons WHERE school_year = ? AND semester = ?", (school_year, semester)).iloc[0]["c"]
    count_visits = fetch_df("SELECT COUNT(*) AS c FROM supervisory_visits_en WHERE school_year = ? AND semester = ?", (school_year, semester)).iloc[0]["c"]
    count_pd = fetch_df("SELECT COUNT(*) AS c FROM professional_development WHERE school_year = ? AND semester = ?", (school_year, semester)).iloc[0]["c"]
    count_peer = fetch_df("SELECT COUNT(*) AS c FROM peer_visits WHERE school_year = ? AND semester = ?", (school_year, semester)).iloc[0]["c"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Demo Lessons", int(count_demo))
    c2.metric("Supervisory Visits", int(count_visits))
    c3.metric("Professional Development", int(count_pd))
    c4.metric("Peer Visits", int(count_peer))


def page_demo_lessons(school_year, semester, admin):
    render_page_shell("Demo Lessons", "Add implementation records for model or practical lessons.")
    render_admin_notice(admin)
    if admin:
        with st.form("demo_lessons_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                teacher_name = st.text_input("Teacher Name")
                implementation_date = st.date_input("Implementation Date", value=date.today())
            with c2:
                class_name = st.text_input("Class")
                uploaded_attachment = st.file_uploader("Attachment", type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "doc", "docx", "ppt", "pptx", "pdf"], key="demo_attachment")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not teacher_name.strip():
                    st.error("Teacher Name is required.")
                else:
                    attachment_path = save_uploaded_file(uploaded_attachment, "demo_lessons")
                    run_query(
                        "INSERT INTO demo_lessons (teacher_name, implementation_date, class_name, attachment, school_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (teacher_name.strip(), implementation_date.isoformat(), class_name.strip(), attachment_path, school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT teacher_name AS 'Teacher Name', implementation_date AS 'Implementation Date', class_name AS 'Class', attachment AS 'Attachment' FROM demo_lessons WHERE school_year = ? AND semester = ? ORDER BY implementation_date DESC, id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_supervisory_visits(school_year, semester, admin):
    render_page_shell("Supervisory Visits", "Document classroom visits, class details, and attached evidence.")
    render_admin_notice(admin)
    if admin:
        with st.form("supervisory_visits_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                teacher_name = st.text_input("Teacher Name")
                visit_date = st.date_input("Date", value=date.today())
            with c2:
                class_name = st.text_input("Class")
                uploaded_attachment = st.file_uploader("Attachment", type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "doc", "docx", "ppt", "pptx", "pdf"], key="visit_attachment")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not teacher_name.strip():
                    st.error("Teacher Name is required.")
                else:
                    attachment_path = save_uploaded_file(uploaded_attachment, "supervisory_visits")
                    run_query(
                        "INSERT INTO supervisory_visits_en (teacher_name, visit_date, class_name, attachment, school_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (teacher_name.strip(), visit_date.isoformat(), class_name.strip(), attachment_path, school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT teacher_name AS 'Teacher Name', visit_date AS 'Date', class_name AS 'Class', attachment AS 'Attachment' FROM supervisory_visits_en WHERE school_year = ? AND semester = ? ORDER BY visit_date DESC, id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_professional_development(school_year, semester, admin):
    render_page_shell("Professional Development", "Track workshops, sessions, and teacher-led development activities.")
    render_admin_notice(admin)
    if admin:
        with st.form("professional_development_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                implementing_teacher = st.text_input("Implementing Teacher")
                title = st.text_input("Title")
            with c2:
                activity_date = st.date_input("Date", value=date.today())
                uploaded_attachment = st.file_uploader("Attachment", type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "doc", "docx", "ppt", "pptx", "pdf"], key="pd_attachment")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not implementing_teacher.strip():
                    st.error("Implementing Teacher is required.")
                else:
                    attachment_path = save_uploaded_file(uploaded_attachment, "professional_development")
                    run_query(
                        "INSERT INTO professional_development (implementing_teacher, title, activity_date, attachment, school_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (implementing_teacher.strip(), title.strip(), activity_date.isoformat(), attachment_path, school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT implementing_teacher AS 'Implementing Teacher', title AS 'Title', activity_date AS 'Date', attachment AS 'Attachment' FROM professional_development WHERE school_year = ? AND semester = ? ORDER BY activity_date DESC, id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_peer_visits(school_year, semester, admin):
    render_page_shell("Peer Visits", "Record exchange visits between teachers and keep brief notes for follow-up.")
    render_admin_notice(admin)
    if admin:
        with st.form("peer_visits_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                visiting_teacher = st.text_input("Visiting Teacher Name")
                visited_teacher = st.text_input("Visited Teacher Name")
            with c2:
                visit_date = st.date_input("Date", value=date.today())
                notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not visiting_teacher.strip() or not visited_teacher.strip():
                    st.error("Both teacher names are required.")
                else:
                    run_query(
                        "INSERT INTO peer_visits (visiting_teacher, visited_teacher, visit_date, notes, school_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (visiting_teacher.strip(), visited_teacher.strip(), visit_date.isoformat(), notes.strip(), school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT visiting_teacher AS 'Visiting Teacher', visited_teacher AS 'Visited Teacher', visit_date AS 'Date', notes AS 'Notes' FROM peer_visits WHERE school_year = ? AND semester = ? ORDER BY visit_date DESC, id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_educational_initiatives(school_year, semester, admin):
    render_page_shell("Educational Initiatives", "Keep a concise record of initiative titles, periods, results, and attachments.")
    render_admin_notice(admin)
    if admin:
        with st.form("educational_initiatives_form", clear_on_submit=True):
            initiative_title = st.text_input("Initiative Title")
            time_period = st.text_input("Time Period")
            results = st.text_area("Results")
            uploaded_attachments = st.file_uploader("Attachments", type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "doc", "docx", "ppt", "pptx", "pdf"], accept_multiple_files=True, key="initiative_attachments")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not initiative_title.strip():
                    st.error("Initiative Title is required.")
                else:
                    attachments_path = save_multiple_uploaded_files(uploaded_attachments, "educational_initiatives")
                    run_query(
                        "INSERT INTO educational_initiatives (initiative_title, time_period, results, attachments, school_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (initiative_title.strip(), time_period.strip(), results.strip(), attachments_path, school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT initiative_title AS 'Initiative Title', time_period AS 'Time Period', results AS 'Results', attachments AS 'Attachments' FROM educational_initiatives WHERE school_year = ? AND semester = ? ORDER BY id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_plc(school_year, semester, admin):
    render_page_shell("Professional Learning Community", "Store PLC titles, time periods, and core recommendations in one place.")
    render_admin_notice(admin)
    if admin:
        with st.form("plc_form", clear_on_submit=True):
            course_title = st.text_input("Course Title")
            time_period = st.text_input("Time Period")
            recommendations = st.text_area("Recommendations")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not course_title.strip():
                    st.error("Course Title is required.")
                else:
                    run_query(
                        "INSERT INTO plc_records (course_title, time_period, recommendations, school_year, semester) VALUES (?, ?, ?, ?, ?)",
                        (course_title.strip(), time_period.strip(), recommendations.strip(), school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT course_title AS 'Course Title', time_period AS 'Time Period', recommendations AS 'Recommendations' FROM plc_records WHERE school_year = ? AND semester = ? ORDER BY id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_files(school_year, semester, admin):
    render_page_shell("Files", "Upload and organize images, videos, Word files, PowerPoint files, PDFs, and more.")
    render_admin_notice(admin)
    if admin:
        with st.form("files_form", clear_on_submit=True):
            file_name = st.text_input("File Name")
            category = st.text_input("Category")
            uploaded_file = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "doc", "docx", "ppt", "pptx", "pdf", "xlsx", "xls", "txt"], key="files_section_upload")
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not file_name.strip():
                    st.error("File Name is required.")
                else:
                    file_path = save_uploaded_file(uploaded_file, "general_files")
                    run_query(
                        "INSERT INTO files_archive_en (file_name, category, file_path, notes, school_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (file_name.strip(), category.strip(), file_path, notes.strip(), school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT file_name AS 'File Name', category AS 'Category', file_path AS 'File Path', notes AS 'Notes' FROM files_archive_en WHERE school_year = ? AND semester = ? ORDER BY id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_calendar(school_year, semester, admin):
    render_page_shell("Calendar", "Use this section to note what will be implemented during the current week.")
    render_admin_notice(admin)
    if admin:
        with st.form("calendar_form", clear_on_submit=True):
            week_item = st.text_input("What will be implemented this week?")
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save")
            if submitted:
                if not week_item.strip():
                    st.error("This field is required.")
                else:
                    run_query(
                        "INSERT INTO weekly_calendar (week_item, notes, school_year, semester) VALUES (?, ?, ?, ?)",
                        (week_item.strip(), notes.strip(), school_year, semester),
                    )
                    st.success("Record saved.")

    df = fetch_df(
        "SELECT week_item AS 'This Week Plan', notes AS 'Notes' FROM weekly_calendar WHERE school_year = ? AND semester = ? ORDER BY id DESC",
        (school_year, semester),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    close_page_shell()

def page_general_feedback(school_year, semester):
    init_db()
    render_page_shell("General Feedback", "Visitors can add one general comment and a star rating here. This feedback is not linked to individual records.")
    feedback_df = fetch_df("SELECT visitor_name, visitor_role, comment_text, rating, created_at FROM general_feedback WHERE school_year = ? AND semester = ? ORDER BY id DESC", (school_year, semester))
    if feedback_df.empty:
        st.info("No feedback has been added yet.")
    else:
        st.markdown("### Visitor Feedback")
        for _, row in feedback_df.iterrows():
            created_text = str(row["created_at"]) if row["created_at"] else ""
            st.markdown(
                f"""
                <div class="feedback-card">
                    <div class="feedback-head">
                        <div>
                            <div>{row["visitor_name"]}</div>
                            <div class="feedback-role">{row["visitor_role"]} | {created_text}</div>
                        </div>
                        <div>{stars_text(int(row["rating"]))}</div>
                    </div>
                    <div class="feedback-text">{row["comment_text"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("### Add General Feedback")
    with st.form("general_feedback_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            visitor_name = st.text_input("Name")
        with col2:
            visitor_role = st.selectbox("Role", ROLES)
        comment_text = st.text_area("Comment")
        rating = st.select_slider("Star Rating", options=[1, 2, 3, 4, 5], value=5, format_func=lambda x: "⭐" * x)
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            if not visitor_name.strip():
                st.error("Name is required.")
            elif not comment_text.strip():
                st.error("Comment is required.")
            else:
                run_query(
                    "INSERT INTO general_feedback (visitor_name, visitor_role, comment_text, rating, school_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                    (visitor_name.strip(), visitor_role, comment_text.strip(), int(rating), school_year, semester),
                )
                st.success("Thank you. Your feedback has been submitted.")
    close_page_shell()


def main():
    ensure_uploads_dir()
    apply_custom_style()
    init_db()
    school_year, semester, page = sidebar_navigation()
    admin = is_admin()
    if page == "Home":
        home_page(school_year, semester)
    elif page == "Demo Lessons":
        page_demo_lessons(school_year, semester, admin)
    elif page == "Supervisory Visits":
        page_supervisory_visits(school_year, semester, admin)
    elif page == "Professional Development":
        page_professional_development(school_year, semester, admin)
    elif page == "Peer Visits":
        page_peer_visits(school_year, semester, admin)
    elif page == "Educational Initiatives":
        page_educational_initiatives(school_year, semester, admin)
    elif page == "Professional Learning Community":
        page_plc(school_year, semester, admin)
    elif page == "Files":
        page_files(school_year, semester, admin)
    elif page == "Calendar":
        page_calendar(school_year, semester, admin)
    elif page == "General Feedback":
        page_general_feedback(school_year, semester)


if __name__ == "__main__":
    main()
