# NL2SQL 智能查询助手

> 基于 LangGraph + Vue3 的自然语言转 SQL 全栈系统，支持实时流式输出与节点进度展示。

---

## 📖 项目简介

NL2SQL 是一个智能数据库查询系统，用户可以用自然语言提问，系统会自动：
1. **解析意图** - 理解用户问题
2. **选择数据表** - 从数据库中找出相关的表
3. **生成 SQL** - 将自然语言转换为 SQL 查询
4. **验证 SQL** - 语法验证与自动修正
5. **安全检查** - 防止 SQL 注入和危险操作
6. **执行查询** - 运行 SQL 并获取结果
7. **生成答案** - 将查询结果转化为自然语言报告

整个过程通过 **SSE (Server-Sent Events)** 实时推送到前端，用户可以看到每个步骤的进度和最终答案的流式输出。

---

## 🏗️ 技术架构

### 后端
| 技术 | 用途 |
|------|------|
| **LangGraph** | 构建多步骤 AI Agent 工作流 |
| **LangChain** | LLM 调用与消息管理 |
| **FastAPI** | RESTful API + SSE 流式接口 |
| **sqlglot** | SQL 语法解析与验证 |
| **SQLite** | 示例数据库 (Chinook) |
| **Uvicorn** | ASGI 服务器 |

### 前端
| 技术 | 用途 |
|------|------|
| **Vue 3** | 前端框架 (Composition API) |
| **TypeScript** | 类型安全 |
| **Pinia** | 状态管理 |
| **Vite 5** | 构建工具 + 开发服务器 |
| **SSE (fetch)** | 实时接收后端事件流 |

---

## 🔄 工作流程

```
用户提问
   │
   ▼
┌─────────────────┐
│  1. 解析意图     │ ← 判断是否相关，识别意图类型
└────────┬────────┘
         │
    ┌────┴────┐
    │ 相关？   │
    └────┬────┘
         │
    ┌────▼─────────────────┐
    │  2. 选择数据表        │ ← 从 Schema 中选择相关表
    └────────┬─────────────┘
             │
    ┌────────▼─────────────┐
    │  3. 生成 SQL         │ ← LLM 将 NL 转为 SQL
    └────────┬─────────────┘
             │
    ┌────────▼─────────────┐
    │  4. 验证 SQL         │ ← 语法检查，失败则重试修正
    └────────┬─────────────┘
             │
    ┌────────▼─────────────┐
    │  5. 沙箱安全检查     │ ← 只读验证、黑名单、注入检测
    └────────┬─────────────┘
             │
    ┌────────▼─────────────┐
    │  6. 执行 SQL         │ ← 运行查询，获取结果
    └────────┬─────────────┘
             │
    ┌────────▼─────────────┐
    │  7. 生成答案         │ ← 将结果转为自然语言报告 (流式)
    └────────┬─────────────┘
             │
             ▼
         返回给用户
```

---

## 🛡️ 安全机制

| 检查项 | 说明 |
|--------|------|
| **语法验证** | 使用 sqlglot 解析 SQL AST，确保语法正确 |
| **只读验证** | 仅允许 SELECT/WITH 语句，拒绝写操作 |
| **关键字黑名单** | 拦截 DROP、DELETE、INSERT、UPDATE、ALTER 等危险操作 |
| **注入检测** | 检测分号后的额外语句，防止多语句注入 |
| **复杂度限制** | 限制 JOIN 数量、子查询深度、查询长度 |
| **自动重试** | SQL 验证失败时，自动将错误反馈给 LLM 修正 (最多 2 次) |

---

## 🚀 快速开始

### 环境要求
- **Python** >= 3.10
- **Node.js** >= 18
- **npm** >= 9

### 1. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM API Key (支持 DeepSeek/Qwen/OpenAI)

# 启动服务
python api/server.py
```

后端将运行在 `http://localhost:8000`

### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:5173`

### 3. 访问应用

打开浏览器访问 `http://localhost:5173`，输入自然语言问题即可开始查询。

---

## 📡 API 接口

### POST `/api/chat`

流式查询接口，使用 SSE 推送实时事件。

**请求体：**
```json
{
  "question": "拥有专辑最多的前3名艺术家",
  "session_id": "可选的会话ID"
}
```

**SSE 事件：**

| 事件类型 | 数据格式 | 说明 |
|---------|---------|------|
| `node_start` | `{"node": "parse_intent", "label": "解析意图"}` | 节点开始执行 |
| `node_progress` | `{"node": "parse_intent", "label": "解析意图", "show": "识别结果..."}` | 节点完成 |
| `token` | `{"content": "你"}` | LLM 生成的 token |
| `done` | `{}` | 查询完成 |

### GET `/health`

健康检查接口。

**响应：**
```json
{ "status": "ok" }
```

---

## ⚙️ 配置说明

### LLM 配置 (`.env`)

支持三种 LLM 提供商：

```env
# 选择提供商: deepseek / qwen / openai
LLM_PROVIDER=deepseek

# DeepSeek (推荐)
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Qwen (通义千问)
QWEN_API_KEY=your-api-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 通用 LLM 参数
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30

# 数据库配置
DB_TYPE=sqlite
DB_PATH=data/chinook.db
```

### 沙箱配置 (`configs/dev.yaml`)

```yaml
sandbox:
  max_result_rows: 100      # 最大返回行数
  max_query_length: 5000    # 最大查询长度
  max_joins: 5              # 最大 JOIN 数量
  max_subquery_depth: 3     # 最大子查询深度
```

---


## 📋 节点说明

| 节点 | 中文名 | 功能 | 输出 |
|------|--------|------|------|
| `parse_intent` | 解析意图 | 判断问题是否相关，识别意图类型 | `is_relevant`, `intent_type` |
| `select_tables` | 选择数据表 | 从数据库 Schema 中选择相关表 | `tables` |
| `generate_sql` | 生成SQL | 将自然语言转换为 SQL | `candidate_sql` |
| `validate_sql` | 验证SQL | 语法验证，失败则重试修正 | `validation` |
| `sandbox_check` | 安全检查 | 只读验证、黑名单、注入检测 | `sandbox` |
| `execute_sql` | 执行SQL | 运行查询，获取结果 | `execution_result` |
| `generate_answer` | 生成答案 | 将结果转为自然语言报告 | `answer` |

---

## 🎨 前端功能

- **实时进度展示** - 每个节点执行时显示步骤和说明
- **流式答案输出** - 最终回答逐字显示，类似 ChatGPT
- **对话历史** - 支持多轮对话
- **自动滚动** - 新消息自动滚动到底部
- **清空对话** - 一键清空聊天记录

---

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---


