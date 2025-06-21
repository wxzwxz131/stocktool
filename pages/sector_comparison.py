import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from stock_data import get_sector_comparison
from sector import SECTORS
import datetime

def app():
    # Add title at the beginning
    st.title("行业股票表现对比")
    st.write("各行业股票当前价格与四月最大涨幅对比")
    
    # Add refresh button at the top
    col1, col2 = st.columns([8, 2])
    with col1:
        st.write("包含价格指标和交易量分析（四个月周期）")
    with col2:
        refresh = st.button("🔄 刷新数据")
    
    # Get sector comparison data
    with st.spinner("正在获取数据..."):
        sector_data = get_sector_comparison(force_refresh=refresh)
    
    # Display data for each sector
    for sector, stocks in sector_data.items():
        st.subheader(f"{sector}行业股票")
        
        if not stocks:
            st.write("暂无数据")
            continue
            
        # Create DataFrame
        df = pd.DataFrame(stocks)
        
        # Prepare columns for display
        display_columns = ['name', 'code', 'latest_price']
        
        # Handle both old and new field names for backward compatibility
        if 'max_4m_increase' in df.columns:
            display_columns.append('max_4m_increase')
        elif 'max_3m_increase' in df.columns:
            display_columns.append('max_3m_increase')
            
        display_columns.append('drop_percentage')
        
        # Add volume columns if they exist
        if 'latest_volume' in df.columns:
            display_columns.extend(['latest_volume', 'max_volume', 'volume_ratio'])
        
        # Create display dataframe
        display_df = df[display_columns].copy()
        
        # Rename columns
        column_names = {
            'name': '股票名称',
            'code': '股票代码', 
            'latest_price': '最新价格',
            'max_4m_increase': '四月最大涨幅(%)',
            'max_3m_increase': '四月最大涨幅(%)',  # Map old field to new display name
            'drop_percentage': '从最高点跌幅(%)',
            'latest_volume': '最新交易量',
            'max_volume': '最大交易量',
            'volume_ratio': '交易量比值(%)'
        }
        
        display_df = display_df.rename(columns=column_names)
        
        # Format volume columns
        if '最新交易量' in display_df.columns:
            display_df['最新交易量'] = display_df['最新交易量'].apply(
                lambda x: f"{x/1000000:.2f}M" if pd.notnull(x) and x >= 1000000 
                else f"{x/1000:.2f}K" if pd.notnull(x) and x >= 1000 
                else f"{x:.0f}" if pd.notnull(x) else "N/A"
            )
        
        if '最大交易量' in display_df.columns:
            display_df['最大交易量'] = display_df['最大交易量'].apply(
                lambda x: f"{x/1000000:.2f}M" if pd.notnull(x) and x >= 1000000 
                else f"{x/1000:.2f}K" if pd.notnull(x) and x >= 1000 
                else f"{x:.0f}" if pd.notnull(x) else "N/A"
            )
        
        if '交易量比值(%)' in display_df.columns:
            display_df['交易量比值(%)'] = display_df['交易量比值(%)'].apply(
                lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A"
            )
        
        # Display as table
        st.dataframe(display_df, use_container_width=True)
        
        # Add volume analysis
        if 'volume_ratio' in df.columns:
            avg_volume_ratio = df['volume_ratio'].mean()
            st.metric(
                label=f"{sector} 平均交易量比值", 
                value=f"{avg_volume_ratio:.2f}%",
                help="当前交易量相对于四个月最大交易量的平均比值"
            )
        
        # Create visualization
        if len(stocks) > 0:
            # Create tabs for different visualizations
            tab1, tab2 = st.tabs(["价格对比", "交易量分析"])
            
            with tab1:
                # Existing price visualization
                fig, ax = plt.subplots(figsize=(12, 6))
                
                names = [stock['name'] for stock in stocks]
                prices = [stock['latest_price'] for stock in stocks]
                # Handle both old and new field names
                increases = [stock.get('max_4m_increase', stock.get('max_3m_increase', 0)) for stock in stocks]
                
                # Create positions for the bars
                x = np.arange(len(names))
                width = 0.35
                
                # Create bars
                price_bars = ax.bar(x - width/2, prices, width, label='当前价格')
                increase_bars = ax.bar(x + width/2, increases, width, label='四月最大涨幅(%)')
                
                # Add labels and title
                ax.set_xlabel('股票')
                ax.set_ylabel('价格/涨幅')
                ax.set_title(f'{sector}行业股票价格对比')
                ax.set_xticks(x)
                ax.set_xticklabels(names, rotation=45, ha='right')
                ax.legend()
                
                plt.tight_layout()
                st.pyplot(fig)
            
            with tab2:
                # New volume visualization
                if 'latest_volume' in df.columns and 'volume_ratio' in df.columns:
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
                    
                    # Volume comparison
                    latest_vols = [stock.get('latest_volume', 0) for stock in stocks]
                    max_vols = [stock.get('max_volume', 0) for stock in stocks]
                    
                    x = np.arange(len(names))
                    width = 0.35
                    
                    ax1.bar(x - width/2, latest_vols, width, label='最新交易量', alpha=0.8)
                    ax1.bar(x + width/2, max_vols, width, label='最大交易量', alpha=0.8)
                    ax1.set_xlabel('股票')
                    ax1.set_ylabel('交易量')
                    ax1.set_title(f'{sector}行业交易量对比')
                    ax1.set_xticks(x)
                    ax1.set_xticklabels(names, rotation=45, ha='right')
                    ax1.legend()
                    
                    # Volume ratio
                    ratios = [stock.get('volume_ratio', 0) for stock in stocks]
                    colors = ['red' if r < 50 else 'green' for r in ratios]
                    
                    ax2.bar(names, ratios, color=colors, alpha=0.7)
                    ax2.set_xlabel('股票')
                    ax2.set_ylabel('交易量比值(%)')
                    ax2.set_title(f'{sector}行业交易量比值（当前/最大）')
                    ax2.set_xticklabels(names, rotation=45, ha='right')
                    ax2.axhline(y=50, color='orange', linestyle='--', label='50%基准线')
                    ax2.legend()
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.info("交易量数据不可用")
        
        # Horizontal divider
        st.markdown("---")

if __name__ == "__main__":
    app()
