import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
from sector import SECTORS
import db

# Initialize with your Tushare token
ts.set_token('')
pro = ts.pro_api()

def update_stock_basic_data():
    """Update the stock basic info database including Hong Kong stocks"""
    try:
        print("从Tushare获取股票基本信息...")
        
        # Get A-share basic info
        print("获取A股基本信息...")
        a_stock_info = pro.stock_basic(exchange='', list_status='L', 
                                      fields='ts_code,symbol,name,area,industry,market')
        
        # Get Hong Kong stock basic info
        print("获取港股基本信息...")
        try:
            hk_stock_info = pro.hk_basic(fields='ts_code,name,fullname,enname,market')
            # Add market column for consistency
            if hk_stock_info is not None and not hk_stock_info.empty:
                hk_stock_info['symbol'] = hk_stock_info['ts_code'].str.replace('.HK', '')
                hk_stock_info['area'] = '香港'
                hk_stock_info['industry'] = '港股'
                hk_stock_info['market'] = 'HK'
                print(f"成功获取 {len(hk_stock_info)} 条港股基本信息")
            else:
                print("港股基本信息获取失败或为空")
                hk_stock_info = pd.DataFrame()
        except Exception as e:
            print(f"获取港股基本信息时发生错误: {e}")
            hk_stock_info = pd.DataFrame()
        
        # Combine A-share and HK stock info
        if a_stock_info is not None and not a_stock_info.empty:
            if not hk_stock_info.empty:
                # Ensure columns match
                common_columns = ['ts_code', 'symbol', 'name', 'area', 'industry', 'market']
                a_stock_info = a_stock_info[common_columns] if 'market' in a_stock_info.columns else a_stock_info
                hk_stock_info = hk_stock_info[common_columns]
                
                stock_info = pd.concat([a_stock_info, hk_stock_info], ignore_index=True)
                print(f"合并后总计 {len(stock_info)} 条股票基本信息")
            else:
                stock_info = a_stock_info
                print(f"仅A股数据，总计 {len(stock_info)} 条股票基本信息")
        else:
            print("A股基本信息获取失败")
            return False
        
        # Save to database
        print("正在保存股票基本信息到数据库...")
        save_success = db.save_stock_basic(stock_info)
        
        if save_success:
            print("股票基本信息保存到数据库成功")
        else:
            print("股票基本信息保存到数据库失败")
            
        return save_success
    except Exception as e:
        print(f"更新股票基本信息发生错误: {e}")
        return False

def get_stock_code(stock_name):
    """Get stock code by name, with support for both A-shares and HK stocks"""
    try:
        # Try to get from database first
        code = db.get_stock_code_from_db(stock_name)
        if code:
            return code
            
        # Try variations of the stock name for better matching
        stock_name_variations = [
            stock_name,
            stock_name.replace('集团', ''),
            stock_name.replace('股份', ''),
            stock_name.replace('有限公司', ''),
            stock_name.replace('公司', ''),
            stock_name + '集团',
            stock_name + '股份'
        ]
        
        for variation in stock_name_variations:
            code = db.get_stock_code_from_db(variation)
            if code:
                print(f"通过名称变体 '{variation}' 找到股票 '{stock_name}' 的代码: {code}")
                return code
            
        print(f"数据库中未找到股票 '{stock_name}' 的代码，尝试更新股票基本数据...")
        
        # If not in database, update stock basic data then try again
        if callable(update_stock_basic_data):
            update_stock_basic_data()
        else:
            print("警告: update_stock_basic_data 不可调用")
            
        # Try again with variations after update
        for variation in stock_name_variations:
            code = db.get_stock_code_from_db(variation)
            if code:
                print(f"更新后通过名称变体 '{variation}' 找到股票 '{stock_name}' 的代码: {code}")
                return code
            
        # If still not found, return None
        print(f"无法找到股票 '{stock_name}' 的代码")
        return None
    except Exception as e:
        print(f"获取股票 '{stock_name}' 代码时发生错误: {e}")
        return None

