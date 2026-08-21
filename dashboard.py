import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import re
import sqlite3
import requests
from datetime import date, datetime
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="داشبورد هوشمند مالی", layout="wide", page_icon="📊")

# ---------- Design system ----------
PAPER = "#EFF3F1"
CARD = "#FFFFFF"
INK = "#16262A"
INK_SOFT = "#4B5D61"
TEAL = "#1E7F79"
TEAL_DARK = "#14514E"
GOLD = "#C89B3C"
BRICK = "#B4483E"
INDIGO = "#2B3A55"
BORDER = "#DCE3E1"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700&family=Lalezar&display=swap');

* {{ direction: rtl; text-align: right; font-family: 'Vazirmatn', sans-serif; }}

.stApp {{ background: {PAPER}; }}
[data-testid="stSidebar"] {{ background: {INDIGO}; }}
[data-testid="stSidebar"] * {{ color: #EAEFEE !important; }}
[data-testid="stSidebar"] .stButton>button {{
    width: 100%; text-align: right; background: transparent;
    border: 1px solid rgba(255,255,255,0.14); border-radius: 10px;
    padding: 0.6rem 0.9rem; margin-bottom: 6px; font-weight: 500;
    transition: background 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
}}
[data-testid="stSidebar"] .stButton>button:hover {{
    background: rgba(255,255,255,0.1); transform: translateX(-3px);
}}
[data-testid="stSidebar"] .stButton>button[kind="primary"] {{
    background: {TEAL}; border-color: {TEAL};
}}

.hero-title {{
    font-family: 'Lalezar', sans-serif; font-size: 34px; color: {INK};
    margin: 0; letter-spacing: 0.5px;
    animation: fadeSlide 0.5s ease both;
}}
.hero-sub {{ color: {INK_SOFT}; font-size: 14px; margin: 4px 0 0; animation: fadeSlide 0.5s ease 0.08s both; }}

.tile-divider {{
    height: 6px; border-radius: 3px; margin: 14px 0 26px;
    background: repeating-linear-gradient(-45deg, {TEAL} 0 10px, {GOLD} 10px 20px);
    opacity: 0.85; transform-origin: right center;
    animation: growIn 0.7s cubic-bezier(.2,.9,.25,1) 0.15s both;
}}

.metric-card {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
    padding: 1.1rem 1.3rem; border-right: 4px solid var(--accent, {TEAL});
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.metric-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 18px rgba(20,30,30,0.08); }}
.metric-label {{ font-size: 13px; color: {INK_SOFT}; margin: 0 0 6px; display: flex; gap: 6px; align-items: center; }}
.metric-value {{
    font-size: 26px; font-weight: 700; color: {INK}; margin: 0;
    font-variant-numeric: tabular-nums;
}}

@keyframes fadeSlide {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes growIn {{
    from {{ transform: scaleX(0); }}
    to {{ transform: scaleX(1); }}
}}
@media (prefers-reduced-motion: reduce) {{
    .hero-title, .hero-sub, .tile-divider, [data-testid="stChatMessage"] {{ animation: none !important; }}
    .metric-card:hover {{ transform: none; }}
}}

.section-label {{
    font-size: 13px; color: {INK_SOFT}; font-weight: 600; margin: 22px 0 10px;
    display: flex; align-items: center; gap: 8px;
}}
.section-label::after {{
    content: ""; flex: 1; height: 1px; background: {BORDER};
    transform-origin: right center; animation: growIn 0.5s ease both;
}}

.stButton>button {{
    border-radius: 10px; font-weight: 500; border: 1px solid {BORDER};
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}}
.stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 14px rgba(20,30,30,0.1); }}
.stButton>button:active {{ transform: translateY(0px) scale(0.98); }}
.stButton>button[kind="primary"] {{
    background: {TEAL}; border-color: {TEAL}; color: white;
}}
.stButton>button[kind="primary"]:hover {{ background: {TEAL_DARK}; border-color: {TEAL_DARK}; }}

[data-testid="stChatMessage"] {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
    padding: 4px 6px; margin-bottom: 10px;
    animation: fadeSlide 0.35s ease both;
}}

