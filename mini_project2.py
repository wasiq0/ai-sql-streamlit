### Utility Functions
import pandas as pd
import sqlite3
from sqlite3 import Error

def create_connection(db_file, delete_db=False):
    import os
    if delete_db and os.path.exists(db_file):
        os.remove(db_file)

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = 1")
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql, drop_table_name=None):
    
    if drop_table_name: # You can optionally pass drop_table_name to drop the table. 
        try:
            c = conn.cursor()
            c.execute("""DROP TABLE IF EXISTS %s""" % (drop_table_name))
        except Error as e:
            print(e)
    
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)
        
def execute_sql_statement(sql_statement, conn):
    cur = conn.cursor()
    cur.execute(sql_statement)

    rows = cur.fetchall()

    return rows

def step1_create_region_table(data_filename, normalized_database_filename):
    # Inputs: Name of the data and normalized database filename
    # Output: None
    region=set()
    with open(data_filename, "r") as a:
      next(a)
      for line in a:
        parts=line.strip().split("\t")
        if len(parts)>=5:
          r= parts[4]
          region.add(r)
    sorted_region = sorted(list(region))
    con= create_connection(normalized_database_filename)
    re_sql= """ CREATE TABLE IF NOT EXISTS Region (
          RegionID INTEGER NOT NULL PRIMARY KEY,
          Region TEXT NOT NULL
      );"""
    create_table(con, re_sql, "Region")
    values=[(regions,) for regions in sorted_region]
    with con:
      curr=con.cursor()
      curr.executemany("INSERT INTO Region (Region) VALUES (?)", values)
    con.close()

    
# WRITE YOUR CODE HERE

def step2_create_region_to_regionid_dictionary(normalized_database_filename):
  conn = create_connection(normalized_database_filename)
  sql_q = "SELECT Region, RegionID FROM Region"
  values = execute_sql_statement(sql_q, conn)
  dict_region = {v[0]: v[1] for v in values}
  conn.close()
  return dict_region

    
# WRITE YOUR CODE HERE


def step3_create_country_table(data_filename, normalized_database_filename):
    # Inputs: Name of the data and normalized database filename
    # Output: None
    dict_reg = step2_create_region_to_regionid_dictionary(normalized_database_filename)
    cct_set = set()
    with open (data_filename, "r") as a:
      next(a)
      for line in a:
        part = line.strip().split("\t")
        if len(part) >=5:
          country = part[3]
          region = part[4]
          cct_set.add((country, region))
    cct_sort = sorted(list(cct_set), key=lambda x: x[0])
    conn = create_connection(normalized_database_filename)

    sql_q = """CREATE TABLE IF NOT EXISTS Country(
          CountryID INTEGER NOT NULL PRIMARY KEY,
          Country TEXT NOT NULL,
          RegionID INTEGER NOT NULL,
          FOREIGN KEY (RegionID) REFERENCES Region(RegionID)
    )"""

    create_table(conn, sql_q, 'Country')
    values=[(country, dict_reg[region]) for country, region in cct_sort]

    with conn:
      curr= conn.cursor()
      curr.executemany("INSERT INTO Country (Country, RegionID) VALUES (?, ?)", values)

    conn.close()

# WRITE YOUR CODE HERE


def step4_create_country_to_countryid_dictionary(normalized_database_filename):
    con = create_connection(normalized_database_filename)
    sql_q="SELECT country, CountryID FROM Country"
    row = execute_sql_statement(sql_q,con)
    dict_country ={rows[0]: rows[1] for rows in row}
    con.close()
    return dict_country
    

    
# WRITE YOUR CODE HERE
        
        
def step5_create_customer_table(data_filename, normalized_database_filename):

