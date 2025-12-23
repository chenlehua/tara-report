<template>
  <div class="image-upload-section">
    <!-- 架构图上传 -->
    <div class="section-card">
      <h3>
        <el-icon><Picture /></el-icon>
        架构图上传
        <span class="optional-hint">(可选)</span>
      </h3>
      
      <div class="image-upload-grid">
        <div 
          v-for="slot in architectureSlots" 
          :key="slot.type"
          class="image-slot"
          :class="{ 'has-image': images[slot.type] }"
        >
          <input 
            :ref="el => setInputRef(slot.type, el)"
            type="file" 
            accept="image/png,image/jpeg,image/jpg,image/gif,image/bmp"
            @change="e => handleImageSelect(e, slot.type)"
            style="display: none"
          />
          
          <div v-if="!images[slot.type]" class="slot-placeholder" @click="triggerSelect(slot.type)">
            <el-icon :size="24"><Picture /></el-icon>
            <span>{{ slot.label }}</span>
            <span class="optional">点击上传</span>
          </div>
          
          <div v-else class="slot-preview">
            <img :src="previews[slot.type]" :alt="slot.label" />
            <div class="preview-overlay">
              <el-button type="primary" circle size="small" @click="triggerSelect(slot.type)">
                <el-icon><RefreshRight /></el-icon>
              </el-button>
              <el-button type="danger" circle size="small" @click="clearImage(slot.type)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <span class="slot-label">{{ slot.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 攻击树图上传 -->
    <div class="section-card">
      <h3>
        <el-icon><Share /></el-icon>
        攻击树图上传
        <span class="optional-hint">(可选，支持多张)</span>
      </h3>
      
      <div class="attack-tree-upload">
        <div class="attack-tree-grid">
          <!-- 已上传的攻击树图 -->
          <div 
            v-for="(tree, index) in attackTrees" 
            :key="index"
            class="attack-tree-item"
          >
            <div class="tree-preview">
              <img :src="tree.preview" :alt="`攻击树 ${index + 1}`" />
              <div class="preview-overlay">
                <el-button type="danger" circle size="small" @click="removeAttackTree(index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <span class="tree-label">攻击树 {{ index + 1 }}</span>
            </div>
          </div>
          
          <!-- 添加新攻击树按钮 -->
          <div class="attack-tree-item add-new" @click="triggerAttackTreeSelect">
            <input 
              ref="attackTreeInputRef"
              type="file" 
              accept="image/png,image/jpeg,image/jpg,image/gif,image/bmp"
              multiple
              @change="handleAttackTreeSelect"
              style="display: none"
            />
            <div class="add-placeholder">
              <el-icon :size="32"><Plus /></el-icon>
              <span>添加攻击树图</span>
            </div>
          </div>
        </div>
        
        <p class="upload-hint" v-if="attackTrees.length > 0">
          已上传 {{ attackTrees.length }} 张攻击树图
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, RefreshRight, Delete, Plus, Share } from '@element-plus/icons-vue'

// 图片类型
type ArchImageType = 'item_boundary_image' | 'system_architecture_image' | 'software_architecture_image' | 'dataflow_image'

// 定义事件 - 使用 change 事件名以匹配 GenerateView
const emit = defineEmits<{
  (e: 'change', images: Record<string, File | null>): void
}>()

// 架构图插槽配置
const architectureSlots: Array<{ type: ArchImageType; label: string }> = [
  { type: 'item_boundary_image', label: '项目边界图' },
  { type: 'system_architecture_image', label: '系统架构图' },
  { type: 'software_architecture_image', label: '软件架构图' },
  { type: 'dataflow_image', label: '数据流图' }
]

// 架构图状态
const inputRefs = ref<Record<string, HTMLInputElement | null>>({})
const images = reactive<Record<ArchImageType, File | null>>({
  item_boundary_image: null,
  system_architecture_image: null,
  software_architecture_image: null,
  dataflow_image: null
})
const previews = reactive<Record<ArchImageType, string>>({
  item_boundary_image: '',
  system_architecture_image: '',
  software_architecture_image: '',
  dataflow_image: ''
})

// 攻击树状态
const attackTreeInputRef = ref<HTMLInputElement | null>(null)
const attackTrees = ref<Array<{ file: File; preview: string }>>([])

// 最大文件大小 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024

function setInputRef(type: string, el: any) {
  if (el) {
    inputRefs.value[type] = el as HTMLInputElement
  }
}

function triggerSelect(type: ArchImageType) {
  inputRefs.value[type]?.click()
}

