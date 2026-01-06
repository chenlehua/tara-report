<template>
  <div class="report-preview" v-if="previewData">
    <!-- 预览头部 -->
    <div class="preview-header">
      <div class="header-info">
        <h2>{{ previewData.report_info?.name || previewData.cover?.project_name || 'TARA报告' }}</h2>
        <div class="meta-info">
          <span class="version">版本: {{ previewData.report_info?.version || previewData.cover?.version || '1.0' }}</span>
          <span class="date">{{ formatDate(previewData.report_info?.created_at) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleDownload">
          <el-icon><Download /></el-icon>
          下载报告
        </el-button>
        <el-button @click="$emit('close')">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon assets">
          <el-icon :size="24"><Box /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ previewData.statistics?.total_assets || previewData.assets?.length || 0 }}</span>
          <span class="stat-label">资产总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon threats">
          <el-icon :size="24"><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ previewData.statistics?.total_threats || previewData.tara_results?.length || 0 }}</span>
          <span class="stat-label">威胁场景</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon risks">
          <el-icon :size="24"><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ previewData.statistics?.high_risk_count || 0 }}</span>
          <span class="stat-label">高风险项</span>
        </div>
      </div>
    </div>

    <!-- 项目信息 -->
    <div class="section-card">
      <h3><el-icon><Document /></el-icon> 项目信息</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">项目名称</span>
          <span class="info-value">{{ previewData.cover?.project_name || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">文档编号</span>
          <span class="info-value">{{ previewData.cover?.document_number || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">版本</span>
          <span class="info-value">{{ previewData.cover?.version || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">数据等级</span>
          <span class="info-value">{{ previewData.cover?.data_level || '-' }}</span>
        </div>
        <div class="info-item" v-if="previewData.cover?.author">
          <span class="info-label">编写人</span>
          <span class="info-value">{{ previewData.cover.author }}</span>
        </div>
        <div class="info-item" v-if="previewData.cover?.reviewer">
          <span class="info-label">审核人</span>
          <span class="info-value">{{ previewData.cover.reviewer }}</span>
        </div>
      </div>
    </div>

    <!-- 相关定义 - 图片预览 -->
    <div class="section-card" v-if="hasDefinitionImages">
      <h3><el-icon><Picture /></el-icon> 架构图预览</h3>
      <div class="image-preview-grid">
        <div class="image-preview-item" v-if="previewData.definitions?.item_boundary_image">
          <span class="image-label">项目边界图</span>
          <el-image 
            :src="getImageUrl(previewData.definitions.item_boundary_image)" 
            fit="contain"
            :preview-src-list="[getImageUrl(previewData.definitions.item_boundary_image)]"
          />
        </div>
        <div class="image-preview-item" v-if="previewData.definitions?.system_architecture_image">
          <span class="image-label">系统架构图</span>
          <el-image 
            :src="getImageUrl(previewData.definitions.system_architecture_image)" 
            fit="contain"
            :preview-src-list="[getImageUrl(previewData.definitions.system_architecture_image)]"
          />
        </div>
        <div class="image-preview-item" v-if="previewData.definitions?.software_architecture_image">
          <span class="image-label">软件架构图</span>
          <el-image 
            :src="getImageUrl(previewData.definitions.software_architecture_image)" 
            fit="contain"
            :preview-src-list="[getImageUrl(previewData.definitions.software_architecture_image)]"
          />
        </div>
        <div class="image-preview-item" v-if="previewData.dataflow_image">
          <span class="image-label">数据流图</span>
          <el-image 
            :src="getImageUrl(previewData.dataflow_image)" 
            fit="contain"
            :preview-src-list="[getImageUrl(previewData.dataflow_image)]"
          />
        </div>
      </div>
    </div>

    <!-- 功能描述 -->
    <div class="section-card" v-if="previewData.definitions?.functional_description">
      <h3><el-icon><Document /></el-icon> 功能描述</h3>
      <div class="description-content">
        {{ previewData.definitions.functional_description }}
      </div>
    </div>

    <!-- 假设条目 -->
    <div class="section-card" v-if="hasAssumptions">
      <h3><el-icon><List /></el-icon> 相关项假设 ({{ assumptionsList.length }})</h3>
      <el-table :data="assumptionsList" stripe max-height="300">
        <el-table-column prop="id" label="假设编号" width="120" />
        <el-table-column prop="description" label="假设描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="source" label="来源" width="150" show-overflow-tooltip v-if="hasAssumptionSource" />
        <el-table-column prop="rationale" label="依据" min-width="200" show-overflow-tooltip v-if="hasAssumptionRationale" />
      </el-table>
    </div>

    <!-- 术语表 -->
    <div class="section-card" v-if="previewData.definitions?.terminology?.length">
      <h3><el-icon><Collection /></el-icon> 术语表 ({{ previewData.definitions.terminology.length }})</h3>
      <el-table :data="previewData.definitions.terminology" stripe max-height="300">
        <el-table-column prop="abbreviation" label="缩写" width="100" />
        <el-table-column prop="english" label="英文全称" min-width="200" />
        <el-table-column prop="chinese" label="中文名称" min-width="150" />
      </el-table>
    </div>

    <!-- 资产列表 -->
    <div class="section-card">
      <h3><el-icon><Box /></el-icon> 资产清单 ({{ previewData.assets?.length || 0 }})</h3>
      <el-table :data="previewData.assets" stripe max-height="400">
        <el-table-column prop="id" label="资产ID" width="100" fixed />
        <el-table-column prop="name" label="资产名称" width="150" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="remarks" label="备注" min-width="200" show-overflow-tooltip />
        <el-table-column label="安全属性" width="280">
          <template #default="{ row }">
            <div class="security-attrs">
              <el-tag size="small" type="danger" v-if="row.authenticity">真实性</el-tag>
              <el-tag size="small" type="warning" v-if="row.integrity">完整性</el-tag>
              <el-tag size="small" type="success" v-if="row.availability">可用性</el-tag>
              <el-tag size="small" type="info" v-if="row.confidentiality">机密性</el-tag>
              <el-tag size="small" v-if="row.non_repudiation">不可抵赖</el-tag>
              <el-tag size="small" type="primary" v-if="row.authorization">授权</el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 攻击树 -->
    <div class="section-card" v-if="previewData.attack_trees?.length">
      <h3><el-icon><Share /></el-icon> 攻击树 ({{ previewData.attack_trees.length }})</h3>
      <div class="attack-trees-grid">
        <div class="attack-tree-item" v-for="(tree, index) in previewData.attack_trees" :key="index">
          <div class="tree-header">
            <span class="tree-asset">{{ tree.asset_id }} - {{ tree.asset_name }}</span>
            <span class="tree-title" v-if="tree.title">{{ tree.title }}</span>
          </div>
          <div class="tree-image" v-if="tree.image_url || tree.image">
            <el-image 
              :src="getImageUrl(tree.image_url || tree.image)" 
              fit="contain"
              :preview-src-list="[getImageUrl(tree.image_url || tree.image)]"
            />
          </div>
          <div class="tree-placeholder" v-else>
            <el-icon :size="32"><Picture /></el-icon>
            <span>暂无攻击树图片</span>
          </div>
        </div>
      </div>
    </div>

    <!-- TARA分析结果 -->
    <div class="section-card">
      <h3><el-icon><Warning /></el-icon> TARA分析结果 ({{ previewData.tara_results?.length || 0 }})</h3>
      <p class="table-hint">💡 点击任意行可查看详细信息</p>
      <el-table 
        :data="previewData.tara_results" 
        stripe 
        max-height="500" 
        :default-sort="{ prop: 'asset_id', order: 'ascending' }"
        class="clickable-table"
        @row-click="handleThreatRowClick"
      >
        <el-table-column prop="asset_id" label="资产ID" width="80" fixed sortable />
        <el-table-column prop="asset_name" label="资产名称" width="120" show-overflow-tooltip />
        <el-table-column prop="stride_model" label="STRIDE" width="100">
          <template #default="{ row }">
            <el-tag :type="getStrideType(row.stride_model)" size="small">
              {{ row.stride_model }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="threat_id" label="威胁ID" width="100" />
        <el-table-column prop="threat_scenario" label="威胁场景" min-width="200" show-overflow-tooltip />
        <el-table-column prop="damage_scenario" label="损害场景" min-width="200" show-overflow-tooltip />
        <el-table-column label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getRiskType(row.residual_risk || row.risk_level)" size="small">
              {{ row.residual_risk || row.risk_level || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="showThreatDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 威胁详情弹窗 -->
    <el-dialog
      v-model="threatDetailVisible"
      :title="`威胁详情 - ${selectedThreat?.threat_id || ''}`"
      width="800px"
      destroy-on-close
    >
      <div class="threat-detail" v-if="selectedThreat">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4>📋 基本信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">资产ID</span>
              <span class="value">{{ selectedThreat.asset_id || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">资产名称</span>
              <span class="value">{{ selectedThreat.asset_name || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">威胁ID</span>
              <span class="value">{{ selectedThreat.threat_id || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">STRIDE模型</span>
              <span class="value">
                <el-tag :type="getStrideType(selectedThreat.stride_model)" size="small">
                  {{ selectedThreat.stride_model || '-' }}
                </el-tag>
              </span>
            </div>
          </div>
        </div>

        <!-- 威胁分析 -->
        <div class="detail-section">
          <h4>⚠️ 威胁分析</h4>
          <div class="detail-full">
            <div class="detail-item full">
              <span class="label">威胁场景</span>
              <span class="value">{{ selectedThreat.threat_scenario || '-' }}</span>
            </div>
            <div class="detail-item full">
              <span class="label">损害场景</span>
              <span class="value">{{ selectedThreat.damage_scenario || '-' }}</span>
            </div>
            <div class="detail-item full">
              <span class="label">攻击路径</span>
              <span class="value">{{ selectedThreat.attack_path || '-' }}</span>
            </div>
          </div>
        </div>

        <!-- 攻击可行性分析 -->
        <div class="detail-section">
          <h4>🎯 攻击可行性分析</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">攻击向量 (AV)</span>
              <span class="value">{{ selectedThreat.attack_vector || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">攻击复杂度 (AC)</span>
              <span class="value">{{ selectedThreat.attack_complexity || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">所需权限 (PR)</span>
              <span class="value">{{ selectedThreat.privilege_required || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">用户交互 (UI)</span>
              <span class="value">{{ selectedThreat.user_interaction || '-' }}</span>
            </div>
            <div class="detail-item" v-if="selectedThreat.elapsed_time !== undefined">
              <span class="label">攻击时间 (ET)</span>
              <span class="value">{{ selectedThreat.elapsed_time || '-' }}</span>
            </div>
            <div class="detail-item" v-if="selectedThreat.specialist_expertise !== undefined">
              <span class="label">专业知识 (SE)</span>
              <span class="value">{{ selectedThreat.specialist_expertise || '-' }}</span>
            </div>
            <div class="detail-item" v-if="selectedThreat.knowledge_of_target !== undefined">
              <span class="label">目标知识 (KT)</span>
              <span class="value">{{ selectedThreat.knowledge_of_target || '-' }}</span>
            </div>
            <div class="detail-item" v-if="selectedThreat.window_of_opportunity !== undefined">
              <span class="label">机会窗口 (WO)</span>
              <span class="value">{{ selectedThreat.window_of_opportunity || '-' }}</span>
            </div>
            <div class="detail-item" v-if="selectedThreat.equipment !== undefined">
              <span class="label">所需设备 (EQ)</span>
              <span class="value">{{ selectedThreat.equipment || '-' }}</span>
            </div>
            <div class="detail-item" v-if="selectedThreat.attack_feasibility !== undefined">
              <span class="label">攻击可行性</span>
              <span class="value">{{ selectedThreat.attack_feasibility || '-' }}</span>
            </div>
          </div>
        </div>

        <!-- 影响分析 -->
        <div class="detail-section">
          <h4>💥 影响分析</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">安全影响 (S)</span>
              <span class="value impact-value" :class="getImpactClass(selectedThreat.safety_impact)">
                {{ selectedThreat.safety_impact ?? '-' }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">财务影响 (F)</span>
              <span class="value impact-value" :class="getImpactClass(selectedThreat.financial_impact)">
                {{ selectedThreat.financial_impact ?? '-' }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">运营影响 (O)</span>
              <span class="value impact-value" :class="getImpactClass(selectedThreat.operational_impact)">
                {{ selectedThreat.operational_impact ?? '-' }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">隐私影响 (P)</span>
              <span class="value impact-value" :class="getImpactClass(selectedThreat.privacy_impact)">
                {{ selectedThreat.privacy_impact ?? '-' }}
              </span>
            </div>
            <div class="detail-item" v-if="selectedThreat.impact_level !== undefined">
              <span class="label">综合影响等级</span>
              <span class="value">{{ selectedThreat.impact_level || '-' }}</span>
            </div>
          </div>
        </div>

        <!-- 风险评估 -->
        <div class="detail-section">
          <h4>📊 风险评估</h4>
          <div class="detail-grid">
            <div class="detail-item" v-if="selectedThreat.risk_value !== undefined">
              <span class="label">风险值</span>
              <span class="value">{{ selectedThreat.risk_value || '-' }}</span>
            </div>
            <div class="detail-item" v-if="selectedThreat.risk_level !== undefined">
              <span class="label">风险等级</span>
              <span class="value">
                <el-tag :type="getRiskType(selectedThreat.risk_level)" size="small">
                  {{ selectedThreat.risk_level || '-' }}
                </el-tag>
              </span>
            </div>
            <div class="detail-item">
              <span class="label">残余风险</span>
              <span class="value">
                <el-tag :type="getRiskType(selectedThreat.residual_risk)" size="small">
                  {{ selectedThreat.residual_risk || '-' }}
                </el-tag>
              </span>
            </div>
            <div class="detail-item" v-if="selectedThreat.risk_treatment !== undefined">
              <span class="label">风险处置</span>
              <span class="value">{{ selectedThreat.risk_treatment || '-' }}</span>
            </div>
          </div>
        </div>

        <!-- 安全措施 -->
        <div class="detail-section">
          <h4>🛡️ 安全措施</h4>
          <div class="detail-full">
            <div class="detail-item full">
              <span class="label">安全措施</span>
              <span class="value">{{ selectedThreat.security_measure || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">有效性</span>
              <span class="value">{{ selectedThreat.effectiveness || '-' }}</span>
            </div>
            <div class="detail-item full">
              <span class="label">安全目标</span>
              <span class="value">{{ selectedThreat.security_goal || '-' }}</span>
            </div>
            <div class="detail-item full" v-if="selectedThreat.cybersecurity_requirements">
              <span class="label">网络安全需求</span>
              <span class="value">{{ selectedThreat.cybersecurity_requirements || '-' }}</span>
            </div>
          </div>
        </div>

        <!-- 其他信息 -->
        <div class="detail-section" v-if="hasOtherInfo(selectedThreat)">
          <h4>📝 其他信息</h4>
          <div class="detail-full">
            <div class="detail-item full" v-if="selectedThreat.remarks">
              <span class="label">备注</span>
              <span class="value">{{ selectedThreat.remarks }}</span>
            </div>
            <div class="detail-item full" v-if="selectedThreat.verification_method">
              <span class="label">验证方法</span>
              <span class="value">{{ selectedThreat.verification_method }}</span>
            </div>
            <div class="detail-item full" v-if="selectedThreat.status">
              <span class="label">状态</span>
              <span class="value">{{ selectedThreat.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>

  <div class="preview-empty" v-else>
    <el-icon :size="64"><DocumentCopy /></el-icon>
    <p>暂无预览数据</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  Download, Close, Box, Warning, CircleClose, 
  Document, Picture, List, Collection, Share, DocumentCopy 
} from '@element-plus/icons-vue'
import { useReportStore } from '@/stores/report'

interface PreviewData {
  report_info?: {
    id: string
    name: string
    version: string
    created_at: string
    file_path: string
    file_size: number
    statistics: any
  }
  cover?: Record<string, any>
  definitions?: Record<string, any>
  assets?: any[]
  dataflow_image?: string
  attack_trees?: any[]
  tara_results?: any[]
  statistics?: Record<string, any>
}

const props = defineProps<{
  previewData: PreviewData | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const reportStore = useReportStore()

// 威胁详情弹窗状态
const threatDetailVisible = ref(false)
const selectedThreat = ref<any>(null)

const hasDefinitionImages = computed(() => {
  if (!props.previewData) return false
  const defs = props.previewData.definitions
  return defs?.item_boundary_image || 
         defs?.system_architecture_image || 
         defs?.software_architecture_image ||
         props.previewData.dataflow_image
})

// 处理假设数据，支持多种格式
const assumptionsList = computed(() => {
  const assumptions = props.previewData?.definitions?.assumptions
  if (!assumptions || !Array.isArray(assumptions)) return []
  
  return assumptions.map((item, index) => {
    // 如果是字符串格式
    if (typeof item === 'string') {
      return {
        id: `ASM-${String(index + 1).padStart(3, '0')}`,
        description: item
      }
    }
    // 如果是对象格式
    return {
      id: item.id || item.assumption_id || `ASM-${String(index + 1).padStart(3, '0')}`,
      description: item.description || item.content || item.text || item.assumption || '',
      source: item.source || '',
      rationale: item.rationale || item.reason || ''
    }
  })
})

const hasAssumptions = computed(() => {
  return assumptionsList.value.length > 0
})

const hasAssumptionSource = computed(() => {
  return assumptionsList.value.some(item => item.source)
})

const hasAssumptionRationale = computed(() => {
  return assumptionsList.value.some(item => item.rationale)
})

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getImageUrl(imagePath?: string): string {
  if (!imagePath) return ''
  // 如果已经是完整的API路径，直接返回
  if (imagePath.startsWith('/api/')) {
    return imagePath
  }
  // 对于其他路径（MinIO路径等），使用当前报告的 image-by-path 接口
  // 注意：这需要 report_id 存在
  if (props.reportId && imagePath) {
    return `/api/v1/reports/${props.reportId}/image-by-path?path=${encodeURIComponent(imagePath)}`
  }
  return imagePath
}

function getStrideType(stride?: string): string {
  if (!stride) return 'info'
  const types: Record<string, string> = {
    'S': 'danger',
    'S欺骗': 'danger',
    'T': 'warning',
    'T篡改': 'warning',
    'R': 'info',
    'R抵赖': 'info',
    'I': 'success',
    'I信息泄露': 'success',
    'D': 'danger',
    'D拒绝服务': 'danger',
    'E': 'warning',
    'E权限提升': 'warning'
  }
  return types[stride] || 'info'
}

function getImpactClass(impact?: number | string): string {
  const value = typeof impact === 'string' ? parseInt(impact) : (impact || 0)
  if (value >= 3) return 'impact-high'
  if (value >= 2) return 'impact-medium'
  return 'impact-low'
}

function getRiskType(risk?: string): string {
  if (!risk) return 'info'
  const types: Record<string, string> = {
    'Critical': 'danger',
    '关键': 'danger',
    'High': 'danger',
    '高': 'danger',
    'Medium': 'warning',
    '中': 'warning',
    'Low': 'success',
    '低': 'success',
    'QM': 'info'
  }
  return types[risk] || 'info'
}

// 显示威胁详情
function showThreatDetail(row: any) {
  selectedThreat.value = row
  threatDetailVisible.value = true
}

// 处理行点击
function handleThreatRowClick(row: any) {
  showThreatDetail(row)
}

// 判断是否有其他信息
function hasOtherInfo(threat: any): boolean {
  return !!(threat?.remarks || threat?.verification_method || threat?.status)
}

async function handleDownload() {
  if (props.previewData?.report_info) {
    await reportStore.downloadReport(
      props.previewData.report_info.id,
      props.previewData.report_info.name || 'TARA报告'
    )
  }
}
</script>

<style scoped lang="scss">
.report-preview {
  padding: 24px;
  max-height: 85vh;
  overflow-y: auto;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: rgba(255, 255, 255, 0.3);
  
  p {
    margin-top: 16px;
    font-size: 14px;
  }
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  h2 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .meta-info {
    display: flex;
    gap: 16px;
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;

  &.assets {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  &.threats {
    background: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
  }

  &.risks {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.section-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 20px;
  margin-bottom: 20px;

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: rgba(255, 255, 255, 0.9);
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.info-value {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.description-content {
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.8);
  white-space: pre-wrap;
}

.image-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.image-preview-item {
  .image-label {
    display: block;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 8px;
  }

  :deep(.el-image) {
    width: 100%;
    height: 200px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
  }
}

.attack-trees-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.attack-tree-item {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;

  .tree-header {
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);

    .tree-asset {
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }

    .tree-title {
      display: block;
      margin-top: 4px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }

  .tree-image {
    padding: 12px;
    
    :deep(.el-image) {
      width: 100%;
      height: 250px;
      border-radius: 4px;
    }
  }

  .tree-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 150px;
    color: rgba(255, 255, 255, 0.3);
    
    span {
      margin-top: 8px;
      font-size: 13px;
    }
  }
}

.security-attrs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.feasibility-info {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;

  .info-tag {
    font-size: 11px;
    padding: 2px 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    color: rgba(255, 255, 255, 0.7);
  }
}

.impact-info {
  display: flex;
  flex-direction: column;
  gap: 2px;

  .impact-item {
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 4px;
    
    &.impact-high {
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
    }
    
    &.impact-medium {
      background: rgba(245, 158, 11, 0.2);
      color: #f59e0b;
    }
    
    &.impact-low {
      background: rgba(34, 197, 94, 0.2);
      color: #22c55e;
    }
  }
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.03);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-border-color: rgba(255, 255, 255, 0.05);
  
  .el-table__cell {
    border-color: rgba(255, 255, 255, 0.05);
  }
}

.clickable-table {
  :deep(.el-table__row) {
    cursor: pointer;
    transition: background-color 0.2s;
    
    &:hover {
      background-color: rgba(59, 130, 246, 0.1) !important;
    }
  }
}

.table-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 12px;
}

/* 威胁详情弹窗样式 */
.threat-detail {
  .detail-section {
    margin-bottom: 24px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    h4 {
      font-size: 14px;
      font-weight: 600;
      color: #409eff;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #ebeef5;
    }
  }
  
  .detail-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .detail-full {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    &.full {
      grid-column: span 2;
    }
    
    .label {
      font-size: 12px;
      color: #909399;
    }
    
    .value {
      font-size: 14px;
      color: #303133;
      line-height: 1.5;
      
      &.impact-value {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 500;
        
        &.impact-high {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }
        
        &.impact-medium {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }
        
        &.impact-low {
          background: rgba(34, 197, 94, 0.1);
          color: #22c55e;
        }
      }
    }
  }
}

:deep(.el-dialog) {
  border-radius: 12px;
  
  .el-dialog__header {
    border-bottom: 1px solid #ebeef5;
    margin-right: 0;
    padding: 16px 20px;
    
    .el-dialog__title {
      font-weight: 600;
    }
  }
  
  .el-dialog__body {
    padding: 20px;
    max-height: 70vh;
    overflow-y: auto;
  }
}
</style>