# WRITE YOUR CODE HERE
    c_dict = step4_create_country_to_countryid_dictionary(normalized_database_filename)
    cust = set()
    with open(data_filename, "r") as a:
      next(a)
      for line in a:
        part= line.strip().split("\t")
        if len(part) >= 5:
          name = part[0]
          address = part[1]
          city = part[2]
          country = part[3]
          
          part_name = name.split()
          first_n = part_name[0]
          if len(part_name) >=3:
            last_n = " ".join(part_name[1:])
          else:
            last_n = part_name[1]
        
        cust.add((first_n, last_n, address, city, country))
    
    sorted_cu = sorted(list(cust), key= lambda x:x[0]+' '+ x[1])
    conn = create_connection(normalized_database_filename)
    sql_q= """CREATE TABLE IF NOT EXISTS Customer (
        CustomerID INTEGER NOT NULL PRIMARY KEY,
        FirstName TEXT NOT NULL,
        LastName TEXT NOT NULL,
        Address TEXT NOT NULL,
        City TEXT NOT NULL,
        CountryID INTEGER NOT NULL,
        FOREIGN KEY (CountryID) REFERENCES Country(CountryID)
    );"""
    create_table(conn, sql_q, "Customer")
    values=[(f, l, a, city, c_dict[country]) for f, l, a, city, country in sorted_cu]   
    with conn:
      cur=conn.cursor()
      cur.executemany("INSERT INTO Customer (FirstName, LastName, Address, City, CountryID) VALUES (?, ?, ?, ?, ?)", values)
    conn.close()
    # WRITE YOUR CODE HERE

    pass


def step6_create_customer_to_customerid_dictionary(normalized_database_filename):
  conn = create_connection(normalized_database_filename)
  sql_q = "SELECT FirstName, LastName, CustomerID FROM Customer"
  row = execute_sql_statement(sql_q, conn)

  dict_cust = {rows[0]+ " "+rows[1]:rows[2] for rows in row}
  conn.close()

  return dict_cust

# WRITE YOUR CODE HERE
        
def step7_create_productcategory_table(data_filename, normalized_database_filename):
    # Inputs: Name of the data and normalized database filename
    # Output: None
    product = set()
    with open(data_filename, "r") as a:
      next(a)
      for line in a:
        part = line.strip().split("\t")
        if len(part) >=11:
          p_cate = part[6].split(";")
          p_desc=part[7].split(";")

          for cate, desc in zip(p_cate, p_desc):
            product.add((cate,desc))
    category_sort = sorted(list(product), key=lambda x:x[0])
    conn = create_connection(normalized_database_filename)
    sql_q = """
    CREATE TABLE IF NOT EXISTS ProductCategory (
        ProductCategoryID INTEGER NOT NULL PRIMARY KEY,
        ProductCategory TEXT NOT NULL,
        ProductCategoryDescription TEXT NOT NULL
    );
    """

    create_table(conn, sql_q, "ProductCategory")
    values = [(cate, desc) for cate, desc in category_sort]

    with conn:
      curr = conn.cursor()
      curr.executemany("INSERT INTO ProductCategory (ProductCategory, ProductCategoryDescription) VALUES (?, ?)", values)
    conn.close()


    pass

    
# WRITE YOUR CODE HERE

def step8_create_productcategory_to_productcategoryid_dictionary(normalized_database_filename):
    conn = create_connection(normalized_database_filename)
    sql_q = "SELECT ProductCategory, ProductCategoryID FROM ProductCategory"
    row = execute_sql_statement(sql_q, conn)
    dict_product = {rows[0]:rows[1] for rows in row}
    conn.close()
    
    return dict_product
    pass
    
# WRITE YOUR CODE HERE
        