def update_daily_data(stock_code, days=120):
    """Update daily price data for a single stock
    
    This is a wrapper around update_daily_data_batch for backward compatibility.
    
    Args:
        stock_code: Stock code to update
        days: Number of days of history to retrieve (default 120 for 4 months)
        
    Returns:
        bool: Success or failure
    """
    print(f"更新单只股票 {stock_code} 的历史数据...")
    
    # Call the batch function with a single stock
    results = update_daily_data_batch([stock_code], days=days)
    
    # Return the result for this stock
    return results.get(stock_code, False)

def update_daily_data_batch(stock_codes, days=120):
    """Update daily price data for multiple stocks at once, supporting both A-shares and HK stocks"""
    if not stock_codes:
        return {}
        
    print(f"批量获取 {len(stock_codes)} 只股票的历史数据...")
    
    # Separate A-shares and HK stocks
    a_stock_codes = [code for code in stock_codes if not code.endswith('.HK')]
    hk_stock_codes = [code for code in stock_codes if code.endswith('.HK')]
    
    print(f"其中A股 {len(a_stock_codes)} 只，港股 {len(hk_stock_codes)} 只")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for Tushare
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    results = {}
    
    try:
        # Process A-shares
        if a_stock_codes:
            print("处理A股数据...")
            chunk_size = 50
            
            for i in range(0, len(a_stock_codes), chunk_size):
                chunk = a_stock_codes[i:i+chunk_size]
                print(f"正在处理第 {i//chunk_size + 1} 批A股数据 ({len(chunk)} 只)...")
                
                for stock_code in chunk:
                    try:
                        print(f"  获取A股 {stock_code} 的历史数据...")
                        hist_data = pro.daily(ts_code=stock_code, 
                                          start_date=start_date_str, 
                                          end_date=end_date_str)
                        
                        if hist_data.empty:
                            print(f"  A股 {stock_code} 在指定日期范围内没有数据")
                            results[stock_code] = False
                            continue
                            
                        print(f"  成功获取A股 {stock_code} 的 {len(hist_data)} 条历史数据记录")
                        
                        # Save to database
                        success = db.save_daily_price(hist_data)
                        results[stock_code] = success
                        
                    except Exception as e:
                        print(f"  获取或保存A股 {stock_code} 的数据时发生错误: {e}")
                        results[stock_code] = False
        
        # Process Hong Kong stocks
        if hk_stock_codes:
            print("处理港股数据...")
            chunk_size = 30  # Smaller chunks for HK stocks as they might have different limits
            
            for i in range(0, len(hk_stock_codes), chunk_size):
                chunk = hk_stock_codes[i:i+chunk_size]
                print(f"正在处理第 {i//chunk_size + 1} 批港股数据 ({len(chunk)} 只)...")
                
                for stock_code in chunk:
                    try:
                        print(f"  获取港股 {stock_code} 的历史数据...")
                        # Use hk_daily for Hong Kong stocks
                        hist_data = pro.hk_daily(ts_code=stock_code,
                                               start_date=start_date_str,
                                               end_date=end_date_str)
                        
                        if hist_data.empty:
                            print(f"  港股 {stock_code} 在指定日期范围内没有数据")
                            results[stock_code] = False
                            continue
                            
                        print(f"  成功获取港股 {stock_code} 的 {len(hist_data)} 条历史数据记录")
                        
                        # Save to database
                        success = db.save_daily_price(hist_data)
                        results[stock_code] = success
                        
                    except Exception as e:
                        print(f"  获取或保存港股 {stock_code} 的数据时发生错误: {e}")
                        results[stock_code] = False
        
        return results
        
    except Exception as e:
        print(f"批量获取股票数据过程中发生错误: {e}")
        return {code: False for code in stock_codes}

