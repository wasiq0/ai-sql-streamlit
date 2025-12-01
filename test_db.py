import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()  # must be called first

POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

print("Connecting to:", DATABASE_URL)

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    print("✅ Connected to Render Postgres")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
