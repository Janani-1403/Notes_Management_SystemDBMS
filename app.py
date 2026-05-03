"""
app.py – Smart Notes Management System
A production-quality Streamlit application with full CRUD, versioning,
reminders, events, trash, and analytics.
"""

import streamlit as st
from datetime import datetime, date, time as dtime
import urllib.parse

import db

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Notes",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bootstrap ─────────────────────────────────────────────────────────────────
db.bootstrap_db()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

/* ── Root tokens ── */
:root {
    --bg:        #0d0f14;
    --surface:   #161a22;
    --surface2:  #1e2330;
    --border:    #2a3040;
    --accent:    #4f8ef7;
    --accent2:   #7c5cf6;
    --green:     #34d399;
    --amber:     #fbbf24;
    --red:       #f87171;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --radius:    12px;
}

/* ── App shell ── */
.stApp { background: var(--bg); font-family: 'DM Sans', sans-serif; color: var(--text); }
section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Headings ── */
h1,h2,h3 { font-family: 'Syne', sans-serif !important; }

/* ── Sidebar nav button ── */
div[data-testid="stSidebar"] .stButton > button {
    width: 100%; text-align: left; background: transparent;
    border: 1px solid transparent; border-radius: 8px;
    color: var(--text) !important; font-size: 0.9rem;
    padding: 0.55rem 1rem; margin: 2px 0;
    transition: all 0.2s;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--surface2); border-color: var(--border);
}

/* ── Main buttons ── */
.stButton > button {
    background: var(--surface2); color: var(--text) !important;
    border: 1px solid var(--border); border-radius: 8px;
    font-family: 'DM Sans', sans-serif; font-size: 0.88rem;
    transition: all 0.18s;
}
.stButton > button:hover { border-color: var(--accent); color: var(--accent) !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stTimeInput > div > div > input {
    background: var(--surface2) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(79,142,247,0.15) !important;
}

/* ── Card ── */
.card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.1rem 1.3rem;
    margin-bottom: 0.7rem; transition: border-color 0.2s;
}
.card:hover { border-color: var(--accent); }
.card-title { font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; margin: 0 0 0.3rem; }
.card-meta  { font-size: 0.78rem; color: var(--muted); }

/* ── Priority badges ── */
.badge {
    display: inline-block; padding: 2px 9px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .04em;
}
.badge-low    { background: rgba(52,211,153,.15); color: var(--green);  border: 1px solid rgba(52,211,153,.3); }
.badge-medium { background: rgba(251,191,36,.15);  color: var(--amber);  border: 1px solid rgba(251,191,36,.3); }
.badge-high   { background: rgba(248,113,113,.15); color: var(--red);    border: 1px solid rgba(248,113,113,.3); }
.badge-urgent { background: rgba(124,92,246,.2);   color: #a78bfa;       border: 1px solid rgba(124,92,246,.4); }

/* ── Stat card ── */
.stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.2rem 1.5rem; text-align: center;
}
.stat-num  { font-family: 'Syne', sans-serif; font-size: 2.2rem; font-weight: 800; line-height: 1; }
.stat-label { font-size: 0.78rem; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: .06em; }

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Success / error pills ── */
.stAlert { border-radius: 8px !important; }

/* ── Section header ── */
.section-header {
    font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 800;
    margin-bottom: 1.2rem; letter-spacing: -0.02em;
}
.section-header span { color: var(--accent); }

/* ── Tag chip ── */
.tag-chip {
    display: inline-block; background: rgba(79,142,247,.12);
    color: var(--accent); border: 1px solid rgba(79,142,247,.25);
    border-radius: 20px; padding: 1px 9px; font-size: 0.72rem; margin: 2px;
}

/* ── Pinned ribbon ── */
.pinned-badge {
    font-size: 0.72rem; color: var(--amber); font-weight: 600;
    margin-left: 6px;
}

