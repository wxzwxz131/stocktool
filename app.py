from flask import Flask, render_template, jsonify, request
import pandas as pd
import threading
import argparse
import sys
import traceback  # Add this import for better error reporting
from stock_data import (
    get_sector_comparison, 
    update_stock_basic_data, 
    get_stock_code, 
    update_daily_data,
    update_daily_data_batch,
    get_all_sector_stocks_data  # Add the new function
)
from sector import SECTORS
from datetime import datetime

# Global variables to track initialization status
initialization_status = {
    'complete': False,
    'in_progress': False,
    'last_update': None,
    'error': None
}

# Create a function to fetch all data on startup
def initialize_data():
    """Fetch all stock data from Tushare and save to database on startup"""
    global initialization_status
    
    # Mark initialization as in progress
    initialization_status['in_progress'] = True
    initialization_status['complete'] = False
    initialization_status['error'] = None
    
    print("\n======== 应用启动: 初始化数据 ========")
    try:
        # Use the optimized function to get all data at once
        get_all_sector_stocks_data(days=120)  # Changed from 90 to 120 days (4 months)
        
        # Update status to complete
        initialization_status['complete'] = True
        initialization_status['in_progress'] = False
        initialization_status['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return True
    except Exception as e:
        error_msg = f"数据初始化发生错误: {e}"
        print(error_msg)
        
        # Update status with error
        initialization_status['complete'] = False
        initialization_status['in_progress'] = False
        initialization_status['error'] = error_msg
        
        return False

# Initialize the Flask app
app = Flask(__name__)

# Define a function to initialize data that will be called later
def start_background_initialization():
    """Run data initialization in a background thread"""
    global initialization_status
    
    # Check if initialization is already in progress
    if initialization_status['in_progress']:
        return False
        
    def init_data_thread():
        print("数据初始化已在后台线程启动")
        try:
            initialize_data()
        except Exception as e:
            error_msg = f"初始化数据时发生错误: {e}"
            print(error_msg)
            initialization_status['error'] = error_msg
            initialization_status['in_progress'] = False
    
    thread = threading.Thread(target=init_data_thread)
    thread.daemon = True
    thread.start()
    return True

@app.route('/initialize', methods=['GET'])
def start_initialization():
    """Start the initialization process on demand"""
    start_background_initialization()
    return jsonify({'status': 'success', 'message': 'Initialization started in background'})

@app.route('/api/init-status')
def check_init_status():
    """API endpoint to check the status of data initialization"""
    global initialization_status
    
    try:
        # Check if sectors have data in the database regardless of initialization status
        has_data = False
        from datetime import datetime, timedelta
        import db
        
        # Check if at least one sector has data in the database
        for sector in SECTORS.keys():
            data, fetch_time = db.get_latest_sector_data(sector)
            if data is not None:
                has_data = True
                break
        
        # If we have data but initialization status is not properly set, fix it
        if has_data and not initialization_status['complete'] and not initialization_status['in_progress']:
            initialization_status['complete'] = True
            initialization_status['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("找到了缓存的行业数据，但初始化状态未设置，已修正状态")
    
        return jsonify({
            'status': 'success',
            'data': {
                'complete': initialization_status['complete'],
                'in_progress': initialization_status['in_progress'],
                'last_update': initialization_status['last_update'],
                'error': initialization_status['error'],
                'has_cached_data': has_data
            }
        })
    except Exception as e:
        print(f"检查初始化状态时发生错误: {e}")
        # Return some safe defaults
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {
                'complete': False,
                'in_progress': False,
                'last_update': None,
                'error': str(e),
                'has_cached_data': False
            }
        })

@app.route('/')
def index():
    """Render the home page without starting initialization"""
    return render_template('index.html')

@app.route('/sector-comparison')
def sector_comparison():
    """Render the sector comparison page without starting initialization"""
    return render_template('sector_comparison.html')

