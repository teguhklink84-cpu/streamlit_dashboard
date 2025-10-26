import streamlit as st
import pandas as pd
import pyodbc
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Database Connection", layout="wide")

st.title("🔌 SQL Server Database Connection")
st.write("Configure and test connection to your SQL Server database")

# Connection Configuration
st.subheader("📋 Connection Settings")

connection_type = st.radio(
    "Connection Type:",
    ["Direct Connection", "SSH Tunnel"],
    horizontal=True
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🖥️ Server Settings")
    server = st.text_input("Server/Host:", "192.168.22.3")
    port = st.number_input("Port:", value=1433, min_value=1, max_value=65535)
    database = st.text_input("Database:", "master")
    
with col2:
    st.markdown("#### 🔐 Authentication")
    username = st.text_input("Username:", "sa")
    password = st.text_input("Password:", type="password")
    trust_cert = st.checkbox("Trust Server Certificate", value=True)

# SSH Tunnel Settings (if selected)
if connection_type == "SSH Tunnel":
    st.markdown("#### 🔒 SSH Tunnel Settings")
    ssh_col1, ssh_col2 = st.columns(2)
    
    with ssh_col1:
        ssh_host = st.text_input("SSH Host:", "202.57.1.106")
        ssh_port = st.number_input("SSH Port:", value=22)
    
    with ssh_col2:
        ssh_username = st.text_input("SSH Username:", "root")
        ssh_password = st.text_input("SSH Password:", type="password")

# Test Connection Button
if st.button("🚀 Test Connection", type="primary"):
    if not all([server, database, username, password]):
        st.error("❌ Please fill all required fields")
    else:
        with st.spinner("Testing connection..."):
            try:
                # Build connection string
                if trust_cert:
                    connection_string = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={server},{port};"
                        f"DATABASE={database};"
                        f"UID={username};"
                        f"PWD={password};"
                        f"TrustServerCertificate=yes;"
                    )
                else:
                    connection_string = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={server},{port};"
                        f"DATABASE={database};"
                        f"UID={username};"
                        f"PWD={password};"
                    )
                
                # Test connection
                conn = pyodbc.connect(connection_string)
                cursor = conn.cursor()
                
                # Get server info
                cursor.execute("SELECT @@VERSION as version")
                version_info = cursor.fetchone()[0]
                
                cursor.execute("SELECT DB_NAME() as db_name")
                db_name = cursor.fetchone()[0]
                
                st.success("✅ Connection Successful!")
                
                # Display connection info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Server", server)
                with col2:
                    st.metric("Database", db_name)
                with col3:
                    st.metric("Status", "Connected")
                
                st.info(f"**Server Version:** {version_info.split(',')[0]}")
                
                # Save connection info to session state
                st.session_state.db_connection = {
                    'server': server,
                    'database': database,
                    'username': username,
                    'connected': True,
                    'connection_string': connection_string
                }
                
                conn.close()
                
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
                st.info("💡 **Troubleshooting tips:**")
                st.write("- Check if server is accessible from this network")
                st.write("- Verify username/password")
                st.write("- Ensure SQL Server allows remote connections")
                st.write("- For cloud deployment, database must be publicly accessible")

# Query Execution (if connected)
if st.session_state.get('db_connection', {}).get('connected'):
    st.markdown("---")
    st.subheader("🔍 Execute Query")
    
    query = st.text_area(
        "SQL Query:",
        value="SELECT TOP 10 * FROM INFORMATION_SCHEMA.TABLES",
        height=100
    )
    
    if st.button("Run Query"):
        try:
            conn = pyodbc.connect(st.session_state.db_connection['connection_string'])
            df = pd.read_sql(query, conn)
            
            st.success(f"✅ Query executed successfully. Returned {len(df)} rows.")
            st.dataframe(df)
            
            # Download results
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Query execution failed: {str(e)}")

# Connection Info
if st.session_state.get('db_connection'):
    st.markdown("---")
    st.subheader("📊 Current Connection")
    
    conn_info = st.session_state.db_connection
    st.json({
        "server": conn_info['server'],
        "database": conn_info['database'],
        "username": conn_info['username'],
        "status": "Connected" if conn_info['connected'] else "Disconnected"
    })
    
    if st.button("Disconnect"):
        st.session_state.db_connection['connected'] = False
        st.rerun()

# Navigation
st.sidebar.markdown("---")
if st.sidebar.button("🏠 Back to Main App"):
    st.switch_page("app.py")