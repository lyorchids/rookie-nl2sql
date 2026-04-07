export interface NodeStep {
  node: string
  label: string
  show: string
  status: 'pending' | 'running' | 'completed'
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  steps: NodeStep[]
  isStreaming: boolean
  timestamp: number
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
}

export interface SSEEvent {
  event: string
  data: Record<string, unknown>
}
