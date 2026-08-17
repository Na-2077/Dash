import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import re
import sqlite3
from datetime import date, datetime
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent

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
    """Parses messy real-world numbers: Persian/Arabic digits, currency symbols,
    thousands separators (، ٬ , space), and parentheses meaning negative."""
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
    "active_tab": "داشبورد",
    "raw_data": None,
    "clean_data": None,
    "column_mapping": None,
    "chat_history": [],
    "pending_auto_analysis": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def get_model():
    if not st.session_state.api_key:
        return None
    genai.configure(api_key=st.session_state.api_key)
    return genai.GenerativeModel("gemini-3.5-flash-lite")


# ---------- Finance agent: real tools instead of guessed numbers ----------
@tool
def get_financial_summary() -> str:
    """خلاصه کلی وضعیت مالی شامل کل درآمد، کل هزینه و سود خالص را برمی‌گرداند."""
    cd = st.session_state.get("clean_data")
    if cd is None:
        return "هنوز داده مالی بارگذاری نشده است."
    return (
        f"کل درآمد: {cd['income'].sum():,.0f}\n"
        f"کل هزینه: {cd['expense'].sum():,.0f}\n"
        f"سود خالص: {cd['profit'].sum():,.0f}"
    )


@tool
def get_profit_loss_by_item() -> str:
    """گزارش سود و زیان را به تفکیک هر آیتم یا دسته‌بندی مالی (در صورت وجود در فایل) برمی‌گرداند."""
    cd = st.session_state.get("clean_data")
    if cd is None:
        return "هنوز داده مالی بارگذاری نشده است."
    if "category" not in cd.columns or cd["category"].isna().all():
        return "داده‌ای برای تفکیک بر اساس آیتم موجود نیست؛ فقط جمع کل درآمد و هزینه در دسترس است."
    g = cd.groupby("category")[["income", "expense"]].sum()
    g["سود"] = g["income"] - g["expense"]
    g = g.sort_values("سود", ascending=False)
    return g.to_string()


@tool
def get_sales_trend() -> str:
    """روند فروش (درآمد) را به تفکیک تاریخ برمی‌گرداند تا رشد یا افت فروش در طول زمان بررسی شود."""
    cd = st.session_state.get("clean_data")
    if cd is None:
        return "هنوز داده مالی بارگذاری نشده است."
    if "date" not in cd.columns or cd["date"].isna().all():
        return "اطلاعات تاریخ در داده موجود نیست."
    trend = cd.groupby(cd["date"].dt.date)["income"].sum()
    return trend.to_string()


FINANCE_SYSTEM_PROMPT = """
شما یک دستیار مدیریت مالی هوشمند برای یک مدیر کسب‌وکار فارسی‌زبان هستید.
همیشه به زبان فارسی و به‌صورت حرفه‌ای پاسخ بده.

هر وقت برای پاسخ به عدد یا آمار واقعی نیاز داری (کل درآمد، کل هزینه، سود خالص، تفکیک سود و زیان
بر اساس آیتم، یا روند فروش در طول زمان)، حتما از ابزارهای موجود استفاده کن و هرگز عدد را حدس نزن
یا از خودت نساز.

اگر کاربر خواست پیشنهاد بازاریابی یا محتوای تبلیغاتی با ذهنیت و سبک یک فرد مشخص ارائه بدهی
(مثلا David Ogilvy، Conrad Gessner یا هر متخصص دیگر)، ابتدا با ابزارها زمینه و اعداد واقعی مالی
را به‌دست بیاور، سپس پاسخ نهایی را دقیقا با سبک نوشتاری، لحن و طرز فکر همان شخص بنویس - نه فقط
اسم او را ذکر کن.
"""


def get_finance_agent():
    if not st.session_state.api_key:
        return None
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=st.session_state.api_key,
        temperature=0.4,
    )
    tools = [get_financial_summary, get_profit_loss_by_item, get_sales_trend]
    return create_agent(model, tools=tools, system_prompt=FINANCE_SYSTEM_PROMPT)


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
    """Ask the AI to inspect headers AND a few sample rows, then classify the
    file into one of three common financial-spreadsheet shapes."""
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


