<template>
  <div class="chat-message" :class="message.role">
    <div class="message-avatar">
      {{ message.role === 'user' ? '👤' : '🤖' }}
    </div>
    <div class="message-content">
      <NodeSteps v-if="message.steps.length > 0" :steps="message.steps" />
      <div class="message-text">
        {{ message.content }}
        <span v-if="message.isStreaming" class="cursor">▊</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '../types'
import NodeSteps from './NodeSteps.vue'

defineProps<{
  message: Message
}>()
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.message-content {
  flex: 1;
  min-width: 0;
  max-width: 70%;
}

.chat-message.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-message.assistant .message-text {
  background: #f0f2f5;
  color: #333;
  border-top-left-radius: 4px;
}

.chat-message.user .message-text {
  background: #1890ff;
  color: #fff;
  border-top-right-radius: 4px;
}

.cursor {
  display: inline-block;
  animation: blink 0.8s infinite;
  color: #1890ff;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