@app.route('/api/sector-data')
def get_sector_data():
    """API endpoint to get sector comparison data in JSON format"""
    try:
        # Check if we need to force a refresh
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Check if initialization is complete (and use that data if available)
        if initialization_status['complete'] and not force_refresh:
            # Use cached data from initialization
            sector_data = get_sector_comparison(force_refresh=False)
        elif force_refresh:
            # If refresh is requested, use the optimized function to get all data at once
            sector_data = get_all_sector_stocks_data(days=120)  # Changed to 120 days
        else:
            # If initialization is not complete and no refresh requested, try to use cached data
            sector_data = get_sector_comparison(force_refresh=False)
        
        # Calculate sector scores for sorting
        sector_scores = {}
        for sector, stocks in sector_data.items():
            if stocks and isinstance(stocks[0], dict) and 'sector_score' in stocks[0]:
                sector_scores[sector] = stocks[0]['sector_score']
            else:
                sector_scores[sector] = 0
        
        # Transform data for JSON response
        formatted_data = {}
        for sector, stocks in sector_data.items():
            formatted_stocks = []
            for stock in stocks:
                formatted_stocks.append({
                    'name': stock['name'],
                    'code': stock['code'],
                    'latest_price': float(stock['latest_price']) if stock['latest_price'] else None,
                    'highest_price': float(stock['highest_price']) if stock['highest_price'] else None,
                    'highest_date': stock['highest_date'],
                    'max_4m_increase': float(stock.get('max_4m_increase', stock.get('max_3m_increase', 0))) if stock.get('max_4m_increase') or stock.get('max_3m_increase') else None,  # Handle both old and new field names
                    'drop_percentage': float(stock['drop_percentage']) if stock['drop_percentage'] else None,
                    'sector_score': float(stock['sector_score']) if 'sector_score' in stock else 0,
                    'latest_volume': float(stock.get('latest_volume', 0)) if stock.get('latest_volume') else None,
                    'max_volume': float(stock.get('max_volume', 0)) if stock.get('max_volume') else None,
                    'volume_ratio': float(stock.get('volume_ratio', 0)) if stock.get('volume_ratio') else None
                })
            formatted_data[sector] = formatted_stocks
        
        # Create a sorted response with sectors in order by score
        sorted_sectors = sorted(formatted_data.keys(), 
                               key=lambda x: sector_scores.get(x, 0), 
                               reverse=True)
        
        return jsonify({
            'status': 'success', 
            'data': formatted_data,
            'sorted_sectors': sorted_sectors,
            'sector_scores': sector_scores
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/sector-data-debug')
def get_sector_data_debug():
    """Debug API endpoint to get sector data with enhanced error reporting"""
    response_data = {
        'status': 'error',
        'message': 'Unknown error occurred',
        'debug_info': {},
        'traceback': None
    }
    
    try:
        print("DEBUG: Start processing debug sector data request")
        response_data['debug_info']['init_status'] = initialization_status
        
        # Try to get any available sector data with fallbacks
        try:
            # First try to get cached data
            print("DEBUG: Getting sector data from database")
            from sector import SECTORS
            import db
            
            # Check if any sector has cached data
            has_cached_data = False
            sectors_with_data = []
            sectors_without_data = []
            
            for sector in SECTORS.keys():
                data, fetch_time = db.get_latest_sector_data(sector, max_age_minutes=1440)  # Accept data up to 24 hours old
                if data is not None:
                    has_cached_data = True
                    sectors_with_data.append(sector)
                else:
                    sectors_without_data.append(sector)
            
            response_data['debug_info']['sectors_with_data'] = sectors_with_data
            response_data['debug_info']['sectors_without_data'] = sectors_without_data
            
            if has_cached_data:
                print(f"DEBUG: Found cached data for {len(sectors_with_data)} sectors")
                sector_data = get_sector_comparison(force_refresh=False)
            else:
                print("DEBUG: No cached data found, initializing minimal dataset")
                sector_data = {}
                for sector in SECTORS.keys():
                    sector_data[sector] = []
            
            # Calculate sector scores for sorting
            sector_scores = {}
            for sector, stocks in sector_data.items():
                sector_score = 0
                if stocks and isinstance(stocks[0], dict) and 'sector_score' in stocks[0]:
                    sector_score = stocks[0]['sector_score']
                sector_scores[sector] = sector_score
            
            # Create a minimal formatted response
            formatted_data = {}
            for sector, stocks in sector_data.items():
                formatted_stocks = []
                for stock in stocks:
                    if isinstance(stock, dict):
                        formatted_stock = {
                            'name': stock.get('name', 'Unknown'),
                            'code': stock.get('code', 'Unknown'),
                            'latest_price': float(stock.get('latest_price', 0)) if stock.get('latest_price') else None,
                            'highest_price': float(stock.get('highest_price', 0)) if stock.get('highest_price') else None,
                            'highest_date': stock.get('highest_date', 'Unknown'),
                            'max_4m_increase': float(stock.get('max_4m_increase', stock.get('max_3m_increase', 0))) if stock.get('max_4m_increase') or stock.get('max_3m_increase') else None,  # Handle both field names
                            'drop_percentage': float(stock.get('drop_percentage', 0)) if stock.get('drop_percentage') else None,
                            'sector_score': float(stock.get('sector_score', 0)) if 'sector_score' in stock else 0,
                            'latest_volume': float(stock.get('latest_volume', 0)) if stock.get('latest_volume') else None,
                            'max_volume': float(stock.get('max_volume', 0)) if stock.get('max_volume') else None,
                            'volume_ratio': float(stock.get('volume_ratio', 0)) if stock.get('volume_ratio') else None
                        }
                        formatted_stocks.append(formatted_stock)
                formatted_data[sector] = formatted_stocks
            
            # Create a sorted response with sectors in order by score
            sorted_sectors = sorted(formatted_data.keys(), 
                                   key=lambda x: sector_scores.get(x, 0), 
                                   reverse=True)
            
            # Success response
            response_data.update({
                'status': 'success', 
                'data': formatted_data,
                'sorted_sectors': sorted_sectors,
                'sector_scores': sector_scores,
                'message': 'Data retrieved successfully (debug endpoint)'
            })
            
            return jsonify(response_data)
            
        except Exception as e:
            print(f"DEBUG: Error getting sector data: {e}")
            response_data['message'] = f"Failed to get sector data: {str(e)}"
            response_data['traceback'] = traceback.format_exc()
            return jsonify(response_data)
            
    except Exception as e:
        print(f"DEBUG: Critical error in debug endpoint: {e}")
        response_data['message'] = f"Critical error: {str(e)}"
        response_data['traceback'] = traceback.format_exc()
        return jsonify(response_data)

# Add a new endpoint for refreshing data
@app.route('/api/refresh-all-data')
def refresh_all_data():
    """API endpoint to refresh all stock data in one go"""
    try:
        # Start refreshing in a background thread
        def refresh_thread():
            try:
                get_all_sector_stocks_data(days=120)  # Changed to 120 days
                print("一次性刷新所有股票数据完成")
            except Exception as e:
                print(f"刷新数据时发生错误: {e}")
        
        thread = threading.Thread(target=refresh_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Started refreshing all stock data in the background'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Stock Analysis Web Application')
    parser.add_argument('--no-init', action='store_true', 
                        help='Start without initializing data (skip data download on startup)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to run the application on (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable additional debug output')
    args = parser.parse_args()
    
    # Set debug mode
    app.config['DEBUG_MODE'] = args.debug
    
    # Immediately fetch data on startup based on command-line parameter
    if not args.no_init:
        print("正在启动应用，首先初始化数据...")
        try:
            initialize_data()
        except Exception as e:
            print(f"初始化数据时发生错误: {e}")
            print("应用将继续启动，但可能需要手动更新数据")
    else:
        print("按照参数设置跳过自动数据初始化。请使用网页界面上的'初始化股票数据'按钮手动初始化。")
    
    # Start the Flask app
    app.run(debug=True, port=args.port)
