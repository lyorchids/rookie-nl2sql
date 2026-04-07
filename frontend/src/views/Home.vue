<template>
  <div class="home">
    <header class="header">
      <h1>NL2SQL 智能查询助手</h1>
      <button v-if="messages.length > 0" class="clear-btn" @click="clearMessages">清空对话</button>
    </header>
    <main class="main">
      <ChatContainer :messages="messages" />
      <ChatInput :disabled="isLoading" @send="handleSend" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useChatStore } from '../stores/chat'
import ChatContainer from '../components/ChatContainer.vue'
import ChatInput from '../components/ChatInput.vue'

const chatStore = useChatStore()
const { messages, isLoading } = storeToRefs(chatStore)
const { sendMessage, clearMessages } = chatStore

function handleSend(question: string) {
  sendMessage(question)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa;
  color: #333;
}
</style>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
}

.header h1 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.clear-btn {
  padding: 6px 12px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  color: #ff4d4f;
  border-color: #ff4d4f;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
