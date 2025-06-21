"""
Hong Kong stock utilities for handling specific HK stock requirements
"""

def get_hk_stock_name_variations(stock_name):
    """Get possible variations of HK stock names"""
    variations = [stock_name]
    
    # Common HK stock suffixes
    hk_suffixes = ['-W', '-SW', ' Holdings', ' Group', ' Limited', ' Ltd', ' Corp', ' Inc']
    
    # Add variations with suffixes
    for suffix in hk_suffixes:
        if not stock_name.endswith(suffix):
            variations.append(stock_name + suffix)
    
    # Remove common suffixes to create base name variations
    for suffix in hk_suffixes:
        if stock_name.endswith(suffix):
            base_name = stock_name[:-len(suffix)]
            if base_name not in variations:
                variations.append(base_name)
    
    # Company name variations
    company_words = ['集团', '控股', '有限公司', '公司']
    for word in company_words:
        if word in stock_name:
            variation = stock_name.replace(word, '').strip()
            if variation and variation not in variations:
                variations.append(variation)
        else:
            variations.append(stock_name + word)
    
    return list(set(variations))  # Remove duplicates

def is_hk_stock_code(stock_code):
    """Check if a stock code is for Hong Kong stock"""
    return stock_code and stock_code.endswith('.HK')

def format_hk_volume(volume):
    """Format HK stock volume (might be in different units)"""
    if volume is None:
        return None
    
    # HK stocks might report volume in different units
    # This function can be extended based on actual data format
    return volume

def get_hk_market_status():
    """Get Hong Kong market trading status"""
    from datetime import datetime
    import pytz
    
    try:
        # Hong Kong timezone
        hk_tz = pytz.timezone('Asia/Hong_Kong')
        now_hk = datetime.now(hk_tz)
        
        # Basic market hours (can be enhanced)
        market_open = now_hk.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_hk.replace(hour=16, minute=0, second=0, microsecond=0)
        
        is_trading_day = now_hk.weekday() < 5  # Monday = 0, Friday = 4
        is_trading_hours = market_open <= now_hk <= market_close
        
        return {
            'is_open': is_trading_day and is_trading_hours,
            'local_time': now_hk.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'is_trading_day': is_trading_day,
            'is_trading_hours': is_trading_hours
        }
    except Exception as e:
        print(f"Error getting HK market status: {e}")
        return {'is_open': False, 'error': str(e)}
