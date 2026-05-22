import streamlit as st

st.set_page_config(
    page_title="活动数据分析平台",
    page_icon="📊",
    layout="wide"
)

st.title("📊 活动数据分析平台")
st.markdown("""
欢迎使用活动数据分析平台！

### 功能介绍

本平台包含两个主要模块：

**1. 美团活动分析**
- 读取美团活动txt文件
- 匹配门店商品数据
- 计算毛利率，判断是否适合参加活动

**2. 淘宝活动爬取**
- 读取淘宝活动txt文件
- 解析JSON数据
- 提取商品信息并导出

### 使用说明

请从左侧导航栏选择您需要使用的功能模块。

### 注意事项

- 请确保上传的文件格式正确
- 美团分析需要同时提供门店商品导出文件
- 支持的文件格式：txt、xlsx
""")

st.sidebar.success("请从左侧选择功能模块")