def get_all_sector_stocks_data(days=120):
    """Get all sector stocks data in a single operation"""
    print("\n======== 开始一次性获取所有行业股票数据 ========")
    try:
        # First update stock basic data
        print("更新股票基本信息...")
        update_stock_basic_data()
        
        # Get all unique stocks from all sectors
        all_stocks = set()
        for sector, stocks in SECTORS.items():
            all_stocks.update(stocks)
        
        print(f"总共需要获取 {len(all_stocks)} 只股票数据")
        
        # Get all stock codes first
        print("获取所有股票代码...")
        stock_codes = {}  # Dictionary mapping stock name to stock code
        stock_names = {}  # Reverse mapping from code to name
        missing_stocks = []
        
        for stock_name in all_stocks:
            code = get_stock_code(stock_name)
            if code:
                stock_codes[stock_name] = code
                stock_names[code] = stock_name
            else:
                missing_stocks.append(stock_name)
                
        if missing_stocks:
            print(f"警告: 未找到 {len(missing_stocks)} 只股票的代码")
            
        print(f"成功获取 {len(stock_codes)} 只股票代码")
        
        # Calculate date range for all stocks
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        # Batch update all stock data at once
        print(f"批量更新所有股票从 {start_date_str} 到 {end_date_str} 的历史数据...")
        code_list = list(stock_codes.values())
        update_results = update_daily_data_batch(code_list, days=days)
        
        # Check update statistics
        update_success_count = sum(1 for success in update_results.values() if success)
        update_fail_count = len(update_results) - update_success_count
        print(f"数据更新结果: {update_success_count} 成功, {update_fail_count} 失败")
        
        # Create the result data structure
        result = {}
        for sector, stock_names_list in SECTORS.items():
            print(f"处理 {sector} 行业的 {len(stock_names_list)} 只股票数据...")
            sector_data = []
            
            for stock_name in stock_names_list:
                stock_code = stock_codes.get(stock_name)
                if not stock_code:
                    print(f"  - 跳过 {stock_name}: 未找到股票代码")
                    continue
                
                # Check if this stock was successfully updated
                if stock_code in update_results and not update_results[stock_code]:
                    print(f"  - 跳过 {stock_name}: 数据更新失败")
                    continue
                
                # Retrieve data from database (should be already updated)
                try:
                    # Get latest price from database
                    latest_price_df = db.get_daily_prices(stock_code, limit=1)
                    if latest_price_df.empty:
                        print(f"  - 跳过 {stock_name}: 无法获取最新价格")
                        continue
                    
                    latest_price = latest_price_df['close'].values[0]
                    latest_volume = latest_price_df['vol'].values[0]  # Get latest volume
                    
                    # Get all data for the period to find highest price and max volume
                    hist_data = db.get_daily_prices(stock_code, start_date_str, end_date_str)
                    if hist_data.empty:
                        print(f"  - 跳过 {stock_name}: 无法获取历史数据")
                        continue
                        
                    # Find highest price
                    hist_data = hist_data.sort_values('trade_date')
                    highest_price_row = hist_data.loc[hist_data['high'].idxmax()]
                    highest_price = highest_price_row['high']
                    highest_date = highest_price_row['trade_date']
                    
                    # Find maximum volume over 4 months
                    max_volume = hist_data['vol'].max()
                    
                    # Calculate volume ratio
                    volume_ratio = (latest_volume / max_volume * 100) if max_volume > 0 else 0
                    
                    # Convert date format for display, fixing future dates
                    try:
                        formatted_date = datetime.strptime(str(highest_date), '%Y%m%d')
                        # Check if date is in the future
                        if formatted_date > datetime.now():
                            print(f"  注意: 检测到未来日期 {highest_date}，使用当前日期代替")
                            formatted_date = datetime.now()
                        formatted_date = formatted_date.strftime('%Y-%m-%d')
                    except Exception as e:
                        print(f"  日期格式化错误: {e}")
                        formatted_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # Get maximum increase
                    hist_data['pct_chg'] = hist_data['pct_chg'].astype(float)
                    max_increase = hist_data['pct_chg'].max()
                    
                    # Calculate drop percentage
                    drop_percentage = calculate_drop_percentage(latest_price, highest_price)
                    
                    # Add stock data to sector (including new volume metrics)
                    sector_data.append({
                        'name': stock_name,
                        'code': stock_code,
                        'latest_price': latest_price,
                        'highest_price': highest_price,
                        'highest_date': formatted_date,
                        'max_4m_increase': max_increase,  # Changed from max_3m_increase
                        'drop_percentage': drop_percentage,
                        'latest_volume': latest_volume,
                        'max_volume': max_volume,
                        'volume_ratio': volume_ratio
                    })
                    print(f"  + 成功处理 {stock_name} 数据")
                    
                except Exception as e:
                    print(f"  - 处理 {stock_name} 数据时出错: {e}")
            
            # Add sector results
            print(f"成功处理 {sector} 行业 {len(sector_data)} 只股票数据 (共 {len(stock_names_list)} 只)")
            
            # Calculate sector score
            sector_score = calculate_sector_score(sector_data)
            
            # Add score to each stock
            for stock in sector_data:
                stock['sector_score'] = sector_score
                
            result[sector] = sector_data
            
            # Save sector data to database
            db.save_sector_data(sector, sector_data)
        
        # Final report
        total_stocks_processed = sum(len(stocks) for stocks in result.values())
        print(f"======== 所有行业股票数据获取完成 ========")
        print(f"总计: {len(all_stocks)} 只股票")
        print(f"处理成功: {total_stocks_processed} 只")
        print(f"未找到代码: {len(missing_stocks)} 只")
        print(f"更新失败: {update_fail_count} 只")
        
        return result
        
    except Exception as e:
        print(f"获取所有行业股票数据时发生错误: {e}")
        return {}

