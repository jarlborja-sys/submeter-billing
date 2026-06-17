import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Submeter Billing Portal", page_icon="⚡", layout="wide")

# Initialize session state for tracking login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- SECURE GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Reads data straight from your private Google Sheet live
    df = conn.read(worksheet="Sheet1", ttl="0m")
    df['Date'] = pd.to_datetime(df['Date'])
    df['Start Date'] = pd.to_datetime(df['Start Date'])
    return df.sort_values(by='Date', ascending=False).reset_index(drop=True)

def save_new_reading(start_date_str, end_date_str, prev_r, curr_r, current_rate):
    df = load_data()
    consumption = curr_r - prev_r
    total_bill = consumption * current_rate
    
    new_row = pd.DataFrame([{
        "Start Date": start_date_str,
        "Date": end_date_str,
        "Previous Reading (kWh)": prev_r,
        "Current Reading (kWh)": curr_r,
        "Consumption (kWh)": consumption,
        "Rate (₱)": current_rate,
        "Total Bill (₱)": total_bill
    }])
    
    # Overwrite duplicate end dates if they exist
    if pd.to_datetime(end_date_str) in df['Date'].values:
        df = df[df['Date'] != pd.to_datetime(end_date_str)]
        
    updated_df = pd.concat([new_row, df], ignore_index=True)
    
    # Push the updated data back up to your Google Sheet
    conn.update(worksheet="Sheet1", data=updated_df)

def delete_entry(index_to_drop):
    df = load_data()
    df = df.drop(index=index_to_drop)
    conn.update(worksheet="Sheet1", data=df)

# App Init
df_history = load_data()
latest_entry = df_history.iloc[0]

st.title("Submeter Billing Dashboard")
st.markdown("---")

# --- SIDEBAR LOGIN / LOGOUT SYSTEM ---
st.sidebar.header("Portal Access")
if not st.session_state.logged_in:
    password_input = st.sidebar.text_input("Enter Admin Password", type="password")
    if st.sidebar.button("Login"):
        if password_input == "admin123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.sidebar.error("Incorrect Password")
else:
    st.sidebar.success("Logged in")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- ADMIN PANEL INTERFACE ---
if st.session_state.logged_in:
    st.header("🛠️ Admin Control Panel")
    
    st.subheader("Add or Update Reading")
    with st.form("reading_form", clear_on_submit=True):
        col_input1, col_input2, col_input3, col_input4, col_input5 = st.columns(5)
        
        with col_input1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col_input2:
            billing_date = st.date_input("End Date", datetime.now())
        with col_input3:
            prev_val = st.number_input("Previous Reading (kWh)", value=float(latest_entry["Current Reading (kWh)"]))
        with col_input4:
            curr_val = st.number_input("Current Reading (kWh)", value=float(latest_entry["Current Reading (kWh)"]))
        with col_input5:
            current_rate = st.number_input("Rate per kWh (₱)", value=float(latest_entry["Rate (₱)"]), step=0.01)
            
        submit_btn = st.form_submit_button("Update Dashboard")
        
        if submit_btn:
            if curr_val >= prev_val:
                save_new_reading(
                    start_date.strftime("%Y-%m-%d"),
                    billing_date.strftime("%Y-%m-%d"),
                    prev_val, 
                    curr_val, 
                    current_rate
                )
                st.success("🎉 Google Sheet successfully updated! Refreshing...")
                st.rerun()
            else:
                st.error("❌ Current reading cannot be less than the previous reading.")
                
    st.subheader("🗑️ Remove / Manage Entries")
    for idx, row in df_history.iterrows():
        s_date_display = row['Start Date'].strftime('%Y-%m-%d')
        e_date_display = row['Date'].strftime('%Y-%m-%d')
        col_del1, col_del2 = st.columns([5, 1])
        
        with col_del1:
            st.info(f"📅 **{s_date_display} to {e_date_display}** | Consumption: {row['Consumption (kWh)']} kWh | Rate: ₱{row['Rate (₱)']:.2f} | Total: ₱{row['Total Bill (₱)']:,.2f}")
        with col_del2:
            if st.button(f"🗑️ Delete", key=f"del_{idx}"):
                delete_entry(idx)
                st.warning(f"Removed entry!")
                st.rerun()
                
    st.markdown("---")

# --- PUBLIC CLIENT VIEW ---
st.header(f"Current Statement Summary ({latest_entry['Date'].strftime('%B %Y')})")

start_formatted = latest_entry['Start Date'].strftime('%B %d, %Y')
end_formatted = latest_entry['Date'].strftime('%B %d, %Y')
st.subheader(f"📅 Reading Period: {start_formatted} — {end_formatted}")

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="Total Consumption", value=f"{latest_entry['Consumption (kWh)']:,.2f} kWh")
with m_col2:
    st.metric(label="Rate per kWh", value=f"₱{latest_entry['Rate (₱)']:.2f}")
with m_col3:
    st.metric(label="Total Amount Due", value=f"₱{latest_entry['Total Bill (₱)']:,.2f}")

with st.expander("View Breakdown Details"):
    st.write(f"**Billing Cycle:** {start_formatted} to {end_formatted}")
    st.write(f"**Previous Reading:** {latest_entry['Previous Reading (kWh)']:,.2f} kWh")
    st.write(f"**Current Reading:** {latest_entry['Current Reading (kWh)']:,.2f} kWh")

st.markdown("---")
st.header("Historical Usage & Trends")
col_graph, col_table = st.columns([2, 1])

with col_graph:
    chart_df = df_history.sort_values(by='Date')
    st.line_chart(data=chart_df, x='Date', y='Consumption (kWh)', use_container_width=True)

with col_table:
    display_df = df_history.copy()
    display_df['Start Date'] = display_df['Start Date'].dt.strftime('%Y-%m-%d')
    display_df['End Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    st.dataframe(display_df[['Start Date', 'End Date', 'Consumption (kWh)', 'Rate (₱)', 'Total Bill (₱)']], use_container_width=True, hide_index=True)
