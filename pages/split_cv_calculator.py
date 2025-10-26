import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

# Cloud-compatible version of helpers
def calculate_split_cv(df):
    """
    Calculate Split CV based on country rules
    ID: SPLIT PLAN A = 60%, SPLIT RO = 40%
    MY: SPLIT PLAN A = 50%, SPLIT RO = 50%
    """
    df = df.copy()
    
    # Initialize new columns
    df['SPLIT PLAN A'] = 0.0
    df['SPLIT RO'] = 0.0
    df['BALANCE B/F'] = 0.0
    
    # Calculate based on country
    for idx, row in df.iterrows():
        country = str(row['COUNTRY']).upper().strip()
        cv_plan_a = float(row['CV PLAN A'])
        cv_ro = float(row['CV RO'])
        balance_cf = float(row['BALANCE C/F'])
        
        if country == 'ID':
            df.at[idx, 'SPLIT PLAN A'] = cv_plan_a * 0.6
            df.at[idx, 'SPLIT RO'] = cv_ro * 0.4
        elif country == 'MY':
            df.at[idx, 'SPLIT PLAN A'] = cv_plan_a * 0.5
            df.at[idx, 'SPLIT RO'] = cv_ro * 0.5
        else:
            # Default to ID rules
            df.at[idx, 'SPLIT PLAN A'] = cv_plan_a * 0.6
            df.at[idx, 'SPLIT RO'] = cv_ro * 0.4
            
        df.at[idx, 'BALANCE B/F'] = balance_cf
    
    return df

def get_export_path(filename):
    """Cloud-compatible export path"""
    return f"/tmp/{filename}"

# Streamlit App
st.set_page_config(page_title="Split CV", layout="wide")

st.title("📊 Split CV Calculator")
st.write("Upload file Excel, sistem akan hitung Split Plan A, RO, dan Balance sesuai rules Country (ID / MY).")

# Upload Excel
uploaded_file = st.file_uploader("📂 Upload file Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ File berhasil diupload!")

        expected_cols = [
            "MEMBER ID", "MEMBER NAME", "COUNTRY", "CV PLAN A", "CV RO",
            "TOTAL CV C/F", "BALANCE C/F", "GRAND TOTAL"
        ]

        if not all(col in df.columns for col in expected_cols):
            st.error(f"❌ File harus memiliki kolom berikut: {expected_cols}")
        else:
            # Show preview
            st.subheader("📋 Preview Data Uploaded")
            st.dataframe(df.head(10))
            
            # Calculate
            with st.spinner("🔄 Menghitung Split CV..."):
                df_result = calculate_split_cv(df)

            # Display results
            st.subheader("📘 Hasil Perhitungan Split CV")
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(df_result))
            with col2:
                st.metric("Total SPLIT PLAN A", f"{df_result['SPLIT PLAN A'].sum():,.0f}")
            with col3:
                st.metric("Total SPLIT RO", f"{df_result['SPLIT RO'].sum():,.0f}")
            with col4:
                st.metric("Total BALANCE B/F", f"{df_result['BALANCE B/F'].sum():,.0f}")
            
            st.dataframe(df_result)

            # Download Section
            st.subheader("💾 Download Options")
            
            # Download to user's device
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_result.to_excel(writer, index=False, sheet_name="Hasil Split CV")
            
            st.download_button(
                label="⬇️ Download Excel Result",
                data=buffer.getvalue(),
                file_name=f"hasil_split_cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {e}")
        st.error("Pastikan file Excel formatnya benar dan tidak corrupt.")
else:
    st.info("📤 Silakan upload file Excel untuk memulai perhitungan.")