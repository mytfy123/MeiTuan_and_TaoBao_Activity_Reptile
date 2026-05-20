import json
import pandas as pd
import re
import streamlit as st
from fuzzywuzzy import fuzz, process

# 设置页面标题
st.set_page_config(page_title="美团活动分析工具", page_icon="📊", layout="wide")

# 自定义函数
def clean_string(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[^\w\u4e00-\u9fff]', '', s)
    return s

def extract_product_info(item):
    price_info = item.get('price', [])
    direct_price = None
    for p in price_info:
        if p.get('poiType') == 'direct':
            direct_price = p.get('min')
            break
    
    price_range = item.get('priceRange', {})
    price_min = price_range.get('min', 0) if isinstance(price_range, dict) else 0
    
    product = {
        '活动ID': item.get('subActId', ''),
        '活动名称': item.get('subActName', ''),
        '商品名称': item.get('name', ''),
        '规格': item.get('spec', ''),
        '组合商品名称': item.get('combineProductName', ''),
        '组合数量': item.get('combineProductSubItemAmount', ''),
        '活动价格': item.get('maxActPrice', ''),
        '最大申请价格': item.get('maxApplyPrice', ''),
        '平台承担金额': item.get('platChargeAmount', ''),
        '当前价格': direct_price if direct_price is not None else price_min,
        '是否可申请': '是' if item.get('canApply') else '否',
        '不可申请原因': item.get('reason', ''),
    }
    return product

def parse_txt_file(uploaded_file):
    activity_name = uploaded_file.name.replace('.txt', '')
    all_products = []
    
    content = uploaded_file.read().decode('utf-8')
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        try:
            data = json.loads(line)
            if data.get('code') == 0 and data.get('data') and data['data'].get('list'):
                for item in data['data']['list']:
                    product = extract_product_info(item)
                    product['活动'] = activity_name
                    all_products.append(product)
        except json.JSONDecodeError as e:
            st.warning(f"解析JSON失败: {e}")
            continue
    
    if all_products:
        df = pd.DataFrame(all_products)
        columns = ['活动'] + [col for col in df.columns if col != '活动']
        return df[columns]
    return None

def find_best_match(target_name, name_list, threshold=80):
    if not target_name or not name_list or len(name_list) == 0:
        return None, 0
    
    target_clean = clean_string(target_name)
    if not target_clean:
        return None, 0
    
    best_match = process.extractOne(target_clean, name_list, scorer=fuzz.token_set_ratio)
    
    if best_match:
        matched_name, score = best_match
        if score >= threshold:
            return matched_name, score
    return None, 0

def calculate_profit_margin(meituan_df, store_df, profit_threshold, match_threshold):
    # 查找商品名称列
    store_name_col = None
    for col in store_df.columns:
        if '商品名称' in col:
            store_name_col = col
            break
    if not store_name_col:
        for col in store_df.columns:
            if '名称' in col and '门店名称' not in col:
                store_name_col = col
                break
    
    # 查找进货价/成本价列
    store_cost_col = None
    for col in ['进货价', '成本价', '进价', '单件成本价']:
        for c in store_df.columns:
            if col in c:
                store_cost_col = c
                break
        if store_cost_col:
            break
    
    if not store_name_col or not store_cost_col:
        return None, store_name_col, store_cost_col
    
    store_df['_clean_name'] = store_df[store_name_col].apply(clean_string)
    store_names = store_df['_clean_name'].tolist()
    store_name_map = {clean_string(row[store_name_col]): row[store_cost_col] for _, row in store_df.iterrows()}
    
    results = []
    
    for _, row in meituan_df.iterrows():
        meituan_name = row['商品名称']
        clean_name = clean_string(meituan_name)
        
        matched_clean_name, score = find_best_match(clean_name, store_names, match_threshold)
        
        if matched_clean_name:
            cost_price = store_name_map.get(matched_clean_name, None)
            
            activity_price = float(row['活动价格']) if pd.notna(row['活动价格']) else 0
            platform_amount = float(row['平台承担金额']) if pd.notna(row['平台承担金额']) else 0
            total_price = activity_price + platform_amount
            
            if cost_price is not None and pd.notna(cost_price) and total_price > 0:
                cost_price = float(cost_price)
                profit = total_price - cost_price
                profit_margin = (profit / total_price) * 100
                participate = '是' if profit_margin > profit_threshold else '否'
            else:
                cost_price = None
                profit = None
                profit_margin = None
                participate = '否（成本价缺失或活动价为0）'
            
            original_name = store_df[store_df['_clean_name'] == matched_clean_name][store_name_col].iloc[0]
            
            results.append({
                '活动': row['活动'],
                '活动ID': row['活动ID'],
                '活动名称': row['活动名称'],
                '美团商品名称': meituan_name,
                '规格': row['规格'],
                '组合商品名称': row['组合商品名称'],
                '组合数量': row['组合数量'],
                '活动价格': activity_price,
                '最大申请价格': row['最大申请价格'],
                '平台承担金额': platform_amount,
                '合计售价': total_price,
                '是否可申请': row['是否可申请'],
                '不可申请原因': row['不可申请原因'],
                '匹配的门店商品名称': original_name,
                '匹配度(%)': score,
                '进货价': cost_price,
                '毛利': profit,
                '毛利率(%)': profit_margin,
                '是否参加活动': participate
            })
        else:
            activity_price = float(row['活动价格']) if pd.notna(row['活动价格']) else 0
            platform_amount = float(row['平台承担金额']) if pd.notna(row['平台承担金额']) else 0
            
            results.append({
                '活动': row['活动'],
                '活动ID': row['活动ID'],
                '活动名称': row['活动名称'],
                '美团商品名称': meituan_name,
                '规格': row['规格'],
                '组合商品名称': row['组合商品名称'],
                '组合数量': row['组合数量'],
                '活动价格': activity_price,
                '最大申请价格': row['最大申请价格'],
                '平台承担金额': platform_amount,
                '合计售价': activity_price + platform_amount,
                '是否可申请': row['是否可申请'],
                '不可申请原因': row['不可申请原因'],
                '匹配的门店商品名称': '未匹配到',
                '匹配度(%)': 0,
                '进货价': None,
                '毛利': None,
                '毛利率(%)': None,
                '是否参加活动': '否（未匹配到商品）'
            })
    
    return pd.DataFrame(results), store_name_col, store_cost_col

# 主应用
def main():
    st.title("📊 美团活动分析工具")
    st.markdown("---")
    
    # 配置区域
    st.sidebar.header("配置选项")
    profit_threshold = st.sidebar.slider("毛利率阈值 (%)", min_value=0, max_value=100, value=35, step=1)
    match_threshold = st.sidebar.slider("模糊匹配阈值 (%)", min_value=0, max_value=100, value=80, step=1)
    
    # 文件上传区域
    st.subheader("📁 上传文件")
    col1, col2 = st.columns(2)
    
    with col1:
        txt_files = st.file_uploader("上传美团活动TXT文件（可多选）", type="txt", accept_multiple_files=True)
    
    with col2:
        store_file = st.file_uploader("上传门店商品导出Excel文件", type=["xlsx", "xls"])
    
    # 处理数据
    if txt_files and store_file:
        st.markdown("---")
        st.subheader("🔄 处理进度")
        
        # 读取美团活动数据
        with st.spinner("正在读取美团活动数据..."):
            all_meituan_dfs = []
            for txt_file in txt_files:
                df = parse_txt_file(txt_file)
                if df is not None:
                    all_meituan_dfs.append(df)
                    st.success(f"已读取: {txt_file.name} ({len(df)}条记录)")
            
            if not all_meituan_dfs:
                st.error("未能读取到任何美团活动数据")
                return
            
            meituan_df = pd.concat(all_meituan_dfs, ignore_index=True)
            st.info(f"合并完成，共 {len(meituan_df)} 条美团活动记录")
        
        # 读取门店商品数据
        with st.spinner("正在读取门店商品数据..."):
            try:
                store_df = pd.read_excel(store_file)
                st.success(f"已读取门店商品数据 ({len(store_df)}条记录)")
            except Exception as e:
                st.error(f"读取门店商品文件失败: {e}")
                return
        
        # 计算毛利
        with st.spinner("正在匹配商品并计算毛利..."):
            result_df, name_col, cost_col = calculate_profit_margin(meituan_df, store_df, profit_threshold, match_threshold)
            
            if result_df is None:
                st.error(f"未能识别必要的列 - 商品名称列: {name_col}, 成本价列: {cost_col}")
                return
            
            st.success(f"匹配完成！")
        
        # 显示结果
        st.markdown("---")
        st.subheader("📈 分析结果")
        
        # 统计信息
        total_count = len(result_df)
        matched_count = len(result_df[result_df['匹配度(%)'] > 0])
        participate_count = len(result_df[result_df['是否参加活动'] == '是'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("总商品数", total_count)
        col2.metric("成功匹配", matched_count)
        col3.metric(f"可参加活动 (>={profit_threshold}%)", participate_count)
        
        # 结果表格
        st.dataframe(result_df)
        
        # 下载按钮
        st.download_button(
            label="📥 下载分析结果",
            data=result_df.to_csv(index=False, encoding='utf-8-sig'),
            file_name="美团活动分析结果.csv",
            mime="text/csv"
        )

if __name__ == '__main__':
    main()
