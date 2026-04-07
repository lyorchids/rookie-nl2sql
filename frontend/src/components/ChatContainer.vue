<template>
  <div class="chat-container">
    <div class="messages-wrapper" ref="messagesRef">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <div class="empty-text">输入你的问题，开始查询</div>
      </div>
      <ChatMessage
        v-for="message in messages"
        :key="message.id"
        :message="message"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Message } from '../types'
import ChatMessage from './ChatMessage.vue'

const props = defineProps<{
  messages: Message[]
}>()

const messagesRef = ref<HTMLElement | null>(null)

watch(
  () => props.messages,
  async () => {
    await nextTick()
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  },
  { deep: true }
)
</script>

<style scoped>
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}

.messages-wrapper {
  height: 100%;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
}
</style>
