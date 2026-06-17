import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Submeter Billing Portal", page_icon="⚡", layout="wide")

DB_FILE = "billing_history.csv"

# Initialize session state for tracking login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Load data helper
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values(by='Date', ascending=False).reset_index(drop=True)
    else:
        # Initial default data if file doesn't exist yet
        initial_data = pd.DataFrame([{
            "Date": pd.to_datetime(datetime.now().strftime("%Y-%m-%d")),
            "Previous Reading (kWh)": 1000.0,
            "Current Reading (kWh)": 1150.0,
            "Consumption (kWh)": 150.0,
            "Rate (₱)": 12.00,
            "Total Bill (₱)": 150.0 * 12.00
        }])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data

# Save data helper
def save_new_reading(prev_r, curr_r, current_rate, date_str):
    df = load_data()
    consumption = curr_r - prev_r
    total_bill = consumption * current_rate
    
    new_row = pd.DataFrame([{
        "Date": pd.to_datetime(date_str),
        "Previous Reading (kWh)": prev_r,
        "Current Reading (kWh)": curr_r,
        "Consumption (kWh)": consumption,
        "Rate (₱)": current_rate,
        "Total Bill (₱)": total_bill
    }])
    
    if pd.to_datetime(date_str) in df['Date'].values:
        df = df[df['Date'] != pd.to_datetime(date_str)]
        
    updated_df = pd.concat([new_row, df], ignore_index=True)
    updated_df.to_csv(DB_FILE, index=False)

# Delete single entry helper
def delete_entry(index_to_drop):
    df = load_data()
    df = df.drop(index=index_to_drop)
    if len(df) == 0:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
    else:
        df.to_csv(DB_FILE, index=False)

# App Init
df_history = load_data()
latest_entry = df_history.iloc[0]

st.title("Submeter Billing Dashboard")
st.markdown("---")

# --- SIDEBAR LOGIN / LOGOUT SYSTEM ---
st.sidebar.header("Portal Access")

if not st.session_state.logged_in:
    # User is currently logged out (Client view mode)
    password_input = st.sidebar.text_input("Enter Admin Password", type="password")
    if st.sidebar.button("Login as Admin"):
        # Change 'admin123' to your desired secure password
        if password_input == "admin123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.sidebar.error("Incorrect Password")
else:
    # User is currently logged in (Admin mode)
    st.sidebar.success("Logged in")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- ADMIN PANEL INTERFACE ---
if st.session_state.logged_in:
    st.header("🛠️ Admin Control Panel")
    
    # Section 1: Add/Update Form
    st.subheader("Add or Update Reading")
    with st.form("reading_form", clear_on_submit=True):
        col_input1, col_input2, col_input3, col_input4 = st.columns(4)
        
        with col_input1:
            billing_date = st.date_input("Billing Date", datetime.now())
        with col_input2:
            prev_val = st.number_input("Previous Reading (kWh)", value=float(latest_entry["Current Reading (kWh)"]))
        with col_input3:
            curr_val = st.number_input("Current Reading (kWh)", value=float(latest_entry["Current Reading (kWh)"]))
        with col_input4:
            current_rate = st.number_input("Rate per kWh (₱)", value=float(latest_entry["Rate (₱)"]), step=0.01)
            
        submit_btn = st.form_submit_button("Update Dashboard")
        
        if submit_btn:
            if curr_val >= prev_val:
                save_new_reading(prev_val, curr_val, current_rate, billing_date.strftime("%Y-%m-%d"))
                st.success("🎉 Dashboard successfully updated! Refreshing...")
                st.rerun()
            else:
                st.error("❌ Current reading cannot be less than the previous reading.")
                
    # Section 2: Manage & Remove Individual Entries
    st.subheader("🗑️ Remove / Manage Entries")
    st.write("Click the trash button next to any entry to permanently remove it.")
    
    for idx, row in df_history.iterrows():
        date_display = row['Date'].strftime('%Y-%m-%d')
        col_del1, col_del2 = st.columns([5, 1])
        
        with col_del1:
            st.info(f"📅 **{date_display}** | Consumption: {row['Consumption (kWh)']} kWh | Rate: ₱{row['Rate (₱)']:.2f} | Total: ₱{row['Total Bill (₱)']:,.2f}")
        with col_del2:
            if st.button(f"🗑️ Delete", key=f"del_{idx}"):
                delete_entry(idx)
                st.warning(f"Removed entry for {date_display}!")
                st.rerun()
                
    st.markdown("---")

# --- PUBLIC CLIENT VIEW ---
st.header(f"Current Statement Summary ({latest_entry['Date'].strftime('%B %Y')})")

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="Total Consumption", value=f"{latest_entry['Consumption (kWh)']:,.2f} kWh")
with m_col2:
    st.metric(label="Rate per kWh", value=f"₱{latest_entry['Rate (₱)']:.2f}")
with m_col3:
    st.metric(label="Total Amount Due", value=f"₱{latest_entry['Total Bill (₱)']:,.2f}")

# Detail breakdown box
with st.expander("View Breakdown Details"):
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
    display_df = df_history[['Date', 'Consumption (kWh)', 'Rate (₱)', 'Total Bill (₱)']].copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    st.dataframe(display_df, use_container_width=True, hide_index=True)
