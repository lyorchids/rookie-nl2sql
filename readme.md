# 项目介绍
暂无介绍
## 功能模块
暂无功能

## 项目结构
```
rookie-nl2sql/
├── graphs/
│   ├── state.py           # State 定义
│   └── base_graph.py      # 基础图实现
├── configs/
│   ├── config.py          # 配置加载器
│   └── dev.yaml           # 开发环境配置
├── .env.example           # 环境变量模板
├── requirements.txt       # 依赖清单
└── README.md             # 项目说明
```

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```
### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件,选择一个 LLM 提供商并填入 API Key
# 注意: M0 阶段不需要 API Key,可以留空。M1 开始需要配置。
```
**支持的 LLM 提供商** (推荐国内用户使用 DeepSeek 或 Qwen):
- **DeepSeek** (推荐): 性价比高,国内访问快 - [获取 API Key](https://platform.deepseek.com/)
- **Qwen** (通义千问): 阿里云生态 - [获取 API Key](https://dashscope.aliyun.com/)
- **OpenAI** (可选): 需要科学上网
