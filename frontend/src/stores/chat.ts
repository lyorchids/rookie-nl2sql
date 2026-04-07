import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message, NodeStep } from '../types'
import { streamChat } from '../api/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)

  async function sendMessage(question: string) {
    if (!question.trim() || isLoading.value) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      steps: [],
      isStreaming: false,
      timestamp: Date.now(),
    }
    messages.value.push(userMessage)

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      steps: [],
      isStreaming: true,
      timestamp: Date.now(),
    }
    messages.value.push(assistantMessage)

    // Get reactive reference by index
    const assistantIndex = messages.value.length - 1

    isLoading.value = true

    await streamChat(question, {
      onNodeStart: (node: string, label: string) => {
        const step: NodeStep = { node, label, show: '', status: 'running' }
        messages.value[assistantIndex].steps.push(step)
      },
      onNodeProgress: (node: string, label: string, show: string) => {
        const msg = messages.value[assistantIndex]
        const step = msg.steps.find(s => s.node === node)
        if (step) {
          step.show = show
          step.status = 'completed'
        }
      },
      onToken: (token: string) => {
        messages.value[assistantIndex].content += token
      },
      onDone: () => {
        messages.value[assistantIndex].isStreaming = false
        isLoading.value = false
      },
      onError: (error: Error) => {
        console.error('Stream error:', error)
        messages.value[assistantIndex].content = `请求失败: ${error.message}`
        messages.value[assistantIndex].isStreaming = false
        isLoading.value = false
      },
    })
  }

  function clearMessages() {
    messages.value = []
    isLoading.value = false
  }

  return {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
  }
})