def step9_create_product_table(data_filename, normalized_database_filename):
    # Inputs: Name of the data and normalized database filename
    # Output: None

    dict_product = step8_create_productcategory_to_productcategoryid_dictionary(normalized_database_filename)
    prods = set()
    with open(data_filename, "r") as a:
      next(a)
      for line in a:
        part = line.strip().split("\t")
        if len(part) >= 11:
          prod_n = part[5].split(';')
          prod_c = part[6].split(';')
          prod_price = part[8].split(';')

          for p_name , p_cat , p_price in zip(prod_n, prod_c, prod_price):
            prods.add((p_name, float(p_price), p_cat ))
      products_sort = sorted(list(prods), key=lambda x:x[0])
      conn = create_connection(normalized_database_filename)
      sql_q = """
    CREATE TABLE IF NOT EXISTS Product (
        ProductID INTEGER NOT NULL PRIMARY KEY,
        ProductName TEXT NOT NULL,
        ProductUnitPrice REAL NOT NULL,
        ProductCategoryID INTEGER NOT NULL,
        FOREIGN KEY (ProductCategoryID) REFERENCES ProductCategory(ProductCategoryID)
    );
    """

    create_table(conn , sql_q , "Product")
    values = [(name, price, dict_product[cat]) for name, price, cat in products_sort]


    with conn:
      cur=conn.cursor()
      cur.executemany("INSERT INTO Product (ProductName, ProductUnitPrice, ProductCategoryID) VALUES (?, ?, ?)", values)
    conn.close()

# WRITE YOUR CODE HERE


def step10_create_product_to_productid_dictionary(normalized_database_filename):
  con = create_connection(normalized_database_filename)
  sql_q = "SELECT ProductName, ProductID FROM Product"
  row = execute_sql_statement(sql_q, con)
  dict_product= {rows[0]:rows[1] for rows in row}
  con.close()
  return dict_product
  pass

# WRITE YOUR CODE HERE
        

def step11_create_orderdetail_table(data_filename, normalized_database_filename):
    # Inputs: Name of the data and normalized database filename
    # Output: None

    dict_cust = step6_create_customer_to_customerid_dictionary(normalized_database_filename)
    dict_product=step10_create_product_to_productid_dictionary(normalized_database_filename)
    order = []
    with open(data_filename, "r") as a:
      next(a)
      for line in a:
        part = line.strip().split("\t")
        if len(part) >= 11:
          name = part[0]
          prod_name = part[5].split(';')
          quan = part[9].split(';')
          order_d = part[10].split(';')

          for prod,qua,dat in zip (prod_name , quan , order_d):
            cus_id=dict_cust[name]
            prod_id=dict_product[prod]
            date = str(dat)
            date_new = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
            order.append((cus_id, prod_id, date_new, int(qua)))

    con = create_connection(normalized_database_filename)
    sql_q = """

      CREATE TABLE IF NOT EXISTS OrderDetail (
        OrderID INTEGER NOT NULL PRIMARY KEY,
        CustomerID INTEGER NOT NULL,
        ProductID INTEGER NOT NULL,
        OrderDate INTEGER NOT NULL,
        QuantityOrdered INTEGER NOT NULL,
        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
        FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
    
    );"""

    create_table(con , sql_q, "OrderDetail")
    with con:
      curr = con.cursor()
      curr.executemany("INSERT INTO OrderDetail (CustomerID, ProductID, OrderDate, QuantityOrdered) VALUES (?, ?, ?, ?)", order)
    con.close()

# WRITE YOUR CODE HERE

def ex1(conn, CustomerName):
    
    # Simply, you are fetching all the rows for a given CustomerName. 
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer and Product table.
    # Pull out the following columns. 
    # Name -- concatenation of FirstName and LastName
    # ProductName
    # OrderDate
    # ProductUnitPrice
    # QuantityOrdered
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- round to two decimal places
    # HINT: USE customer_to_customerid_dict to map customer name to customer id and then use where clause with CustomerID
  dict_cust= step6_create_customer_to_customerid_dictionary('normalized.db')
  cus_id=dict_cust[CustomerName]
  sql_statement = f"""
    SELECT c.FirstName || ' ' || c.LastName Name,
    p.ProductName, ol.OrderDate, p.ProductUnitPrice, ol.QuantityOrdered,
    Round((p.ProductUnitPrice * ol.QuantityOrdered),2) Total
    From OrderDetail ol
    JOIN Customer c ON ol.CustomerID = c.CustomerID
    JOIN Product p ON ol.ProductID = p.ProductID
    WHERE c.CustomerID = {cus_id}
    """
