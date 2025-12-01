import os
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

# -------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------
load_dotenv()

def get_db_url():
    return f"postgresql://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@" \
           f"{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DATABASE')}"

# -------------------------------------------------------------
# File path
# -------------------------------------------------------------
DATA_FILE = "tests/data.csv"
if not Path(DATA_FILE).exists():
    raise FileNotFoundError(f"{DATA_FILE} does not exist!")

# -------------------------------------------------------------
# DDL SQL
# -------------------------------------------------------------
DDL_SQL = """
DROP TABLE IF EXISTS orderdetail CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS productcategory CASCADE;
DROP TABLE IF EXISTS customer CASCADE;
DROP TABLE IF EXISTS country CASCADE;
DROP TABLE IF EXISTS region CASCADE;

CREATE TABLE region (
    regionid   SERIAL PRIMARY KEY,
    region     TEXT NOT NULL
);

CREATE TABLE country (
    countryid  SERIAL PRIMARY KEY,
    country    TEXT NOT NULL,
    regionid   INTEGER NOT NULL REFERENCES region(regionid)
);

CREATE TABLE customer (
    customerid SERIAL PRIMARY KEY,
    firstname  TEXT NOT NULL,
    lastname   TEXT NOT NULL,
    address    TEXT NOT NULL,
    city       TEXT NOT NULL,
    countryid  INTEGER NOT NULL REFERENCES country(countryid)
);

CREATE TABLE productcategory (
    productcategoryid SERIAL PRIMARY KEY,
    productcategory   TEXT NOT NULL,
    productcategorydescription TEXT NOT NULL
);

CREATE TABLE product (
    productid   SERIAL PRIMARY KEY,
    productname TEXT NOT NULL,
    productunitprice REAL NOT NULL,
    productcategoryid INTEGER NOT NULL REFERENCES productcategory(productcategoryid)
);

CREATE TABLE orderdetail (
    orderid        SERIAL PRIMARY KEY,
    customerid     INTEGER NOT NULL REFERENCES customer(customerid),
    productid      INTEGER NOT NULL REFERENCES product(productid),
    orderdate      DATE NOT NULL,
    quantityordered INTEGER NOT NULL
);
"""

# -------------------------------------------------------------
# Parsing functions
# -------------------------------------------------------------
def parse_regions(path):
    regions = set()
    with open(path, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 4 and parts[4].strip():
                regions.add(parts[4].strip())
    return sorted(regions)

def parse_countries(path):
    pairs = set()
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 4:
                country = parts[3].strip()
                region = parts[4].strip()
                if country and region:
                    pairs.add((country, region))
    return sorted(pairs, key=lambda x: x[0])

def parse_productcategories(path):
    cats = set()
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 7:
                cat_list = parts[6].split(";")
                desc_list = parts[7].split(";")
                for cat, desc in zip(cat_list, desc_list):
                    cat, desc = cat.strip(), desc.strip()
                    if cat:
                        cats.add((cat, desc))
    return sorted(cats, key=lambda x: x[0])

def parse_products(path):
    prods = set()
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 8:
                names = parts[5].split(";")
                cats = parts[6].split(";")
                prices = parts[8].split(";")
                for n, c, p in zip(names, cats, prices):
                    n, c, p = n.strip(), c.strip(), p.strip()
                    if n and c and p:
                        try:
                            price = float(p)
                        except ValueError:
                            continue
                        prods.add((n, c, price))
    return sorted(prods, key=lambda x: x[0])

def parse_customers(path, valid_countries):
    custs = set()
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 4:
                name, address, city, country = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
                if not country or country not in valid_countries:
                    continue
                if not name:
                    continue
                first, last = name.split()[0], " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
                custs.add((first, last, address, city, country))
    return sorted(custs, key=lambda x: (x[0] + " " + x[1]))

def parse_orders(path, customer_map, product_map):
    orders = []
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 10:
                name = " ".join(parts[0].split()).strip()
                if name not in customer_map:
                    continue
                cust_id = customer_map[name]

                prod_names = [x.strip() for x in parts[5].split(";")]
                qtys = [x.strip() for x in parts[9].split(";")]
                dates = [x.strip() for x in parts[10].split(";")]

                for pn, q, dt in zip(prod_names, qtys, dates):
                    if pn not in product_map:
                        continue
                    try:
                        qty = int(q)
                        orderdate = datetime.strptime(dt, "%Y%m%d").date()
                    except Exception:
                        continue
                    orders.append((cust_id, product_map[pn], orderdate, qty))
    return orders

# -------------------------------------------------------------
# Main
# -------------------------------------------------------------
def main():
    DATABASE_URL = get_db_url()
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()

    print("Dropping and creating tables...")
    cur.execute(DDL_SQL)
    conn.commit()
    print("✅ Tables created")

    # Regions
    print("Inserting regions...")
    regions = parse_regions(DATA_FILE)
    extras.execute_batch(cur, "INSERT INTO region (region) VALUES (%s)", [(r,) for r in regions])
    conn.commit()
    cur.execute("SELECT region, regionid FROM region")
    region_map = {r: rid for r, rid in cur.fetchall()}

    # Countries
    print("Inserting countries...")
    country_pairs = parse_countries(DATA_FILE)
    country_rows = [(c, region_map[r]) for c, r in country_pairs if r in region_map]
    extras.execute_batch(cur, "INSERT INTO country (country, regionid) VALUES (%s, %s)", country_rows)
    conn.commit()
    cur.execute("SELECT country, countryid FROM country")
    country_map = {c: cid for c, cid in cur.fetchall()}

    # Product Categories
    print("Inserting product categories...")
    categories = parse_productcategories(DATA_FILE)
    extras.execute_batch(cur, "INSERT INTO productcategory (productcategory, productcategorydescription) VALUES (%s, %s)", categories)
    conn.commit()
    cur.execute("SELECT productcategory, productcategoryid FROM productcategory")
    cat_map = {c: cid for c, cid in cur.fetchall()}

    # Products
    print("Inserting products...")
    products_raw = parse_products(DATA_FILE)
    product_rows = [(n, price, cat_map[c]) for n, c, price in products_raw if c in cat_map]
    extras.execute_batch(cur, "INSERT INTO product (productname, productunitprice, productcategoryid) VALUES (%s, %s, %s)", product_rows)
    conn.commit()
    cur.execute("SELECT productname, productid FROM product")
    product_map = {n: pid for n, pid in cur.fetchall()}

    # Customers
    print("Inserting customers...")
    customers_raw = parse_customers(DATA_FILE, set(country_map.keys()))
    customer_rows = [(f, l, addr, city, country_map[country]) for f, l, addr, city, country in customers_raw]
    extras.execute_batch(cur, "INSERT INTO customer (firstname, lastname, address, city, countryid) VALUES (%s, %s, %s, %s, %s)", customer_rows)
    conn.commit()
    cur.execute("SELECT firstname, lastname, customerid FROM customer")
    cust_map = {f"{f} {l}".strip(): cid for f, l, cid in cur.fetchall()}

    # Orders
    print("Inserting orders...")
    orders = parse_orders(DATA_FILE, cust_map, product_map)
    extras.execute_batch(cur, "INSERT INTO orderdetail (customerid, productid, orderdate, quantityordered) VALUES (%s, %s, %s, %s)", orders, page_size=5000)
    conn.commit()

    cur.close()
    conn.close()
    print("✅ Finished populating mini-project2 sales database")

# -------------------------------------------------------------
if __name__ == "__main__":
    main()