def resolve_column(df: pd.DataFrame, name):
    """Matches an AI-returned column name to the real dataframe column, even if
    it differs by whitespace, case, or Persian/Arabic Yeh-Kaf variants."""
    if name is None:
        return None
    name = str(name)
    if name in df.columns:
        return name

    def normalize(s):
        s = str(s).strip()
        s = s.replace("ي", "ی").replace("ك", "ک")
        s = re.sub(r"\s+", " ", s)
        return s.lower()

    target = normalize(name)
    for col in df.columns:
        if normalize(col) == target:
            return col

    raise KeyError(f"ستون «{name}» در فایل پیدا نشد.")


def build_clean_data(raw_data: pd.DataFrame, structure: dict) -> pd.DataFrame:
    """Turns raw_data into a dataframe with income/expense/profit columns,
    based on whichever structure the AI detected."""
    df = raw_data.copy()
    kind = structure.get("structure")
    date_col = resolve_column(df, structure.get("date_column"))

    if kind == "separate_columns":
        income_col = resolve_column(df, structure["income_column"])
        expense_col = resolve_column(df, structure["expense_column"])
        df["income"] = df[income_col].apply(clean_number)
        df["expense"] = df[expense_col].apply(clean_number).abs()

    elif kind == "single_amount":
        amount_col = resolve_column(df, structure["amount_column"])
        convention = structure.get("sign_convention", "positive_is_income")
        amounts = df[amount_col].apply(clean_number)
        if convention == "positive_is_income":
            df["income"] = amounts.clip(lower=0)
            df["expense"] = (-amounts.clip(upper=0))
        else:
            df["income"] = (-amounts.clip(upper=0))
            df["expense"] = amounts.clip(lower=0)

    elif kind == "amount_with_type":
        amount_col = resolve_column(df, structure["amount_column"])
        type_col = resolve_column(df, structure["type_column"])
        income_values = set(str(v).strip().lower() for v in structure.get("income_values", []))
        expense_values = set(str(v).strip().lower() for v in structure.get("expense_values", []))
        amounts = df[amount_col].apply(clean_number).abs()
        types = df[type_col].astype(str).str.strip().str.lower()
        df["income"] = amounts.where(types.isin(income_values), 0.0)
        df["expense"] = amounts.where(types.isin(expense_values), 0.0)

    else:
        raise ValueError("ساختار شناسایی‌شده پشتیبانی نمی‌شود.")

    df["profit"] = df["income"] - df["expense"]

    category_col = None
    try:
        category_col = resolve_column(df, structure.get("category_column"))
    except KeyError:
        category_col = None
    if category_col:
        df["category"] = df[category_col].astype(str).str.strip()
    elif kind == "amount_with_type":
        # No separate category column, but the type column itself often carries
        # the itemized label (e.g. "حقوق", "اجاره"), so fall back to it.
        df["category"] = df[structure["type_column"]].astype(str).str.strip()
    else:
        df["category"] = None

    if date_col and date_col in df.columns:
        df = df.rename(columns={date_col: "date"})
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")

    return df


# ---------- HR: task management (SQLite-backed, survives restarts) ----------
TASKS_DB_PATH = "tasks.db"


