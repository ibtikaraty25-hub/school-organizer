
import base64
import sqlite3
import uuid
from contextlib import closing
from datetime import date
from pathlib import Path

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
ROLES = ["Teacher", "Administrator", "Supervisor", "Other"]

ADMIN_PASSWORD = "hana123"  # change this


# ---------- utilities ----------
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
    saved = []
    for f in uploaded_files:
        p = save_uploaded_file(f, subfolder)
        if p:
            saved.append(p)
    return " | ".join(saved)


def stars_text(value: int) -> str:
    value = max(1, min(5, int(value)))
    return "⭐" * value


# ---------- style ----------
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


# ---------- db ----------
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


# ---------- auth ----------
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


# ---------- layout ----------
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


def render_admin_notice(admin: bool):
    if admin:
        st.success("Admin mode: add and edit are enabled.")
    else:
        st.info("Viewer mode: viewing and general feedback only.")


def sidebar_navigation():
    st.sidebar.title("Navigation")
    school_year = st.sidebar.selectbox("School Year", SCHOOL_YEARS, index=0)
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
    st.sidebar.caption("Use one academic year at a time for cleaner records.")
    if st.sidebar.button("Initialize Database", use_container_width=True):
        init_db()
        st.sidebar.success("Database is ready.")
    return school_year, page


# ---------- generic admin add/edit ----------
def add_and_edit_simple(
    *,
    page_title: str,
    note: str,
    admin: bool,
    table_name: str,
    year: str,
    upload_subfolder: str | None,
    fields: list,
):
    """
    fields example:
    [
      {"name":"teacher_name","label":"Teacher Name","type":"text","required":True},
      {"name":"implementation_date","label":"Implementation Date","type":"date"},
      {"name":"class_name","label":"Class","type":"text"},
      {"name":"attachment","label":"Attachment","type":"file"},
    ]
    """
    render_page_shell(page_title, note)
    render_admin_notice(admin)

    if admin:
        st.markdown("### Add New Record")
        with st.form(f"add_{table_name}", clear_on_submit=True):
            values = {}
            for i in range(0, len(fields), 2):
                cols = st.columns(2) if i + 1 < len(fields) else [st.container()]
                chunk = fields[i : i + 2]
                for col, field in zip(cols, chunk):
                    with col:
                        ftype = field["type"]
                        name = field["name"]
                        label = field["label"]
                        if ftype == "text":
                            values[name] = st.text_input(label)
                        elif ftype == "textarea":
                            values[name] = st.text_area(label)
                        elif ftype == "date":
                            values[name] = st.date_input(label, value=date.today())
                        elif ftype == "file":
                            values[name] = st.file_uploader(
                                label,
                                type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "doc", "docx", "ppt", "pptx", "pdf", "xlsx", "xls", "txt"],
                                accept_multiple_files=field.get("multiple", False),
                                key=f"add_{table_name}_{name}",
                            )
            submitted = st.form_submit_button("Save")
            if submitted:
                for field in fields:
                    if field.get("required"):
                        value = values.get(field["name"])
                        if field["type"] == "text" and not str(value).strip():
                            st.error(f'{field["label"]} is required.')
                            close_page_shell()
                            return
                        if field["type"] == "textarea" and not str(value).strip():
                            st.error(f'{field["label"]} is required.')
                            close_page_shell()
                            return

                db_values = {}
                for field in fields:
                    name = field["name"]
                    val = values.get(name)
                    if field["type"] == "date":
                        db_values[name] = val.isoformat() if val else ""
                    elif field["type"] == "file":
                        if field.get("multiple", False):
                            db_values[name] = save_multiple_uploaded_files(val, upload_subfolder or table_name)
                        else:
                            db_values[name] = save_uploaded_file(val, upload_subfolder or table_name)
                    else:
                        db_values[name] = str(val).strip()

                columns = [f["name"] for f in fields] + ["school_year"]
                placeholders = ", ".join(["?"] * len(columns))
                run_query(
                    f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                    tuple(db_values[c] for c in [f["name"] for f in fields]) + (year,),
                )
                st.success("Record saved.")
                st.rerun()

    select_cols = ["id"] + [f["name"] for f in fields]
    df = fetch_df(
        f"SELECT {', '.join(select_cols)} FROM {table_name} WHERE school_year = ? ORDER BY id DESC",
        (year,),
    )

    st.markdown("### Records")
    if df.empty:
        st.info("No records found.")
    else:
        show_df = df.copy()
        rename_map = {f["name"]: f["label"] for f in fields}
        show_df = show_df.rename(columns=rename_map)
        st.dataframe(show_df, use_container_width=True, hide_index=True)

    if admin and not df.empty:
        st.markdown("### Edit Existing Record")
        options = {f"ID {row['id']}": int(row["id"]) for _, row in df.iterrows()}
        selected_label = st.selectbox("Select record to edit", list(options.keys()))
        selected_id = options[selected_label]
        row = df[df["id"] == selected_id].iloc[0]

        with st.form(f"edit_{table_name}"):
            edit_values = {}
            for i in range(0, len(fields), 2):
                cols = st.columns(2) if i + 1 < len(fields) else [st.container()]
                chunk = fields[i : i + 2]
                for col, field in zip(cols, chunk):
                    with col:
                        name = field["name"]
                        label = field["label"]
                        ftype = field["type"]
                        current = row[name]
                        if ftype == "text":
                            edit_values[name] = st.text_input(label, value="" if pd.isna(current) else str(current), key=f"edit_{table_name}_{name}_{selected_id}")
                        elif ftype == "textarea":
                            edit_values[name] = st.text_area(label, value="" if pd.isna(current) else str(current), key=f"edit_{table_name}_{name}_{selected_id}")
                        elif ftype == "date":
                            try:
                                current_date = pd.to_datetime(current).date() if current else date.today()
                            except Exception:
                                current_date = date.today()
                            edit_values[name] = st.date_input(label, value=current_date, key=f"edit_{table_name}_{name}_{selected_id}")
                        elif ftype == "file":
                            st.caption(f"Current file(s): {current if current else 'No file'}")
                            edit_values[name] = st.file_uploader(
                                f"Replace {label} (optional)",
                                type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "doc", "docx", "ppt", "pptx", "pdf", "xlsx", "xls", "txt"],
                                accept_multiple_files=field.get("multiple", False),
                                key=f"edit_{table_name}_{name}_{selected_id}",
                            )

            submitted = st.form_submit_button("Update Record")
            if submitted:
                update_values = {}
                for field in fields:
                    name = field["name"]
                    val = edit_values.get(name)
                    current = row[name]
                    if field["type"] == "date":
                        update_values[name] = val.isoformat() if val else ""
                    elif field["type"] == "file":
                        if field.get("multiple", False):
                            saved = save_multiple_uploaded_files(val, upload_subfolder or table_name)
                            update_values[name] = saved if saved else current
                        else:
                            saved = save_uploaded_file(val, upload_subfolder or table_name)
                            update_values[name] = saved if saved else current
                    else:
                        update_values[name] = str(val).strip()

                set_clause = ", ".join([f"{f['name']} = ?" for f in fields])
                params = tuple(update_values[f["name"]] for f in fields) + (selected_id,)
                run_query(
                    f"UPDATE {table_name} SET {set_clause} WHERE id = ?",
                    params,
                )
                st.success("Record updated.")
                st.rerun()

    close_page_shell()


