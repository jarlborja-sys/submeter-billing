def load_data():
    # Changed worksheet="Sheet1" to worksheet=0 to bypass the Google 400 error bug
    df = conn.read(worksheet=0, ttl="0m")
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
    
    if pd.to_datetime(end_date_str) in df['Date'].values:
        df = df[df['Date'] != pd.to_datetime(end_date_str)]
        
    updated_df = pd.concat([new_row, df], ignore_index=True)
    
    # Changed worksheet="Sheet1" to worksheet=0 here as well
    conn.update(worksheet=0, data=updated_df)

def delete_entry(index_to_drop):
    df = load_data()
    df = df.drop(index=index_to_drop)
    # Changed worksheet="Sheet1" to worksheet=0 here as well
    conn.update(worksheet=0, data=df)
