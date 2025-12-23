<template>
  <div class="generate-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <h1>
          <el-icon><Document /></el-icon>
          一键生成报告
        </h1>
        <p class="subtitle">上传JSON数据文件和图片，一键生成TARA分析报告</p>
      </div>
    </div>

    <!-- 主要内容 -->
    <div class="content-wrapper">
      <!-- 左侧上传区域 -->
      <div class="upload-section">
        <div class="section-card">
          <h3>
            <el-icon><Document /></el-icon>
            数据文件上传
          </h3>
          <FileUpload 
            ref="fileUploadRef"
            accept-types=".json,application/json"
            @change="handleFileChange"
          />
        </div>

        <ImageUpload 
          ref="imageUploadRef"
          @change="handleImageChange"
        />

        <!-- 生成按钮 -->
        <div class="action-section">
          <el-button 
            type="primary" 
            size="large"
            :loading="generating"
            :disabled="!hasJsonFile"
            @click="handleGenerate"
          >
            <el-icon v-if="!generating"><MagicStick /></el-icon>
            {{ generating ? '正在生成...' : '一键生成TARA报告' }}
          </el-button>
          
          <p class="tip" v-if="!hasJsonFile">
            <el-icon><InfoFilled /></el-icon>
            请先上传JSON格式的报告数据文件
          </p>
        </div>
      </div>

      <!-- 右侧预览区域 -->
      <div class="preview-section">
        <div class="section-card preview-card">
          <h3>
            <el-icon><View /></el-icon>
            数据预览
          </h3>
          
          <div class="preview-empty" v-if="!parsedData">
            <el-icon :size="48"><DocumentCopy /></el-icon>
            <p>上传JSON文件后可预览数据内容</p>
          </div>

          <div class="preview-content" v-else>
            <!-- 统计信息 -->
            <div class="preview-stats">
              <div class="stat-item">
                <span class="stat-value">{{ parsedData.assets?.assets?.length || 0 }}</span>
                <span class="stat-label">资产数量</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ parsedData.tara_results?.results?.length || 0 }}</span>
                <span class="stat-label">威胁场景</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ parsedData.definitions?.assumptions?.length || 0 }}</span>
                <span class="stat-label">假设条目</span>
              </div>
            </div>

            <!-- 数据详情 -->
            <el-collapse v-model="activeCollapse">
              <el-collapse-item title="封面信息" name="cover">
                <div class="data-grid">
                  <div class="data-item">
                    <span class="label">项目名称</span>
                    <span class="value">{{ parsedData.cover?.project_name }}</span>
                  </div>
                  <div class="data-item">
                    <span class="label">文档编号</span>
                    <span class="value">{{ parsedData.cover?.document_number }}</span>
                  </div>
                  <div class="data-item">
                    <span class="label">版本</span>
                    <span class="value">{{ parsedData.cover?.version }}</span>
                  </div>
                </div>
              </el-collapse-item>
              
              <el-collapse-item title="资产列表" name="assets">
                <el-table :data="parsedData.assets?.assets?.slice(0, 5)" size="small">
                  <el-table-column prop="id" label="ID" width="80" />
                  <el-table-column prop="name" label="名称" />
                  <el-table-column prop="category" label="分类" width="100" />
                </el-table>
                <p class="more-hint" v-if="(parsedData.assets?.assets?.length || 0) > 5">
                  还有 {{ (parsedData.assets?.assets?.length || 0) - 5 }} 条数据...
                </p>
              </el-collapse-item>

              <el-collapse-item title="威胁分析结果" name="tara">
                <el-table :data="parsedData.tara_results?.results?.slice(0, 5)" size="small">
                  <el-table-column prop="asset_id" label="资产ID" width="80" />
                  <el-table-column prop="stride_model" label="STRIDE" width="80" />
                  <el-table-column prop="threat_scenario" label="威胁场景" show-overflow-tooltip />
                </el-table>
                <p class="more-hint" v-if="(parsedData.tara_results?.results?.length || 0) > 5">
                  还有 {{ (parsedData.tara_results?.results?.length || 0) - 5 }} 条数据...
                </p>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>
    </div>

    <!-- 生成成功弹窗 -->
    <el-dialog
      v-model="showSuccessDialog"
      title="报告生成成功"
      width="500"
      :close-on-click-modal="false"
    >
      <div class="success-content">
        <el-icon class="success-icon" :size="64"><CircleCheck /></el-icon>
        <h3>{{ generatedReport?.name }}</h3>
        <p>报告已成功生成，可以预览或下载</p>
      </div>
      <template #footer>
        <el-button @click="showSuccessDialog = false">关闭</el-button>
        <el-button type="primary" @click="handlePreview">
          <el-icon><View /></el-icon>
          预览报告
        </el-button>
        <el-button type="success" @click="handleDownload">
          <el-icon><Download /></el-icon>
          下载报告
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览抽屉 -->
    <el-drawer
      v-model="showPreviewDrawer"
      title="报告预览"
      size="80%"
      :destroy-on-close="true"
    >
      <ReportPreview 
        :preview-data="previewData"
        @close="showPreviewDrawer = false"
      />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Document, MagicStick, InfoFilled, View, DocumentCopy,
  CircleCheck, Download
} from '@element-plus/icons-vue'
import FileUpload from '@/components/FileUpload.vue'
import ImageUpload from '@/components/ImageUpload.vue'
import ReportPreview from '@/components/ReportPreview.vue'
import { useReportStore } from '@/stores/report'
import type { TARAReportData, ReportInfo, PreviewData } from '@/types'

