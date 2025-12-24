<template>
  <div class="generator-page animate-fadeIn">
    <div class="page-header">
      <h1>一键生成TARA报告</h1>
      <p class="page-desc">上传JSON参数文件和相关图片，快速生成专业的威胁分析与风险评估报告</p>
    </div>

    <div class="generator-content">
      <!-- 左侧：上传区域 -->
      <div class="upload-section">
        <!-- JSON文件上传 -->
        <div class="card upload-card">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <path d="M14 2v6h6"/>
            </svg>
            上传JSON数据文件
          </h3>
          
          <div 
            class="upload-zone"
            :class="{ dragover: isDragging }"
            @drop.prevent="handleJsonDrop"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @click="$refs.jsonInput.click()"
          >
            <input 
              ref="jsonInput"
              type="file" 
              accept=".json"
              style="display: none"
              @change="handleJsonSelect"
            >
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17,8 12,3 7,8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <p v-if="!jsonFile">点击或拖拽上传JSON文件</p>
            <p v-else class="file-selected">{{ jsonFile.name }}</p>
            <span class="upload-hint">支持 .json 格式</span>
          </div>

          <div v-if="jsonFile" class="file-item">
            <div class="file-icon json">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <path d="M14 2v6h6"/>
              </svg>
            </div>
            <div class="file-info">
              <div class="file-name">{{ jsonFile.name }}</div>
              <div class="file-size">{{ formatFileSize(jsonFile.size) }}</div>
            </div>
            <button class="btn-remove" @click="removeJsonFile">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 图片上传 -->
        <div class="card upload-card">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <path d="M21 15l-5-5L5 21"/>
            </svg>
            上传相关图片（可选）
          </h3>

          <div class="image-upload-grid">
            <ImageUploader
              v-for="item in imageTypes"
              :key="item.type"
              :label="item.label"
              :image-type="item.type"
              :uploaded-image="uploadedImages[item.type]"
              @upload="handleImageUpload"
              @remove="removeImage"
            />
          </div>
        </div>

        <!-- 攻击树上传 -->
        <div class="card upload-card">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 3v18"/>
              <path d="M18 9l-6-6-6 6"/>
              <path d="M6 15h12"/>
              <circle cx="6" cy="18" r="2"/>
              <circle cx="18" cy="18" r="2"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>
            上传攻击树图片（可选）
          </h3>
          <p class="section-hint">可以上传多张攻击树图片，并为每张图片添加描述。上传的图片将自动替换JSON中的attack_trees字段。</p>

          <div class="attack-trees-upload">
            <div 
              v-for="(tree, index) in attackTrees" 
              :key="index"
              class="attack-tree-item"
            >
              <div class="attack-tree-header">
                <span class="attack-tree-index">攻击树 #{{ index + 1 }}</span>
                <button class="btn-remove-tree" @click="removeAttackTree(index)" title="删除此攻击树">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
              
              <div class="attack-tree-content">
                <div class="attack-tree-image-upload">
                  <div 
                    v-if="!tree.file"
                    class="upload-area small"
                    @click="triggerAttackTreeUpload(index)"
                    @drop.prevent="handleAttackTreeDrop($event, index)"
                    @dragover.prevent
                  >
                    <input 
                      :ref="el => attackTreeInputs[index] = el"
                      type="file" 
                      accept="image/*"
                      style="display: none"
                      @change="handleAttackTreeSelect($event, index)"
                    >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <rect x="3" y="3" width="18" height="18" rx="2"/>
                      <circle cx="8.5" cy="8.5" r="1.5"/>
                      <path d="M21 15l-5-5L5 21"/>
                    </svg>
                    <span>点击上传图片</span>
                  </div>
                  <div v-else class="preview-area small">
                    <img :src="getPreviewUrl(tree.file)" :alt="`攻击树 ${index + 1}`">
                    <div class="overlay">
                      <button class="btn-change" @click="triggerAttackTreeUpload(index)">更换</button>
                    </div>
                  </div>
                </div>
                
                <div class="attack-tree-info">
                  <div class="form-group">
                    <label>资产ID</label>
                    <input 
                      v-model="tree.asset_id" 
                      type="text" 
                      placeholder="如: A001"
                      class="form-input"
                    >
                  </div>
                  <div class="form-group">
                    <label>资产名称</label>
                    <input 
                      v-model="tree.asset_name" 
                      type="text" 
                      placeholder="如: 车载控制系统"
                      class="form-input"
                    >
                  </div>
                  <div class="form-group">
                    <label>攻击树标题</label>
                    <input 
                      v-model="tree.title" 
                      type="text" 
                      placeholder="如: 针对XX的攻击树分析"
                      class="form-input"
                    >
                  </div>
                  <div class="form-group full-width">
                    <label>描述</label>
                    <textarea 
                      v-model="tree.description" 
                      placeholder="请输入攻击树描述..."
                      class="form-textarea"
                      rows="2"
                    ></textarea>
                  </div>
                </div>
              </div>
            </div>

            <button class="btn btn-add-tree" @click="addAttackTree">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="16"/>
                <line x1="8" y1="12" x2="16" y2="12"/>
              </svg>
              添加攻击树
            </button>
          </div>
        </div>

        <!-- 生成按钮 -->
        <div class="generate-section">
          <button 
            class="btn btn-primary generate-btn"
            :disabled="!jsonFile || isGenerating"
            @click="generateReport"
          >
            <svg v-if="!isGenerating" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/>
            </svg>
            <svg v-else class="animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
              <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
            </svg>
            {{ isGenerating ? '正在生成...' : '一键生成TARA报告' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 生成成功弹窗 -->
    <div v-if="showSuccessModal" class="modal-overlay" @click="closeSuccessModal">
      <div class="modal-content success-modal" @click.stop>
        <div class="success-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="m9 12 2 2 4-4"/>
          </svg>
        </div>
        <h3>报告生成成功！</h3>
        <p class="success-message">您的TARA报告已成功生成，可以前往报告中心查看和下载。</p>
        <div class="success-stats" v-if="generatedReport?.statistics">
          <div class="stat-item">
            <span class="stat-value">{{ generatedReport.statistics.assets_count || 0 }}</span>
            <span class="stat-label">资产数量</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ generatedReport.statistics.threats_count || 0 }}</span>
            <span class="stat-label">威胁场景</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ generatedReport.statistics.high_risk_count || 0 }}</span>
            <span class="stat-label">高风险项</span>
          </div>
        </div>
        <div class="success-actions">
          <router-link to="/reports" class="btn btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            前往报告中心
          </router-link>
          <a :href="downloadUrl" class="btn btn-secondary" download>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            立即下载
          </a>
          <button class="btn btn-ghost" @click="resetAndContinue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/>
            </svg>
            继续生成
          </button>
        </div>
      </div>
    </div>

    <!-- 图片预览模态框 -->
    <div v-if="imageModal.show" class="modal-overlay" @click="closeImageModal">
      <div class="modal-content image-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ imageModal.title }}</h3>
          <button class="btn-close" @click="closeImageModal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <img :src="imageModal.url" :alt="imageModal.title">
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { uploadImage } from '@/api'
import ImageUploader from '@/components/ImageUploader.vue'