function validateFile(file: File): boolean {
  if (file.size > MAX_FILE_SIZE) {
    ElMessage.error(`文件 ${file.name} 太大，最大支持 10MB`)
    return false
  }
  
  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp']
  if (!validTypes.includes(file.type)) {
    ElMessage.error(`文件 ${file.name} 格式不支持，请上传 PNG/JPG/GIF/BMP 格式`)
    return false
  }
  
  return true
}

function handleImageSelect(event: Event, type: ArchImageType) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    
    if (!validateFile(file)) {
      input.value = ''
      return
    }
    
    images[type] = file
    
    // 生成预览URL
    const reader = new FileReader()
    reader.onload = (e) => {
      previews[type] = e.target?.result as string
    }
    reader.readAsDataURL(file)
    
    emitChange()
  }
}

function clearImage(type: ArchImageType) {
  images[type] = null
  previews[type] = ''
  if (inputRefs.value[type]) {
    inputRefs.value[type]!.value = ''
  }
  emitChange()
}

// 攻击树相关方法
function triggerAttackTreeSelect() {
  attackTreeInputRef.value?.click()
}

function handleAttackTreeSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    const files = Array.from(input.files)
    
    for (const file of files) {
      if (!validateFile(file)) {
        continue
      }
      
      const reader = new FileReader()
      reader.onload = (e) => {
        attackTrees.value.push({
          file: file,
          preview: e.target?.result as string
        })
        emitChange()
      }
      reader.readAsDataURL(file)
    }
    
    // 清空input以便可以重复选择相同文件
    input.value = ''
  }
}

function removeAttackTree(index: number) {
  attackTrees.value.splice(index, 1)
  emitChange()
}

function emitChange() {
  const result: Record<string, File | null> = { ...images }
  
  // 添加攻击树图片，使用 attack_tree_0, attack_tree_1 等命名
  attackTrees.value.forEach((tree, index) => {
    result[`attack_tree_${index}`] = tree.file
  })
  
  // 添加攻击树数量
  result['_attack_tree_count'] = attackTrees.value.length as any
  
  emit('change', result)
}

// 清除所有图片
function clearImages() {
  Object.keys(images).forEach(key => {
    images[key as ArchImageType] = null
    previews[key as ArchImageType] = ''
  })
  attackTrees.value = []
  emitChange()
}

// 暴露方法供父组件使用
defineExpose({
  getImages: () => ({ 
    ...images, 
    attackTrees: attackTrees.value.map(t => t.file) 
  }),
  clearImages,
  clearAll: clearImages
})
</script>

<style scoped lang="scss">
.image-upload-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 24px;

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 20px;
    
    .optional-hint {
      font-size: 12px;
      font-weight: normal;
      color: rgba(255, 255, 255, 0.4);
    }
  }
}

.image-upload-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.image-slot {
  aspect-ratio: 16 / 9;
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &.has-image {
    border-style: solid;
    border-color: transparent;
  }
  
  &:hover {
    border-color: rgba(59, 130, 246, 0.5);
  }
}

.slot-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.02);
  transition: background 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .el-icon {
    color: rgba(255, 255, 255, 0.3);
  }
  
  span {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .optional {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.3);
  }
}

.slot-preview {
  position: relative;
  width: 100%;
  height: 100%;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .preview-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  &:hover .preview-overlay {
    opacity: 1;
  }
  
  .slot-label {
    position: absolute;
    bottom: 8px;
    left: 8px;
    font-size: 12px;
    color: white;
    background: rgba(0, 0, 0, 0.6);
    padding: 4px 8px;
    border-radius: 4px;
  }
}

// 攻击树样式
.attack-tree-upload {
  .upload-hint {
    margin-top: 12px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    text-align: center;
  }
}

.attack-tree-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.attack-tree-item {
  aspect-ratio: 4 / 3;
  border-radius: 8px;
  overflow: hidden;
  
  &.add-new {
    border: 2px dashed rgba(255, 255, 255, 0.1);
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: rgba(59, 130, 246, 0.5);
      background: rgba(59, 130, 246, 0.1);
    }
  }
  
  .add-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: rgba(255, 255, 255, 0.4);
    
    span {
      font-size: 13px;
    }
  }
  
  .tree-preview {
    position: relative;
    width: 100%;
    height: 100%;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .preview-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    
    &:hover .preview-overlay {
      opacity: 1;
    }
    
    .tree-label {
      position: absolute;
      bottom: 8px;
      left: 8px;
      font-size: 12px;
      color: white;
      background: rgba(0, 0, 0, 0.6);
      padding: 4px 8px;
      border-radius: 4px;
    }
  }
}
</style>