const reportStore = useReportStore()

const fileUploadRef = ref()
const imageUploadRef = ref()

const jsonFile = ref<File | null>(null)
const images = ref<Record<string, File | null>>({})
const parsedData = ref<TARAReportData | null>(null)
const activeCollapse = ref(['cover'])

const showSuccessDialog = ref(false)
const showPreviewDrawer = ref(false)
const generatedReport = ref<ReportInfo | null>(null)
const previewData = ref<PreviewData | null>(null)

const generating = computed(() => reportStore.generating)
const hasJsonFile = computed(() => !!jsonFile.value)

async function handleFileChange(files: File[]) {
  if (files.length > 0) {
    jsonFile.value = files[0]
    // 解析JSON预览
    try {
      const content = await files[0].text()
      parsedData.value = JSON.parse(content)
    } catch (e) {
      ElMessage.error('JSON文件解析失败，请检查文件格式')
      parsedData.value = null
    }
  } else {
    jsonFile.value = null
    parsedData.value = null
  }
}

function handleImageChange(imgs: Record<string, File | null>) {
  images.value = imgs
}

async function handleGenerate() {
  if (!jsonFile.value) {
    ElMessage.warning('请先上传JSON数据文件')
    return
  }

  try {
    // 提取攻击树图片
    const attackTreeImages: File[] = []
    const attackTreeCount = (images.value as any)['_attack_tree_count'] || 0
    for (let i = 0; i < attackTreeCount; i++) {
      const file = images.value[`attack_tree_${i}`]
      if (file) {
        attackTreeImages.push(file)
      }
    }

    const response = await reportStore.generateReport(jsonFile.value, {
      item_boundary_image: images.value.item_boundary_image || undefined,
      system_architecture_image: images.value.system_architecture_image || undefined,
      software_architecture_image: images.value.software_architecture_image || undefined,
      dataflow_image: images.value.dataflow_image || undefined,
      attack_tree_images: attackTreeImages.length > 0 ? attackTreeImages : undefined
    })

    if (response.success && response.report_info) {
      generatedReport.value = response.report_info
      showSuccessDialog.value = true
      
      // 清空上传
      fileUploadRef.value?.clearFiles()
      imageUploadRef.value?.clearImages()
      jsonFile.value = null
      parsedData.value = null
      images.value = {}
      
      ElMessage.success('报告生成成功！')
    } else {
      ElMessage.error(response.message || '报告生成失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '报告生成失败')
  }
}

async function handlePreview() {
  if (generatedReport.value) {
    await reportStore.fetchPreview(generatedReport.value.id)
    previewData.value = reportStore.previewData
    showSuccessDialog.value = false
    showPreviewDrawer.value = true
  }
}

async function handleDownload() {
  if (generatedReport.value) {
    await reportStore.downloadReport(generatedReport.value.id, generatedReport.value.name)
    showSuccessDialog.value = false
  }
}
</script>

<style scoped lang="scss">
.generate-view {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 24px;

  h1 {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .subtitle {
    color: rgba(255, 255, 255, 0.5);
    font-size: 15px;
  }
}

.content-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.section-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 24px;
  margin-bottom: 20px;

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 20px;
  }
}

.action-section {
  text-align: center;
  padding: 24px 0;

  .el-button {
    font-size: 16px;
    padding: 16px 40px;
    height: auto;
  }

  .tip {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-top: 16px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.4);
  }
}

.preview-card {
  height: fit-content;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.preview-empty {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.3);

  p {
    margin-top: 16px;
    font-size: 14px;
  }
}

.preview-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 12px;

  .stat-value {
    font-size: 28px;
    font-weight: 700;
    color: #3b82f6;
  }

  .stat-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
    margin-top: 4px;
  }
}

.data-grid {
  display: grid;
  gap: 12px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);

  .label {
    color: rgba(255, 255, 255, 0.5);
    font-size: 13px;
  }

  .value {
    color: rgba(255, 255, 255, 0.9);
    font-size: 13px;
  }
}

.more-hint {
  margin-top: 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
}

.success-content {
  text-align: center;
  padding: 20px;

  .success-icon {
    color: #10b981;
    margin-bottom: 16px;
  }

  h3 {
    font-size: 18px;
    margin-bottom: 8px;
  }

  p {
    color: rgba(255, 255, 255, 0.5);
  }
}

:deep(.el-collapse-item__header) {
  background: transparent;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

:deep(.el-collapse-item__content) {
  background: transparent;
  padding-top: 12px;
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.03);
}
</style>
