# 美团活动分析工具

一个基于 Streamlit 的美团活动数据分析工具，用于匹配门店商品、计算毛利并判断商品是否适合参加活动。

## 功能特点

- 📁 支持批量上传美团活动 TXT 文件
- 📊 自动匹配美团商品与门店商品（模糊匹配）
- 💰 自动计算毛利和毛利率
- 🎯 根据毛利率阈值判断是否参加活动
- 📥 支持下载分析结果

## 技术栈

- Python 3.8+
- Streamlit
- Pandas
- FuzzyWuzzy

## 快速开始

### 本地运行

```bash
# 克隆项目
git clone https://github.com/your-username/meituan-analysis-app.git
cd meituan-analysis-app

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

### 部署到 Streamlit Cloud

1. Fork 本项目到你的 GitHub
2. 登录 [Streamlit Cloud](https://share.streamlit.io/)
3. 点击 "New app"
4. 选择你的 GitHub 仓库
5. 设置主文件路径为 `app.py`
6. 点击 "Deploy"

## 使用说明

1. **上传文件**：
   - 上传一个或多个美团活动 TXT 文件
   - 上传门店商品导出 Excel 文件

2. **配置参数**（侧边栏）：
   - 毛利率阈值：大于此值的商品可参加活动（默认 35%）
   - 模糊匹配阈值：匹配相似度阈值（默认 80%）

3. **查看结果**：
   - 查看统计信息（总商品数、成功匹配数、可参加活动数）
   - 查看详细分析表格
   - 下载分析结果 CSV 文件

## 文件结构

```
meituan-analysis-app/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖列表
└── README.md           # 项目说明
```

## 数据格式

### 美团活动 TXT 文件
每行一个 JSON 对象，包含活动商品信息。

### 门店商品 Excel 文件
需包含以下列：
- 商品名称（或包含"名称"的列）
- 进货价/成本价（或包含"成本"、"进价"的列）

## License

MIT