// 状态
const isDragging = ref(false)
const isGenerating = ref(false)
const jsonFile = ref(null)
const uploadedImages = ref({})
const generatedReport = ref(null)
const showSuccessModal = ref(false)

// 攻击树相关状态
const attackTrees = ref([])
const attackTreeInputs = ref([])

const imageModal = ref({
  show: false,
  url: '',
  title: ''
})

// 图片类型配置
const imageTypes = [
  { type: 'item_boundary', label: '项目边界图' },
  { type: 'system_architecture', label: '系统架构图' },
  { type: 'software_architecture', label: '软件架构图' },
  { type: 'dataflow', label: '数据流图' }
]

// 计算属性
const downloadUrl = computed(() => {
  return generatedReport.value ? `/api/reports/${generatedReport.value.report_id}/download` : ''
})

const previewImages = computed(() => {
  if (!generatedReport.value?.preview_data?.images) return {}
  const images = generatedReport.value.preview_data.images
  return Object.fromEntries(
    Object.entries(images).filter(([_, url]) => url)
  )
})

const hasImages = computed(() => {
  return Object.keys(previewImages.value).length > 0
})

// 方法
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handleJsonDrop(e) {
  isDragging.value = false
  const files = e.dataTransfer.files
  if (files.length > 0 && files[0].name.endsWith('.json')) {
    jsonFile.value = files[0]
  }
}

function handleJsonSelect(e) {
  const files = e.target.files
  if (files.length > 0) {
    jsonFile.value = files[0]
  }
}

function removeJsonFile() {
  jsonFile.value = null
}

async function handleImageUpload({ file, imageType }) {
  try {
    const result = await uploadImage(file, imageType)
    if (result.success) {
      uploadedImages.value[imageType] = {
        id: result.image_id,
        url: result.image_url,
        file: file
      }
    }
  } catch (error) {
    alert('图片上传失败: ' + error.message)
  }
}

function removeImage(imageType) {
  delete uploadedImages.value[imageType]
}

function getImageLabel(type) {
  const item = imageTypes.find(i => i.type === type)
  return item ? item.label : type
}

// 攻击树相关方法
function addAttackTree() {
  attackTrees.value.push({
    asset_id: '',
    asset_name: '',
    title: '',
    description: '',
    file: null
  })
}

