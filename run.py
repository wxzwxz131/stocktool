"""
Convenience script to start the stock analysis application with different options.
"""
import os
import sys
import subprocess

def show_help():
    """Display help information"""
    print("""
Stock Analysis Application Runner

Usage: python run.py [option]

Options:
  --quick       Start without initializing data (faster startup)
  --init        Start with data initialization (default)
  --help        Show this help message
    """)

def main():
    """Main entry point"""
    # Get the app.py path
    app_path = os.path.join(os.path.dirname(__file__), 'app.py')
    
    # Default options
    options = []
    
    # Process command line args
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == '--quick':
            print("快速启动模式: 跳过数据初始化...")
            options.append('--no-init')
        elif arg == '--help':
            show_help()
            return
        elif arg == '--init':
            print("正常启动模式: 包含数据初始化...")
        else:
            print(f"未知选项: {arg}")
            show_help()
            return
    
    # Start the application
    cmd = [sys.executable, app_path] + options
    print(f"启动命令: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