# WRITE YOUR CODE HERE
  return sql_statement

def ex2(conn, CustomerName):
    
    # Simply, you are summing the total for a given CustomerName. 
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer and Product table.
    # Pull out the following columns. 
    # Name -- concatenation of FirstName and LastName
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round to two decimal places
    # HINT: USE customer_to_customerid_dict to map customer name to customer id and then use where clause with CustomerID
    
    dict_cust= step6_create_customer_to_customerid_dictionary('normalized.db')
    cus_id=dict_cust[CustomerName]
    sql_statement =f"""
    SELECT c.FirstName || ' ' || c.LastName Name,
    round(sum(p.ProductUnitPrice * ol.QuantityOrdered), 2) Total
    from OrderDetail ol
    join customer c on ol.CustomerID = c.CustomerID
    join product p on ol.ProductID = p.ProductID
    WHERE c.CustomerID = {cus_id}
    group by c.FirstName, c.LastName
    """
# WRITE YOUR CODE HERE
    return sql_statement

def ex3(conn):
    
    # Simply, find the total for all the customers
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer and Product table.
    # Pull out the following columns. 
    # Name -- concatenation of FirstName and LastName
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round to two decimal places
    # ORDER BY Total Descending 
    
    sql_statement = """
    select c.FirstName || ' ' || c.LastName Name,
    round(sum(p.ProductUnitPrice * ol.QuantityOrdered), 2) Total
    from OrderDetail ol
    join customer c on ol.CustomerID = c.CustomerID
    join product p on ol.ProductID = p.ProductID
    group by c.CustomerID, c.FirstName, c.LastName
    order by total desc
    """
# WRITE YOUR CODE HERE
    return sql_statement

def ex4(conn):
    
    # Simply, find the total for all the region
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer, Product, Country, and 
    # Region tables.
    # Pull out the following columns. 
    # Region
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round to two decimal places
    # ORDER BY Total Descending 
    
    sql_statement = """
    select re.region, 
    Round(sum(p.ProductUnitPrice * ol.QuantityOrdered), 2) Total
    from OrderDetail ol
    join customer c on ol.CustomerID = c.CustomerID
    join product p on ol.ProductID = p.ProductID
    join country cy on c.CountryID = cy.CountryID
    join region re on cy.RegionID = re.RegionID
    group by re.region
    order by total desc 
    """
# WRITE YOUR CODE HERE
    return sql_statement

def ex5(conn):
    
    # Simply, find the total for all the countries
    # Write an SQL statement that SELECTs From the OrderDetail table and joins with the Customer, Product, and Country table.
    # Pull out the following columns. 
    # Country
    # Total -- which is calculated from multiplying ProductUnitPrice with QuantityOrdered -- sum first and then round
    # ORDER BY Total Descending 

    sql_statement = """
    select cy.country, 
    round(sum(p.ProductUnitPrice * ol.QuantityOrdered)) as Total
    from OrderDetail ol
    join Customer c on ol.CustomerID = c.CustomerID
    join Product p on ol.ProductID = p.ProductID
    join Country cy on c.CountryID = cy.CountryID
    group by cy.Country
    order by Total DESC
    """

# WRITE YOUR CODE HERE
    return sql_statement


def ex6(conn):
    
    # Rank the countries within a region based on order total
    # Output Columns: Region, Country, CountryTotal, TotalRank
    # Hint: Round the the total
    # Hint: Sort ASC by Region

    sql_statement = """
    select re.region, cy.country, 
    round(sum(p.ProductUnitPrice * ol.QuantityOrdered), 0) CountryTotal,
    rank() over (partition by re.region order by sum(p.ProductUnitPrice * ol.QuantityOrdered) DESC) as TotalRank
    from OrderDetail ol

    join customer c on ol.CustomerID = c.CustomerID
    join product p on ol.ProductID = p.ProductID
    join country cy on c.CountryID = cy.CountryID
    join region re on cy.RegionID = re.RegionID
    GROUP BY re.Region, cy.Country
    order by re.Region ASC

    """
