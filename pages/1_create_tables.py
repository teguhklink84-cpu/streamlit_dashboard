import streamlit as st
import psycopg2

st.title("🧱 Create Tables in Neon Database")

db = st.secrets["connections"]["neon"]

conn = psycopg2.connect(
    host=db["host"],
    database=db["database"],
    user=db["user"],
    password=db["password"],
    port=db["port"],
    sslmode=db.get("sslmode", "require")
)
cur = conn.cursor()

create_members = """
CREATE TABLE IF NOT EXISTS members (
    member_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(100),
    country VARCHAR(50),
    join_date DATE
);
"""

create_sales = """
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    sale_date DATE,
    transaction_id VARCHAR(20),
    product_name VARCHAR(100),
    quantity INT,
    tdp NUMERIC(12,2)
);
"""

try:
    cur.execute(create_members)
    cur.execute(create_sales)
    conn.commit()
    st.success("✅ Tables 'members' and 'sales' created successfully!")
except Exception as e:
    st.error(f"⚠️ Error: {e}")
finally:
    cur.close()
    conn.close()