def get_tasks_db():
    conn = sqlite3.connect(TASKS_DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assignee TEXT,
            description TEXT,
            due_date TEXT,
            priority TEXT,
            status TEXT DEFAULT 'در حال انجام',
            created_at TEXT
        )
    """)
    return conn


def add_task(title, assignee, description, due_date_val, priority):
    conn = get_tasks_db()
    conn.execute(
        "INSERT INTO tasks (title, assignee, description, due_date, priority, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (
            title, assignee, description,
            due_date_val.isoformat() if due_date_val else None,
            priority, "در حال انجام", datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_tasks(status_filter=None) -> pd.DataFrame:
    conn = get_tasks_db()
    query = "SELECT id, title, assignee, description, due_date, priority, status FROM tasks"
    params = ()
    if status_filter and status_filter != "همه":
        query += " WHERE status = ?"
        params = (status_filter,)
    query += " ORDER BY due_date IS NULL, due_date ASC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def update_task_status(task_id, new_status):
    conn = get_tasks_db()
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_tasks_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_due_soon_tasks(days_ahead: int = 3) -> pd.DataFrame:
    """Tasks that are overdue or due within `days_ahead` days, excluding completed ones."""
    df = get_tasks()
    if df.empty:
        return df
    df = df[df["status"] != "انجام‌شده"].copy()
    df["due_date_parsed"] = pd.to_datetime(df["due_date"], errors="coerce")
    today = pd.Timestamp(date.today())
    df["روز باقیمانده"] = (df["due_date_parsed"] - today).dt.days
    return df[df["روز باقیمانده"] <= days_ahead].sort_values("روز باقیمانده")


def generate_reminder_message(task_row) -> str:
    """Uses the plain Gemini model (not the agent) to draft a short, friendly
    Persian reminder message for one task."""
    model = get_model()
    if not model:
        return "ابتدا کلید API را در تب تنظیمات وارد کنید."
    due = task_row.get("due_date") or "نامشخص"
    prompt = f"""
    یک پیام یادآوری کوتاه، محترمانه و حرفه‌ای به زبان فارسی برای یک همکار بنویس.
    عنوان تسک: {task_row.get('title')}
    مسئول تسک: {task_row.get('assignee') or 'نامشخص'}
    مهلت انجام: {due}
    اولویت: {task_row.get('priority') or 'نامشخص'}
    پیام باید کوتاه (حداکثر ۴-۵ خط)، مودبانه و مستقیم باشد و لحن دستوری تند نداشته باشد.
    فقط متن پیام را بنویس، بدون توضیح اضافه.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"خطا در تولید پیام: {e}"


