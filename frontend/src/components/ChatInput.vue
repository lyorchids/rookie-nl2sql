<template>
  <div class="chat-input">
    <div class="input-wrapper">
      <textarea
        v-model="inputValue"
        class="input-textarea"
        placeholder="输入你的问题..."
        :disabled="disabled"
        @keydown.enter.exact.prevent="handleSend"
        rows="1"
      ></textarea>
      <button
        class="send-button"
        :disabled="disabled || !inputValue.trim()"
        @click="handleSend"
      >
        <span v-if="!disabled">发送</span>
        <span v-else class="loading-icon">⟳</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [value: string]
}>()

const inputValue = ref('')

function handleSend() {
  const value = inputValue.value.trim()
  if (!value || props.disabled) return
  emit('send', value)
  inputValue.value = ''
}
</script>

<style scoped>
.chat-input {
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  max-width: 800px;
  margin: 0 auto;
  align-items: flex-end;
}

.input-textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
  max-height: 120px;
}

.input-textarea:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.input-textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  padding: 10px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
  height: 42px;
}

.send-button:hover:not(:disabled) {
  background: #40a9ff;
}

.send-button:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.loading-icon {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