# ---------- pages ----------
def home_page(school_year):
    render_hero()
    st.markdown(
        f'<div class="info-strip">Current selection: <b>{school_year}</b></div>',
        unsafe_allow_html=True,
    )
    count_demo = fetch_df("SELECT COUNT(*) AS c FROM demo_lessons WHERE school_year = ?", (school_year,)).iloc[0]["c"]
    count_visits = fetch_df("SELECT COUNT(*) AS c FROM supervisory_visits_en WHERE school_year = ?", (school_year,)).iloc[0]["c"]
    count_pd = fetch_df("SELECT COUNT(*) AS c FROM professional_development WHERE school_year = ?", (school_year,)).iloc[0]["c"]
    count_peer = fetch_df("SELECT COUNT(*) AS c FROM peer_visits WHERE school_year = ?", (school_year,)).iloc[0]["c"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Demo Lessons", int(count_demo))
    c2.metric("Supervisory Visits", int(count_visits))
    c3.metric("Professional Development", int(count_pd))
    c4.metric("Peer Visits", int(count_peer))


def page_demo_lessons(school_year, admin):
    add_and_edit_simple(
        page_title="Demo Lessons",
        note="Add implementation records for model or practical lessons.",
        admin=admin,
        table_name="demo_lessons",
        year=school_year,
        upload_subfolder="demo_lessons",
        fields=[
            {"name": "teacher_name", "label": "Teacher Name", "type": "text", "required": True},
            {"name": "implementation_date", "label": "Implementation Date", "type": "date"},
            {"name": "class_name", "label": "Class", "type": "text"},
            {"name": "attachment", "label": "Attachment", "type": "file"},
        ],
    )


def page_supervisory_visits(school_year, admin):
    add_and_edit_simple(
        page_title="Supervisory Visits",
        note="Document classroom visits, class details, and attached evidence.",
        admin=admin,
        table_name="supervisory_visits_en",
        year=school_year,
        upload_subfolder="supervisory_visits",
        fields=[
            {"name": "teacher_name", "label": "Teacher Name", "type": "text", "required": True},
            {"name": "visit_date", "label": "Date", "type": "date"},
            {"name": "class_name", "label": "Class", "type": "text"},
            {"name": "attachment", "label": "Attachment", "type": "file"},
        ],
    )


def page_professional_development(school_year, admin):
    add_and_edit_simple(
        page_title="Professional Development",
        note="Track workshops, sessions, and teacher-led development activities.",
        admin=admin,
        table_name="professional_development",
        year=school_year,
        upload_subfolder="professional_development",
        fields=[
            {"name": "implementing_teacher", "label": "Implementing Teacher", "type": "text", "required": True},
            {"name": "title", "label": "Title", "type": "text"},
            {"name": "activity_date", "label": "Date", "type": "date"},
            {"name": "attachment", "label": "Attachment", "type": "file"},
        ],
    )


def page_peer_visits(school_year, admin):
    add_and_edit_simple(
        page_title="Peer Visits",
        note="Record exchange visits between teachers and keep brief notes for follow-up.",
        admin=admin,
        table_name="peer_visits",
        year=school_year,
        upload_subfolder=None,
        fields=[
            {"name": "visiting_teacher", "label": "Visiting Teacher Name", "type": "text", "required": True},
            {"name": "visited_teacher", "label": "Visited Teacher Name", "type": "text", "required": True},
            {"name": "visit_date", "label": "Date", "type": "date"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    )


def page_educational_initiatives(school_year, admin):
    add_and_edit_simple(
        page_title="Educational Initiatives",
        note="Keep a concise record of initiative titles, periods, results, and attachments.",
        admin=admin,
        table_name="educational_initiatives",
        year=school_year,
        upload_subfolder="educational_initiatives",
        fields=[
            {"name": "initiative_title", "label": "Initiative Title", "type": "text", "required": True},
            {"name": "time_period", "label": "Time Period", "type": "text"},
            {"name": "results", "label": "Results", "type": "textarea"},
            {"name": "attachments", "label": "Attachments", "type": "file", "multiple": True},
        ],
    )


def page_plc(school_year, admin):
    add_and_edit_simple(
        page_title="Professional Learning Community",
        note="Store PLC titles, time periods, and core recommendations in one place.",
        admin=admin,
        table_name="plc_records",
        year=school_year,
        upload_subfolder=None,
        fields=[
            {"name": "course_title", "label": "Course Title", "type": "text", "required": True},
            {"name": "time_period", "label": "Time Period", "type": "text"},
            {"name": "recommendations", "label": "Recommendations", "type": "textarea"},
        ],
    )


def page_files(school_year, admin):
    add_and_edit_simple(
        page_title="Files",
        note="Upload and organize images, videos, Word files, PowerPoint files, PDFs, and more.",
        admin=admin,
        table_name="files_archive_en",
        year=school_year,
        upload_subfolder="general_files",
        fields=[
            {"name": "file_name", "label": "File Name", "type": "text", "required": True},
            {"name": "category", "label": "Category", "type": "text"},
            {"name": "file_path", "label": "Upload File", "type": "file"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    )


def page_calendar(school_year, admin):
    add_and_edit_simple(
        page_title="Calendar",
        note="Use this section to note what will be implemented during the current week.",
        admin=admin,
        table_name="weekly_calendar",
        year=school_year,
        upload_subfolder=None,
        fields=[
            {"name": "week_item", "label": "What will be implemented this week?", "type": "text", "required": True},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    )


def page_general_feedback(school_year):
    init_db()
    render_page_shell(
        "General Feedback",
        "Visitors can add one general comment and a star rating here. This feedback is not linked to individual records."
    )

    feedback_df = fetch_df(
        "SELECT visitor_name, visitor_role, comment_text, rating, created_at FROM general_feedback WHERE school_year = ? ORDER BY id DESC",
        (school_year,),
    )

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
                    "INSERT INTO general_feedback (visitor_name, visitor_role, comment_text, rating, school_year) VALUES (?, ?, ?, ?, ?)",
                    (visitor_name.strip(), visitor_role, comment_text.strip(), int(rating), school_year),
                )
                st.success("Thank you. Your feedback has been submitted.")
                st.rerun()
    close_page_shell()


# ---------- main ----------
def main():
    ensure_uploads_dir()
    apply_custom_style()
    init_db()
    school_year, page = sidebar_navigation()
    admin = is_admin()

    if page == "Home":
        home_page(school_year,)
    elif page == "Demo Lessons":
        page_demo_lessons(school_year, admin)
    elif page == "Supervisory Visits":
        page_supervisory_visits(school_year, admin)
    elif page == "Professional Development":
        page_professional_development(school_year, admin)
    elif page == "Peer Visits":
        page_peer_visits(school_year, admin)
    elif page == "Educational Initiatives":
        page_educational_initiatives(school_year, admin)
    elif page == "Professional Learning Community":
        page_plc(school_year, admin)
    elif page == "Files":
        page_files(school_year, admin)
    elif page == "Calendar":
        page_calendar(school_year, admin)
    elif page == "General Feedback":
        page_general_feedback(school_year,)


if __name__ == "__main__":
    main()