/* ── Overdue highlight ── */
.overdue { border-left: 3px solid var(--red) !important; }
.upcoming-r { border-left: 3px solid var(--accent) !important; }
.done-r { opacity: 0.55; }

/* ── Full note view ── */
.note-full-title {
    font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800;
    line-height: 1.2; margin-bottom: 0.5rem;
}
.note-full-content {
    font-size: 1rem; line-height: 1.75; color: var(--text);
    white-space: pre-wrap;
}

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 3rem 1rem; color: var(--muted);
}
.empty-state .icon { font-size: 3rem; }
.empty-state p { font-size: 0.9rem; margin-top: 0.5rem; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    background: transparent; color: var(--muted) !important;
    font-family: 'DM Sans', sans-serif; font-size: 0.88rem;
    border-radius: 0; border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important; border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid var(--border); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_ss("page", "dashboard")
_ss("view_note_id", None)
_ss("edit_note_id", None)


# ── Helpers ───────────────────────────────────────────────────────────────────

PRIORITY_COLORS = {"low": "badge-low", "medium": "badge-medium",
                   "high": "badge-high", "urgent": "badge-urgent"}

def badge(p):
    cls = PRIORITY_COLORS.get(p, "badge-medium")
    return f'<span class="badge {cls}">{p}</span>'

def tag_chips(tags_str):
    if not tags_str:
        return ""
    return " ".join(f'<span class="tag-chip">#{t}</span>' for t in tags_str.split(",") if t)

def maps_url(location):
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(location)}"

def fmt_dt(dt):
    if not dt:
        return "—"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    return dt.strftime("%b %d, %Y  %H:%M")

def fmt_date(d):
    if not d:
        return "—"
    if isinstance(d, str):
        try:
            d = date.fromisoformat(d)
        except Exception:
            return d
    return d.strftime("%b %d, %Y")

def nav(page):
    st.session_state.page = page
    st.session_state.view_note_id = None
    st.session_state.edit_note_id = None

def empty_state(icon, msg):
    st.markdown(f'<div class="empty-state"><div class="icon">{icon}</div><p>{msg}</p></div>',
                unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("🏠", "Dashboard",  "dashboard"),
    ("📝", "Add Note",   "add_note"),
    ("📋", "My Notes",   "view_notes"),
    ("🔔", "Reminders",  "reminders"),
    ("📅", "Events",     "events"),
    ("🗑️", "Trash",      "trash"),
]