# WRITE YOUR CODE HERE
    df = pd.read_sql_query(sql_statement, conn)
    return sql_statement



def ex7(conn):
    
    # Rank the countries within a region based on order total, BUT only select the TOP country, meaning rank = 1!
    # Output Columns: Region, Country, Total, TotalRank
    # Hint: Round the the total
    # Hint: Sort ASC by Region
    # HINT: Use "WITH"

    sql_statement = """
  WITH RankedCountries AS (
  SELECT re.Region, cy.Country, 
  ROUND(SUM(p.ProductUnitPrice * ol.QuantityOrdered)) AS CountryTotal,
  RANK() OVER (PARTITION BY re.Region ORDER BY SUM(p.ProductUnitPrice * ol.QuantityOrdered) DESC) AS CountryRegionalRank
  FROM OrderDetail ol
  JOIN Customer c ON ol.CustomerID = c.CustomerID
  JOIN Product p ON ol.ProductID = p.ProductID
  JOIN Country cy on c.CountryID = cy.CountryID
  JOIN Region re ON cy.RegionID = re.RegionID
  GROUP BY re.Region, cy.Country 
  )

  SELECT Region, Country, CountryTotal, CountryRegionalRank
  FROM RankedCountries
  WHERE CountryRegionalRank = 1
  ORDER BY Region ASC


    """
# WRITE YOUR CODE HERE
    return sql_statement

def ex8(conn):
    
    # Sum customer sales by Quarter and year
    # Output Columns: Quarter,Year,CustomerID,Total
    # HINT: Use "WITH"
    # Hint: Round the the total
    # HINT: YOU MUST CAST YEAR TO TYPE INTEGER!!!!

    sql_statement = """
      WITH custsales AS (
          SELECT 
              CASE
                  WHEN CAST(SUBSTR(ol.OrderDate, 6, 2) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                  WHEN CAST(SUBSTR(ol.OrderDate, 6, 2) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                  WHEN CAST(SUBSTR(ol.OrderDate, 6, 2) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                  ELSE 'Q4'
              END AS Quarter,
              CAST(SUBSTR(ol.OrderDate, 1, 4) AS INTEGER) AS Year,
              ol.CustomerID,
              ROUND(SUM(p.ProductUnitPrice * ol.QuantityOrdered),0) AS Total
          FROM OrderDetail ol
          JOIN Product p ON ol.ProductID = p.ProductID
          GROUP BY Quarter, Year, ol.CustomerID
      )
      SELECT Quarter, Year, CustomerID, Total
      FROM custsales
      ORDER BY Year ASC, Quarter ASC, CustomerID ASC;


    """
# WRITE YOUR CODE HERE
    return sql_statement

def ex9(conn):
    
    # Rank the customer sales by Quarter and year, but only select the top 5 customers!
    # Output Columns: Quarter, Year, CustomerID, Total
    # HINT: Use "WITH"
    # Hint: Round the the total
    # HINT: YOU MUST CAST YEAR TO TYPE INTEGER!!!!
    # HINT: You can have multiple CTE tables;
    # WITH table1 AS (), table2 AS ()


    sql_statement = """

      WITH CustomerSales AS (
          SELECT
              CASE
                  WHEN CAST(SUBSTR(ol.OrderDate, 6, 2) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                  WHEN CAST(SUBSTR(ol.OrderDate, 6, 2) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                  WHEN CAST(SUBSTR(ol.OrderDate, 6, 2) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                  ELSE 'Q4'
              END AS Quarter,
              CAST(SUBSTR(ol.OrderDate, 1, 4) AS INTEGER) AS Year,
              ol.CustomerID,
              ROUND(SUM(p.ProductUnitPrice * ol.QuantityOrdered), 0) AS Total
          FROM OrderDetail ol
          JOIN Product p ON ol.ProductID = p.ProductID
          GROUP BY Quarter, Year, ol.CustomerID
      ),
      RankedSales AS (
          SELECT 
              Quarter, 
              Year, 
              CustomerID, 
              Total,
              RANK() OVER (PARTITION BY Quarter, Year ORDER BY Total DESC) AS CustomerRank
          FROM CustomerSales
      )
      SELECT Quarter, Year, CustomerID, Total, CustomerRank
      FROM RankedSales
      WHERE CustomerRank <= 5
      ORDER BY Year, Quarter, CustomerRank;

    """

