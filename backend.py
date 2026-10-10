from fastapi import FastAPI, HTTPException
import sqlite3
import requests
import json

app = FastAPI()

def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY, item TEXT, amount REAL, category TEXT, date DATE)''')
    conn.commit()
    conn.close()

init_db()

def extract_with_gemma(user_input: str):
    prompt = f"""
    You are a strict data extraction AI. Extract the item, amount, and category from the following text.
    Text: "{user_input}"
    
    You must respond ONLY with a valid JSON object. Do not include markdown formatting, backticks, or any other conversational text.
    Format exactly like this: {{"item": "string", "amount": number, "category": "string"}}
    """
    
    # Call your local Gemma model on the Mac
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": "gemma4:e4b",
        "prompt": prompt,
        "stream": False,
        "format": "json" # Forces the Ollama engine to constrain output to JSON
    })
    
    try:
        # Parse the JSON returned by Gemma
        return json.loads(response.json()['response'])
    except json.JSONDecodeError:
        raise ValueError("Gemma failed to output valid JSON.")

@app.post("/add_expense/")
def add_expense(user_input: str):
    try:
        expense_data = extract_with_gemma(user_input)
        
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute("INSERT INTO expenses (item, amount, category, date) VALUES (?, ?, ?, date('now'))",
                  (expense_data['item'], expense_data['amount'], expense_data['category']))
        conn.commit()
        conn.close()
        
        return {"status": "success", "data": expense_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_expenses/")
def get_expenses():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("SELECT * FROM expenses")
    rows = c.fetchall()
    conn.close()
    return rows