[data-testid="stFileUploaderDropzone"] {{
    background: {CARD}; border: 1.5px dashed {TEAL}; border-radius: 12px;
    transition: border-color 0.2s ease, background 0.2s ease;
}}
[data-testid="stFileUploaderDropzone"]:hover {{ border-color: {TEAL_DARK}; background: #F7FAF9; }}

.stTextInput>div>div>input, .stChatInput textarea {{
    border-radius: 10px !important; transition: box-shadow 0.15s ease;
}}

hr {{ border-color: {BORDER}; }}

/* --- استایل‌های جدید برای گزارش هوش مصنوعی --- */
.ai-report-card {{
    background: #F7FAF9;
    border: 1px solid #DCE3E1;
    border-right: 5px solid #1E7F79;
    border-radius: 12px;
    padding: 25px;
    margin-top: 15px;
    line-height: 1.9;
    font-size: 15px;
    color: #16262A;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
}}
.ai-report-card h1, .ai-report-card h2, .ai-report-card h3 {{
    color: #14514E !important;
    margin-top: 0;
    font-family: 'Lalezar', sans-serif;
}}
.ai-report-card ul {{ padding-right: 20px; }}

</style>
""", unsafe_allow_html=True)


def metric_card(label, value, icon, accent, index=0):
    """Metric card with an animated count-up number (runs in its own component iframe)."""
    delay = index * 90
    html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@600;700&display=swap');
    html, body {{ margin:0; background: transparent; font-family:'Vazirmatn',sans-serif; direction: rtl; }}
    .card {{
        background:{CARD}; border:1px solid {BORDER}; border-radius:12px;
        padding:1.1rem 1.3rem; border-right:4px solid {accent}; box-sizing:border-box;
        opacity:0; animation: rise 0.4s ease {delay}ms both;
    }}
    .label {{ font-size:13px; color:{INK_SOFT}; margin:0 0 6px; display:flex; gap:6px; align-items:center; }}
    .value {{ font-size:26px; font-weight:700; color:{INK}; margin:0; font-variant-numeric: tabular-nums; }}
    @keyframes rise {{ from {{ opacity:0; transform: translateY(8px);}} to {{ opacity:1; transform: translateY(0);}} }}
    </style>
    <div class="card">
      <p class="label">{icon} {label}</p>
      <p class="value" id="v">۰</p>
    </div>
    <script>
    (function() {{
      const el = document.getElementById('v');
      const target = {value};
      const duration = 900;
      const startDelay = {delay};
      setTimeout(() => {{
        const start = performance.now();
        function tick(now) {{
          const p = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          const current = Math.round(target * eased);
          el.textContent = current.toLocaleString('en-US');
          if (p < 1) requestAnimationFrame(tick);
        }}
        requestAnimationFrame(tick);
      }}, startDelay);
    }})();
    </script>
    """
    components.html(html, height=100)


def section_label(text):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


# ---------- Robust numeric cleaning ----------
def to_western_digits(s: str) -> str:
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"
    for i, d in enumerate(persian):
        s = s.replace(d, str(i))
    for i, d in enumerate(arabic):
        s = s.replace(d, str(i))
    return s


def clean_number(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    if s == "":
        return 0.0
    s = to_western_digits(s)
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    if s.strip().startswith("-"):
        negative = True
    s = re.sub(r"[^\d.]", "", s)
    if s in ("", "."):
        return 0.0
    try:
        num = float(s)
    except ValueError:
        return 0.0
    return -abs(num) if negative else num


# ---------- Session state defaults ----------
defaults = {
    "api_key": st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else "",
    "telegram_token": st.secrets.get("TELEGRAM_BOT_TOKEN", "") if hasattr(st, "secrets") else "",
    "active_tab": "داشبورد",
    "raw_data": None,
    "clean_data": None,
    "column_mapping": None,
    "chat_history": [],
    "pending_auto_analysis": False,
    "new_telegram_senders": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def get_model():
    if not st.session_state.api_key:
        return None
    genai.configure(api_key=st.session_state.api_key)
    return genai.GenerativeModel("gemini-3.5-flash-lite")  # بروزرسانی نام مدل به نسخه معتبر و سریع


def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("پاسخ هوش مصنوعی شامل JSON معتبر نبود.")
    return json.loads(match.group(0))


def go_to(tab_name, **flags):
    st.session_state.active_tab = tab_name
    for k, v in flags.items():
        st.session_state[k] = v
    st.rerun()


def detect_structure(model, raw_data: pd.DataFrame) -> dict:
    columns = list(raw_data.columns)
    sample_rows = raw_data.head(4).astype(str).to_dict(orient="records")
    prompt = f"""
    You are analyzing a financial spreadsheet.
    Column headers: {columns}
    Sample rows (first {len(sample_rows)}): {json.dumps(sample_rows, ensure_ascii=False)}

    Headers and values may be in Persian, English, or mixed, and naming can vary a lot
    between files. Decide which of these three shapes the data actually has, and
    return ONLY a JSON object matching exactly one shape below (no markdown, no commentary):

    1) Separate income and expense columns:
    {{"structure": "separate_columns", "date_column": "<col name or null>", "income_column": "<col name>", "expense_column": "<col name>", "category_column": "<col name or null>"}}

    2) A single signed amount column (positive means income, negative means expense, or vice versa):
    {{"structure": "single_amount", "date_column": "<col name or null>", "amount_column": "<col name>", "sign_convention": "positive_is_income" or "negative_is_income", "category_column": "<col name or null>"}}

    3) A single amount column plus a text category/type column that says whether each row is income or expense:
    {{"structure": "amount_with_type", "date_column": "<col name or null>", "amount_column": "<col name>", "type_column": "<col name>", "income_values": ["value1", "value2"], "expense_values": ["value1", "value2"], "category_column": "<col name or null>"}}

    In every shape, "category_column" is optional: if there is any column describing WHAT each
    transaction is for (e.g. "شرح", "دسته‌بندی", "توضیحات", "شرح تراکنش", item/description/category
    name — NOT the same thing as the income/expense classification itself), name it there so the
    individual items can be broken down later. If no such column exists, use null.

    Pick whichever shape genuinely matches the sample data. Return ONLY the JSON object.
    """
    response = model.generate_content(prompt)
    return extract_json(response.text)


def build_clean_data(raw_data: pd.DataFrame, structure: dict) -> pd.DataFrame:
    df = raw_data.copy()
    kind = structure.get("structure")
    date_col = structure.get("date_column")

    if kind == "separate_columns":
        income_col = structure["income_column"]
        expense_col = structure["expense_column"]
        df["income"] = df[income_col].apply(clean_number)
        df["expense"] = df[expense_col].apply(clean_number).abs()

    elif kind == "single_amount":
        amount_col = structure["amount_column"]
        convention = structure.get("sign_convention", "positive_is_income")
        amounts = df[amount_col].apply(clean_number)
        if convention == "positive_is_income":
            df["income"] = amounts.clip(lower=0)
            df["expense"] = (-amounts.clip(upper=0))
        else:
            df["income"] = (-amounts.clip(upper=0))
            df["expense"] = amounts.clip(lower=0)

    elif kind == "amount_with_type":
        amount_col = structure["amount_column"]
        type_col = structure["type_column"]
        income_values = set(str(v).strip().lower() for v in structure.get("income_values", []))
        expense_values = set(str(v).strip().lower() for v in structure.get("expense_values", []))
        amounts = df[amount_col].apply(clean_number).abs()
        types = df[type_col].astype(str).str.strip().str.lower()
        df["income"] = amounts.where(types.isin(income_values), 0.0)
        df["expense"] = amounts.where(types.isin(expense_values), 0.0)

    else:
        raise ValueError("ساختار شناسایی‌شده پشتیبانی نمی‌شود.")

    df["profit"] = df["income"] - df["expense"]

    category_col = structure.get("category_column")
    if category_col and category_col in df.columns:
        df["category"] = df[category_col].astype(str).str.strip()
    elif kind == "amount_with_type":
        df["category"] = df[structure["type_column"]].astype(str).str.strip()
    else:
        df["category"] = None

    if date_col and date_col in df.columns:
        df = df.rename(columns={date_col: "date"})
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")

    return df


# ================= Telegram task module =================
TASKS_DB_PATH = "tasks.db"
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def get_tasks_db():
    conn = sqlite3.connect(TASKS_DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            chat_id TEXT UNIQUE NOT NULL,
            username TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            assignee_id INTEGER,
            due_date TEXT,
            priority TEXT,
            status TEXT DEFAULT 'ارسال‌شده',
            created_at TEXT,
            FOREIGN KEY(assignee_id) REFERENCES employees(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS telegram_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    return conn


def tg_call(method, **params):
    """Low-level call to the Telegram Bot API. Returns the parsed JSON response,
    or a dict with ok=False if the request itself failed (e.g. no internet, bad token)."""
    token = st.session_state.get("telegram_token")
    if not token:
        return {"ok": False, "description": "توکن ربات تنظیم نشده است."}
    try:
        r = requests.post(
            TELEGRAM_API.format(token=token, method=method),
            json={k: v for k, v in params.items() if v is not None},
            timeout=10,
        )
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


def tg_get_updates():
    """Long-poll-free fetch of new Telegram updates since the last processed offset."""
    conn = get_tasks_db()
    row = conn.execute("SELECT value FROM telegram_state WHERE key='offset'").fetchone()
    conn.close()
    offset = int(row[0]) + 1 if row else None
    result = tg_call("getUpdates", offset=offset, timeout=0)
    if not result or not result.get("ok"):
        return []
    updates = result.get("result", [])
    if updates:
        max_id = max(u["update_id"] for u in updates)
        conn = get_tasks_db()
        conn.execute("INSERT OR REPLACE INTO telegram_state (key, value) VALUES ('offset', ?)", (str(max_id),))
        conn.commit()
        conn.close()
    return updates


def tg_send_task_message(chat_id, task_id, title, description, due_date_val, priority):
    text = f"📌 تسک جدید: {title}\n"
    if description:
        text += f"📝 {description}\n"
    if due_date_val:
        text += f"📅 مهلت: {due_date_val}\n"
    text += f"⭐ اولویت: {priority}\n\nوقتی انجامش دادید، روی دکمه زیر بزنید 👇"
    reply_markup = {"inline_keyboard": [[{"text": "✅ انجام شد", "callback_data": f"done:{task_id}"}]]}
    return tg_call("sendMessage", chat_id=chat_id, text=text, reply_markup=reply_markup)


def tg_answer_callback(callback_query_id, text):
    return tg_call("answerCallbackQuery", callback_query_id=callback_query_id, text=text)


def add_employee(name, chat_id, username=None):
    conn = get_tasks_db()
    try:
        conn.execute(
            "INSERT INTO employees (name, chat_id, username) VALUES (?,?,?)",
            (name, str(chat_id), username),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def get_employees() -> pd.DataFrame:
    conn = get_tasks_db()
    df = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    return df


def get_registered_chat_ids() -> set:
    df = get_employees()
    return set(df["chat_id"].astype(str)) if not df.empty else set()


def add_task_and_notify(title, description, employee_row, due_date_val, priority):
    conn = get_tasks_db()
    cur = conn.execute(
        "INSERT INTO tasks (title, description, assignee_id, due_date, priority, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (
            title, description, int(employee_row["id"]),
            due_date_val.isoformat() if due_date_val else None,
            priority, "ارسال‌شده", datetime.now().isoformat(),
        ),
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    result = tg_send_task_message(
        employee_row["chat_id"], task_id, title, description, due_date_val, priority
    )
    return task_id, result


def get_tasks_with_employee() -> pd.DataFrame:
    conn = get_tasks_db()
    df = pd.read_sql_query("""
        SELECT tasks.id, tasks.title, tasks.description, tasks.due_date, tasks.priority, tasks.status,
               employees.name AS assignee, employees.chat_id AS assignee_chat_id
        FROM tasks LEFT JOIN employees ON tasks.assignee_id = employees.id
        ORDER BY tasks.id DESC
    """, conn)
    conn.close()
    return df


def process_telegram_updates():
    """Poll Telegram for new 'done' button presses and mark matching tasks complete.
    Verifies the chat_id that pressed the button actually matches the task's assignee,
    so one employee can't mark another's task as done."""
    updates = tg_get_updates()
    confirmed = []
    for u in updates:
        cq = u.get("callback_query")
        if not cq:
            continue
        data = cq.get("data", "")
        if not data.startswith("done:"):
            continue
        task_id = data.split(":", 1)[1]
        chat_id = str(cq["from"]["id"])
        conn = get_tasks_db()
        row = conn.execute("""
            SELECT tasks.id, employees.chat_id FROM tasks
            JOIN employees ON tasks.assignee_id = employees.id
            WHERE tasks.id = ?
        """, (task_id,)).fetchone()
        if row and str(row[1]) == chat_id:
            conn.execute("UPDATE tasks SET status='انجام‌شده' WHERE id=?", (task_id,))
            conn.commit()
            confirmed.append(task_id)
            tg_answer_callback(cq["id"], "✅ ثبت شد، ممنون!")
        else:
            tg_answer_callback(cq["id"], "⚠️ این تسک برای شما نیست.")
        conn.close()
    return confirmed


# ---------- Sidebar navigation ----------
with st.sidebar:
    st.markdown(f"<p style='font-family:Lalezar; font-size:22px; margin-bottom:2px;'>📊 مالی هوشمند</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; opacity:0.7; margin-top:0;'>دستیار مالی مبتنی بر هوش مصنوعی</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    nav_items = [
        ("داشبورد", "📊"),
        ("بارگذاری داده", "📁"),
        ("دستیار هوش مصنوعی", "🧠"),
        ("تسک‌های تلگرام", "🧑‍💼"),
        ("تنظیمات", "⚙️"),
    ]
    for name, icon in nav_items:
        btn_type = "primary" if st.session_state.active_tab == name else "secondary"
        if st.button(f"{icon}  {name}", use_container_width=True, type=btn_type, key=f"nav_{name}"):
            st.session_state.active_tab = name
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    status = "متصل" if st.session_state.api_key else "بدون کلید"
    dot = TEAL if st.session_state.api_key else BRICK
    st.markdown(f"<p style='font-size:12px;'><span style='color:{dot};'>●</span> وضعیت API: {status}</p>", unsafe_allow_html=True)


# ---------- Header ----------
st.markdown('<p class="hero-title">داشبورد هوشمند مالی</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">تحلیل داده مالی و مشاوره مدیریتی با هوش مصنوعی</p>', unsafe_allow_html=True)
st.markdown('<div class="tile-divider"></div>', unsafe_allow_html=True)

# ---------- TAB: settings ----------
if st.session_state.active_tab == "تنظیمات":
    section_label("⚙️ کلید API")
    st.write("کلید Gemini API خود را وارد کنید. این کلید فقط در حافظه این نشست ذخیره می‌شود و در دیسک یا گیت‌هاب ذخیره نمی‌شود.")
    key_input = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
    c1, c2 = st.columns(2)
    if c1.button("ذخیره کلید", type="primary", use_container_width=True):
        st.session_state.api_key = key_input
        st.success("کلید ذخیره شد.")
    if c2.button("تست اتصال", use_container_width=True):
        model = get_model()
        if not model:
            st.error("ابتدا کلید را وارد کنید.")
        else:
            try:
                r = model.generate_content("در یک کلمه بگو سلام")
                st.success(f"اتصال موفق بود. پاسخ نمونه: {r.text.strip()}")
            except Exception as e:
                st.error(f"اتصال ناموفق: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("🤖 توکن ربات تلگرام")
    st.write("توکن را از @BotFather در تلگرام بگیرید (دستور /newbot). این توکن هم فقط در حافظه این نشست می‌ماند.")
    tg_input = st.text_input("Telegram Bot Token", value=st.session_state.telegram_token, type="password")
    tc1, tc2 = st.columns(2)
    if tc1.button("ذخیره توکن", type="primary", use_container_width=True):
        st.session_state.telegram_token = tg_input
        st.success("توکن ذخیره شد.")
    if tc2.button("تست ربات", use_container_width=True):
        result = tg_call("getMe")
        if result and result.get("ok"):
            bot_name = result["result"].get("username", "؟")
            st.success(f"اتصال موفق بود. نام ربات: @{bot_name}")
        else:
            st.error(f"اتصال ناموفق: {result.get('description') if result else 'خطای نامشخص'}")

# ---------- TAB: data upload ----------
elif st.session_state.active_tab == "بارگذاری داده":
    section_label("📁 بارگذاری داده مالی")
    if not st.session_state.api_key:
        st.warning("برای پردازش هوشمند ستون‌ها، ابتدا کلید API را در تب تنظیمات وارد کنید.")

    uploaded_file = st.file_uploader("فایل اکسل یا CSV خود را آپلود کنید", type=["csv", "xlsx"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                raw_data = pd.read_csv(uploaded_file)
            else:
                raw_data = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"خطا در خواندن فایل: {e}")
            raw_data = None

        if raw_data is not None:
            st.session_state.raw_data = raw_data
            section_label("پیش‌نمایش داده خام")
            st.dataframe(raw_data.head(5), use_container_width=True)

            if st.button("پردازش داده با هوش مصنوعی", type="primary"):
                model = get_model()
                if not model:
                    st.error("ابتدا کلید API را در تب تنظیمات وارد کنید.")
                else:
                    structure = None
                    with st.spinner("در حال شناسایی ساختار داده..."):
                        try:
                            structure = detect_structure(model, raw_data)
                        except Exception as e:
                            st.error(f"خطا در تحلیل ساختار داده: {e}")

                    if structure:
                        try:
                            clean_data = build_clean_data(raw_data, structure)
                            st.session_state.clean_data = clean_data
                            st.session_state.column_mapping = structure
                            st.success("داده با موفقیت پردازش شد. اکنون به تب داشبورد بروید.")
                            with st.expander("جزئیات ساختار شناسایی‌شده توسط هوش مصنوعی"):
                                st.json(structure)
                        except Exception as e:
                            st.error(f"خطا در ساخت داده تمیز: {e}")

# ---------- TAB: dashboard ----------
elif st.session_state.active_tab == "داشبورد":
    clean_data = st.session_state.clean_data
    if clean_data is None:
        st.info("هنوز داده‌ای پردازش نشده است. لطفاً فایل خود را در بخش 'بارگذاری داده' آپلود و پردازش کنید.")
        if st.button("رفتن به بارگذاری داده", type="primary"):
            go_to("بارگذاری داده")
    else:
        total_income = clean_data["income"].sum()
        total_expense = clean_data["expense"].sum()
        total_profit = clean_data["profit"].sum()

        section_label("خلاصه وضعیت مالی")
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("کل درآمد", total_income, "💰", TEAL, index=0)
        with col2:
            metric_card("کل هزینه‌ها", total_expense, "🧾", BRICK, index=1)
        with col3:
            metric_card("سود خالص", total_profit, "📈", GOLD, index=2)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- نمودارهای حرفه‌ای با Plotly ---
        section_label("📊 تحلیل بصری داده‌ها")

        has_date = "date" in clean_data.columns
        has_categories = (
            "category" in clean_data.columns
            and clean_data["category"].notna().any()
            and clean_data["category"].nunique() > 1
        )

        if has_date:
            time_data = clean_data.groupby("date")[["income", "expense"]].sum().reset_index()
            fig_time = px.area(time_data, x="date", y=["income", "expense"],
                               labels={"value": "مبلغ", "date": "تاریخ", "variable": "نوع تراکنش"},
                               color_discrete_map={"income": TEAL, "expense": BRICK},
                               title="روند درآمد و هزینه در گذر زمان")
            fig_time.update_layout(font_family="Vazirmatn", title_x=0.5, legend_title_text="", hovermode="x unified")
            newnames = {'income': 'درآمد', 'expense': 'هزینه'}
            fig_time.for_each_trace(lambda t: t.update(name=newnames.get(t.name, t.name),
                                                       legendgroup=newnames.get(t.name, t.name),
                                                       hovertemplate=t.hovertemplate.replace(t.name, newnames.get(t.name, t.name))))
            st.plotly_chart(fig_time, use_container_width=True)

        if has_categories:
            breakdown = clean_data.groupby("category")[["income", "expense"]].sum()

            c1, c2 = st.columns(2)
            with c1:
                exp_data = breakdown[breakdown["expense"] > 0].reset_index()
                if not exp_data.empty:
                    fig_pie = px.pie(exp_data, values="expense", names="category", hole=0.4,
                                     title="ترکیب هزینه‌ها", color_discrete_sequence=px.colors.qualitative.Prism)
                    fig_pie.update_layout(font_family="Vazirmatn", title_x=0.5)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("هزینه‌ای برای نمایش ترکیب وجود ندارد.")

            with c2:
                breakdown_reset = breakdown.reset_index().sort_values("income", ascending=False)
                fig_bar = go.Figure(data=[
                    go.Bar(name='درآمد', x=breakdown_reset['category'], y=breakdown_reset['income'], marker_color=TEAL),
                    go.Bar(name='هزینه', x=breakdown_reset['category'], y=breakdown_reset['expense'], marker_color=BRICK)
                ])
                fig_bar.update_layout(barmode='group', title="مقایسه درآمد و هزینه به تفکیک دسته‌بندی",
                                      font_family="Vazirmatn", title_x=0.5, margin=dict(t=50))
                st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        section_label("✨ گزارش مدیریتی هوشمند")
        st.write("با کلیک روی دکمه زیر، هوش مصنوعی داده‌های شما را بررسی کرده و یک گزارش مدیریتی تمیز و طبقه‌بندی شده ارائه می‌دهد.")

        if st.button("تولید گزارش هوشمند وضعیت مالی", type="primary"):
            model = get_model()
            if not model:
                st.error("ابتدا کلید API را در تب تنظیمات وارد کنید.")
            else:
                with st.spinner("در حال استخراج الگوها و نگارش گزارش مدیریتی..."):
                    prompt = f"""
                    شما یک مشاور مالی ارشد و تحلیلگر داده هستید. وضعیت مالی زیر را بررسی کنید:
                    - مجموع درآمد: {total_income:,.0f}
                    - مجموع هزینه‌ها: {total_expense:,.0f}
                    - سود خالص: {total_profit:,.0f}

                    اگر دسته‌بندی‌هایی وجود دارد: (پرتکرارترین‌ها یا بیشترین مبالغ را مرور کن).

                    لطفاً یک گزارش فوق‌العاده تمیز، ساختاریافته و با لحن حرفه‌ای در زبان فارسی بنویس.
                    حتماً از فرمت Markdown استفاده کن.
                    بخش‌های الزامی گزارش:
                    ۱. **وضعیت کلی**: یک پاراگراف خلاصه از سلامت مالی.
                    ۲. **نقاط قوت**: بولت‌پوینت‌های کوتاه.
                    ۳. **نقاط ضعف یا هشدارها**: بولت‌پوینت‌های کوتاه.
                    ۴. **سه پیشنهاد عملیاتی**: برای افزایش سود.

                    از ایموجی‌های مناسب برای هر تیتر استفاده کن و متن را به گونه‌ای بنویس که در یک داشبورد بسیار شیک و خوانا به نظر برسد.
                    """
                    try:
                        response = model.generate_content(prompt)
                        st.markdown(f'<div class="ai-report-card">{response.text}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"خطا در تولید گزارش هوشمند: {e}")

# ---------- TAB: AI assistant (chat) ----------
elif st.session_state.active_tab == "دستیار هوش مصنوعی":
    section_label("🧠 گفتگوی آزاد با دستیار مالی")
    st.write("در اینجا می‌توانید هرگونه سوال دلخواهی را درباره وضعیت مالی خود از هوش مصنوعی بپرسید.")

    model = get_model()
    if not model:
        st.warning("ابتدا کلید API را در تب تنظیمات وارد کنید.")
    else:
        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🧠"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])

        user_msg = st.chat_input("سوال خود را درباره وضعیت مالی بپرسید...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.chat_message("user", avatar="🧑"):
                st.write(user_msg)

            context_note = ""
            if st.session_state.clean_data is not None:
                cd = st.session_state.clean_data
                context_note = (
                    f"\n(Context: total income {cd['income'].sum()}, "
                    f"total expense {cd['expense'].sum()}, "
                    f"total profit {cd['profit'].sum()}.)"
                )

            history_for_api = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in st.session_state.chat_history[:-1]
            ]

            with st.chat_message("assistant", avatar="🧠"):
                with st.spinner("در حال پردازش..."):
                    try:
                        chat = model.start_chat(history=history_for_api)
                        response = chat.send_message(
                            "Answer in Persian, as a financial advisor. " + user_msg + context_note
                        )
                        st.write(response.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"خطا: {e}")

# ---------- TAB: Telegram tasks ----------
elif st.session_state.active_tab == "تسک‌های تلگرام":
    section_label("🧑‍💼 مدیریت تسک از طریق تلگرام")

    if not st.session_state.telegram_token:
        st.warning("ابتدا توکن ربات تلگرام را در تب تنظیمات وارد و تست کنید.")
    else:
        section_label("۱. ثبت کارکنان جدید")
        st.caption(
            "هر کارمند باید اول در تلگرام به ربات شما پیام بدهد (مثلا /start)، سپس اینجا نمایش داده "
            "می‌شود تا اسمش را ثبت کنید. طبق قوانین تلگرام، ربات نمی‌تواند بدون این مرحله شروع‌کننده مکالمه باشد."
        )
        if st.button("بررسی پیام‌های جدید از تلگرام"):
            with st.spinner("در حال دریافت پیام‌ها..."):
                updates = tg_get_updates()
            registered = get_registered_chat_ids()
            new_senders = {}
            for u in updates:
                msg = u.get("message")
                if msg and "from" in msg:
                    cid = str(msg["from"]["id"])
                    if cid not in registered:
                        new_senders[cid] = {
                            "name": msg["from"].get("first_name", ""),
                            "username": msg["from"].get("username", ""),
                        }
            st.session_state.new_telegram_senders.update(new_senders)
            if not new_senders:
                st.info("پیام جدیدی از کارمند ثبت‌نشده‌ای یافت نشد.")

        for cid, info in list(st.session_state.new_telegram_senders.items()):
            with st.container(border=True):
                cols = st.columns([2, 2, 1])
                name_input = cols[0].text_input(f"اسم کارمند (chat_id: {cid})", value=info["name"], key=f"name_{cid}")
                cols[1].write(f"یوزرنیم: @{info['username']}" if info["username"] else "یوزرنیم ندارد")
                if cols[2].button("ثبت", key=f"reg_{cid}"):
                    add_employee(name_input, cid, info["username"])
                    st.success(f"{name_input} ثبت شد.")
                    del st.session_state.new_telegram_senders[cid]
                    st.rerun()

        employees_df = get_employees()
        if not employees_df.empty:
            st.caption("کارکنان ثبت‌شده:")
            st.dataframe(employees_df[["name", "username"]], use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section_label("۲. ایجاد تسک جدید")
        if employees_df.empty:
            st.info("ابتدا حداقل یک کارمند ثبت کنید.")
        else:
            with st.form("telegram_task_form", clear_on_submit=True):
                title = st.text_input("عنوان تسک")
                description = st.text_area("توضیحات", height=80)
                assignee_name = st.selectbox("کارمند مسئول", employees_df["name"].tolist())
                fc1, fc2 = st.columns(2)
                due_date_val = fc1.date_input("مهلت انجام", value=None)
                priority = fc2.selectbox("اولویت", ["پایین", "متوسط", "بالا"], index=1)
                submitted = st.form_submit_button("ارسال تسک در تلگرام", type="primary")
                if submitted:
                    if not title.strip():
                        st.error("عنوان تسک الزامی است.")
                    else:
                        employee_row = employees_df[employees_df["name"] == assignee_name].iloc[0]
                        task_id, result = add_task_and_notify(
                            title.strip(), description.strip(), employee_row, due_date_val, priority
                        )
                        if result and result.get("ok"):
                            st.success(f"تسک برای {assignee_name} در تلگرام ارسال شد.")
                        else:
                            st.error(f"تسک ثبت شد ولی ارسال تلگرام ناموفق بود: {result}")
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        section_label("۳. بررسی تاییدیه‌ها")
        st.caption("چون این یک اپ Streamlit ساده است نه یک سرور همیشه‌روشن، تاییدیه‌ها فوری نیستند — هر بار این دکمه را بزنید یا صفحه را باز کنید بررسی می‌شود.")
        if st.button("بررسی تاییدیه‌های جدید از تلگرام"):
            with st.spinner("در حال بررسی..."):
                confirmed = process_telegram_updates()
            if confirmed:
                st.success(f"{len(confirmed)} تسک به‌عنوان انجام‌شده ثبت شد.")
            else:
                st.info("تاییدیه جدیدی یافت نشد.")

        st.markdown("<br>", unsafe_allow_html=True)
        section_label("لیست تسک‌ها")
        tasks_df = get_tasks_with_employee()
        if tasks_df.empty:
            st.info("هنوز تسکی ثبت نشده است.")
        else:
            st.dataframe(
                tasks_df[["title", "assignee", "due_date", "priority", "status"]],
                use_container_width=True, hide_index=True
            )
