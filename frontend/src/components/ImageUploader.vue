<template>
  <div class="image-uploader">
    <div 
      v-if="!uploadedImage"
      class="upload-area"
      :class="{ dragover: isDragging }"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @click="$refs.fileInput.click()"
    >
      <input 
        ref="fileInput"
        type="file" 
        accept="image/*"
        style="display: none"
        @change="handleSelect"
      >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <path d="M21 15l-5-5L5 21"/>
      </svg>
      <span class="label">{{ label }}</span>
      <span class="hint">点击上传</span>
    </div>

    <div v-else class="preview-area">
      <img :src="previewUrl" :alt="label">
      <div class="overlay">
        <span class="label">{{ label }}</span>
        <button class="btn-remove" @click="handleRemove">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="isUploading" class="uploading-overlay">
      <svg class="animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
        <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
      </svg>
      <span>上传中...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  imageType: {
    type: String,
    required: true
  },
  uploadedImage: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['upload', 'remove'])

const isDragging = ref(false)
const isUploading = ref(false)

const previewUrl = computed(() => {
  if (props.uploadedImage?.file) {
    return URL.createObjectURL(props.uploadedImage.file)
  }
  return props.uploadedImage?.url || ''
})

function handleDrop(e) {
  isDragging.value = false
  const files = e.dataTransfer.files
  if (files.length > 0 && files[0].type.startsWith('image/')) {
    uploadFile(files[0])
  }
}

function handleSelect(e) {
  const files = e.target.files
  if (files.length > 0) {
    uploadFile(files[0])
  }
}

async function uploadFile(file) {
  isUploading.value = true
  try {
    emit('upload', { file, imageType: props.imageType })
  } finally {
    isUploading.value = false
  }
}

function handleRemove() {
  emit('remove', props.imageType)
}
</script>

<style scoped>
.image-uploader {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 16/10;
}

.upload-area {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--bg-tertiary);
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover,
.upload-area.dragover {
  border-color: var(--brand-blue);
  background: rgba(59,130,246,0.05);
}

.upload-area svg {
  width: 32px;
  height: 32px;
  color: var(--text-muted);
}

.upload-area .label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.upload-area .hint {
  font-size: 11px;
  color: var(--text-muted);
}

.preview-area {
  width: 100%;
  height: 100%;
  position: relative;
}

.preview-area img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(transparent 50%, rgba(0,0,0,0.7));
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.preview-area:hover .overlay {
  opacity: 1;
}

.overlay .label {
  font-size: 12px;
  color: white;
  font-weight: 500;
}

.btn-remove {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: rgba(239,68,68,0.8);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove svg {
  width: 16px;
  height: 16px;
}

.uploading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.uploading-overlay svg {
  width: 24px;
  height: 24px;
  color: white;
}

.uploading-overlay span {
  font-size: 12px;
  color: white;
}
</style>
