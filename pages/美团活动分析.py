import streamlit as st
import pandas as pd
import json
import re
from fuzzywuzzy import fuzz, process
from io import BytesIO

# ============================================================
# 配置选项（请根据需要修改）
# ============================================================
PROFIT_THRESHOLD = 35               # 毛利率阈值（%），大于此值可参加活动
MATCH_THRESHOLD = 80                # 模糊匹配阈值（%），大于此值认为匹配成功
# ============================================================


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


def parse_txt_files(uploaded_files):
    all_dataframes = []
    
    for uploaded_file in uploaded_files:
        activity_name = uploaded_file.name.replace('.txt', '')
        all_products = []
        
        content = uploaded_file.read().decode('utf-8')
        lines = content.split('\n')
        
        for line in lines:
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
            except json.JSONDecodeError:
                continue
        
        if all_products:
            df = pd.DataFrame(all_products)
            all_dataframes.append(df)
    
    if not all_dataframes:
        return None
    
    merged_df = pd.concat(all_dataframes, ignore_index=True)
    columns = ['活动'] + [col for col in merged_df.columns if col != '活动']
    merged_df = merged_df[columns]
    return merged_df


def find_best_match(target_name, name_list):
    if not target_name or not name_list or len(name_list) == 0:
        return None, 0
    
    target_clean = clean_string(target_name)
    if not target_clean:
        return None, 0
    
    best_match = process.extractOne(target_clean, name_list, scorer=fuzz.token_set_ratio)
    
    if best_match:
        matched_name, score = best_match
        if score >= MATCH_THRESHOLD:
            return matched_name, score
    return None, 0


def calculate_profit_margin(meituan_df, store_file):
    store_df = pd.read_excel(store_file)
    
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
    
    store_cost_col = None
    for col in ['进货价', '成本价', '进价', '单件成本价']:
        for c in store_df.columns:
            if col in c:
                store_cost_col = c
                break
        if store_cost_col:
            break
    
    if not store_name_col:
        st.error("门店商品导出文件中未找到商品名称列")
        return None
    
    if not store_cost_col:
        st.error("门店商品导出文件中未找到进货价/成本价列")
        return None
    
    store_df['_clean_name'] = store_df[store_name_col].apply(clean_string)
    store_names = store_df['_clean_name'].tolist()
    store_name_map = {clean_string(row[store_name_col]): row[store_cost_col] for _, row in store_df.iterrows()}
    
    results = []
    
    for _, row in meituan_df.iterrows():
        meituan_name = row['商品名称']
        clean_name = clean_string(meituan_name)
        
        matched_clean_name, score = find_best_match(clean_name, store_names)
        
        if matched_clean_name:
            cost_price = store_name_map.get(matched_clean_name, None)
            
            activity_price = float(row['活动价格']) if pd.notna(row['活动价格']) else 0
            platform_amount = float(row['平台承担金额']) if pd.notna(row['平台承担金额']) else 0
            total_price = activity_price + platform_amount
            
            if cost_price is not None and pd.notna(cost_price) and total_price > 0:
                cost_price = float(cost_price)
                profit = total_price - cost_price
                profit_margin = (profit / total_price) * 100
                participate = '是' if profit_margin > PROFIT_THRESHOLD else '否'
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
    
    result_df = pd.DataFrame(results)
    return result_df


def main():
    st.title("🏪 美团活动分析")
    
    with st.sidebar:
        st.header("配置参数")
        global PROFIT_THRESHOLD, MATCH_THRESHOLD
        PROFIT_THRESHOLD = st.slider("毛利率阈值 (%)", min_value=0, max_value=100, value=35, step=1)
        MATCH_THRESHOLD = st.slider("模糊匹配阈值 (%)", min_value=0, max_value=100, value=80, step=1)
    
    st.subheader("Step 1: 上传美团活动txt文件")
    txt_files = st.file_uploader("选择美团活动txt文件", type="txt", accept_multiple_files=True)
    
    st.subheader("Step 2: 上传门店商品导出文件")
    store_file = st.file_uploader("选择门店商品导出文件 (xlsx格式)", type="xlsx")
    
    if st.button("开始分析"):
        if not txt_files:
            st.error("请先上传美团活动txt文件")
            return
        if not store_file:
            st.error("请先上传门店商品导出文件")
            return
        
        with st.spinner("正在读取美团活动txt文件..."):
            meituan_df = parse_txt_files(txt_files)
            if meituan_df is None:
                st.error("未能读取到任何数据")
                return
            st.success(f"成功读取 {len(meituan_df)} 条记录")
        
        with st.spinner("正在匹配门店商品并计算毛利..."):
            result_df = calculate_profit_margin(meituan_df, store_file)
            if result_df is None:
                return
        
        st.subheader("分析结果")
        st.dataframe(result_df)
        
        total_count = len(result_df)
        matched_count = len(result_df[result_df['匹配度(%)'] > 0])
        participate_count = len(result_df[result_df['是否参加活动'] == '是'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("总商品数", total_count)
        col2.metric("成功匹配", matched_count)
        col3.metric("可参加活动", participate_count)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False)
        output.seek(0)
        
        st.download_button(
            label="下载分析结果",
            data=output,
            file_name="美团活动分析结果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


if __name__ == '__main__':
    main()
