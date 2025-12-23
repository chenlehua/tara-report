<template>
  <div 
    class="file-upload"
    :class="{ 'is-dragover': isDragover, 'has-file': !!uploadedFile }"
    @dragover.prevent="isDragover = true"
    @dragleave.prevent="isDragover = false"
    @drop.prevent="handleDrop"
  >
    <input 
      ref="fileInput"
      type="file" 
      accept=".json"
      @change="handleFileSelect"
      style="display: none"
    />
    
    <div v-if="!uploadedFile" class="upload-placeholder" @click="triggerSelect">
      <el-icon :size="48" class="upload-icon"><UploadFilled /></el-icon>
      <h3>上传 JSON 数据文件</h3>
      <p>拖拽文件到此处，或点击选择文件</p>
      <p class="file-hint">支持 .json 格式</p>
    </div>
    
    <div v-else class="file-info">
      <div class="file-details">
        <el-icon :size="32" class="file-icon"><Document /></el-icon>
        <div class="file-meta">
          <span class="file-name">{{ uploadedFile.name }}</span>
          <span class="file-size">{{ formatSize(uploadedFile.size) }}</span>
        </div>
      </div>
      <div class="file-actions">
        <el-button type="primary" text @click="triggerSelect">
          <el-icon><RefreshRight /></el-icon>
          更换文件
        </el-button>
        <el-button type="danger" text @click="clearFile">
          <el-icon><Delete /></el-icon>
          移除
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { UploadFilled, Document, RefreshRight, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits<{
  (e: 'file-selected', file: File): void
  (e: 'file-cleared'): void
  (e: 'data-parsed', data: any): void
}>()

const fileInput = ref<HTMLInputElement>()
const isDragover = ref(false)
const uploadedFile = ref<File | null>(null)

function triggerSelect() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    processFile(input.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragover.value = false
  const files = event.dataTransfer?.files
  if (files && files[0]) {
    if (files[0].type === 'application/json' || files[0].name.endsWith('.json')) {
      processFile(files[0])
    } else {
      ElMessage.warning('请上传 JSON 格式文件')
    }
  }
}

async function processFile(file: File) {
  uploadedFile.value = file
  emit('file-selected', file)
  
  // 解析JSON内容
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    emit('data-parsed', data)
  } catch (error) {
    ElMessage.error('JSON 文件解析失败')
    console.error('JSON parse error:', error)
  }
}

function clearFile() {
  uploadedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  emit('file-cleared')
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped lang="scss">
.file-upload {
  border: 2px dashed rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s ease;
  
  &.is-dragover {
    border-color: #409eff;
    background: rgba(64, 158, 255, 0.1);
  }
  
  &.has-file {
    border-style: solid;
    border-color: rgba(255, 255, 255, 0.1);
  }
}

.upload-placeholder {
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  
  .upload-icon {
    color: rgba(255, 255, 255, 0.3);
    margin-bottom: 16px;
  }
  
  h3 {
    font-size: 18px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 8px;
  }
  
  p {
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
    margin-bottom: 4px;
  }
  
  .file-hint {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.3);
  }
}

.file-info {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .file-icon {
    color: #409eff;
  }
  
  .file-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .file-name {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
  }
  
  .file-size {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.file-actions {
  display: flex;
  gap: 8px;
}
</style>
