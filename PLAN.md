# NL2SQL 全栈项目计划

## 项目结构

```
rookie-nl2sql/
├── backend/              # Python 后端 (FastAPI + LangGraph)
│   ├── configs/          # 配置文件
│   ├── data/             # 数据库文件
│   ├── graphs/           # LangGraph 图定义
│   │   ├── nodes/        # 节点实现
│   │   ├── base_graph.py # 主图
│   │   └── state.py      # 状态定义
│   ├── prompts/          # 提示词模板
│   ├── tools/            # 工具类
│   ├── api/              # FastAPI 接口 (待创建)
│   └── requirements.txt  # Python 依赖
├── frontend/             # Vue3 前端 (待创建)
│   └── src/
│       ├── api/          # API 请求
│       ├── components/   # 组件
│       ├── types/        # 类型定义
│       ├── stores/       # 状态管理
│       └── views/        # 页面
└── PLAN.md               # 本文件
```

---

## 前端布局设计

```
┌─────────────────────────────────────────────────────┐
│                    聊天消息区域                        │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ [AI] 节点步骤展示                             │   │
│  │   ✓ 解析意图 - 识别用户意图...                │   │
│  │   ✓ 选择数据表 - 选择相关表...                │   │
│  │   ✓ 生成SQL - 生成查询语句...                 │   │
│  │   ✓ 验证SQL - 验证SQL语法...                  │   │
│  │   ✓ 安全检查 - 检查SQL安全性...               │   │
│  │   ✓ 执行SQL - 执行查询...                     │   │
│  │   ✓ 生成答案 - 生成最终回答...                 │   │
│  │                                             │   │
│  │   [流式输出] 根据查询结果，拥有专辑最多的...    │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│                          ┌──────────────────────┐  │
│                          │ [用户] 拥有专辑最多... │  │
│                          └──────────────────────┘  │
│                                                     │
├─────────────────────────────────────────────────────┤
│  ┌────────────────────────────┐  ┌───────────────┐ │
│  │ [输入框__________________] │  │   [发送按钮]   │ │
│  └────────────────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 布局说明

1. **上下结构**：上方是聊天消息区域，下方是用户输入框
2. **消息排列**：
   - 用户消息：右对齐
   - AI 消息：左对齐
3. **AI 消息内容**：
   - 先显示节点步骤（每个节点的中文名 + 说明文字）
   - 步骤完成后，在下方流式输出最终回答

---

## 实施计划

### 阶段一：后端 SSE 接口

#### 1.1 新增 FastAPI 服务
- 文件：`backend/api/server.py`
- 功能：
  - POST `/api/chat` 接收用户问题
  - 使用 `astream_events` 推送 SSE 事件
  - 事件格式：

    | 事件类型 | 数据格式 | 说明 |
    |---------|---------|------|
    | `node_start` | `{"node": "parse_intent"}` | 节点开始执行 |
    | `node_progress` | `{"node": "parse_intent", "show": "识别结果..."}` | 节点完成 |
    | `token` | `{"content": "你"}` | LLM token |
    | `done` | `{}` | 流式输出结束 |

#### 1.2 修改 `base_graph.py`
- 将 `run_query` 改造为异步生成器
- 返回 SSE 格式的事件流

#### 1.3 节点中文映射
```python
NODE_LABELS = {
    "parse_intent": "解析意图",
    "select_tables": "选择数据表",
    "generate_sql": "生成SQL",
    "validate_sql": "验证SQL",
    "sandbox_check": "安全检查",
    "execute_sql": "执行SQL",
    "generate_answer": "生成答案"
}
```

---

### 阶段二：前端项目初始化

#### 2.1 创建 Vue3 项目
- 使用 Vite + Vue3 + TypeScript
- 安装依赖：`pinia`, `element-plus`, `@vueuse/core`

#### 2.2 目录结构
```
frontend/
├── src/
│   ├── api/
│   │   └── chat.ts           # SSE 请求封装
│   ├── components/
│   │   ├── ChatMessage.vue   # 消息气泡组件
│   │   ├── NodeSteps.vue     # 节点步骤展示
│   │   ├── ChatInput.vue     # 输入框组件
│   │   └── ChatContainer.vue # 聊天容器
│   ├── types/
│   │   └── index.ts          # TypeScript 类型
│   ├── stores/
│   │   └── chat.ts           # Pinia 状态管理
│   ├── views/
│   │   └── Home.vue          # 主页面
│   ├── App.vue
│   └── main.ts
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

### 阶段三：前端类型定义

#### 3.1 核心类型
```typescript
interface NodeStep {
  node: string          // 节点英文名
  label: string         // 节点中文名
  show: string          // 说明文字
  status: 'pending' | 'running' | 'completed'
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string       // 最终回答内容
  steps?: NodeStep[]    // 节点步骤
  isStreaming: boolean  // 是否正在流式输出
  timestamp: number
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  currentMessage: Message | null
}
```

---

### 阶段四：前端组件实现

#### 4.1 `ChatInput.vue` - 输入框组件
- 文本输入框
- 发送按钮（支持 Enter 发送）
- 加载状态禁用

#### 4.2 `NodeSteps.vue` - 节点步骤组件
- 显示节点步骤列表
- 每个步骤显示：状态图标 + 中文名 + 说明
- 动画效果：步骤逐个出现

#### 4.3 `ChatMessage.vue` - 消息气泡组件
- 用户消息：右对齐，蓝色背景
- AI 消息：左对齐，白色背景
- 内部包含 `NodeSteps` 组件和流式文本

#### 4.4 `ChatContainer.vue` - 聊天容器
- 消息列表展示
- 自动滚动到底部
- 加载骨架屏

#### 4.5 `Home.vue` - 主页面
- 整合所有组件
- 处理发送逻辑

---

### 阶段五：SSE 事件处理

#### 5.1 `api/chat.ts` - SSE 请求封装
```typescript
export async function streamChat(
  question: string,
  callbacks: {
    onNodeStart: (node: string) => void
    onNodeProgress: (node: string, show: string) => void
    onToken: (token: string) => void
    onDone: () => void
    onError: (error: Error) => void
  }
): Promise<void>
```

#### 5.2 事件解析逻辑
- 使用 `fetch` + `ReadableStream` 接收 SSE
- 按行解析 `event:` 和 `data:` 字段
- 根据事件类型调用对应回调

---

### 阶段六：状态管理

#### 6.1 `stores/chat.ts` - Pinia Store
- `sendMessage(question)`: 发送消息并处理 SSE
- 管理消息列表和加载状态
- 处理流式输出状态

---

### 阶段七：样式优化

- 响应式布局
- 消息气泡样式
- 节点步骤动画
- 加载状态指示器
- 滚动条美化

---

## 执行顺序

1. ✅ 创建计划文档
2. ⬜ 后端 SSE 接口 (`backend/api/server.py`)
3. ⬜ 修改 `base_graph.py` 支持事件流
4. ⬜ 前端项目初始化
5. ⬜ 类型定义
6. ⬜ 组件实现
7. ⬜ SSE 事件处理
8. ⬜ 状态管理
9. ⬜ 样式优化
10. ⬜ 联调测试