with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0.5rem 1.5rem;'>
        <div style='font-family:Syne,sans-serif;font-size:1.35rem;font-weight:800;
                    letter-spacing:-0.02em;'>
            <span style='color:#4f8ef7;'>Smart</span> Notes
        </div>
        <div style='font-size:0.75rem;color:#64748b;margin-top:2px;'>Location Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    for icon, label, page_key in NAV_ITEMS:
        active = "🔹 " if st.session_state.page == page_key else ""
        if st.button(f"{icon}  {active}{label}", key=f"nav_{page_key}"):
            nav(page_key)

    st.markdown("<hr>", unsafe_allow_html=True)
    stats = db.get_dashboard_stats()
    st.markdown(f"""
    <div style='padding:0.5rem;font-size:0.78rem;color:#64748b;line-height:1.9;'>
        📝 {stats['total_notes']} notes &nbsp;|&nbsp; 📌 {stats['pinned']} pinned<br>
        🔔 {stats['active_reminders']} reminders<br>
        📅 {stats['total_events']} events
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    stats = db.get_dashboard_stats()
    st.markdown('<div class="section-header">Good day! <span>Here\'s your overview.</span></div>',
                unsafe_allow_html=True)

    # ── Stat row ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    def stat(col, num, label, color="#4f8ef7"):
        col.markdown(f"""
        <div class="stat-card">
            <div class="stat-num" style="color:{color};">{num}</div>
            <div class="stat-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    stat(c1, stats["total_notes"],      "Total Notes")
    stat(c2, stats["pinned"],           "Pinned",       "#fbbf24")
    stat(c3, stats["active_reminders"], "Reminders",    "#34d399")
    stat(c4, stats["overdue_reminders"],"Overdue",      "#f87171")
    stat(c5, stats["total_events"],     "Events",       "#7c5cf6")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.6, 1])

    # ── Pinned notes ──────────────────────────────────────────────────────────
    with col_left:
        st.markdown("### 📌 Pinned Notes")
        pinned = db.get_notes(pinned_only=True)
        if pinned:
            for n in pinned[:5]:
                tags_html = tag_chips(n.get("tags"))
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">{n['title']} {badge(n['priority'])}</div>
                    <div class="card-meta">{n['content'][:100]}{'…' if len(n['content'])>100 else ''}</div>
                    <div style="margin-top:6px;">{tags_html}</div>
                    <div class="card-meta" style="margin-top:6px;">Updated {fmt_dt(n['updated_at'])}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("Open", key=f"dash_open_{n['id']}"):
                    st.session_state.view_note_id = n["id"]
                    nav("view_notes")
                    st.rerun()
        else:
            empty_state("📌", "No pinned notes yet. Pin important notes for quick access.")

    # ── Priority breakdown + overdue reminders ────────────────────────────────
    with col_right:
        st.markdown("### 📊 Priority Breakdown")
        bp = stats.get("by_priority", {})
        has_any = False
        rows_html = ""
        for p in ["urgent", "high", "medium", "low"]:
            cnt = bp.get(p, 0)
            if cnt:
                has_any = True
                rows_html += f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:8px 4px;border-bottom:1px solid #2a3040;">
                    <span>{badge(p)}</span>
                    <span style="font-family:Syne,sans-serif;font-weight:700;font-size:1rem;">{cnt}</span>
                </div>"""
        if has_any:
            st.markdown(rows_html, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#64748b;font-size:0.85rem;'>No notes yet.</div>",
                        unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🔴 Overdue Reminders")
        overdue = db.get_reminders(status="expired")[:4]
        if overdue:
            for r in overdue:
                st.markdown(f"""
                <div class="card overdue">
                    <div class="card-title" style="font-size:0.88rem;">{r['description']}</div>
                    <div class="card-meta">Due: {fmt_dt(r['remind_at'])}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.success("No overdue reminders! 🎉")

    # ── Recent notes ──────────────────────────────────────────────────────────
    st.markdown("### 🕐 Recent Notes")
    recent = db.get_notes()[:6]
    if recent:
        cols = st.columns(3)
        for i, n in enumerate(recent):
            with cols[i % 3]:
                tags_html = tag_chips(n.get("tags"))
                pin_mark = '<span class="pinned-badge">📌 PINNED</span>' if n["is_pinned"] else ""
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">{n['title']} {badge(n['priority'])} {pin_mark}</div>
                    <div class="card-meta">{n['content'][:80]}{'…' if len(n['content'])>80 else ''}</div>
                    <div style="margin-top:6px;">{tags_html}</div>
                    <div class="card-meta" style="margin-top:6px;">{fmt_dt(n['updated_at'])}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("Open →", key=f"recent_open_{n['id']}"):
                    st.session_state.view_note_id = n["id"]
                    nav("view_notes")
                    st.rerun()
    else:
        empty_state("📝", "No notes yet. Click 'Add Note' to create your first one!")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ADD NOTE
# ══════════════════════════════════════════════════════════════════════════════

