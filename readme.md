# 项目介绍
自然语言转sql，执行sql查询并得到结果，并将结果告诉提问者
## 功能模块
流程：
1. 用户提问、llm解析用户意图进行判断，若是无关数据库查询问题，直接回答，若是关于数据库查询，跳到步骤2
2. llm理解Schema、抽取相应的表和字段，明白字段意思，注入到sql_prompt中，进行步骤3
3. llm根据sql_prompt 生成sql, 进行步骤4
4. 

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
```
**支持的 LLM 提供商** (推荐国内用户使用 DeepSeek 或 Qwen):
- **DeepSeek** (推荐): 性价比高,国内访问快 - [获取 API Key](https://platform.deepseek.com/)
- **Qwen** (通义千问): 阿里云生态 - [获取 API Key](https://dashscope.aliyun.com/)
- **OpenAI** (可选): 需要科学上网
