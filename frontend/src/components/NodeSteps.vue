<template>
  <div class="node-steps">
    <div
      v-for="(step, index) in steps"
      :key="step.node"
      class="step-item"
      :class="step.status"
      :style="{ animationDelay: `${index * 0.1}s` }"
    >
      <div class="step-icon">
        <span v-if="step.status === 'completed'" class="icon-check">✓</span>
        <span v-else-if="step.status === 'running'" class="icon-loading">⟳</span>
        <span v-else class="icon-pending">○</span>
      </div>
      <div class="step-content">
        <div class="step-label">{{ step.label }}</div>
        <div v-if="step.show" class="step-show">{{ step.show }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NodeStep } from '../types'

defineProps<{
  steps: NodeStep[]
}>()
</script>

<style scoped>
.node-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 13px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  opacity: 0;
  animation: fadeIn 0.3s ease forwards;
}

.step-item.running .step-icon {
  color: #1890ff;
}

.step-item.running .icon-loading {
  display: inline-block;
  animation: spin 1s linear infinite;
}

.step-item.completed .step-icon {
  color: #52c41a;
}

.step-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #bfbfbf;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-label {
  font-weight: 500;
  color: #333;
}

.step-show {
  color: #666;
  font-size: 12px;
  margin-top: 2px;
  line-height: 1.4;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
