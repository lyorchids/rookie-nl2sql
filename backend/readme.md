# 项目介绍
自然语言转sql，执行sql查询并得到结果，并将结果告诉提问者
## 功能模块
修改点： 

1. 将sql重新生成变成一个环，在条件路由中设置条件
2. 意图解析两种选择： 
   无关问题直接回答，sql问题一步一步执行
   进行意图澄清，需要对话历史，澄清完进行一下步，否则让用户进行输入
3. 生成答案的提示词模板需要修改。
4. 还没有想到


### 模块说明

| 步骤 | 模块 | 功能 | 文件 |
|------|------|------|------|
| 1 | 意图解析 (parse_intent) | 解析用户问题意图，识别问题类型（聚合/排名/查询/未知），提取数量词和时间范围 | `graphs/base_graph.py` |
| 2 | 表选择 (select_tables) | LLM 理解数据库 Schema，从所有表中选择与用户问题相关的表，并进行表名验证 | `graphs/nodes/select_tables.py` |
| 3 | SQL 生成 (generate_sql) | 根据选中的表结构和用户问题，LLM 生成对应的 SQL 查询语句 | `graphs/nodes/generate_sql.py` |
| 4 | SQL 验证 (validate_sql) | 使用 sqlglot 验证 SQL 语法正确性；若验证失败，将错误信息反馈给 LLM 进行修正（最多重试 2 次） | `graphs/nodes/validate_sql.py`<br>`tools/sql_validator.py` |
| 5 | 沙箱检查 (sandbox_check) | 安全检查：只读权限验证（仅允许 SELECT）、危险关键字黑名单（DROP/DELETE/INSERT 等）、多语句注入检测、查询复杂度限制（JOIN 数量/子查询深度） | `graphs/nodes/sandbox_check.py`<br>`tools/sql_sandbox.py` |
| 6 | SQL 执行 (execute_sql) | 执行通过验证和安全检查的 SQL 查询，返回查询结果 | `graphs/nodes/execute_sql.py`<br>`tools/db.py` |
| 7 | 答案生成 (generate_answer) | 将 SQL 执行结果转化为用户友好的详细数据分析报告；统一处理所有场景（执行成功/失败/沙箱拦截/无数据） | `graphs/nodes/generate_answer.py` |

### 安全机制

- **语法验证**: 使用 sqlglot 进行 SQL 语法解析，确保生成的 SQL 语法正确
- **沙箱隔离**: 多层安全检查，防止恶意 SQL 注入和危险操作
  - 只读权限检查（仅允许 SELECT/WITH 语句）
  - 危险关键字黑名单（DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, ATTACH, DETACH, PRAGMA 等）
  - 多语句注入检测（防止分号后的额外语句）
  - 查询复杂度限制（最大 JOIN 数量、子查询深度、查询长度）
- **重试机制**: SQL 语法验证失败时，自动将错误信息反馈给 LLM 进行修正

### 配置说明

- **数据库方言**: 支持可配置的 SQL 方言（默认 sqlite，可扩展 mysql/postgres 等）
- **重试次数**: 可配置 SQL 验证重试次数（默认 2 次）
- **沙箱限制**: 可配置最大结果行数、最大查询长度、最大 JOIN 数量、最大子查询深度

## 项目结构
```
rookie-nl2sql/
├── graphs/
│   ├── state.py                   # State 定义
│   ├── base_graph.py              # 基础图实现
│   └── nodes/
├── tools/
├── prompts/
├── configs/
├── data/
├── tests/                         # 测试文件
├── scripts/                       # 脚本文件
├── requirements.txt               # 依赖清单
└── README.md                      # 项目说明
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
