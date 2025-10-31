import streamlit as st
import psycopg2
import os
import sys
import json
import pandas as pd
import io
from datetime import datetime

db = st.secrets["connections"]["neon"]

conn = psycopg2.connect(
    host=db["ep-dawn-firefly-a1j273g4-pooler.ap-southeast-1.aws.neon.tech"],
    database=db["neondb"],
    user=db["neondb_owner"],
    password=db["npg_HCP4qEAZxn1i"],
    port=db["5432"],
    sslmode=db.get("sslmode", "require")
)

df = pd.read_sql("SELECT NOW() AS server_time;", conn)
st.success("✅ Connected to Neon Database")
st.write(df)


# Cloud-compatible database module
try:
    from utils.database import db
    CLOUD_MODE = False
except ImportError:
    # Fallback untuk cloud environment
    CLOUD_MODE = True
    st.warning("⚠️ Cloud Mode - Using demo data")

# Cloud-compatible database class
class CloudDatabase:
    def __init__(self):
        self.connected = False
    
    def connect(self, ssh_config, sql_config):
        self.connected = True
        return True
    
    def connect_direct(self, sql_config):
        self.connected = True
        return True
    
    def execute_query(self, query, timeout=30):
        # Return sample data untuk demo di cloud
        if "msmemb" in query:
            # Sample member data
            return pd.DataFrame({
                'member_id': ['MEM001', 'MEM002'],
                'full_name': ['John Doe', 'Jane Smith'],
                'country': ['Indonesia', 'Malaysia'],
                'join_date': ['2024-01-01', '2024-01-02']
            }), 1.0, None
        elif "newtrh" in query:
            # Sample sales data
            return pd.DataFrame({
                'sale_date': ['2024-01-01', '2024-01-02'],
                'transaction_id': ['TRX001', 'TRX002'],
                'product_name': ['Product A', 'Product B'],
                'quantity': [2, 5],
                'tdp': [100, 250]
            }), 1.0, None
        else:
            return pd.DataFrame(), 1.0, None
    
    def get_database_info(self):
        return {
            'Database Name': 'Cloud Demo',
            'Server Name': 'Cloud Environment'
        }
    
    def close(self):
        self.connected = False

# Use cloud database if local database not available
if CLOUD_MODE:
    db = CloudDatabase()
else:
    from utils.database import db

# Cloud-compatible helpers
def get_export_path(filename):
    return f"/tmp/{filename}"

def calculate_split_cv(df):
    # Simple calculation for demo
    df['SPLIT PLAN A'] = df['CV PLAN A'] * 0.6
    df['SPLIT RO'] = df['CV RO'] * 0.4
    df['BALANCE B/F'] = df['BALANCE C/F']
    return df

# ... (rest of your app.py code tetap sama)
st.set_page_config(
    page_title="Integrated Data Management System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session states
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'connection_type' not in st.session_state:
    st.session_state.connection_type = None
# ... (lanjutkan dengan kode app.py Anda yang sudah ada)
if st.sidebar.button("🔌 Database Connection"):
    st.switch_page("pages/database_connection.py")