def calculate_drop_percentage(current_price, highest_price):
    """Calculate the drop percentage from highest price to current price"""
    if current_price is None or highest_price is None or highest_price == 0:
        return None
    
    drop = ((current_price - highest_price) / highest_price) * 100
    return drop

def calculate_sector_score(sector_data):
    """Calculate a score for a sector based on absolute drop percentages"""
    if not sector_data:
        return 0
    
    # Get absolute drop percentages for all stocks in the sector
    drop_percentages = []
    for stock in sector_data:
        if stock['drop_percentage'] is not None:
            drop_percentages.append(abs(stock['drop_percentage']))
    
    # Calculate average if there are values
    if drop_percentages:
        return sum(drop_percentages) / len(drop_percentages)
    return 0

def get_sector_comparison(force_refresh=False):
    """Get comparison data for all sectors using database caching"""
    result = {}
    
    # First check if we have fresh data for all sectors
    all_sectors_fresh = True
    if not force_refresh:
        for sector in SECTORS.keys():
            data, fetch_time = db.get_latest_sector_data(sector)
            if data is None:  # No fresh data
                all_sectors_fresh = False
                print(f"找不到 {sector} 行业的缓存数据")
                break
            result[sector] = data
            
            # Log when we're using cached data
            if fetch_time:
                print(f"使用缓存的 {sector} 行业数据 (获取时间: {fetch_time})")
    else:
        all_sectors_fresh = False
        print("强制刷新模式，跳过缓存检查")
    
    # If all sectors have fresh data, calculate scores and return
    if all_sectors_fresh:
        print("所有行业数据均从缓存获取，无需重新获取")
        
        # Calculate scores for cached data
        sector_scores = {}
        for sector, stocks in result.items():
            sector_scores[sector] = calculate_sector_score(stocks)
        
        # Add scores to result
        for sector in result:
            for stock in result[sector]:
                if isinstance(stock, dict):  # Ensure it's a dict before adding a key
                    stock['sector_score'] = sector_scores[sector]
        
        return result
    
    try:
        # Otherwise, get fresh data for all sectors
        print("缓存数据不完整或已过期，重新获取所有行业数据")
        result = get_all_sector_stocks_data()
        return result
    except Exception as e:
        print(f"获取行业数据时发生错误: {e}")
        # Return any partial results we may have
        if result:
            print(f"返回部分缓存数据 ({len(result)} 个行业)")
            return result
        # If no results, create an empty result structure
        empty_result = {}
        for sector in SECTORS.keys():
            empty_result[sector] = []
        print("没有可用数据，返回空结构")
        return empty_result

# Ensure stock basic data is up to date when the module is loaded
# update_stock_basic_data()
