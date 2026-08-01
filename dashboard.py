import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re

# ---- Config ----
# Never hardcode API keys. Put GEMINI_API_KEY in .streamlit/secrets.toml
# or as an environment variable.
API_KEY = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None
if not API_KEY:
    st.error("کلید API جیمینای تنظیم نشده است. آن را در secrets.toml قرار دهید.")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="داشبورد هوشمند مالی", layout="wide")

st.markdown("""
<style>
    * { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("📊 داشبورد هوشمند مالی با هوش مصنوعی")


def extract_json(text: str) -> dict:
    """Pull the first {...} block out of a model response, tolerant of
    markdown fences or extra commentary around the JSON."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("پاسخ هوش مصنوعی شامل JSON معتبر نبود.")
    return json.loads(match.group(0))


@st.cache_data(show_spinner=False)
def get_column_mapping(columns: list) -> dict:
    prompt = f"""
    Look at these column headers from a user's financial file: {columns}.
    They might be in English, Persian, or any language.
    Map them to these standard keys: 'date', 'income', 'expense'.
    Only include a key if you find a clearly matching column.
    Return ONLY a valid JSON object mapping the original column names to the standard keys.
    """
    response = model.generate_content(prompt)
    return extract_json(response.text)


@st.cache_data(show_spinner=False)
def get_analysis(total_income: float, total_expense: float, total_profit: float) -> str:
    prompt = f"""
    You are an expert financial advisor. Review this financial summary:
    Total Income: {total_income}
    Total Expenses: {total_expense}
    Net Profit: {total_profit}

    Write a short, professional analysis in Persian (فارسی).
    Highlight any concerns, praise good margins, and give 3 actionable tips
    for the manager to improve profitability based on these numbers.
    """
    response = model.generate_content(prompt)
    return response.text


uploaded_file = st.file_uploader("فایل اکسل یا CSV خود را آپلود کنید", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            raw_data = pd.read_csv(uploaded_file)
        else:
            raw_data = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"خطا در خواندن فایل: {e}")
        st.stop()

    if raw_data.empty:
        st.warning("فایل آپلود شده خالی است.")
        st.stop()

    st.write("داده‌های خام:", raw_data.head(3))

    with st.spinner("هوش مصنوعی در حال پردازش و یکسان‌سازی داده‌ها..."):
        try:
            column_mapping = get_column_mapping(list(raw_data.columns))
        except Exception as e:
            st.error(f"خطا در تحلیل ستون‌ها توسط هوش مصنوعی: {e}")
            st.stop()

        missing = [k for k in ('income', 'expense') if k not in column_mapping.values()]
        if missing:
            st.error(
                "هوش مصنوعی نتوانست این ستون‌ها را شناسایی کند: "
                + "، ".join(missing)
                + ". لطفاً نام ستون‌ها را بررسی کنید."
            )
            st.stop()

        clean_data = raw_data.rename(columns=column_mapping)
        clean_data['income'] = pd.to_numeric(clean_data['income'], errors='coerce').fillna(0)
        clean_data['expense'] = pd.to_numeric(clean_data['expense'], errors='coerce').fillna(0)
        clean_data['profit'] = clean_data['income'] - clean_data['expense']

        if 'date' in clean_data.columns:
            clean_data['date'] = pd.to_datetime(clean_data['date'], errors='coerce')
            clean_data = clean_data.sort_values('date')
            chart_data = clean_data.set_index('date')[['income', 'expense']]
        else:
            chart_data = clean_data[['income', 'expense']]

    st.markdown("### 📈 خلاصه وضعیت مالی")

    total_income = clean_data['income'].sum()
    total_expense = clean_data['expense'].sum()
    total_profit = clean_data['profit'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("کل درآمد", f"{total_income:,.0f}")
    col2.metric("کل هزینه‌ها", f"{total_expense:,.0f}")
    col3.metric("سود خالص", f"{total_profit:,.0f}")

    st.bar_chart(chart_data)

    st.markdown("### 🧠 تحلیل هوش مصنوعی برای مدیریت بهتر")
    with st.spinner("در حال تولید تحلیل‌های مدیریتی..."):
        try:
            analysis = get_analysis(total_income, total_expense, total_profit)
            st.info(analysis)
        except Exception as e:
            st.error(f"خطا در تولید تحلیل: {e}")
