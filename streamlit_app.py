import streamlit as st
import pandas as pd
import psycopg2
import bcrypt
from dotenv import load_dotenv
import os
import openai

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

POSTGRES_USERNAME = st.secrets["POSTGRES_USERNAME"]
POSTGRES_PASSWORD = st.secrets["POSTGRES_PASSWORD"]
POSTGRES_SERVER   = st.secrets["POSTGRES_SERVER"]
POSTGRES_DATABASE = st.secrets["POSTGRES_DATABASE"]
POSTGRES_PORT     = st.secrets.get("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

HASHED_PASSWORD = st.secrets["HASHED_PASSWORD"].encode("utf-8")

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

# -------------------------
# Login system
# -------------------------
def login_screen():
    st.title("🔐 Secure Login")
    password = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if bcrypt.checkpw(password.encode("utf-8"), HASHED_PASSWORD):
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

def require_login():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        login_screen()

# -------------------------
# Database connection
# -------------------------
@st.cache_resource
def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

def run_query(sql):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"SQL Execution Error: {e}")
        return None

# -------------------------
# AI SQL generation using OpenAI
# -------------------------
SALES_SCHEMA = """
region(regionid, region)
country(countryid, country, regionid)
customer(customerid, firstname, lastname, address, city, countryid)
productcategory(productcategoryid, productcategory, productcategorydescription)
product(productid, productname, productunitprice, productcategoryid)
orderdetail(orderid, customerid, productid, orderdate, quantityordered)
"""

def generate_sql_ai(question):
    prompt = f"""
You are an expert PostgreSQL developer. Convert the following natural-language question into a single valid SQL query.

Database schema:
{SALES_SCHEMA}

Rules:
- Output ONLY SQL (no explanations)
- Use JOINs correctly
- Use aliases c, p, co, r
- Add LIMIT 100 if the query might return a lot of rows

Question: {question}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        sql = response['choices'][0]['message']['content'].strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql
    except Exception as e:
        st.error(f"OpenAI Error: {e}")
        return None

# -------------------------
# Example questions
# -------------------------
EXAMPLE_QUESTIONS = [
    "Show total sales revenue per region",
    "List customers who ordered more than 10 items",
    "Top 5 best selling products",
    "Show monthly revenue for 2023",
    "Which country has the most customers?"
]

# -------------------------
# Main app
# -------------------------
def main():
    require_login()
    st.title("🤖 AI + SQL Runner — Sales Database")
    st.markdown("Ask natural questions or write SQL directly below.")

    # Sidebar
    st.sidebar.title("💡 Example Questions")
    for q in EXAMPLE_QUESTIONS:
        st.sidebar.markdown(f"- {q}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # AI question input
    st.subheader("Ask in English (AI → SQL)")
    user_question = st.text_input("Your question here...")
    if st.button("✨ Generate SQL"):
        if user_question.strip():
            with st.spinner("AI is generating SQL..."):
                sql = generate_sql_ai(user_question)
                if sql:
                    st.session_state.generated_sql = sql

    # SQL textarea
    st.subheader("📝 SQL Query (Editable)")
    sql_input = st.text_area("SQL:", value=st.session_state.get("generated_sql", ""), height=200)

    # Run query
    if st.button("▶️ Run Query"):
        if sql_input.strip():
            with st.spinner("Running SQL..."):
                df = run_query(sql_input)
            if df is not None:
                st.success(f"Returned {len(df)} rows.")
                st.dataframe(df, use_container_width=True)
                st.session_state.query_history = st.session_state.get("query_history", [])
                st.session_state.query_history.append({"query": sql_input, "rows": len(df)})

    # Query history
    if st.session_state.get("query_history"):
        st.markdown("---")
        st.subheader("📜 Query History (Last 5)")
        for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
            with st.expander(f"Query {i+1} — {item['rows']} rows"):
                st.code(item["query"], language="sql")

if __name__ == "__main__":
    main()