def page_add_note():
    st.markdown('<div class="section-header">Add <span>New Note</span></div>',
                unsafe_allow_html=True)

    with st.form("add_note_form", clear_on_submit=True):
        title    = st.text_input("Title *", placeholder="Give your note a clear title…")
        content  = st.text_area("Content *", height=180, placeholder="Write your note here…")
        col1, col2 = st.columns(2)
        priority = col1.selectbox("Priority", ["medium", "low", "high", "urgent"],
                                  format_func=str.capitalize)
        tags_raw = col2.text_input("Tags (comma-separated)", placeholder="work, ideas, todo")
        location = st.text_input("📍 Location", placeholder="e.g. Coffee Shop, MG Road, Bangalore")

        st.markdown("#### ⏰ Add Reminder (optional)")
        c1, c2, c3 = st.columns(3)
        add_reminder  = c1.checkbox("Attach a reminder")
        remind_date   = c2.date_input("Date", value=date.today()) if add_reminder else None
        remind_time   = c3.time_input("Time", value=dtime(9, 0))  if add_reminder else None

        submitted = st.form_submit_button("✨ Save Note", use_container_width=True)

    if submitted:
        errors = []
        if not title.strip():   errors.append("Title is required.")
        if not content.strip(): errors.append("Content is required.")

        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
        else:
            tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
            note_id = db.create_note(title.strip(), content.strip(), priority,
                                     location.strip() or None, tags_list)
            if note_id and add_reminder and remind_date and remind_time:
                remind_dt = datetime.combine(remind_date, remind_time)
                db.create_reminder(f"Reminder for: {title.strip()}", remind_dt, note_id=note_id)

            if note_id:
                st.success("✅ Note saved successfully!")
            else:
                st.error("❌ Failed to save note. Please try again.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: VIEW NOTES
# ══════════════════════════════════════════════════════════════════════════════

def page_view_notes():
    # ── Full note view ────────────────────────────────────────────────────────
    if st.session_state.view_note_id:
        _render_full_note(st.session_state.view_note_id)
        return

    # ── Edit note view ────────────────────────────────────────────────────────
    if st.session_state.edit_note_id:
        _render_edit_note(st.session_state.edit_note_id)
        return

    # ── Notes list ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">My <span>Notes</span></div>',
                unsafe_allow_html=True)

    # Search & filters
    c1, c2, c3 = st.columns([2.5, 1, 1])
    search   = c1.text_input("🔍 Search", placeholder="Search title or content…", label_visibility="collapsed")
    pf       = c2.selectbox("Priority", ["All", "Low", "Medium", "High", "Urgent"],
                            label_visibility="collapsed")
    all_tags = ["All"] + db.get_all_tags()
    tf       = c3.selectbox("Tag", all_tags, label_visibility="collapsed")

    notes = db.get_notes(search=search, priority_filter=pf if pf != "All" else None,
                         tag_filter=tf if tf != "All" else None)

    if not notes:
        empty_state("📭", "No notes found. Try adjusting your filters.")
        return

    st.markdown(f"<div style='color:#64748b;font-size:0.82rem;margin-bottom:0.8rem;'>{len(notes)} note(s)</div>",
                unsafe_allow_html=True)

    for n in notes:
        tags_html = tag_chips(n.get("tags"))
        pin_mark  = '<span class="pinned-badge">📌</span>' if n["is_pinned"] else ""
        loc_html  = (f'<span style="font-size:0.75rem;color:#64748b;">📍 {n["location"]}</span>'
                     if n.get("location") else "")

        st.markdown(f"""
        <div class="card">
            <div class="card-title">{pin_mark} {n['title']} {badge(n['priority'])}</div>
            <div class="card-meta">{n['content'][:120]}{'…' if len(n['content'])>120 else ''}</div>
            <div style="margin-top:6px;">{tags_html} {loc_html}</div>
            <div class="card-meta" style="margin-top:6px;">Updated {fmt_dt(n['updated_at'])}</div>
        </div>""", unsafe_allow_html=True)

        bc1, bc2, bc3, bc4 = st.columns([1, 1, 1, 1])
        if bc1.button("Open", key=f"open_{n['id']}"):
            st.session_state.view_note_id = n["id"]
            st.rerun()
        if bc2.button("Edit", key=f"edit_{n['id']}"):
            st.session_state.edit_note_id = n["id"]
            st.rerun()
        pin_label = "Unpin" if n["is_pinned"] else "Pin"
        if bc3.button(pin_label, key=f"pin_{n['id']}"):
            db.toggle_pin(n["id"], n["is_pinned"])
            st.rerun()
        if bc4.button("Delete", key=f"del_{n['id']}"):
            db.soft_delete_note(n["id"])
            st.rerun()


