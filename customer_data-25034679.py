import sqlite3
import random
import os
import math
from datetime import datetime, timedelta, date
import numpy as np
DB_PATH = "customer_data.db"
# Fixed seeds make the generated database reproducible.
SEED = 20261105
random.seed(SEED)
np.random.seed(SEED)
N_BASE_CUSTOMERS = 880
DUP_CUSTOMER_RATE = 0.02
N_ORDERS = 1150
MISSING = {
    "birth_year": 0.055,
    "satisfaction_score": 0.12,
    "postcode": 0.02,
    "payment_method": 0.015,
    "temperature_c": 0.02,
}
FIRST = [
    "Amelia", "Oliver", "Isla", "George", "Ava", "Noah", "Mia", "Leo",
    "Grace", "Arthur", "Freya", "Oscar", "Lily", "Harry", "Ella", "Jack",
    "Sofia", "Charlie", "Evie", "Thomas", "Aisha", "Adam", "Priya", "Ravi",
    "Fatima", "Zara", "Ibrahim", "Mei", "Daniel", "Emily", "Hassan", "Lucas",
    "Nina", "Arjun", "Layla", "Ethan", "Maya", "Hannah", "Yusuf", "Mariam",
    "Benjamin", "Ruby", "Jacob", "Imogen", "Samuel", "Anaya", "Joseph", "Leah",
    "Mohammed", "Chloe", "Reuben", "Anika", "Edward", "Ishaan", "Sana", "Ellie"
]
LAST = [
    "Smith", "Jones", "Taylor", "Brown", "Wilson", "Davies", "Evans", "Patel",
    "Khan", "Singh", "Walker", "Wright", "Robinson", "Wood", "Thompson", "White",
    "Hall", "Green", "Clark", "Lewis", "Young", "King", "Scott", "Adams",
    "Baker", "Ali", "Shah", "Chen", "Morgan", "Cooper", "Hughes", "Edwards",
    "Morris", "Price", "Bennett", "Reid", "Murphy", "Cook", "Bailey", "Foster",
    "Ward", "Brooks", "Kelly", "Richardson", "Cox", "Gray", "James", "Ahmed",
    "Begum", "Hussain", "Woodward", "Barnes", "Ross", "Dixon", "Pearson", "Webb"
]
# Weighted names and towns avoid uniform distributions.
LAST_W = [1/(r+1)**0.6 for r in range(len(LAST))]
TOWNS = [("Oxford","OX"),("Birmingham","B"),("Manchester","M"),("London","E"),
         ("Leeds","LS"),("Bristol","BS"),("Cambridge","CB"),("Nottingham","NG")]
TOWN_W = [0.10,0.17,0.15,0.30,0.09,0.08,0.04,0.07]
STORES = [
 ("ST001","Oxford City","Oxford","OX1",51.7520,-1.2577),
 ("ST002","Birmingham Central","Birmingham","B1",52.4862,-1.8904),
 ("ST003","Manchester Market","Manchester","M1",53.4808,-2.2426),
 ("ST004","London East","London","E1",51.5155,-0.0722),
 ("ST005","Leeds Centre","Leeds","LS1",53.8008,-1.5491),
 ("ST006","Bristol Harbour","Bristol","BS1",51.4545,-2.5879),
 ("ST007","Cambridge Square","Cambridge","CB1",52.2053,0.1218),
 ("ST008","Nottingham High Street","Nottingham","NG1",52.9548,-1.1581)]
STORE_BY_CITY = {s[2]: s[0] for s in STORES}
CITY_TEMP_OFFSET = {"Oxford":0,"Birmingham":-0.3,"Manchester":-0.8,"London":0.8,
                    "Leeds":-1.0,"Bristol":0.5,"Cambridge":-0.2,"Nottingham":-0.4}
