# 活动数据分析平台

一个基于 Streamlit 的多页面应用，用于分析美团和淘宝的活动数据。

## 功能特性

### 🏪 美团活动分析
- 读取美团活动 txt 文件
- 匹配门店商品数据
- 计算毛利率，判断是否适合参加活动
- 支持模糊匹配商品名称

### 🛒 淘宝活动爬取
- 读取淘宝活动 txt 文件
- 解析 JSON 数据
- 提取商品信息并导出

## 技术栈

- Python 3.8+
- Streamlit 1.35.0
- Pandas 2.2.2
- FuzzyWuzzy 0.18.0

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 本地运行

```bash
streamlit run app.py
```

### 部署到 Streamlit Community Cloud

1. 将项目上传到 GitHub
2. 访问 [Streamlit Community Cloud](https://share.streamlit.io/)
3. 连接您的 GitHub 仓库
4. 选择主文件为 `app.py`
5. 点击 "Deploy"

## 使用说明

### 美团活动分析

1. 在左侧导航栏选择 "美团活动分析"
2. 上传美团活动 txt 文件（支持多选）
3. 上传门店商品导出文件（xlsx 格式）
4. 调整配置参数（可选）
5. 点击 "开始分析"
6. 查看分析结果并下载

### 淘宝活动爬取

1. 在左侧导航栏选择 "淘宝活动爬取"
2. 上传淘宝活动 txt 文件（支持多选）
3. 点击 "开始解析"
4. 查看解析结果并下载

## 项目结构

```
├── app.py                 # 主应用入口
├── requirements.txt       # 依赖列表
├── README.md             # 项目说明
└── pages/
    ├── 美团活动分析.py     # 美团活动分析页面
    └── 淘宝活动爬取.py     # 淘宝活动爬取页面
```

## 配置参数

### 美团活动分析

- **毛利率阈值**：默认 35%，大于此值认为可参加活动
- **模糊匹配阈值**：默认 80%，大于此值认为匹配成功

## License

MIT License