function removeAttackTree(index) {
  attackTrees.value.splice(index, 1)
}

function triggerAttackTreeUpload(index) {
  const input = attackTreeInputs.value[index]
  if (input) {
    input.click()
  }
}

function handleAttackTreeSelect(e, index) {
  const files = e.target.files
  if (files.length > 0 && files[0].type.startsWith('image/')) {
    attackTrees.value[index].file = files[0]
  }
}

function handleAttackTreeDrop(e, index) {
  const files = e.dataTransfer.files
  if (files.length > 0 && files[0].type.startsWith('image/')) {
    attackTrees.value[index].file = files[0]
  }
}

function getPreviewUrl(file) {
  if (file) {
    return URL.createObjectURL(file)
  }
  return ''
}

async function generateReport() {
  if (!jsonFile.value) return
  
  isGenerating.value = true
  
  try {
    // 读取并解析JSON文件
    const jsonContent = await readJsonFile(jsonFile.value)
    
    // 如果有攻击树数据，更新JSON中的attack_trees字段
    if (attackTrees.value.length > 0) {
      const attackTreesData = attackTrees.value.filter(tree => tree.file || tree.asset_id || tree.asset_name).map((tree, index) => ({
        asset_id: tree.asset_id || `AT${String(index + 1).padStart(3, '0')}`,
        asset_name: tree.asset_name || `攻击树 ${index + 1}`,
        title: tree.title || '',
        description: tree.description || '',
        // 图片将在后端处理
        attack_tree_image: ''
      }))
      
      if (!jsonContent.attack_trees) {
        jsonContent.attack_trees = {}
      }
      jsonContent.attack_trees.attack_trees = attackTreesData
    }
    
    // 创建新的JSON Blob
    const updatedJsonBlob = new Blob([JSON.stringify(jsonContent, null, 2)], { type: 'application/json' })
    const updatedJsonFile = new File([updatedJsonBlob], jsonFile.value.name, { type: 'application/json' })
    
    // 准备图片数据
    const images = {
      item_boundary: uploadedImages.value.item_boundary?.file,
      system_architecture: uploadedImages.value.system_architecture?.file,
      software_architecture: uploadedImages.value.software_architecture?.file,
      dataflow: uploadedImages.value.dataflow?.file,
      attack_trees: attackTrees.value.filter(tree => tree.file).map(tree => tree.file)
    }
    
    // 调用批量上传API
    const { uploadAndGenerate } = await import('@/api')
    const result = await uploadAndGenerate(updatedJsonFile, images)
    
    if (result.success) {
      generatedReport.value = {
        report_id: result.report_info.id,
        statistics: result.report_info.statistics,
        preview_data: {
          images: {}
        }
      }
      // 显示成功弹窗
      showSuccessModal.value = true
    } else {
      alert('生成失败: ' + result.message)
    }
  } catch (error) {
    alert('生成失败: ' + error.message)
  } finally {
    isGenerating.value = false
  }
}

// 读取JSON文件内容
function readJsonFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = JSON.parse(e.target.result)
        resolve(content)
      } catch (error) {
        reject(new Error('JSON解析失败: ' + error.message))
      }
    }
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsText(file)
  })
}

function showImageModal(url, title) {
  imageModal.value = { show: true, url, title }
}

function closeImageModal() {
  imageModal.value = { show: false, url: '', title: '' }
}

function closeSuccessModal() {
  showSuccessModal.value = false
}

function resetAndContinue() {
  showSuccessModal.value = false
  jsonFile.value = null
  uploadedImages.value = {}
  attackTrees.value = []
  generatedReport.value = null
}
</script>

<style scoped>
.generator-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.page-desc {
  color: var(--text-muted);
  font-size: 15px;
}

.generator-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.upload-card h3,
.preview-card h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.upload-card h3 svg,
.preview-card h3 svg {
  width: 20px;
  height: 20px;
  color: var(--brand-blue);
}

.upload-zone {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 24px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 16px;
}

.upload-zone:hover,
.upload-zone.dragover {
  border-color: var(--brand-blue);
  background: rgba(59,130,246,0.05);
}

