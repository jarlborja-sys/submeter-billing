import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Submeter Billing Portal", page_icon="⚡", layout="wide")

DB_FILE = "billing_history.csv"
FIXED_RATE = 12.00  # ₱12.00 per kWh

# Load data helper
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values(by='Date', ascending=False)
    else:
        # Initial dummy data if file doesn't exist
        initial_data = pd.DataFrame([{
            "Date": pd.to_datetime(datetime.now().strftime("%Y-%m-%d")),
            "Previous Reading (kWh)": 1000.0,
            "Current Reading (kWh)": 1150.0,
            "Consumption (kWh)": 150.0,
            "Rate (₱)": FIXED_RATE,
            "Total Bill (₱)": 150.0 * FIXED_RATE
        }])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data

# Save data helper
def save_new_reading(prev_r, curr_r, date_str):
    df = load_data()
    consumption = curr_r - prev_r
    total_bill = consumption * FIXED_RATE
    
    new_row = pd.DataFrame([{
        "Date": pd.to_datetime(date_str),
        "Previous Reading (kWh)": prev_r,
        "Current Reading (kWh)": curr_r,
        "Consumption (kWh)": consumption,
        "Rate (₱)": FIXED_RATE,
        "Total Bill (₱)": total_bill
    }])
    
    # Check if date already exists to avoid duplication
    if pd.to_datetime(date_str) in df['Date'].values:
        df = df[df['Date'] != pd.to_datetime(date_str)]
        
    updated_df = pd.concat([new_row, df], ignore_index=True)
    updated_df.to_csv(DB_FILE, index=False)

# App Init
df_history = load_data()
latest_entry = df_history.iloc[0]

st.title("Submeter Billing Dashboard")
st.markdown("---")

# Sidebar Configuration for Admin Login
st.sidebar.header("Admin Access")
admin_password = st.sidebar.text_input("Enter Admin Password", type="password")

# ADMIN PANEL (Only visible with correct password)
# Change 'admin123' to any password you prefer
if admin_password == "admin123":
    st.sidebar.success("Logged In as Admin")
    st.header("🛠️ Admin Control Panel (Update Readings)")
    
    with st.form("reading_form", clear_on_submit=True):
        col_input1, col_input2, col_input3 = st.columns(3)
        
        with col_input1:
            billing_date = st.date_input("Billing Date", datetime.now())
        with col_input2:
            # Defaults to previous current reading
            prev_val = st.number_input("Previous Reading (kWh)", value=float(latest_entry["Current Reading (kWh)"]))
        with col_input3:
            curr_val = st.number_input("Current Reading (kWh)", value=float(latest_entry["Current Reading (kWh)"]))
            
        submit_btn = st.form_submit_form_button = st.form_submit_button("Update Dashboard")
        
        if submit_btn:
            if curr_val >= prev_val:
                save_new_reading(prev_val, curr_val, billing_date.strftime("%Y-%m-%d"))
                st.success("🎉 Dashboard successfully updated! Refreshing...")
                st.rerun()
            else:
                st.error("❌ Current reading cannot be less than the previous reading.")
    st.markdown("---")
elif admin_password != "":
    st.sidebar.error("Incorrect password")

# CLIENT VIEW (Publicly visible)
st.header(f"Current Statement Summary ({latest_entry['Date'].strftime('%B %Y')})")

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="Total Consumption", value=f"{latest_entry['Consumption (kWh)']:,.2f} kWh")
with m_col2:
    st.metric(label="Rate per kWh", value=f"₱{latest_entry['Rate (₱)']:.2f}")
with m_col3:
    st.metric(label="Total Amount Due", value=f"₱{latest_entry['Total Bill (₱)']:,.2f}")

# Detail breakdown box
with st.expander("🔍 View Breakdown Details"):
    st.write(f"**Previous Reading:** {latest_entry['Previous Reading (kWh)']:,.2f} kWh")
    st.write(f"**Current Reading:** {latest_entry['Current Reading (kWh)']:,.2f} kWh")
    st.write(f"**Formula Used:** $(Current - Previous) \\times Rate = Total$")

st.markdown("---")
st.header("Historical Usage & Trends")

# Graph and Data logs
col_graph, col_table = st.columns([2, 1])

with col_graph:
    chart_df = df_history.sort_values(by='Date')
    st.line_chart(data=chart_df, x='Date', y='Consumption (kWh)', use_container_width=True)

with col_table:
    # Display simplified historical log table for client
    display_df = df_history[['Date', 'Consumption (kWh)', 'Total Bill (₱)']].copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    st.dataframe(display_df, use_container_width=True, hide_index=True)
