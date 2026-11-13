# Financial Dashboard

An interactive [Streamlit](https://streamlit.io/) dashboard for exploring financial data, visualizing income and expenses, and generating management reports with Google Gemini.

> **Note:** The application interface is currently in Persian, while this document is maintained in English.

## Features

- Upload financial data as CSV or Excel (`.xlsx`).
- Automatically map source columns to date, income, and expense fields with Gemini.
- Review cleaned data before analysis.
- Explore financial metrics and interactive Plotly charts.
- Generate an AI-assisted financial status report.
- Ask questions about the uploaded data through the dashboard assistant.
- Keep the Gemini API key in the current Streamlit session instead of writing it to the repository.

## Requirements

- Python 3.9 or newer
- A [Google Gemini API key](https://ai.google.dev/)

## Quick start

### 1. Create a virtual environment

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the dashboard

```bash
streamlit run dashboard.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## Using the dashboard

1. Open the **Settings** section and enter your Gemini API key.
2. Open the data upload section and upload a CSV or Excel file.
3. Let the application detect and map the date, income, and expense columns.
4. Review the processed data.
5. Open the dashboard or AI assistant to analyze the results and generate a report.

## Input data

The included `d.csv` file is a small sample dataset with these columns:

| Column | Description |
| --- | --- |
| `تاریخ` | Transaction or reporting date |
| `درآمد` | Income |
| `هزینه` | Expense |

Uploaded files should contain columns that can be mapped to a date, income, and expense value. CSV and Excel files with different column names can be used when Gemini can identify their meaning.

## Gemini API configuration

The key can be entered from the dashboard settings. For local Streamlit configuration, it can also be provided through `st.secrets`:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your-api-key"
```

Never commit `secrets.toml`, API keys, or other credentials to Git. The application does not write the key to disk when it is entered through the UI.

## Project structure

```text
.
├── dashboard.py      # Streamlit application
├── d.csv             # Sample financial data
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```

## Development

To update the application, edit `dashboard.py`, then restart Streamlit:

```bash
streamlit run dashboard.py
```

Keep sample data small and anonymized. Do not use production financial records or real credentials in the repository.

## License

No license has been specified for this repository yet.
