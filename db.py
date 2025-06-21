import sqlite3
import pandas as pd
import os
import json
from datetime import datetime, timedelta

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'stock_data.db')

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create stock basic info table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_basic (
        ts_code TEXT PRIMARY KEY,
        symbol TEXT,
        name TEXT,
        area TEXT,
        industry TEXT,
        last_updated TIMESTAMP
    )
    ''')
    
    # Create price data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_code TEXT,
        trade_date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        pre_close REAL,
        change REAL,
        pct_chg REAL,
        vol REAL,
        amount REAL,
        UNIQUE(ts_code, trade_date)
    )
    ''')
    
    # Create sector comparison data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sector_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sector TEXT,
        data_json TEXT,
        fetch_time TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def save_stock_basic(df):
    """Save stock basic information to database with better error handling"""
    if df is None or df.empty:
        print("保存股票基本信息失败: 数据为空")
        return False
    
    print(f"准备保存 {len(df)} 条股票基本信息到数据库...")
    conn = sqlite3.connect(DB_PATH)
    # Add last_updated column
    df['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Ensure market column exists
        if 'market' not in df.columns:
            df['market'] = 'CN'  # Default to Chinese market
        
        # Save to database
        print("执行数据库保存操作...")
        df.to_sql('stock_basic', conn, if_exists='replace', index=False)
        print("股票基本信息保存完成")
        
        # Show statistics
        cursor = conn.cursor()
        cursor.execute("SELECT market, COUNT(*) FROM stock_basic GROUP BY market")
        market_stats = cursor.fetchall()
        print("保存的股票统计:")
        for market, count in market_stats:
            market_name = {'CN': 'A股', 'HK': '港股', None: '其他'}.get(market, market)
            print(f"  {market_name}: {count} 只")
        
        conn.close()
        return True
    except Exception as e:
        print(f"保存股票基本信息到数据库时发生错误: {e}")
        conn.close()
        return False

def get_stock_basic():
    """Retrieve all stock basic info from database"""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql('SELECT * FROM stock_basic', conn)
        conn.close()
        return df
    except:
        conn.close()
        return None

def get_stock_code_from_db(stock_name):
    """Get stock code from database by name with fuzzy matching"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Try exact match first
    cursor.execute('SELECT ts_code FROM stock_basic WHERE name = ?', (stock_name,))
    result = cursor.fetchone()
    
    if result:
        conn.close()
        return result[0]
    
    # Try fuzzy matching for common variations
    name_patterns = [
        f'%{stock_name}%',  # Contains the name
        f'{stock_name}%',   # Starts with the name
        f'%{stock_name}',   # Ends with the name
    ]
    
    for pattern in name_patterns:
        cursor.execute('SELECT ts_code, name FROM stock_basic WHERE name LIKE ? LIMIT 5', (pattern,))
        results = cursor.fetchall()
        
        if results:
            # If multiple matches, try to find the best one
            for ts_code, db_name in results:
                # Prefer exact matches without extra words
                if db_name == stock_name:
                    conn.close()
                    return ts_code
                # Prefer matches that start with the search term
                if db_name.startswith(stock_name):
                    print(f"模糊匹配找到: '{stock_name}' -> '{db_name}' ({ts_code})")
                    conn.close()
                    return ts_code
            
            # If no perfect match, return the first result
            ts_code, db_name = results[0]
            print(f"模糊匹配找到: '{stock_name}' -> '{db_name}' ({ts_code})")
            conn.close()
            return ts_code
    
    conn.close()
    return None

def save_daily_price(df):
    """Save daily price data to database"""
    if df is None or df.empty:
        print("保存股票价格数据失败: 数据为空")
        return False
    
    print(f"准备保存 {len(df)} 条股票价格记录到数据库...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Convert DataFrame to list of tuples for batch insertion
        records = df.to_dict('records')
        new_records = 0
        updated_records = 0
        
        for record in records:
            # Check if this record already exists
            cursor.execute(
                'SELECT id FROM daily_prices WHERE ts_code = ? AND trade_date = ?',
                (record['ts_code'], record['trade_date'])
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                update_fields = []
                update_values = []
                
                for key, value in record.items():
                    if key not in ('ts_code', 'trade_date'):
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                # Add the WHERE clause parameters
                update_values.append(record['ts_code'])
                update_values.append(record['trade_date'])
                
                cursor.execute(
                    f"UPDATE daily_prices SET {', '.join(update_fields)} WHERE ts_code = ? AND trade_date = ?",
                    update_values
                )
                updated_records += 1
            else:
                # Insert new record
                placeholders = ', '.join(['?'] * len(record))
                fields = ', '.join(record.keys())
                cursor.execute(
                    f"INSERT INTO daily_prices ({fields}) VALUES ({placeholders})",
                    list(record.values())
                )
                new_records += 1
    
        conn.commit()
        print(f"股票价格数据保存完成: {new_records} 条新记录, {updated_records} 条更新记录")
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"保存股票价格数据时发生错误: {e}")
        return False

def get_daily_prices(ts_code, start_date=None, end_date=None, limit=None):
    """Retrieve daily price data for a stock code within date range"""
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT * FROM daily_prices WHERE ts_code = ?"
    params = [ts_code]
    
    if start_date:
        query += " AND trade_date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND trade_date <= ?"
        params.append(end_date)
    
    query += " ORDER BY trade_date DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(int(limit))
    
    try:
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        conn.close()
        print(f"Error retrieving daily prices: {e}")
        return pd.DataFrame()  # Return empty DataFrame instead of None

def save_sector_data(sector, data):
    """Save sector comparison data as JSON"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_json = json.dumps(data)
    
    cursor.execute(
        'INSERT INTO sector_data (sector, data_json, fetch_time) VALUES (?, ?, ?)',
        (sector, data_json, now)
    )
    
    conn.commit()
    conn.close()
    return True

def get_latest_sector_data(sector, max_age_minutes=30):
    """Get the latest sector data if it's fresh enough"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calculate the oldest acceptable timestamp
        oldest_acceptable = (datetime.now() - timedelta(minutes=max_age_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        # First try to get data newer than the specified age
        cursor.execute(
            'SELECT data_json, fetch_time FROM sector_data WHERE sector = ? AND fetch_time > ? ORDER BY fetch_time DESC LIMIT 1',
            (sector, oldest_acceptable)
        )
        
        result = cursor.fetchone()
        
        # If no fresh data, try to get any data for this sector as a fallback
        if not result:
            cursor.execute(
                'SELECT data_json, fetch_time FROM sector_data WHERE sector = ? ORDER BY fetch_time DESC LIMIT 1',
                (sector,)
            )
            result = cursor.fetchone()
            # If we found older data, log that we're using it
            if result:
                print(f"警告: 使用过期的 {sector} 行业数据 (获取时间: {result[1]})")
        
        conn.close()
        
        if result:
            try:
                return json.loads(result[0]), result[1]
            except json.JSONDecodeError:
                print(f"Error decoding JSON for sector {sector}")
                return [], result[1]
        return None, None
    except Exception as e:
        print(f"Error retrieving sector data: {e}")
        return None, None

def is_data_fresh(ts_code, days=1):
    """Check if we have fresh data for a stock"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate the oldest acceptable timestamp
    oldest_acceptable = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cursor.execute(
        'SELECT COUNT(*) FROM daily_prices WHERE ts_code = ? AND trade_date >= ?',
        (ts_code, oldest_acceptable.replace('-', ''))
    )
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

# Initialize database when module is imported
init_db()