.upload-icon {
  width: 36px;
  height: 36px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.upload-zone p {
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.upload-zone .file-selected {
  color: var(--brand-blue);
  font-weight: 500;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 12px;
}

.file-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-icon.json {
  background: rgba(245,158,11,0.15);
  color: #F59E0B;
}

.file-icon svg {
  width: 22px;
  height: 22px;
}

.file-info {
  flex: 1;
}

.file-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.file-size {
  font-size: 12px;
  color: var(--text-muted);
}

.btn-remove {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-remove:hover {
  background: rgba(239,68,68,0.1);
  color: var(--danger);
}

.btn-remove svg {
  width: 18px;
  height: 18px;
}

.image-upload-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.generate-section {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
}

.generate-btn {
  padding: 18px 48px;
  font-size: 16px;
}

.generate-btn svg {
  width: 22px;
  height: 22px;
}

/* Preview Section */
.preview-section {
  position: sticky;
  top: 32px;
  height: fit-content;
}

.preview-card {
  padding: 24px;
}

.preview-empty {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-muted);
}

.preview-empty svg {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.preview-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 12px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.stat-icon svg {
  width: 22px;
  height: 22px;
}

.stat-icon.blue { background: rgba(99,102,241,0.1); color: #6366f1; }
.stat-icon.yellow { background: rgba(245,158,11,0.1); color: #f59e0b; }
.stat-icon.red { background: rgba(239,68,68,0.1); color: #ef4444; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.images-preview h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.image-preview-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  aspect-ratio: 16/10;
  background: var(--bg-tertiary);
}

.image-preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.image-preview-item:hover img {
  transform: scale(1.05);
}

.image-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  font-size: 11px;
  color: white;
}

.preview-actions {
  display: flex;
  gap: 12px;
}

.preview-actions .btn {
  flex: 1;
  justify-content: center;
}

.preview-actions .btn svg {
  width: 18px;
  height: 18px;
}

/* Image Modal */
.image-modal {
  width: auto;
  max-width: 90vw;
  max-height: 90vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.btn-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 20px;
}

.modal-body img {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 8px;
}

@media (max-width: 1200px) {
  .generator-content {
    grid-template-columns: 1fr;
  }
  
  .preview-section {
    position: static;
  }
  
  .image-upload-grid {
    grid-template-columns: 1fr;
  }
}

/* 攻击树上传样式 */
.section-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
  line-height: 1.5;
}

.attack-trees-upload {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.attack-tree-item {
  background: var(--bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.attack-tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--border-color);
}

.attack-tree-index {
  font-weight: 600;
  font-size: 14px;
  color: var(--brand-blue);
}

.btn-remove-tree {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-remove-tree:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.btn-remove-tree svg {
  width: 16px;
  height: 16px;
}

.attack-tree-content {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 16px;
  padding: 16px;
}

.attack-tree-image-upload {
  width: 200px;
}

.upload-area.small {
  width: 100%;
  height: 150px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--bg-secondary);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area.small:hover {
  border-color: var(--brand-blue);
  background: rgba(59, 130, 246, 0.05);
}

.upload-area.small svg {
  width: 32px;
  height: 32px;
  color: var(--text-muted);
}

.upload-area.small span {
  font-size: 12px;
  color: var(--text-muted);
}

.preview-area.small {
  width: 100%;
  height: 150px;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

.preview-area.small img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-area.small .overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.preview-area.small:hover .overlay {
  opacity: 1;
}

.btn-change {
  padding: 6px 12px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-change:hover {
  background: rgba(255, 255, 255, 0.3);
}

.attack-tree-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.attack-tree-info .full-width {
  grid-column: span 3;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--brand-blue);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  resize: vertical;
  font-family: inherit;
  transition: all 0.2s;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--brand-blue);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.btn-add-tree {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  background: transparent;
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-add-tree:hover {
  border-color: var(--brand-blue);
  color: var(--brand-blue);
  background: rgba(59, 130, 246, 0.05);
}

.btn-add-tree svg {
  width: 20px;
  height: 20px;
}

@media (max-width: 768px) {
  .attack-tree-content {
    grid-template-columns: 1fr;
  }
  
  .attack-tree-image-upload {
    width: 100%;
  }
  
  .attack-tree-info {
    grid-template-columns: 1fr;
  }
  
  .attack-tree-info .full-width {
    grid-column: span 1;
  }
}

/* 成功弹窗样式 */
.success-modal {
  width: 480px;
  max-width: 90vw;
  text-align: center;
  padding: 40px 32px;
  background: var(--bg-card);
  border-radius: 20px;
  border: 1px solid var(--border-color);
}

.success-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.1));
  border-radius: 50%;
}

.success-icon svg {
  width: 40px;
  height: 40px;
  color: #22c55e;
}

.success-modal h3 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.success-message {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 24px;
  line-height: 1.6;
}

.success-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  padding: 20px;
  margin-bottom: 24px;
  background: var(--bg-tertiary);
  border-radius: 12px;
}

.success-stats .stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.success-stats .stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--brand-blue);
}

.success-stats .stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.success-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.success-actions .btn {
  width: 100%;
  justify-content: center;
  padding: 14px 24px;
}

.success-actions .btn svg {
  width: 18px;
  height: 18px;
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-ghost:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
}
</style>
