import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from . import config


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)


def save_many(events):
    """Salva uma lista de eventos no Google Sheets. Cria planilha/aba se não existir."""
    if not events:
        return

    try:
        client = get_client()
        sheet = client.open(config.GOOGLE_SHEET).worksheet(config.WORKSHEET)
    except Exception:
        try:
            client = get_client()
            try:
                spreadsheet = client.open(config.GOOGLE_SHEET)
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create(config.GOOGLE_SHEET)

            try:
                sheet = spreadsheet.worksheet(config.WORKSHEET)
            except gspread.WorksheetNotFound:
                sheet = spreadsheet.add_worksheet(title=config.WORKSHEET, rows=1000, cols=20)
                # Cabeçalho
                sheet.append_row([
                    "timestamp", "event_id", "session_id", "user_id",
                    "operation_id", "page", "module", "event", "action",
                    "duration_ms", "company_name", "company_sector", "completion_pct",
                    "ai_used", "metadata"
                ])
        except Exception:
            raise

    rows = []
    for e in events:
        rows.append([
            e.timestamp,
            e.event_id,
            e.session_id,
            e.user_id,
            e.operation_id,
            e.page,
            e.module,
            e.event,
            e.action,
            e.duration_ms,
            e.company_name,
            e.company_sector,
            e.completion_pct,
            e.ai_used,
            str(e.metadata)
        ])

    if rows:
        sheet.append_rows(rows, value_input_option="USER_ENTERED")
