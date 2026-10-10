import streamlit as st
import requests
import pandas as pd
import sqlite3
try:
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
except:
    df = pd.DataFrame()

# Page setup
st.set_page_config(page_title="Pocket-Guard", layout="centered")
st.title("PocketGuard")
st.sidebar.header("⚙️ Financial Settings")

# Set a default budget if it doesn't exist yet
if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = 5000

# Input to let the user change their budget
new_budget = st.sidebar.number_input(
    "Set Monthly Budget (₹)", 
    min_value=0, 
    value=st.session_state.monthly_budget, 
    step=500
)
st.session_state.monthly_budget = new_budget

# Calculate total spent from the database safely
total_spent = 0
if not df.empty and 'amount' in df.columns:
    total_spent = df['amount'].sum()

remaining_budget = st.session_state.monthly_budget - total_spent

# Display visual metrics in the sidebar
st.sidebar.divider()
st.sidebar.metric("Total Spent", f"₹{total_spent}")
st.sidebar.metric(
    "Remaining Budget", 
    f"₹{remaining_budget}", 
    delta=f"₹{remaining_budget}" if remaining_budget > 0 else "Over budget!",
    delta_color="normal" if remaining_budget > 0 else "inverse"
)
st.write("Your completely private, local AI expense manager powered by Gemma.")

# Input section
st.subheader("Log a new expense")
user_input = st.text_input("Example: I paid 500 rupees for train tickets back home", placeholder="What did you spend money on?")

if st.button("Log Expense"):
    if user_input:
        with st.spinner("Gemma is processing your expense locally..."):
            res = requests.post(f"http://localhost:8000/add_expense/?user_input={user_input}")
            if res.status_code == 200:
                st.success(f"Successfully logged! {res.json()['data']}")
            else:
                st.error("Could not parse the expense. Please try phrasing it differently.")

st.markdown("---")
st.subheader("📷 Scan a Receipt")
# This opens the Mac webcam directly in the browser
receipt_image = st.camera_input("Take a photo of your receipt") 

if receipt_image is not None:
    st.success("Receipt captured!")
    # For now, just display it. Once Gemma is running, 
    # you can pass this image through OCR (like Tesseract) 
    # and feed the text to the AI for automatic logging.
    st.image(receipt_image)
st.subheader("Expense Dashboard")

# Fetch and display data
if st.button("Load/Refresh Data"):
    res = requests.get("http://localhost:8000/get_expenses/")
    if res.status_code == 200:
        data = res.json()
        if data:
            # Convert SQLite rows to a nice Pandas DataFrame
            df = pd.DataFrame(data, columns=["ID", "Item", "Amount", "Category", "Date"])
            st.dataframe(df, use_container_width=True)
            
            # Auto-generate a chart
            st.write("Spending by Category:")
            category_totals = df.groupby("Category")["Amount"].sum()
            st.bar_chart(category_totals)
        else:
            st.info("No expenses logged yet.")
            # Assuming your database is loaded into a Pandas dataframe named 'df'
            # Safely try to load the database, or create an empty dataframe if it fails

if not df.empty:
    # Convert dataframe to CSV format
    csv_data = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Download Expenses as CSV",
        data=csv_data,
        file_name="pistachio_expenses.csv",
        mime="text/csv",
        type="primary"
    )
    st.divider()
st.subheader("🛑 The Impulse Buy Checker")
st.write("Not sure if you should drop ₹500? Let the AI review it before you spend.")

# Create a clean form for the user to fill out
with st.form("impulse_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        wanted_item = st.text_input("What do you want to buy?", placeholder="e.g., A new hoodie")
        item_price = st.number_input("How much does it cost (₹)?", min_value=0)
        
    with col2:
        reason = st.selectbox(
            "Why do you want it?", 
            ["Just craving it", "Social outing / Date", "Need it for college", "Absolute emergency"]
        )
        
    check_button = st.form_submit_button("Judge My Purchase")

# What happens when they click the button
if check_button:
    if wanted_item and item_price > 0:
        with st.spinner("Analyzing your budget and checking the vibe..."):
            
            # --- THIS IS THE PLACEHOLDER UNTIL GEMMA FINISHES ---
            # Once Gemma is ready, you will replace this fake response 
            # with your requests.post() call to FastAPI.
            
            st.warning(f"**AI Preview (Waiting for Gemma):** You want to spend ₹{item_price} on {wanted_item}. Based on your current budget, I would recommend waiting 24 hours before buying this to see if the craving passes!")
    else:
        st.error("Please enter an item and a price.")