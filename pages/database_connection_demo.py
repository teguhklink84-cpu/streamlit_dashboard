import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Database Connection Demo", layout="wide")

st.title("🔌 Database Connection - Demo Mode")
st.warning("⚠️ Cloud Environment - Using simulated database connection")

# Simulated database connection
def simulate_database_connection(server, database, username, password):
    """Simulate database connection for demo purposes"""
    if not all([server, database, username, password]):
        return False, "Missing connection parameters"
    
    # Simulate connection delay
    import time
    time.sleep(2)
    
    # Simple authentication simulation
    if len(password) < 3:
        return False, "Invalid credentials"
    
    return True, "Connection successful"

def generate_sample_data(table_name):
    """Generate sample data based on table name"""
    if "member" in table_name.lower():
        return pd.DataFrame({
            'member_id': [f'MEM{str(i).zfill(3)}' for i in range(1, 11)],
            'full_name': [f'Customer {i}' for i in range(1, 11)],
            'country': ['Indonesia'] * 5 + ['Malaysia'] * 5,
            'join_date': [datetime.now() - timedelta(days=i*30) for i in range(10)],
            'status': ['Active'] * 8 + ['Inactive'] * 2
        })
    elif "sales" in table_name.lower():
        return pd.DataFrame({
            'transaction_id': [f'TRX{str(i).zfill(3)}' for i in range(1, 11)],
            'sale_date': [datetime.now() - timedelta(days=i) for i in range(10)],
            'product_name': [f'Product {chr(65 + i % 5)}' for i in range(10)],
            'quantity': np.random.randint(1, 10, 10),
            'amount': np.random.randint(100, 5000, 10),
            'member_id': [f'MEM{str(np.random.randint(1, 6)).zfill(3)}' for _ in range(10)]
        })
    else:
        return pd.DataFrame({
            'id': range(1, 11),
            'name': [f'Table {i}' for i in range(1, 11)],
            'type': ['BASE TABLE'] * 10,
            'created_date': [datetime.now() - timedelta(days=i*100) for i in range(10)]
        })

# Connection Interface
st.subheader("📋 Connection Settings (Simulated)")

col1, col2 = st.columns(2)

with col1:
    server = st.text_input("Server/Host:", "demo-sql-server.database.windows.net")
    database = st.text_input("Database:", "demo_database")
    
with col2:
    username = st.text_input("Username:", "demo_user")
    password = st.text_input("Password:", type="password", value="demo123")

# Test Connection
if st.button("🚀 Test Connection", type="primary"):
    with st.spinner("Simulating database connection..."):
        success, message = simulate_database_connection(server, database, username, password)
        
        if success:
            st.success("✅ Connection Successful! (Simulated)")
            
            # Display connection info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Server", server)
            with col2:
                st.metric("Database", database)
            with col3:
                st.metric("Status", "Connected")
            
            st.session_state.db_connected = True
            st.session_state.connection_info = {
                'server': server,
                'database': database,
                'username': username
            }
        else:
            st.error(f"❌ Connection failed: {message}")

# Query Execution
if st.session_state.get('db_connected'):
    st.markdown("---")
    st.subheader("🔍 Execute Sample Queries")
    
    query_type = st.selectbox(
        "Choose Sample Query:",
        ["Show Tables", "Member Data", "Sales Data", "Custom Query"]
    )
    
    if query_type == "Show Tables":
        query = "SELECT * FROM INFORMATION_SCHEMA.TABLES"
        table_name = "information_schema.tables"
    elif query_type == "Member Data":
        query = "SELECT * FROM msmemb LIMIT 10"
        table_name = "msmemb"
    elif query_type == "Sales Data":
        query = "SELECT * FROM newtrh WHERE sale_date >= '2024-01-01'"
        table_name = "newtrh"
    else:
        query = st.text_area("Enter Custom Query:", "SELECT * FROM your_table LIMIT 10")
        table_name = "custom_query"
    
    if st.button("Run Query"):
        with st.spinner("Executing query..."):
            # Generate sample data based on query type
            df = generate_sample_data(table_name)
            
            st.success(f"✅ Query executed successfully. Returned {len(df)} rows.")
            st.code(query, language="sql")
            st.dataframe(df)
            
            # Download results
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# Database Management Features
if st.session_state.get('db_connected'):
    st.markdown("---")
    st.subheader("🗃️ Database Management")
    
    tab1, tab2, tab3 = st.tabs(["📊 Schema Info", "🔧 Admin Tools", "📈 Analytics"])
    
    with tab1:
        st.write("**Database Schema Information**")
        schema_df = pd.DataFrame({
            'Table Name': ['msmemb', 'newtrh', 'msprod', 'trstock', 'mssponsor'],
            'Rows': [15000, 50000, 300, 1200, 18000],
            'Size (MB)': [25.6, 89.3, 2.1, 5.7, 31.2],
            'Last Updated': ['2024-10-25', '2024-10-26', '2024-10-20', '2024-10-24', '2024-10-25']
        })
        st.dataframe(schema_df)
    
    with tab2:
        st.write("**Database Administration**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Cache"):
                st.success("Cache refreshed successfully!")
            if st.button("📋 Generate ERD"):
                st.info("ERD diagram generated (simulated)")
        with col2:
            if st.button("🛡️ Backup Database"):
                st.success("Backup completed (simulated)")
            if st.button("📈 Performance Stats"):
                st.info("Performance report generated (simulated)")
    
    with tab3:
        st.write("**Database Analytics**")
        # Sample charts
        chart_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            'Sales': [12000, 15000, 11000, 18000, 20000],
            'New Members': [150, 180, 120, 220, 250]
        })
        st.line_chart(chart_data.set_index('Month'))

# Navigation
st.sidebar.markdown("---")
if st.sidebar.button("🏠 Back to Main App"):
    st.switch_page("app.py")