import psycopg2
from psycopg2 import extras
import csv
from pathlib import Path
import time

# Your Render Postgres URL
DATABASE_URL = "postgresql://mini_project2_yj4w_user:sNkMFh1XE2dMWQILlHClDd6hrVc2szbQ@dpg-d4mipqbuibrs738kf2t0-a.oregon-postgres.render.com/mini_project2_yj4w"

# Connect to the database
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

# Example: test connection
cursor.execute("SELECT NOW();")
print("Connected! Current time in DB:", cursor.fetchone())

cursor.close()
conn.close()
