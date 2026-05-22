import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO

def parse_taobao_txt(uploaded_files):
    all_products = []
    
    for uploaded_file in uploaded_files:
        activity_name = uploaded_file.name.replace('.txt', '')
        
        content = uploaded_file.read().decode('utf-8')
        content = content.strip()
        
        json_objects = []
        current_obj = []
        brace_count = 0
        
        for char in content:
            if char == '{':
                brace_count += 1
                current_obj.append(char)
            elif char == '}':
                brace_count -= 1
                current_obj.append(char)
                if brace_count == 0:
                    json_objects.append(''.join(current_obj))
                    current_obj = []
            else:
                if brace_count > 0:
                    current_obj.append(char)
        
        for json_str in json_objects:
            try:
                data = json.loads(json_str)
                result_data = data.get('data', {}).get('data', {}).get('resultData', [])
                if isinstance(result_data, list):
                    for product in result_data:
                        product['activityName'] = activity_name
                        all_products.append(product)
            except json.JSONDecodeError:
                continue
    
    return all_products


def main():
    st.title("🛒 淘宝活动爬取")
    
    st.subheader("上传淘宝活动txt文件")
    txt_files = st.file_uploader("选择淘宝活动txt文件", type="txt", accept_multiple_files=True)
    
    if st.button("开始解析"):
        if not txt_files:
            st.error("请先上传淘宝活动txt文件")
            return
        
        with st.spinner("正在解析淘宝活动数据..."):
            all_products = parse_taobao_txt(txt_files)
            
            if not all_products:
                st.error("未能解析到任何商品数据")
                return
            
            df = pd.DataFrame(all_products)
            
            if not df.empty:
                columns = ['activityName', 'name', 'priceCny', 'onSale', 'valid', 'reason']
                available_columns = [col for col in columns if col in df.columns]
                df = df[available_columns]
                
                column_mapping = {
                    'activityName': '活动名称',
                    'name': '商品名称',
                    'priceCny': '价格(元)',
                    'onSale': '是否在售',
                    'valid': '是否有效',
                    'reason': '原因'
                }
                df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        st.subheader("解析结果")
        st.dataframe(df)
        
        st.metric("商品总数", len(all_products))
        st.metric("处理文件数", len(txt_files))
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        
        st.download_button(
            label="下载商品数据",
            data=output,
            file_name="淘宝商品数据.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


if __name__ == '__main__':
    main()