def _render_full_note(note_id):
    n = db.get_note_by_id(note_id)
    if not n:
        st.error("Note not found.")
        st.session_state.view_note_id = None
        st.rerun()
        return

    if st.button("← Back to Notes"):
        st.session_state.view_note_id = None
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    pin_mark = '<span class="pinned-badge">📌 PINNED</span>' if n["is_pinned"] else ""
    st.markdown(f"""
    <div class="note-full-title">{n['title']} {pin_mark}</div>
    <div style="margin-bottom:0.8rem;">{badge(n['priority'])}</div>
    """, unsafe_allow_html=True)

    tags_html = tag_chips(n.get("tags"))
    if tags_html:
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    if n.get("location"):
        url = maps_url(n["location"])
        st.markdown(f'📍 <a href="{url}" target="_blank" style="color:#4f8ef7;">{n["location"]}</a>',
                    unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:0.78rem;color:#64748b;margin:0.5rem 0 1.2rem;'>
        Created: {fmt_dt(n['created_at'])} &nbsp;|&nbsp; Updated: {fmt_dt(n['updated_at'])}
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="note-full-content">', unsafe_allow_html=True)
    st.write(n["content"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("✏️ Edit"):
        st.session_state.edit_note_id = note_id
        st.session_state.view_note_id = None
        st.rerun()
    if c2.button("🗑️ Delete"):
        db.soft_delete_note(note_id)
        st.session_state.view_note_id = None
        st.success("Moved to trash.")
        st.rerun()
    pin_label = "📌 Unpin" if n["is_pinned"] else "📌 Pin"
    if c3.button(pin_label):
        db.toggle_pin(note_id, n["is_pinned"])
        st.rerun()

    # Version history
    with st.expander("🕐 Version History"):
        versions = db.get_versions(note_id)
        if versions:
            for v in versions:
                vc1, vc2 = st.columns([3, 1])
                vc1.markdown(f"""
                <div style='padding:0.4rem 0;border-bottom:1px solid #2a3040;'>
                    <strong>v{v['version_num']}</strong>  –  {v['title']}
                    <span style='font-size:0.75rem;color:#64748b;margin-left:8px;'>
                        {fmt_dt(v['saved_at'])}
                    </span>
                </div>""", unsafe_allow_html=True)
                if vc2.button("Restore", key=f"restore_v_{v['id']}"):
                    db.restore_version(note_id, v["id"])
                    st.success(f"Restored to version {v['version_num']}!")
                    st.rerun()
        else:
            st.info("No previous versions found.")


def _render_edit_note(note_id):
    n = db.get_note_by_id(note_id)
    if not n:
        st.error("Note not found.")
        st.session_state.edit_note_id = None
        st.rerun()
        return

    st.markdown('<div class="section-header">Edit <span>Note</span></div>',
                unsafe_allow_html=True)
    if st.button("← Back"):
        st.session_state.edit_note_id = None
        st.rerun()

    current_tags = n.get("tags") or ""
    with st.form("edit_note_form"):
        title    = st.text_input("Title *", value=n["title"])
        content  = st.text_area("Content *", value=n["content"], height=200)
        c1, c2   = st.columns(2)
        priority = c1.selectbox("Priority",
                                ["low", "medium", "high", "urgent"],
                                index=["low","medium","high","urgent"].index(n["priority"]),
                                format_func=str.capitalize)
        tags_raw = c2.text_input("Tags", value=current_tags)
        location = st.text_input("📍 Location", value=n.get("location") or "")
        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)

    if submitted:
        errors = []
        if not title.strip():   errors.append("Title is required.")
        if not content.strip(): errors.append("Content is required.")
        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
        else:
            tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
            db.update_note(note_id, title.strip(), content.strip(), priority,
                           location.strip() or None, tags_list)
            st.success("✅ Note updated successfully!")
            st.session_state.edit_note_id = None
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: REMINDERS
# ══════════════════════════════════════════════════════════════════════════════

def page_reminders():
    st.markdown('<div class="section-header">⏰ <span>Reminders</span></div>',
                unsafe_allow_html=True)

    # Add reminder form
    with st.expander("➕ Add New Reminder", expanded=False):
        with st.form("add_reminder_form", clear_on_submit=True):
            desc   = st.text_input("Description *", placeholder="What do you need to remember?")
            c1, c2 = st.columns(2)
            r_date = c1.date_input("Date", value=date.today())
            r_time = c2.time_input("Time", value=dtime(9, 0))
            submitted = st.form_submit_button("Add Reminder", use_container_width=True)

        if submitted:
            if not desc.strip():
                st.error("⚠️ Description is required.")
            else:
                remind_dt = datetime.combine(r_date, r_time)
                db.create_reminder(desc.strip(), remind_dt)
                st.success("✅ Reminder added!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📅 Upcoming", "⚠️ Expired", "✅ Done"])

    def render_reminders(reminders, status):
        if not reminders:
            empty_state("🔔", f"No {status} reminders.")
            return
        for r in reminders:
            now      = datetime.now()
            is_over  = r["remind_at"] < now and not r["is_done"]
            css_cls  = "overdue" if is_over else ("done-r" if r["is_done"] else "upcoming-r")
            note_tag = f" (Note #{r['note_id']})" if r.get("note_id") else ""

            st.markdown(f"""
            <div class="card {css_cls}">
                <div class="card-title" style="font-size:0.95rem;">{r['description']}{note_tag}</div>
                <div class="card-meta">🕐 {fmt_dt(r['remind_at'])}</div>
            </div>""", unsafe_allow_html=True)

            bc1, bc2, _ = st.columns([1, 1, 4])
            if not r["is_done"]:
                if bc1.button("✅ Done", key=f"rdone_{r['id']}"):
                    db.mark_reminder_done(r["id"])
                    st.rerun()
            if bc2.button("🗑️ Delete", key=f"rdel_{r['id']}"):
                db.soft_delete_reminder(r["id"])
                st.rerun()

    with tab1: render_reminders(db.get_reminders("upcoming"), "upcoming")
    with tab2: render_reminders(db.get_reminders("expired"),  "expired")
    with tab3: render_reminders(db.get_reminders("done"),     "done")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EVENTS
# ══════════════════════════════════════════════════════════════════════════════

def page_events():
    st.markdown('<div class="section-header">📅 <span>Events</span></div>',
                unsafe_allow_html=True)

    with st.expander("➕ Add New Event", expanded=False):
        with st.form("add_event_form", clear_on_submit=True):
            title   = st.text_input("Title *", placeholder="Event title…")
            desc    = st.text_area("Description", height=80)
            c1, c2  = st.columns(2)
            etype   = c1.selectbox("Type", ["general", "scheduled"], format_func=str.capitalize)
            edate   = c2.date_input("Date", value=date.today()) if etype == "scheduled" else None
            submitted = st.form_submit_button("Add Event", use_container_width=True)

        if submitted:
            if not title.strip():
                st.error("⚠️ Title is required.")
            else:
                db.create_event(title.strip(), desc.strip() or None, etype,
                                edate if etype == "scheduled" else None)
                st.success("✅ Event added!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🌐 General", "📆 Upcoming", "🗓️ Past"])

    def render_events(events):
        if not events:
            empty_state("📅", "No events here yet.")
            return
        for e in events:
            date_html = f'<div class="card-meta" style="margin-top:4px;">📅 {fmt_date(e["event_date"])}</div>' if e.get("event_date") else ""
            desc_html = f'<div class="card-meta" style="margin-top:4px;">{e["description"]}</div>' if e.get("description") else ""
            type_badge = f'<span style="font-size:0.72rem;color:#7c5cf6;background:rgba(124,92,246,.12);border:1px solid rgba(124,92,246,.25);border-radius:20px;padding:1px 8px;">{e["event_type"].capitalize()}</span>'
            st.markdown(f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div class="card-title">{e['title']}</div>
                    {type_badge}
                </div>
                {desc_html}
                {date_html}
            </div>""", unsafe_allow_html=True)
            if st.button("🗑️ Delete", key=f"evdel_{e['id']}"):
                db.soft_delete_event(e["id"])
                st.rerun()

    with tab1: render_events(db.get_events("general"))
    with tab2: render_events(db.get_events("upcoming"))
    with tab3: render_events(db.get_events("past"))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TRASH
# ══════════════════════════════════════════════════════════════════════════════

def page_trash():
    st.markdown('<div class="section-header">🗑️ <span>Trash</span></div>',
                unsafe_allow_html=True)
    st.markdown("<div style='color:#64748b;font-size:0.85rem;margin-bottom:1rem;'>Items here are soft-deleted. Restore or permanently delete them.</div>",
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Notes", "🔔 Reminders", "📅 Events"])

    with tab1:
        deleted_notes = db.get_notes(include_deleted=True)
        if not deleted_notes:
            empty_state("🗑️", "Trash is empty for notes.")
        for n in deleted_notes:
            st.markdown(f"""
            <div class="card" style="opacity:0.7;">
                <div class="card-title">{n['title']} {badge(n['priority'])}</div>
                <div class="card-meta">Deleted: {fmt_dt(n.get('deleted_at'))}</div>
            </div>""", unsafe_allow_html=True)
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("♻️ Restore", key=f"rnote_{n['id']}"):
                db.restore_note(n["id"])
                st.success("Note restored!")
                st.rerun()
            if c2.button("🔥 Delete", key=f"pnote_{n['id']}"):
                db.permanent_delete_note(n["id"])
                st.warning("Permanently deleted.")
                st.rerun()

    with tab2:
        deleted_rem = db.get_reminders(include_deleted=True)
        if not deleted_rem:
            empty_state("🗑️", "Trash is empty for reminders.")
        for r in deleted_rem:
            st.markdown(f"""
            <div class="card" style="opacity:0.7;">
                <div class="card-title">{r['description']}</div>
                <div class="card-meta">Deleted: {fmt_dt(r.get('deleted_at'))}</div>
            </div>""", unsafe_allow_html=True)
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("♻️ Restore", key=f"rrem_{r['id']}"):
                db.restore_reminder(r["id"])
                st.rerun()
            if c2.button("🔥 Delete", key=f"prem_{r['id']}"):
                db.permanent_delete_reminder(r["id"])
                st.rerun()

    with tab3:
        deleted_ev = db.get_events(include_deleted=True)
        if not deleted_ev:
            empty_state("🗑️", "Trash is empty for events.")
        for e in deleted_ev:
            st.markdown(f"""
            <div class="card" style="opacity:0.7;">
                <div class="card-title">{e['title']}</div>
                <div class="card-meta">Deleted: {fmt_dt(e.get('deleted_at'))}</div>
            </div>""", unsafe_allow_html=True)
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("♻️ Restore", key=f"rev_{e['id']}"):
                db.restore_event(e["id"])
                st.rerun()
            if c2.button("🔥 Delete", key=f"pev_{e['id']}"):
                db.permanent_delete_event(e["id"])
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

PAGE_MAP = {
    "dashboard":  page_dashboard,
    "add_note":   page_add_note,
    "view_notes": page_view_notes,
    "reminders":  page_reminders,
    "events":     page_events,
    "trash":      page_trash,
}

current_page = st.session_state.get("page", "dashboard")
PAGE_MAP.get(current_page, page_dashboard)()
