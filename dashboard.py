import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re

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
    transition: background 0.15s ease;
}}
[data-testid="stSidebar"] .stButton>button:hover {{ background: rgba(255,255,255,0.08); }}
[data-testid="stSidebar"] .stButton>button[kind="primary"] {{
    background: {TEAL}; border-color: {TEAL};
}}

.hero-title {{
    font-family: 'Lalezar', sans-serif; font-size: 34px; color: {INK};
    margin: 0; letter-spacing: 0.5px;
}}
.hero-sub {{ color: {INK_SOFT}; font-size: 14px; margin: 4px 0 0; }}

.tile-divider {{
    height: 6px; border-radius: 3px; margin: 14px 0 26px;
    background: repeating-linear-gradient(-45deg, {TEAL} 0 10px, {GOLD} 10px 20px);
    opacity: 0.85;
}}

.metric-card {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
    padding: 1.1rem 1.3rem; border-right: 4px solid var(--accent, {TEAL});
    animation: riseIn 0.35s ease both;
}}
.metric-label {{ font-size: 13px; color: {INK_SOFT}; margin: 0 0 6px; display: flex; gap: 6px; align-items: center; }}
.metric-value {{
    font-size: 26px; font-weight: 700; color: {INK}; margin: 0;
    font-variant-numeric: tabular-nums;
}}
@keyframes riseIn {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@media (prefers-reduced-motion: reduce) {{ .metric-card {{ animation: none; }} }}

.section-label {{
    font-size: 13px; color: {INK_SOFT}; font-weight: 600; margin: 22px 0 10px;
    display: flex; align-items: center; gap: 8px;
}}
.section-label::after {{ content: ""; flex: 1; height: 1px; background: {BORDER}; }}

.stButton>button {{
    border-radius: 10px; font-weight: 500; border: 1px solid {BORDER};
}}
.stButton>button[kind="primary"] {{
    background: {TEAL}; border-color: {TEAL}; color: white;
}}
.stButton>button[kind="primary"]:hover {{ background: {TEAL_DARK}; border-color: {TEAL_DARK}; }}

[data-testid="stChatMessage"] {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
    padding: 4px 6px; margin-bottom: 10px;
}}

[data-testid="stFileUploaderDropzone"] {{
    background: {CARD}; border: 1.5px dashed {TEAL}; border-radius: 12px;
}}

.stTextInput>div>div>input, .stChatInput textarea {{
    border-radius: 10px !important;
}}

hr {{ border-color: {BORDER}; }}
</style>
""", unsafe_allow_html=True)


def metric_card(label, value, icon, accent):
    st.markdown(f"""
    <div class="metric-card" style="--accent: {accent};">
        <p class="metric-label">{icon} {label}</p>
        <p class="metric-value">{value:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)


def section_label(text):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


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


# ---------- Sidebar navigation ----------
with st.sidebar:
    st.markdown(f"<p style='font-family:Lalezar; font-size:22px; margin-bottom:2px;'>📊 مالی هوشمند</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; opacity:0.7; margin-top:0;'>دستیار مالی مبتنی بر هوش مصنوعی</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    nav_items = [
        ("داشبورد", "📊"),
        ("بارگذاری داده", "📁"),
        ("دستیار هوش مصنوعی", "🧠"),
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
                    with st.spinner("در حال یکسان‌سازی ستون‌ها..."):
                        mapping = None
                        try:
                            columns = list(raw_data.columns)
                            prompt = f"""
                            Look at these column headers from a user's financial file: {columns}.
                            They might be in English, Persian, or any language.
                            Map them to these standard keys: 'date', 'income', 'expense'.
                            Only include a key if you find a clearly matching column.
                            Return ONLY a valid JSON object mapping the original column names to the standard keys.
                            """
                            response = model.generate_content(prompt)
                            mapping = extract_json(response.text)
                        except Exception as e:
                            st.error(f"خطا در تحلیل ستون‌ها: {e}")

                    if mapping:
                        missing = [k for k in ("income", "expense") if k not in mapping.values()]
                        if missing:
                            st.error("این ستون‌ها شناسایی نشدند: " + "، ".join(missing))
                        else:
                            clean_data = raw_data.rename(columns=mapping)
                            clean_data["income"] = pd.to_numeric(clean_data["income"], errors="coerce").fillna(0)
                            clean_data["expense"] = pd.to_numeric(clean_data["expense"], errors="coerce").fillna(0)
                            clean_data["profit"] = clean_data["income"] - clean_data["expense"]
                            if "date" in clean_data.columns:
                                clean_data["date"] = pd.to_datetime(clean_data["date"], errors="coerce")
                                clean_data = clean_data.sort_values("date")
                            st.session_state.clean_data = clean_data
                            st.session_state.column_mapping = mapping
                            st.success("داده با موفقیت پردازش شد. اکنون به تب داشبورد بروید.")
                            st.json(mapping)

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
            metric_card("کل درآمد", total_income, "💰", TEAL)
        with col2:
            metric_card("کل هزینه‌ها", total_expense, "🧾", BRICK)
        with col3:
            metric_card("سود خالص", total_profit, "📈", GOLD)

        section_label("روند درآمد و هزینه")
        if "date" in clean_data.columns:
            chart_data = clean_data.set_index("date")[["income", "expense"]]
        else:
            chart_data = clean_data[["income", "expense"]]
        st.bar_chart(chart_data, color=[TEAL, BRICK])

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🧠 تحلیل با هوش مصنوعی", type="primary"):
            go_to("دستیار هوش مصنوعی", pending_auto_analysis=True)

# ---------- TAB: AI assistant (chat) ----------
elif st.session_state.active_tab == "دستیار هوش مصنوعی":
    section_label("🧠 دستیار هوش مصنوعی")

    model = get_model()
    if not model:
        st.warning("ابتدا کلید API را در تب تنظیمات وارد کنید.")
    else:
        if st.session_state.pending_auto_analysis and st.session_state.clean_data is not None:
            st.session_state.pending_auto_analysis = False
            cd = st.session_state.clean_data
            total_income = cd["income"].sum()
            total_expense = cd["expense"].sum()
            total_profit = cd["profit"].sum()
            with st.spinner("در حال تولید تحلیل اولیه..."):
                prompt = f"""
                You are an expert financial advisor. Review this financial summary:
                Total Income: {total_income}
                Total Expenses: {total_expense}
                Net Profit: {total_profit}

                Write a short, professional analysis in Persian (فارسی).
                Highlight any concerns, praise good margins, and give 3 actionable tips
                for the manager to improve profitability based on these numbers.
                """
                try:
                    response = model.generate_content(prompt)
                    st.session_state.chat_history.append({"role": "user", "content": "لطفا وضعیت مالی من را تحلیل کن."})
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
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
                with st.spinner("در حال فکر کردن..."):
                    try:
                        chat = model.start_chat(history=history_for_api)
                        response = chat.send_message(
                            "Answer in Persian, as a financial advisor. " + user_msg + context_note
                        )
                        st.write(response.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"خطا: {e}")