# ---------- Sidebar navigation ----------
with st.sidebar:
    st.markdown(f"<p style='font-family:Lalezar; font-size:22px; margin-bottom:2px;'>📊 مالی هوشمند</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; opacity:0.7; margin-top:0;'>دستیار مالی مبتنی بر هوش مصنوعی</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    nav_items = [
        ("داشبورد", "📊"),
        ("بارگذاری داده", "📁"),
        ("دستیار هوش مصنوعی", "🧠"),
        ("منابع انسانی", "👥"),
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
        st.info("هنوز داده‌ای پردازش نشده است.")
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

        section_label("روند درآمد و هزینه")
        if "date" in clean_data.columns:
            chart_data = clean_data.set_index("date")[["income", "expense"]]
        else:
            chart_data = clean_data[["income", "expense"]]
        chart_data = chart_data.rename(columns={"income": "درآمد", "expense": "هزینه"})
        st.bar_chart(chart_data, color=[TEAL, BRICK])

        has_categories = (
            "category" in clean_data.columns
            and clean_data["category"].notna().any()
            and clean_data["category"].nunique() > 1
        )
        if has_categories:
            section_label("جزئیات آیتم‌ها")
            breakdown = (
                clean_data.groupby("category")[["income", "expense"]]
                .sum()
                .assign(تعداد=clean_data.groupby("category").size())
                .rename(columns={"income": "درآمد", "expense": "هزینه"})
                .sort_values("درآمد", ascending=False)
            )
            st.dataframe(breakdown, use_container_width=True)
            st.bar_chart(breakdown[["درآمد", "هزینه"]], color=[TEAL, BRICK])

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🧠 تحلیل با هوش مصنوعی", type="primary"):
            go_to("دستیار هوش مصنوعی", pending_auto_analysis=True)

# ---------- TAB: AI assistant (chat) ----------
elif st.session_state.active_tab == "دستیار هوش مصنوعی":
    section_label("🧠 دستیار هوش مصنوعی")

    agent = get_finance_agent()
    if not agent:
        st.warning("ابتدا کلید API را در تب تنظیمات وارد کنید.")
    else:
        if st.session_state.pending_auto_analysis and st.session_state.clean_data is not None:
            st.session_state.pending_auto_analysis = False
            user_prompt = "لطفا وضعیت مالی من را تحلیل کن، نقاط قوت و نگرانی‌ها را بگو و ۳ پیشنهاد عملی بده."
            with st.spinner("در حال تولید تحلیل اولیه..."):
                try:
                    result = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
                    reply = result["messages"][-1].content
                    st.session_state.chat_history.append({"role": "user", "content": "لطفا وضعیت مالی من را تحلیل کن."})
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"خطا در تولید تحلیل: {e}")

        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🧠"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])

        user_msg = st.chat_input("سوال خود را درباره وضعیت مالی بپرسید...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.chat_message("user", avatar="🧑"):
                st.write(user_msg)

            messages_for_agent = [
                {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
                for m in st.session_state.chat_history
            ]

            with st.chat_message("assistant", avatar="🧠"):
                with st.spinner("در حال فکر کردن..."):
                    try:
                        result = agent.invoke({"messages": messages_for_agent})
                        reply = result["messages"][-1].content
                        st.write(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"خطا: {e}")

# ---------- TAB: HR / task management ----------
elif st.session_state.active_tab == "منابع انسانی":
    section_label("👥 منابع انسانی — تسک‌ها و یادآوری")

    due_soon = get_due_soon_tasks(days_ahead=3)
    if not due_soon.empty:
        overdue = due_soon[due_soon["روز باقیمانده"] < 0]
        upcoming = due_soon[due_soon["روز باقیمانده"] >= 0]
        if not overdue.empty:
            names = "، ".join(overdue["title"].tolist())
            st.error(f"⏰ {len(overdue)} تسک از سررسید گذشته: {names}")
        if not upcoming.empty:
            names = "، ".join(upcoming["title"].tolist())
            st.warning(f"🔔 {len(upcoming)} تسک تا ۳ روز آینده سررسید دارد: {names}")

    section_label("افزودن تسک جدید")
    with st.form("add_task_form", clear_on_submit=True):
        fc1, fc2 = st.columns(2)
        title = fc1.text_input("عنوان تسک")
        assignee = fc2.text_input("مسئول تسک")
        description = st.text_area("توضیحات (اختیاری)", height=80)
        fc3, fc4 = st.columns(2)
        due_date_val = fc3.date_input("مهلت انجام", value=None)
        priority = fc4.selectbox("اولویت", ["پایین", "متوسط", "بالا"], index=1)
        submitted = st.form_submit_button("افزودن تسک", type="primary")
        if submitted:
            if not title.strip():
                st.error("عنوان تسک الزامی است.")
            else:
                add_task(title.strip(), assignee.strip(), description.strip(), due_date_val, priority)
                st.success("تسک اضافه شد.")
                st.rerun()

    section_label("لیست تسک‌ها")
    status_choice = st.selectbox("فیلتر وضعیت", ["همه", "در حال انجام", "انجام‌شده"], key="task_status_filter")
    tasks_df = get_tasks(status_choice)

    if tasks_df.empty:
        st.info("هنوز تسکی ثبت نشده است.")
    else:
        for _, row in tasks_df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{row['title']}**")
                    meta = []
                    if row["assignee"]:
                        meta.append(f"مسئول: {row['assignee']}")
                    if row["due_date"]:
                        meta.append(f"مهلت: {row['due_date']}")
                    meta.append(f"اولویت: {row['priority']}")
                    meta.append(f"وضعیت: {row['status']}")
                    st.caption(" | ".join(meta))
                    if row["description"]:
                        st.write(row["description"])
                with c2:
                    if row["status"] != "انجام‌شده":
                        if st.button("✅ تکمیل شد", key=f"done_{row['id']}", use_container_width=True):
                            update_task_status(row["id"], "انجام‌شده")
                            st.rerun()
                    else:
                        if st.button("↩️ بازگردانی", key=f"undo_{row['id']}", use_container_width=True):
                            update_task_status(row["id"], "در حال انجام")
                            st.rerun()
                    if st.button("🗑️ حذف", key=f"del_{row['id']}", use_container_width=True):
                        delete_task(row["id"])
                        st.rerun()
                with c3:
                    if st.button("✉️ متن یادآوری", key=f"remind_{row['id']}", use_container_width=True):
                        with st.spinner("در حال نوشتن پیام..."):
                            msg = generate_reminder_message(row)
                        st.text_area("پیام آماده (کپی کنید)", value=msg, height=120, key=f"msg_{row['id']}")