# WRITE YOUR CODE HERE
    return sql_statement

def ex10(conn):
    
    # Rank the monthy sales
    # Output Columns: Quarter, Year, CustomerID, Total
    # HINT: Use "WITH"
    # Hint: Round the the total

    sql_statement = """
    WITH MonthlySale AS (
    SELECT 
    CASE SUBSTR(ol.OrderDate, 6,2)
    WHEN '01' THEN 'January'
    WHEN '02' THEN 'February'
    WHEN '03' THEN 'March'
    WHEN '04' THEN 'April'
    WHEN '05' THEN 'May'
    WHEN '06' THEN 'June'
    WHEN '07' THEN 'July'
    WHEN '08' THEN 'August'
    WHEN '09' THEN 'September'
    WHEN '10' THEN 'October'
    WHEN '11' THEN 'November'
    WHEN '12' THEN 'December'
    END AS Month,
    SUM(ROUND(p.ProductUnitPrice * ol.QuantityOrdered)) AS Total
    FROM Product p
    JOIN OrderDetail ol ON ol.ProductID = p.ProductID
    GROUP BY Month
  )
  SELECT Month, Round(Total) AS Total, 
  RANK() OVER (ORDER BY Total DESC) AS TotalRank
  From MonthlySale
    """

# WRITE YOUR CODE HERE
    return sql_statement

def ex11(conn):
    
    # Find the MaxDaysWithoutOrder for each customer 
    # Output Columns: 
    # CustomerID,
    # FirstName,
    # LastName,
    # Country,
    # OrderDate, 
    # PreviousOrderDate,
    # MaxDaysWithoutOrder
    # order by MaxDaysWithoutOrder desc
    # HINT: Use "WITH"; I created two CTE tables
    # HINT: Use Lag
    sql_statement = """

WITH CustomerOrders AS (
    SELECT 
        c.CustomerID,
        c.FirstName,
        c.LastName,
        cy.Country,
        od.OrderDate,
        LAG(od.OrderDate) OVER (PARTITION BY c.CustomerID ORDER BY od.OrderDate) AS PreviousOrderDate,
        JULIANDAY(od.OrderDate) - JULIANDAY(LAG(od.OrderDate) OVER (PARTITION BY c.CustomerID ORDER BY od.OrderDate)) AS DaysWithoutOrder
    FROM OrderDetail od
    JOIN Customer c ON od.CustomerID = c.CustomerID
    JOIN Country cy ON c.CountryID = cy.CountryID
),
MGap AS (
    SELECT 
        CustomerID, 
        MAX(DaysWithoutOrder) AS MaxDaysWithoutOrder
    FROM CustomerOrders
    WHERE DaysWithoutOrder IS NOT NULL
    GROUP BY CustomerID
)
SELECT 
    co.CustomerID,
    co.FirstName,
    co.LastName,
    co.Country,
    co.OrderDate,
    co.PreviousOrderDate,
    mg.MaxDaysWithoutOrder * 1.0 AS MaxDaysWithoutOrder
FROM CustomerOrders co
JOIN MaxGap mg 
    ON co.CustomerID = mg.CustomerID 
   AND co.DaysWithoutOrder = mg.MaxDaysWithoutOrder
WHERE co.OrderDate = (
    SELECT MIN(OrderDate)
    FROM CustomerOrders sub
    WHERE sub.CustomerID = co.CustomerID
      AND sub.DaysWithoutOrder = mg.MaxDaysWithoutOrder
)
ORDER BY MaxDaysWithoutOrder DESC, co.CustomerID DESC;
    """
# WRITE YOUR CODE HERE
    return sql_statement