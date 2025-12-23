<template>
  <div class="reports-page animate-fadeIn">
    <div class="page-header">
      <div class="header-left">
        <h1>报告中心</h1>
        <p class="page-desc">管理和查看所有已生成的TARA分析报告</p>
      </div>
      <router-link to="/generator" class="btn btn-primary">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        新建报告
      </router-link>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <svg class="animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
        <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
      </svg>
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="reports.length === 0" class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <path d="M14 2v6h6"/>
        <path d="M12 18v-6"/>
        <path d="M9 15l3-3 3 3"/>
      </svg>
      <h3>暂无报告</h3>
      <p>开始创建您的第一份TARA分析报告</p>
      <router-link to="/generator" class="btn btn-primary">
        立即创建
      </router-link>
    </div>

    <!-- 报告列表 -->
    <div v-else class="reports-grid">
      <div 
        v-for="report in reports" 
        :key="report.id" 
        class="card report-card"
      >
        <div class="report-header">
          <div class="report-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <path d="M14 2v6h6"/>
            </svg>
          </div>
          <span class="badge badge-success">{{ report.status === 'completed' ? '已完成' : report.status }}</span>
        </div>

        <h3 class="report-name">{{ report.name }}</h3>
        <p class="report-project">{{ report.project_name }}</p>

        <div class="report-meta">
          <div class="meta-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            {{ formatDate(report.created_at) }}
          </div>
        </div>

        <div class="report-stats">
          <div class="stat">
            <span class="stat-value">{{ report.statistics?.assets_count || 0 }}</span>
            <span class="stat-label">资产</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ report.statistics?.threats_count || 0 }}</span>
            <span class="stat-label">威胁</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ report.statistics?.high_risk_count || 0 }}</span>
            <span class="stat-label">高风险</span>
          </div>
        </div>

        <div class="report-actions">
          <router-link :to="`/reports/${report.id}`" class="btn btn-secondary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            预览
          </router-link>
          
          <!-- 下载下拉菜单 -->
          <div class="download-dropdown" :class="{ active: activeDropdown === report.id }">
            <button class="btn btn-primary dropdown-trigger" @click="toggleDropdown(report.id)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7,10 12,15 17,10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              下载
              <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            <div class="dropdown-menu">
              <a :href="getDownloadUrl(report.id)" class="dropdown-item" @click="closeDropdown">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <path d="M14 2v6h6"/>
                  <path d="M8 13h8"/>
                  <path d="M8 17h8"/>
                  <path d="M8 9h2"/>
                </svg>
                <div class="item-content">
                  <span class="item-title">Excel 格式</span>
                  <span class="item-desc">.xlsx 电子表格</span>
                </div>
              </a>
              <a :href="getPdfDownloadUrl(report.id)" class="dropdown-item" @click="closeDropdown">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <path d="M14 2v6h6"/>
                  <path d="M10 9H8v6h2v-2h1a2 2 0 100-4h-1z"/>
                  <path d="M16 9h-2v6h2a2 2 0 002-2v-2a2 2 0 00-2-2z"/>
                </svg>
                <div class="item-content">
                  <span class="item-title">PDF 格式</span>
                  <span class="item-desc">.pdf 便携文档</span>
                </div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getReports, getDownloadUrl, getPdfDownloadUrl } from '@/api'

const isLoading = ref(true)
const reports = ref([])
const activeDropdown = ref(null)

onMounted(async () => {
  try {
    const result = await getReports()
    if (result.success) {
      reports.value = result.reports
    }
  } catch (error) {
    console.error('获取报告列表失败:', error)
  } finally {
    isLoading.value = false
  }
  
  // 点击外部关闭下拉菜单
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(event) {
  if (!event.target.closest('.download-dropdown')) {
    activeDropdown.value = null
  }
}

function toggleDropdown(reportId) {
  activeDropdown.value = activeDropdown.value === reportId ? null : reportId
}

function closeDropdown() {
  activeDropdown.value = null
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleDelete(reportId) {
  if (confirm('确定要删除这份报告吗？')) {
    // 调用删除API
  }
}
</script>

<style scoped>
.reports-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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

.page-header .btn svg {
  width: 18px;
  height: 18px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.loading-state svg {
  width: 40px;
  height: 40px;
  color: var(--brand-blue);
  margin-bottom: 16px;
}

.loading-state span {
  color: var(--text-muted);
}

.empty-state svg {
  width: 80px;
  height: 80px;
  color: var(--text-muted);
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-muted);
  margin-bottom: 24px;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
}

.report-card {
  padding: 24px;
  transition: all 0.2s;
}

.report-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
  border-color: rgba(99,102,241,0.3);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.report-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.report-icon.blue {
  background: rgba(59,130,246,0.12);
  color: #60A5FA;
}

.report-icon svg {
  width: 24px;
  height: 24px;
}

.report-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.report-project {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.report-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-muted);
}

.meta-item svg {
  width: 16px;
  height: 16px;
}

.report-stats {
  display: flex;
  gap: 24px;
  padding: 16px 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 20px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.report-actions {
  display: flex;
  gap: 12px;
}

.report-actions .btn {
  flex: 1;
  justify-content: center;
  padding: 10px 16px;
}

.report-actions .btn svg {
  width: 16px;
  height: 16px;
}

/* 下载下拉菜单 */
.download-dropdown {
  position: relative;
  flex: 1;
}

.dropdown-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.dropdown-arrow {
  width: 14px;
  height: 14px;
  transition: transform 0.2s;
}

.download-dropdown.active .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  right: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(10px);
  transition: all 0.2s ease;
  z-index: 100;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.download-dropdown.active .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-primary);
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: rgba(99, 102, 241, 0.1);
}

.dropdown-item svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: var(--text-muted);
}

.dropdown-item:hover svg {
  color: var(--brand-blue);
}

.item-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-title {
  font-weight: 500;
  font-size: 14px;
}

.item-desc {
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 800px) {
  .reports-grid {
    grid-template-columns: 1fr;
  }
}
</style>
