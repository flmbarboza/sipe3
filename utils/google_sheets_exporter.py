# utils/google_sheets_exporter.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

class GoogleSheetsExporter:
    def __init__(self, sheet_name="UX_Analytics"):
        self.sheet_name = sheet_name
        
        # Pega credenciais do Streamlit secrets
        self.creds = self._get_credentials()
        self.client = gspread.authorize(self.creds)
        
        # Tenta abrir ou criar a planilha
        try:
            self.sheet = self.client.open(sheet_name)
        except:
            self.sheet = self.client.create(sheet_name)
            # Compartilha com você (opcional)
            # self.sheet.share('seu_email@gmail.com', perm_type='user', role='writer')
    
    def _get_credentials(self):
        """Pega credenciais do secrets.toml"""
        creds_dict = {
            "type": st.secrets["google"]["type"],
            "project_id": st.secrets["google"]["project_id"],
            "private_key_id": st.secrets["google"]["private_key_id"],
            "private_key": st.secrets["google"]["private_key"],
            "client_email": st.secrets["google"]["client_email"],
            "client_id": st.secrets["google"]["client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"]
        }
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    def append_events(self, events_data):
        """Adiciona eventos à planilha"""
        df = pd.DataFrame(events_data)
        
        if df.empty:
            return
        
        # Adiciona timestamp de processamento
        df['processed_at'] = datetime.now().isoformat()
        
        # Converte metadados para JSON string
        if 'metadata' in df.columns:
            df['metadata'] = df['metadata'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
        
        # Tenta abrir a worksheet "Eventos"
        try:
            worksheet = self.sheet.worksheet("Eventos")
        except:
            worksheet = self.sheet.add_worksheet(title="Eventos", rows=1000, cols=20)
            # Adiciona cabeçalho
            worksheet.append_row(df.columns.tolist())
        
        # Adiciona dados
        for _, row in df.iterrows():
            worksheet.append_row(row.tolist())
    
    def append_session(self, session_data):
        """Adiciona resumo de sessão"""
        df = pd.DataFrame([session_data])
        
        try:
            worksheet = self.sheet.worksheet("Sessões")
        except:
            worksheet = self.sheet.add_worksheet(title="Sessões", rows=1000, cols=20)
            worksheet.append_row(df.columns.tolist())
        
        for _, row in df.iterrows():
            worksheet.append_row(row.tolist())
    
    def load_all_data(self):
        """Carrega todos os dados da planilha"""
        try:
            events_worksheet = self.sheet.worksheet("Eventos")
            events_data = events_worksheet.get_all_records()
            events_df = pd.DataFrame(events_data)
        except:
            events_df = pd.DataFrame()
        
        try:
            sessions_worksheet = self.sheet.worksheet("Sessões")
            sessions_data = sessions_worksheet.get_all_records()
            sessions_df = pd.DataFrame(sessions_data)
        except:
            sessions_df = pd.DataFrame()
        
        return events_df, sessions_df