CATALOGUE = {
 "Home": ([("Reusable Water Bottle",12.50),("Desk Lamp",22.50),("Storage Basket",16.75),
           ("Notebook Set",7.25),("Scented Candle",9.50)], ["Eco","Premium","Compact","Large"]),
 "Grocery": ([("Coffee Beans 500g",8.40),("Pasta 1kg",2.20),("Protein Bar Box",13.25),
              ("Porridge Oats 1kg",2.60),("Olive Oil 500ml",6.90)], ["Organic","Family Pack","Value","Premium"]),
 "Electronics": ([("Wireless Earbuds",39.99),("Phone Charger",11.99),("Bluetooth Speaker",27.99),
                  ("Power Bank",19.99)], ["Mini","Pro","Travel","Rugged"]),
 "Beauty": ([("Face Moisturiser",9.80),("Shampoo",5.60),("Sunscreen SPF30",10.50),
             ("Hand Cream",4.80)], ["Sensitive","Travel Size","Fragrance Free","Hydrating"]),
 "Clothing": ([("Cotton T-Shirt",14.00),("Hoodie",32.00),("Wool Scarf",18.00),
               ("Denim Jacket",54.00)], ["Organic","Lightweight","Relaxed Fit","Classic"]),
 "Books": ([("Paperback Novel",8.99),("Cookbook",15.99),("Travel Guide",12.99),
            ("Sketchbook",6.75)], ["Illustrated","Gift Edition","Pocket Edition","Hardback"]),
 "Sports": ([("Yoga Mat",24.99),("Resistance Bands",12.99),("Running Socks",6.50),
             ("Football",16.00)], ["Beginner","Pro","Compact","Outdoor"]),
}
PARTNER_CATEGORY = {"Sports":"Grocery","Books":"Grocery","Beauty":"Beauty","Electronics":"Electronics",
                    "Home":"Home","Clothing":"Sports","Grocery":"Books"}
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE customers (
 customer_id TEXT PRIMARY KEY,
 first_name TEXT NOT NULL,
 last_name TEXT NOT NULL,
 email TEXT NOT NULL UNIQUE,
 postcode TEXT,
 town TEXT NOT NULL,
 birth_year INTEGER CHECK(birth_year BETWEEN 1940 AND 2008 OR birth_year IS NULL),
 gender TEXT NOT NULL CHECK(gender IN ('Female','Male','Non-binary','Prefer not to say')),
 loyalty_tier TEXT NOT NULL CHECK(loyalty_tier IN ('Bronze','Silver','Gold','Platinum')),
 joined_date TEXT NOT NULL,
 satisfaction_score INTEGER CHECK(satisfaction_score BETWEEN 1 AND 5 OR satisfaction_score IS NULL)
);
CREATE TABLE products (
 product_id INTEGER PRIMARY KEY,
 product_name TEXT NOT NULL UNIQUE,
 category TEXT NOT NULL CHECK(category IN ('Home','Grocery','Electronics','Beauty','Clothing','Books','Sports')),
 list_price REAL NOT NULL CHECK(list_price > 0),
 demand_band TEXT NOT NULL CHECK(demand_band IN ('Low','Medium','High')),
 product_status TEXT NOT NULL CHECK(product_status IN ('Active','Discontinued')),
 discontinued_date TEXT,
 CHECK((product_status='Discontinued') = (discontinued_date IS NOT NULL))
);
CREATE TABLE stores (
 store_id TEXT PRIMARY KEY,
 store_name TEXT NOT NULL UNIQUE,
 city TEXT NOT NULL,
 postcode_area TEXT NOT NULL,
 latitude REAL NOT NULL CHECK(latitude BETWEEN 49 AND 60),
 longitude REAL NOT NULL CHECK(longitude BETWEEN -8 AND 2)
);
CREATE TABLE orders (
 order_id INTEGER PRIMARY KEY,
 customer_id TEXT NOT NULL REFERENCES customers(customer_id),
 store_id TEXT NOT NULL REFERENCES stores(store_id),
 order_datetime TEXT NOT NULL,
 order_channel TEXT NOT NULL CHECK(order_channel IN ('In-store','Web','Mobile app')),
 order_status TEXT NOT NULL CHECK(order_status IN ('Completed','Returned','Cancelled')),
 temperature_c REAL CHECK(temperature_c BETWEEN -10 AND 40 OR temperature_c IS NULL)
);
CREATE TABLE order_items (
 order_id INTEGER NOT NULL REFERENCES orders(order_id),
 line_number INTEGER NOT NULL CHECK(line_number > 0),
 product_id INTEGER NOT NULL REFERENCES products(product_id),
 quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 12),
 unit_price REAL NOT NULL CHECK(unit_price > 0),
 discount_pct REAL NOT NULL CHECK(discount_pct BETWEEN 0 AND 0.70),
 PRIMARY KEY(order_id, line_number),
 UNIQUE(order_id, product_id)
);
CREATE TABLE store_inventory (
 store_id TEXT NOT NULL REFERENCES stores(store_id),
 product_id INTEGER NOT NULL REFERENCES products(product_id),
 stock_level INTEGER NOT NULL CHECK(stock_level >= 0),
 reorder_level INTEGER NOT NULL CHECK(reorder_level >= 0),
 last_counted TEXT,
 PRIMARY KEY(store_id, product_id)
);
CREATE TABLE payments (
 payment_id INTEGER PRIMARY KEY,
 order_id INTEGER NOT NULL UNIQUE REFERENCES orders(order_id),
 payment_method TEXT CHECK(payment_method IN ('Card','Cash','Gift card','Digital wallet') OR payment_method IS NULL),
 amount_paid REAL NOT NULL CHECK(amount_paid >= 0),
 payment_status TEXT NOT NULL CHECK(payment_status IN ('Paid','Refunded','Pending'))
);
CREATE TABLE raw_import_staging (
 raw_record_id INTEGER PRIMARY KEY,
 source_batch TEXT NOT NULL,
 customer_email TEXT,
 product_label TEXT,
 recorded_quantity INTEGER,
 notes TEXT
);
"""
def build_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    cur.executescript(SCHEMA)
    customers = []
    END_DATE = datetime(2026, 10, 31)
    def make_customer(i):
        first = random.choice(FIRST)
        last = random.choices(LAST, weights=LAST_W)[0]
        town = random.choices([t[0] for t in TOWNS], weights=TOWN_W)[0]
        prefix = dict(TOWNS)[town]
        postcode = (f"{prefix}{random.randint(1,9)} {random.randint(1,9)}"
                    f"{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}")
        joined = datetime(2019, 1, 1) + timedelta(days=random.randint(0, 2800))
        while True:
            age_at_join = np.random.normal(38, 13)
            if 18 <= age_at_join <= 80 and joined.year - int(age_at_join) >= 1940:
                break
        birth_year = joined.year - int(age_at_join)
        gender = random.choices(["Female","Male","Non-binary","Prefer not to say"],
                                weights=[0.49,0.47,0.02,0.02])[0]
        tier = random.choices(["Bronze","Silver","Gold","Platinum"], weights=[0.45,0.32,0.17,0.06])[0]
        satisfaction = random.choices([1,2,3,4,5], weights=[0.05,0.08,0.17,0.35,0.35])[0]
        return dict(first=first, last=last, town=town, postcode=postcode, joined=joined,
                    birth_year=birth_year, gender=gender, tier=tier, sat=satisfaction,
                    )
    # Add controlled near-duplicates to practise matching customer records.
    base = [make_customer(i) for i in range(N_BASE_CUSTOMERS)]
    n_dups = int(round(N_BASE_CUSTOMERS * DUP_CUSTOMER_RATE))
    dup_sources = random.sample(range(N_BASE_CUSTOMERS), n_dups)
    people = list(base)
    for src in dup_sources:
        d = dict(base[src])
        if random.random() < 0.5 and len(d["last"]) > 3:
            k = random.randint(1, len(d["last"]) - 2)
            d["last"] = d["last"][:k] + d["last"][k+1:]
        d["joined"] = base[src]["joined"] + timedelta(days=random.randint(30, 600))
        if d["joined"] > END_DATE - timedelta(days=30):
            d["joined"] = END_DATE - timedelta(days=30)
        people.append(d)
    # Missing values are inserted deliberately using the rates in MISSING.
    m_birth = m_sat = m_post = 0
    for i, p in enumerate(people):
        birth_year = p["birth_year"]
        if random.random() < MISSING["birth_year"]:
            birth_year = None
            m_birth += 1
        sat = p["sat"]
        if random.random() < MISSING["satisfaction_score"]:
            sat = None
            m_sat += 1
        postcode = p["postcode"]
        if random.random() < MISSING["postcode"]:
            postcode = None
            m_post += 1
        first = p["first"].lower()
        last = p["last"].lower()
        email_style = random.choice((1, 2, 3, 4))
        if email_style == 1:
            email = f"{first}.{last}{i + 1:04d}@example.invalid"
        elif email_style == 2:
            email = f"{first[0]}{last}{i + 1:04d}@example.invalid"
        elif email_style == 3:
            email = f"{first}_{last}{i + 1:04d}@example.invalid"
        else:
            email = f"{last}.{first}{i + 1:04d}@example.invalid"
        customers.append((f"C{i+1:05d}", p["first"], p["last"], email, postcode, p["town"],
                          birth_year, p["gender"], p["tier"], p["joined"].date().isoformat(),
                          sat))
    cur.executemany("INSERT INTO customers VALUES(?,?,?,?,?,?,?,?,?,?,?)", customers)
    nc = len(customers)
    products = []
    pid = 0
    base_index = []
    for category, (bases, variants) in CATALOGUE.items():
        for name, price in bases:
            bi = len(set(base_index))
            for v in [None] + variants:
                pid += 1
                pname = name if v is None else f"{v} {name}"
                pprice = price if v is None else round(price * np.random.uniform(0.85, 1.30), 2)
                products.append([pid, pname, category, pprice, "Medium", "Active", None])
                base_index.append(bi)
    n_prod = len(products)
    for p in random.sample(products, int(n_prod * 0.08)):
        p[5] = "Discontinued"
        p[6] = (datetime(2024, 6, 1) + timedelta(days=random.randint(0, 760))).date().isoformat()
    disc_ord = np.array([date.fromisoformat(p[6]).toordinal() if p[6] else 10**9 for p in products])
    cat_arr = np.array([p[2] for p in products])
    base_pop = np.random.lognormal(0, 0.8, size=len(set(base_index)))
    base_w = np.array([base_pop[b] * (1.0 if products[i][1] in
                       [x[0] for c in CATALOGUE.values() for x in c[0]] else 0.5)
                       for i, b in enumerate(base_index)])
    cur.executemany("INSERT INTO stores VALUES(?,?,?,?,?,?)", STORES)
    cur.executemany("INSERT INTO products VALUES(?,?,?,?,?,?,?)", [tuple(p) for p in products])
    start = datetime(2024, 1, 1)
    all_days = [start + timedelta(days=d) for d in range((END_DATE - start).days + 1)]
    dw = []
    for day in all_days:
        w = 1.35 if day.weekday() >= 5 else 1.0
        if day.month in (11, 12): w *= 1.25
        if day.month in (1, 2): w *= 0.82
        dw.append(w)
    dw = np.array(dw)
    cum_days = np.cumsum(dw / dw.sum())
    cust_ids = [c[0] for c in customers]
    cust_join = [date.fromisoformat(c[9]) for c in customers]
    cust_town = [c[5] for c in customers]
    cw = np.random.gamma(1.5, 1.0, size=nc)
    cw /= cw.sum()
    store_city = {s[0]: s[2] for s in STORES}
    orders, order_items, payments = [], [], []
    units_sold = np.zeros(n_prod)
    m_temp = m_pay = 0
    for order_id in range(1, N_ORDERS + 1):
        ci = int(np.random.choice(nc, p=cw))
        lo = max(0, (cust_join[ci] - start.date()).days)
        lo_cum = cum_days[lo - 1] if lo > 0 else 0.0
        di = int(np.searchsorted(cum_days, np.random.uniform(lo_cum, 1.0), side="right"))
        day = all_days[min(di, len(all_days) - 1)]
        channel = random.choices(["In-store","Web","Mobile app"], weights=[0.53,0.30,0.17])[0]
        if channel == "In-store":
            hour = random.randint(8, 21)
        else:
            hour = random.choices(range(24), weights=[1,1,1,1,1,1,2,3,4,4,4,4,5,5,4,4,4,5,6,8,9,9,6,3])[0]
        dt = day + timedelta(hours=hour, minutes=random.randint(0, 59))
        home_store = STORE_BY_CITY[cust_town[ci]]
        store_id = home_store if random.random() < 0.85 else random.choice(STORES)[0]
        status = random.choices(["Completed","Returned","Cancelled"], weights=[0.94,0.045,0.015])[0]
        seasonal_mean = 10 + 8 * math.sin((dt.month - 4) / 12 * 2 * math.pi) + CITY_TEMP_OFFSET[store_city[store_id]]
        temp = round(float(np.clip(np.random.normal(seasonal_mean, 4), -4, 29)), 1)
        if random.random() < MISSING["temperature_c"]:
            temp = None
            m_temp += 1
        orders.append((order_id, cust_ids[ci], store_id, dt.isoformat(timespec="minutes"), channel, status, temp))
        avail = disc_ord > day.toordinal()
        basket_size = random.choices([1,2,3,4,5,6], weights=[0.28,0.29,0.20,0.12,0.07,0.04])[0]
        w = base_w * avail
        chosen = [int(np.random.choice(n_prod, p=w / w.sum()))]
        for _ in range(basket_size - 1):
            w = base_w * avail
            # Complementary categories create useful basket associations.
            if random.random() < 0.40:
                w = w * (cat_arr == PARTNER_CATEGORY[products[chosen[0]][2]])
            w[chosen] = 0
            if w.sum() == 0:
                w = base_w * avail
                w[chosen] = 0
            chosen.append(int(np.random.choice(n_prod, p=w / w.sum())))
        total = 0.0
        for line_number, pi in enumerate(chosen, start=1):
            qty = random.choices([1,2,3,4], weights=[0.70,0.20,0.08,0.02])[0]
            unit_price = round(products[pi][3] * np.random.uniform(0.92, 1.08), 2)
            disc = random.choices([0,0.05,0.10,0.15,0.20], weights=[0.60,0.15,0.14,0.08,0.03])[0]
            order_items.append((order_id, line_number, products[pi][0], qty, unit_price, disc))
            total += qty * unit_price * (1 - disc)
            if status == "Completed":
                units_sold[pi] += qty
        if channel == "In-store":
            method = random.choices(["Card","Cash","Gift card","Digital wallet"], weights=[0.56,0.18,0.08,0.18])[0]
        else:
            method = random.choices(["Card","Gift card","Digital wallet"], weights=[0.62,0.08,0.30])[0]
        if random.random() < MISSING["payment_method"]:
            method = None
            m_pay += 1
        pstatus = "Refunded" if status == "Returned" else "Pending" if status == "Cancelled" else "Paid"
        payments.append((order_id, order_id, method, round(total, 2), pstatus))
    cur.executemany("INSERT INTO orders VALUES(?,?,?,?,?,?,?)", orders)
    cur.executemany("INSERT INTO order_items VALUES(?,?,?,?,?,?)", order_items)
    cur.executemany("INSERT INTO payments VALUES(?,?,?,?,?)", payments)
    order_rank = np.argsort(np.argsort(units_sold)) / n_prod
    for i, p in enumerate(products):
        p[4] = "Low" if order_rank[i] < 1/3 else "Medium" if order_rank[i] < 2/3 else "High"
    cur.executemany("UPDATE products SET demand_band=? WHERE product_id=?", [(p[4], p[0]) for p in products])
    inv, m_cnt = [], 0
    mean_stock = {"Low": 12, "Medium": 30, "High": 70}
    for s in STORES:
        for p in products:
            # Some store-product pairs are absent to model sparse stock.
            if random.random() > 0.85:
                continue
            m = mean_stock[p[4]] * (0.3 if p[5] == "Discontinued" else 1.0)
            stock = int(np.random.poisson(m))
            reorder = max(2, int(m * 0.3))
            counted = (datetime(2026, 10, 31) - timedelta(days=random.randint(0, 90))).date().isoformat()
            if random.random() < 0.03:
                counted = None
                m_cnt += 1
            inv.append((s[0], p[0], stock, reorder, counted))
    cur.executemany("INSERT INTO store_inventory VALUES(?,?,?,?,?)", inv)
    sample = random.sample(order_items, 150)
    cust_email = {c[0]: c[3] for c in customers}
    order_cust = {o[0]: o[1] for o in orders}
    staging = []
    n_miss_email = n_miss_label = n_messy = 0
    for k, it in enumerate(sample, start=1):
        email = cust_email[order_cust[it[0]]]
        label = products[it[2] - 1][1]
        note = None
        r = random.random()
        if r < 0.04:
            email = None
            n_miss_email += 1
            note = "Missing email"
        elif r < 0.08:
            label = None
            n_miss_label += 1
            note = "Missing product label"
        elif r < 0.12:
            label = random.choice([label.upper(), label.lower(), label + " "])
            n_messy += 1
            note = "Inconsistent case/whitespace in label"
        staging.append([k, random.choice(["batch_A","batch_B","batch_C"]), email, label, it[3], note])
    # Add staging anomalies for data-cleaning practice.
    n_exact = int(len(staging) * 0.03)
    for src in random.sample(staging, n_exact):
        staging.append([len(staging) + 1, src[1], src[2], src[3], src[4], "Duplicate source fields from record %d" % src[0]])
    cur.executemany("INSERT INTO raw_import_staging VALUES(?,?,?,?,?,?)", [tuple(s) for s in staging])
    ns = len(staging)
    con.commit()
    print("Database:", os.path.abspath(DB_PATH))
    for t in ["customers","products","stores","orders","order_items","store_inventory","payments",
              "raw_import_staging"]:
        print(f"{t:20s}", cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    con.close()
if __name__ == "__main__":
    build_database()