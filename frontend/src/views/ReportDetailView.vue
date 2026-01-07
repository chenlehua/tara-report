<template>
  <div class="report-detail-page animate-fadeIn">
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <svg class="animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
        <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
      </svg>
      <span>加载中...</span>
    </div>

    <template v-else-if="report">
      <!-- 页面头部 -->
      <div class="detail-header">
        <div class="header-left">
          <button class="btn-back" @click="$router.back()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            返回
          </button>
          <div class="title-section">
            <h1>{{ report.name }}</h1>
            <div class="header-meta">
              <span class="badge badge-success">已完成</span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                {{ formatDate(report.created_at) }}
              </span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <!-- 下载下拉菜单 -->
          <div class="download-dropdown" :class="{ active: showDownloadDropdown }">
            <button class="btn btn-primary dropdown-trigger" @click="toggleDownloadDropdown">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7,10 12,15 17,10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              下载报告
              <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            <div class="dropdown-menu" @click.stop>
              <a :href="downloadUrl" class="dropdown-item" @click="closeDownloadDropdown">
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
              <a :href="pdfDownloadUrl" class="dropdown-item" @click="closeDownloadDropdown">
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

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <path d="M8 21h8"/>
              <path d="M12 17v4"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ report.statistics?.assets_count || 0 }}</span>
            <span class="stat-label">资产数量</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon yellow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ report.statistics?.threats_count || 0 }}</span>
            <span class="stat-label">威胁场景</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon red">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
              <path d="m14.5 9-5 5"/>
              <path d="m9.5 9 5 5"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ report.statistics?.high_risk_count || 0 }}</span>
            <span class="stat-label">高风险项</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ report.statistics?.measures_count || 0 }}</span>
            <span class="stat-label">安全措施</span>
          </div>
        </div>
      </div>

      <!-- 项目信息 -->
      <div class="section-card">
        <h2>项目信息</h2>
        <div class="section-content">
          <p class="section-desc">本报告基于 ISO/SAE 21434 标准，对目标系统进行了全面的威胁分析和风险评估 (TARA)。</p>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">项目名称</span>
              <span class="info-value">{{ report.project_name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">报告标题</span>
              <span class="info-value">{{ report.cover?.report_title || report.name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">文档编号</span>
              <span class="info-value">{{ report.cover?.document_number || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">版本</span>
              <span class="info-value">{{ report.cover?.version || 'V1.0' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">数据等级</span>
              <span class="info-value">{{ report.cover?.data_level || '秘密' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">生成时间</span>
              <span class="info-value">{{ formatDate(report.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 架构图预览 -->
      <div v-if="hasImages" class="section-card">
        <h2>架构图</h2>
        <div class="section-content">
          <div class="images-grid">
            <div 
              v-if="report.definitions?.item_boundary_image"
              class="image-card"
              @click="showImageModal(report.definitions.item_boundary_image, '项目边界图')"
            >
              <img :src="getImageSrc(report.definitions.item_boundary_image)" alt="项目边界图">
              <div class="image-title">项目边界图</div>
            </div>
            <div 
              v-if="report.definitions?.system_architecture_image"
              class="image-card"
              @click="showImageModal(report.definitions.system_architecture_image, '系统架构图')"
            >
              <img :src="getImageSrc(report.definitions.system_architecture_image)" alt="系统架构图">
              <div class="image-title">系统架构图</div>
            </div>
            <div 
              v-if="report.definitions?.software_architecture_image"
              class="image-card"
              @click="showImageModal(report.definitions.software_architecture_image, '软件架构图')"
            >
              <img :src="getImageSrc(report.definitions.software_architecture_image)" alt="软件架构图">
              <div class="image-title">软件架构图</div>
            </div>
            <div 
              v-if="report.assets?.dataflow_image"
              class="image-card"
              @click="showImageModal(report.assets.dataflow_image, '数据流图')"
            >
              <img :src="getImageSrc(report.assets.dataflow_image)" alt="数据流图">
              <div class="image-title">数据流图</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 功能描述 -->
      <div v-if="report.definitions?.functional_description" class="section-card">
        <h2>功能描述</h2>
        <div class="section-content">
          <p class="functional-desc">{{ report.definitions.functional_description }}</p>
        </div>
      </div>

      <!-- 相关项假设 -->
      <div v-if="assumptions.length > 0" class="section-card">
        <h2>相关项假设 ({{ assumptions.length }})</h2>
        <div class="section-content">
          <table class="data-table">
            <thead>
              <tr>
                <th>假设编号</th>
                <th>假设描述</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in assumptions" :key="index">
                <td>{{ item.id }}</td>
                <td>{{ item.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 资产列表 -->
      <div v-if="assets.length > 0" class="section-card">
        <h2>资产清单 ({{ assets.length }})</h2>
        <div class="section-content">
          <table class="data-table">
            <thead>
              <tr>
                <th>资产ID</th>
                <th>资产名称</th>
                <th>分类</th>
                <th>备注</th>
                <th>安全属性</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="asset in assets" :key="asset.id">
                <td>{{ asset.id }}</td>
                <td>{{ asset.name }}</td>
                <td>{{ asset.category }}</td>
                <td>{{ asset.remarks }}</td>
                <td>
                  <span v-if="asset.authenticity" class="attr-tag">真实性</span>
                  <span v-if="asset.integrity" class="attr-tag">完整性</span>
                  <span v-if="asset.availability" class="attr-tag">可用性</span>
                  <span v-if="asset.confidentiality" class="attr-tag">机密性</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 攻击树 -->
      <div v-if="attackTrees.length > 0" class="section-card">
        <h2>攻击树分析 ({{ attackTrees.length }})</h2>
        <div class="section-content">
          <div class="attack-trees-grid">
            <div 
              v-for="(tree, index) in attackTrees" 
              :key="index"
              class="attack-tree-card"
            >
              <div class="attack-tree-header">
                <div class="tree-info">
                  <span class="tree-id">{{ tree.asset_id || `AT${String(index + 1).padStart(3, '0')}` }}</span>
                  <span class="tree-name">{{ tree.asset_name || tree.title || `攻击树 ${index + 1}` }}</span>
                </div>
              </div>
              <div class="attack-tree-body">
                <div 
                  v-if="tree.image || tree.image_url || tree.attack_tree_image"
                  class="tree-image"
                  @click="showImageModal(tree.image || tree.image_url || tree.attack_tree_image, tree.asset_name || tree.title || `攻击树 ${index + 1}`)"
                >
                  <img :src="getImageSrc(tree.image || tree.image_url || tree.attack_tree_image)" :alt="tree.asset_name || tree.title">
                  <div class="image-overlay">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                    <span>点击查看大图</span>
                  </div>
                </div>
                <div v-else class="tree-placeholder">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <path d="M21 15l-5-5L5 21"/>
                  </svg>
                  <span>暂无攻击树图片</span>
                </div>
              </div>
              <div class="attack-tree-footer" v-if="tree.description || tree.title">
                <p v-if="tree.title" class="tree-title">{{ tree.title }}</p>
                <p v-if="tree.description" class="tree-desc">{{ tree.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TARA分析结果 -->
      <div v-if="taraResults.length > 0" class="section-card">
        <h2>威胁分析结果 ({{ taraResults.length }})</h2>
        <div class="section-content">
          <p class="table-hint">点击任意行可查看威胁详情</p>
          <table class="data-table clickable-table">
            <thead>
              <tr>
                <th>资产ID</th>
                <th>资产名称</th>
                <th>STRIDE</th>
                <th>威胁场景</th>
                <th>攻击向量</th>
                <th>影响等级</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(result, index) in taraResults" :key="index" @click="showThreatDetail(result)">
                <td>{{ result.asset_id }}</td>
                <td>{{ result.asset_name }}</td>
                <td>
                  <span class="stride-badge">{{ result.stride_model }}</span>
                </td>
                <td class="threat-cell">{{ result.threat_scenario }}</td>
                <td>{{ result.attack_vector }}</td>
                <td>
                  <span :class="['impact-badge', getImpactClass(result.operational_impact)]">
                    {{ result.operational_impact }}
                  </span>
                </td>
                <td>
                  <button class="btn-view-detail" @click.stop="showThreatDetail(result)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                    详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 术语表 -->
      <div v-if="terminology.length > 0" class="section-card">
        <h2>术语表</h2>
        <div class="section-content">
          <table class="data-table">
            <thead>
              <tr>
                <th>缩写</th>
                <th>英文全称</th>
                <th>中文名称</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="term in terminology" :key="term.abbreviation">
                <td>{{ term.abbreviation }}</td>
                <td>{{ term.english }}</td>
                <td>{{ term.chinese }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

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

    <!-- 威胁详情弹窗 -->
    <div v-if="threatModal.show" class="modal-overlay" @click="closeThreatModal">
      <div class="modal-content threat-modal" @click.stop>
        <div class="modal-header">
          <h3>威胁分析详情 - TARA Results</h3>
          <button class="btn-close" @click="closeThreatModal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body threat-detail-body" v-if="threatModal.data">
          <!-- 1. 资产信息 Asset Information (A-G列) -->
          <div class="detail-section">
            <h4>📋 资产信息 Asset Information</h4>
            <table class="excel-table">
              <thead>
                <tr>
                  <th>Asset ID<br/>资产ID</th>
                  <th>Asset Name<br/>资产名称</th>
                  <th>细分类-子领域一</th>
                  <th>细分类-子领域二</th>
                  <th>细分类-子领域三</th>
                  <th>Category<br/>分类</th>
                  <th>Security Attributes<br/>安全属性</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ threatModal.data.asset_id || '-' }}</td>
                  <td>{{ threatModal.data.asset_name || '-' }}</td>
                  <td>{{ threatModal.data.subdomain1 || '-' }}</td>
                  <td>{{ threatModal.data.subdomain2 || '-' }}</td>
                  <td>{{ threatModal.data.subdomain3 || '-' }}</td>
                  <td>{{ threatModal.data.category || '-' }}</td>
                  <td>{{ threatModal.data.security_attribute || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 2. 威胁分析 Threat Analysis (H-K列) -->
          <div class="detail-section">
            <h4>⚠️ 威胁分析 Threat Analysis</h4>
            <table class="excel-table">
              <thead>
                <tr>
                  <th>STRIDE Model<br/>STRIDE模型</th>
                  <th>Potential Threat and Damage Scenario<br/>潜在威胁和损害场景</th>
                  <th>Attack Path<br/>攻击路径</th>
                  <th>来源<br/>WP29威胁映射</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><span class="stride-badge">{{ threatModal.data.stride_model || '-' }}</span></td>
                  <td class="text-left">{{ threatModal.data.threat_scenario || '-' }}</td>
                  <td class="text-left">{{ threatModal.data.attack_path || '-' }}</td>
                  <td>{{ threatModal.data.wp29_mapping || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 3. 攻击可行性分析 Attack Feasibility Analysis (L-U列) -->
          <div class="detail-section">
            <h4>🎯 攻击可行性分析 Attack Feasibility Analysis</h4>
            <table class="excel-table">
              <thead>
                <tr>
                  <th colspan="2">Attack Vector(V)<br/>攻击向量</th>
                  <th colspan="2">Attack Complexity(C)<br/>攻击复杂度</th>
                  <th colspan="2">Privileges Required(P)<br/>权限要求</th>
                  <th colspan="2">User Interaction(U)<br/>用户交互</th>
                  <th colspan="2">Attack Feasibility<br/>攻击可行性计算</th>
                </tr>
                <tr class="sub-header">
                  <th>内容</th>
                  <th>指标值</th>
                  <th>内容</th>
                  <th>指标值</th>
                  <th>等级</th>
                  <th>指标值</th>
                  <th>等级</th>
                  <th>指标值</th>
                  <th>计算值</th>
                  <th>等级</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ threatModal.data.attack_vector || '-' }}</td>
                  <td class="calc-value">{{ calcAttackVectorValue(threatModal.data.attack_vector) }}</td>
                  <td>{{ threatModal.data.attack_complexity || '-' }}</td>
                  <td class="calc-value">{{ calcAttackComplexityValue(threatModal.data.attack_complexity) }}</td>
                  <td>{{ threatModal.data.privileges_required || threatModal.data.privilege_required || '-' }}</td>
                  <td class="calc-value">{{ calcPrivilegesValue(threatModal.data.privileges_required || threatModal.data.privilege_required) }}</td>
                  <td>{{ threatModal.data.user_interaction || '-' }}</td>
                  <td class="calc-value">{{ calcUserInteractionValue(threatModal.data.user_interaction) }}</td>
                  <td class="calc-value highlight">{{ calcAttackFeasibilityValue(threatModal.data) }}</td>
                  <td>
                    <span :class="['feasibility-badge', getFeasibilityClass(calcAttackFeasibilityLevel(threatModal.data))]">
                      {{ calcAttackFeasibilityLevel(threatModal.data) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 4. 影响分析 Impact Analysis (V-AI列) -->
          <div class="detail-section">
            <h4>💥 影响分析 Impact Analysis</h4>
            <table class="excel-table">
              <thead>
                <tr>
                  <th colspan="3">Safety<br/>安全</th>
                  <th colspan="3">Financial<br/>经济</th>
                  <th colspan="3">Operational<br/>操作</th>
                  <th colspan="3">Privacy & Legislation<br/>隐私和法律</th>
                  <th colspan="2">Impact Level Calculation<br/>影响等级计算</th>
                </tr>
                <tr class="sub-header">
                  <th>内容</th>
                  <th>注释</th>
                  <th>指标值</th>
                  <th>内容</th>
                  <th>注释</th>
                  <th>指标值</th>
                  <th>内容</th>
                  <th>注释</th>
                  <th>指标值</th>
                  <th>内容</th>
                  <th>注释</th>
                  <th>指标值</th>
                  <th>影响计算</th>
                  <th>影响等级</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span :class="['impact-value', getImpactValueClass(threatModal.data.safety_impact)]">
                      {{ threatModal.data.safety_impact || '-' }}
                    </span>
                  </td>
                  <td class="note-cell">{{ getSafetyNote(threatModal.data.safety_impact) }}</td>
                  <td class="calc-value">{{ calcImpactValue(threatModal.data.safety_impact) }}</td>
                  <td>
                    <span :class="['impact-value', getImpactValueClass(threatModal.data.financial_impact)]">
                      {{ threatModal.data.financial_impact || '-' }}
                    </span>
                  </td>
                  <td class="note-cell">{{ getFinancialNote(threatModal.data.financial_impact) }}</td>
                  <td class="calc-value">{{ calcImpactValue(threatModal.data.financial_impact) }}</td>
                  <td>
                    <span :class="['impact-value', getImpactValueClass(threatModal.data.operational_impact)]">
                      {{ threatModal.data.operational_impact || '-' }}
                    </span>
                  </td>
                  <td class="note-cell">{{ getOperationalNote(threatModal.data.operational_impact) }}</td>
                  <td class="calc-value">{{ calcImpactValue(threatModal.data.operational_impact) }}</td>
                  <td>
                    <span :class="['impact-value', getImpactValueClass(threatModal.data.privacy_impact)]">
                      {{ threatModal.data.privacy_impact || '-' }}
                    </span>
                  </td>
                  <td class="note-cell">{{ getPrivacyNote(threatModal.data.privacy_impact) }}</td>
                  <td class="calc-value">{{ calcImpactValue(threatModal.data.privacy_impact) }}</td>
                  <td class="calc-value highlight">{{ calcTotalImpactValue(threatModal.data) }}</td>
                  <td>
                    <span :class="['impact-level-badge', getImpactLevelClass(calcImpactLevel(threatModal.data))]">
                      {{ calcImpactLevel(threatModal.data) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 5. 风险评估与安全需求 Risk Assessment & Security Requirements (AJ-AN列) -->
          <div class="detail-section">
            <h4>📊 风险评估与安全需求 Risk Assessment & Security Requirements</h4>
            <table class="excel-table">
              <thead>
                <tr>
                  <th>Risk Level<br/>风险等级</th>
                  <th>Risk Treatment Decision<br/>风险处置决策</th>
                  <th>Security Goal<br/>安全目标</th>
                  <th>Security Requirement<br/>安全需求</th>
                  <th>Source来源<br/>WP29 Control Mapping</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span :class="['risk-badge', getRiskClass(calcRiskLevel(threatModal.data))]">
                      {{ calcRiskLevel(threatModal.data) }}
                    </span>
                  </td>
                  <td>{{ calcRiskTreatment(threatModal.data) }}</td>
                  <td>{{ calcSecurityGoal(threatModal.data) }}</td>
                  <td class="text-left">{{ threatModal.data.security_requirement || threatModal.data.security_measure || '-' }}</td>
                  <td>{{ calcWP29ControlMapping(threatModal.data.stride_model) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 6. 其他信息 (如有) -->
          <div class="detail-section" v-if="threatModal.data.threat_id || threatModal.data.remarks || threatModal.data.residual_risk">
            <h4>📝 其他信息 Additional Information</h4>
            <table class="excel-table">
              <thead>
                <tr>
                  <th v-if="threatModal.data.threat_id">Threat ID<br/>威胁ID</th>
                  <th v-if="threatModal.data.residual_risk">Residual Risk<br/>残余风险</th>
                  <th v-if="threatModal.data.effectiveness">Effectiveness<br/>有效性</th>
                  <th v-if="threatModal.data.cal">CAL</th>
                  <th v-if="threatModal.data.component">Component<br/>组件</th>
                  <th v-if="threatModal.data.status">Status<br/>状态</th>
                  <th v-if="threatModal.data.remarks">Remarks<br/>备注</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td v-if="threatModal.data.threat_id">{{ threatModal.data.threat_id }}</td>
                  <td v-if="threatModal.data.residual_risk">
                    <span :class="['risk-badge', getRiskClass(threatModal.data.residual_risk)]">
                      {{ threatModal.data.residual_risk }}
                    </span>
                  </td>
                  <td v-if="threatModal.data.effectiveness">{{ threatModal.data.effectiveness }}</td>
                  <td v-if="threatModal.data.cal">{{ threatModal.data.cal }}</td>
                  <td v-if="threatModal.data.component">{{ threatModal.data.component }}</td>
                  <td v-if="threatModal.data.status">{{ threatModal.data.status }}</td>
                  <td v-if="threatModal.data.remarks" class="text-left">{{ threatModal.data.remarks }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 计算公式说明 -->
          <div class="detail-section formula-section">
            <h4>📐 计算公式说明 Calculation Formulas</h4>
            <div class="formula-list">
              <div class="formula-item">
                <span class="formula-label">攻击可行性计算:</span>
                <code>8.22 × 攻击向量值 × 攻击复杂度值 × 权限要求值 × 用户交互值</code>
              </div>
              <div class="formula-item">
                <span class="formula-label">影响计算:</span>
                <code>安全指标值 + 经济指标值 + 操作指标值 + 隐私指标值</code>
              </div>
              <div class="formula-item">
                <span class="formula-label">指标值映射:</span>
                <code>可忽略不计的=0, 中等的=1, 重大的=10, 严重的=1000</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { getReport, getDownloadUrl, getPdfDownloadUrl } from '@/api'

const route = useRoute()
const isLoading = ref(true)
const report = ref(null)

const imageModal = ref({
  show: false,
  url: '',
  title: ''
})

const threatModal = ref({
  show: false,
  data: null
})

// 计算属性
const downloadUrl = computed(() => {
  return report.value ? getDownloadUrl(report.value.id) : ''
})

const pdfDownloadUrl = computed(() => {
  return report.value ? getPdfDownloadUrl(report.value.id) : ''
})

// 下载下拉菜单状态
const showDownloadDropdown = ref(false)

function toggleDownloadDropdown() {
  showDownloadDropdown.value = !showDownloadDropdown.value
}

function closeDownloadDropdown() {
  showDownloadDropdown.value = false
}

const assets = computed(() => {
  return report.value?.assets?.assets || []
})

const taraResults = computed(() => {
  return report.value?.tara_results?.results || []
})

const attackTrees = computed(() => {
  return report.value?.attack_trees?.attack_trees || []
})

const terminology = computed(() => {
  return report.value?.definitions?.terminology || []
})

// 计算假设列表 - 支持多种数据格式
const assumptions = computed(() => {
  if (!report.value?.definitions?.assumptions) return []
  
  const assumptionsData = report.value.definitions.assumptions
  
  // 如果是数组
  if (Array.isArray(assumptionsData)) {
    return assumptionsData.map((item, index) => {
      // 如果是字符串数组
      if (typeof item === 'string') {
        return {
          id: `假设${index + 1}`,
          description: item
        }
      }
      // 如果是对象数组
      return {
        id: item.id || item.assumption_id || `假设${index + 1}`,
        description: item.description || item.content || item.text || item
      }
    })
  }
  
  return []
})

const hasImages = computed(() => {
  const defs = report.value?.definitions || {}
  const assets = report.value?.assets || {}
  return defs.item_boundary_image || 
         defs.system_architecture_image || 
         defs.software_architecture_image ||
         assets.dataflow_image
})

// 生命周期
onMounted(async () => {
  const reportId = route.params.id
  try {
    const data = await getReport(reportId)
    report.value = data
  } catch (error) {
    console.error('获取报告详情失败:', error)
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
    showDownloadDropdown.value = false
  }
}

// 方法
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

function getImageSrc(imagePath) {
  if (!imagePath) return ''
  // 如果已经是完整的API路径，直接返回
  if (imagePath.startsWith('/api/')) return imagePath
  if (imagePath.startsWith('http')) return imagePath
  // 使用当前报告的 image-by-path 接口
  const reportId = report.value?.id || report.value?.report_id || route.params.id
  if (reportId && imagePath) {
    return `/api/v1/reports/${reportId}/image-by-path?path=${encodeURIComponent(imagePath)}`
  }
  return imagePath
}

function getImpactClass(impact) {
  const map = {
    '严重的': 'critical',
    '重大的': 'high',
    '中等的': 'medium',
    '可忽略不计的': 'low'
  }
  return map[impact] || 'medium'
}

function showImageModal(imagePath, title) {
  imageModal.value = {
    show: true,
    url: getImageSrc(imagePath),
    title
  }
}

function closeImageModal() {
  imageModal.value = { show: false, url: '', title: '' }
}

function showThreatDetail(threat) {
  threatModal.value = {
    show: true,
    data: threat
  }
}

function closeThreatModal() {
  threatModal.value = { show: false, data: null }
}

function getDetailImpactClass(impact) {
  const value = typeof impact === 'string' ? parseInt(impact) : (impact || 0)
  if (value >= 3) return 'impact-high'
  if (value >= 2) return 'impact-medium'
  return 'impact-low'
}

function getRiskClass(risk) {
  if (!risk) return ''
  const riskMap = {
    'Critical': 'risk-critical',
    '关键': 'risk-critical',
    'High': 'risk-high',
    '高': 'risk-high',
    'Medium': 'risk-medium',
    '中': 'risk-medium',
    'Low': 'risk-low',
    '低': 'risk-low',
    'QM': 'risk-qm'
  }
  return riskMap[risk] || ''
}

// 攻击可行性等级样式
function getFeasibilityClass(level) {
  if (!level) return ''
  const map = {
    '很高': 'feasibility-very-high',
    '高': 'feasibility-high',
    '中': 'feasibility-medium',
    '低': 'feasibility-low',
    '很低': 'feasibility-very-low'
  }
  return map[level] || ''
}

// 影响值样式
function getImpactValueClass(impact) {
  if (!impact) return ''
  const map = {
    '严重的': 'impact-severe',
    '重大的': 'impact-major',
    '中等的': 'impact-moderate',
    '可忽略不计的': 'impact-negligible'
  }
  return map[impact] || ''
}

// 影响等级样式
function getImpactLevelClass(level) {
  if (!level) return ''
  const map = {
    '严重的': 'level-severe',
    '重大的': 'level-major',
    '中等的': 'level-moderate',
    '可忽略不计的': 'level-negligible',
    '无影响': 'level-none'
  }
  return map[level] || ''
}

// 安全影响注释
function getSafetyNote(impact) {
  const notes = {
    '可忽略不计的': '没有受伤',
    '中等的': '轻伤和中等伤害',
    '重大的': '严重伤害(生存概率高)',
    '严重的': '危及生命(生存概率不确定)或致命伤害'
  }
  return notes[impact] || '-'
}

// 经济影响注释
function getFinancialNote(impact) {
  const notes = {
    '可忽略不计的': '财务损失不会产生任何影响',
    '中等的': '财务损失会产生中等影响',
    '重大的': '财务损失会产生重大影响',
    '严重的': '财务损失会产生严重影响'
  }
  return notes[impact] || '-'
}

// 操作影响注释
function getOperationalNote(impact) {
  const notes = {
    '可忽略不计的': '操作损坏不会导致车辆功能减少',
    '中等的': '操作损坏会导致车辆功能中等减少',
    '重大的': '操作损坏会导致车辆功能重大减少',
    '严重的': '操作损坏会导致车辆功能丧失'
  }
  return notes[impact] || '-'
}

// 隐私影响注释
function getPrivacyNote(impact) {
  const notes = {
    '可忽略不计的': '隐私危害不会产生任何影响',
    '中等的': '隐私危害会产生中等影响',
    '重大的': '隐私危害会产生重大影响',
    '严重的': '隐私危害会产生严重影响'
  }
  return notes[impact] || '-'
}

// ==================== Excel 计算函数 ====================

// 攻击向量指标值计算 (M列)
function calcAttackVectorValue(attackVector) {
  const values = {
    '网络': 0.85,
    '邻居': 0.62,
    '本地': 0.55,
    '物理': 0.2
  }
  return values[attackVector] ?? 0
}

// 攻击复杂度指标值计算 (O列)
function calcAttackComplexityValue(complexity) {
  const values = {
    '低': 0.77,
    '高': 0.44
  }
  return values[complexity] ?? 0
}

// 权限要求指标值计算 (Q列)
function calcPrivilegesValue(privileges) {
  const values = {
    '无': 0.85,
    '低': 0.62,
    '高': 0.27
  }
  return values[privileges] ?? 0
}

// 用户交互指标值计算 (S列)
function calcUserInteractionValue(interaction) {
  const values = {
    '不需要': 0.85,
    '需要': 0.62
  }
  return values[interaction] ?? 0
}

// 攻击可行性计算值 (T列): 8.22 * M * O * Q * S
function calcAttackFeasibilityValue(data) {
  const av = calcAttackVectorValue(data.attack_vector)
  const ac = calcAttackComplexityValue(data.attack_complexity)
  const pr = calcPrivilegesValue(data.privileges_required || data.privilege_required)
  const ui = calcUserInteractionValue(data.user_interaction)
  
  const result = 8.22 * av * ac * pr * ui
  return result.toFixed(2)
}

// 攻击可行性等级 (U列)
function calcAttackFeasibilityLevel(data) {
  const value = parseFloat(calcAttackFeasibilityValue(data))
  if (value <= 1.05) return '很低'
  if (value <= 1.99) return '低'
  if (value <= 2.99) return '中'
  if (value <= 3.99) return '高'
  return '很高'
}

// 影响指标值计算 (X/AA/AD/AG列)
function calcImpactValue(impact) {
  const values = {
    '可忽略不计的': 0,
    '中等的': 1,
    '重大的': 10,
    '严重的': 1000
  }
  return values[impact] ?? 0
}

// 影响总计算值 (AH列)
function calcTotalImpactValue(data) {
  const safety = calcImpactValue(data.safety_impact)
  const financial = calcImpactValue(data.financial_impact)
  const operational = calcImpactValue(data.operational_impact)
  const privacy = calcImpactValue(data.privacy_impact)
  return safety + financial + operational + privacy
}

// 影响等级 (AI列)
function calcImpactLevel(data) {
  const total = calcTotalImpactValue(data)
  if (total >= 1000) return '严重的'
  if (total >= 100) return '重大的'
  if (total >= 10) return '中等的'
  if (total >= 1) return '可忽略不计的'
  return '无影响'
}

// 风险等级计算 (AJ列)
function calcRiskLevel(data) {
  const impactLevel = calcImpactLevel(data)
  const feasibilityLevel = calcAttackFeasibilityLevel(data)
  
  // QM条件
  if (impactLevel === '无影响' && feasibilityLevel === '无') return 'QM'
  
  // Low条件
  if (impactLevel === '无影响' && feasibilityLevel !== '无') return 'Low'
  if (impactLevel === '可忽略不计的' && ['很低', '低', '中'].includes(feasibilityLevel)) return 'Low'
  if (impactLevel === '中等的' && ['很低', '低'].includes(feasibilityLevel)) return 'Low'
  if (impactLevel === '重大的' && feasibilityLevel === '很低') return 'Low'
  
  // Medium条件
  if (impactLevel === '可忽略不计的' && ['高', '很高'].includes(feasibilityLevel)) return 'Medium'
  if (impactLevel === '中等的' && feasibilityLevel === '中') return 'Medium'
  if (impactLevel === '重大的' && feasibilityLevel === '低') return 'Medium'
  if (impactLevel === '严重的' && feasibilityLevel === '很低') return 'Medium'
  
  // High条件
  if (impactLevel === '中等的' && ['高', '很高'].includes(feasibilityLevel)) return 'High'
  if (impactLevel === '重大的' && feasibilityLevel === '中') return 'High'
  if (impactLevel === '严重的' && feasibilityLevel === '低') return 'High'
  
  // Critical条件
  return 'Critical'
}

// 风险处置决策 (AK列)
function calcRiskTreatment(data) {
  const riskLevel = calcRiskLevel(data)
  if (riskLevel === 'QM' || riskLevel === 'Low') return '保留风险'
  if (riskLevel === 'Medium') return '降低风险'
  return '降低风险/规避风险/转移风险'
}

// 安全目标 (AL列)
function calcSecurityGoal(data) {
  const treatment = calcRiskTreatment(data)
  if (treatment === '保留风险') return '/'
  if (treatment === '降低风险' || treatment === '降低风险/规避风险/转移风险') {
    return '需要定义安全目标'
  }
  return ''
}

// WP29控制映射 (AN列)
function calcWP29ControlMapping(strideModel) {
  const mapping = {
    'T篡改': 'M10',
    'D拒绝服务': 'M13',
    'I信息泄露': 'M11',
    'S欺骗': 'M23',
    'R抵赖': 'M24',
    'E权限提升': 'M16'
  }
  return mapping[strideModel] || '-'
}
</script>

<style scoped>
.report-detail-page {
  max-width: 1200px;
  margin: 0 auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-state svg {
  width: 40px;
  height: 40px;
  color: var(--brand-blue);
  margin-bottom: 16px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  gap: 24px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-back:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.title-section h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-muted);
}

.meta-item svg {
  width: 14px;
  height: 14px;
}

.header-actions .btn svg {
  width: 18px;
  height: 18px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-icon.blue { background: rgba(99,102,241,0.1); color: #6366f1; }
.stat-icon.yellow { background: rgba(245,158,11,0.1); color: #f59e0b; }
.stat-icon.red { background: rgba(239,68,68,0.1); color: #ef4444; }
.stat-icon.green { background: rgba(34,197,94,0.1); color: #22c55e; }

.stat-info .stat-value {
  font-size: 28px;
  font-weight: 700;
  display: block;
}

.stat-info .stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

/* Section Cards */
.section-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
}

.section-card h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.section-content {
  padding: 20px;
}

.section-desc {
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: var(--text-muted);
}

.info-value {
  font-size: 14px;
  font-weight: 500;
}

/* Images Grid */
.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.image-card {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  aspect-ratio: 16/10;
  background: var(--bg-tertiary);
}

.image-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.image-card:hover img {
  transform: scale(1.05);
}

.image-title {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  font-size: 13px;
  color: white;
  font-weight: 500;
}

.functional-desc {
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
}

/* Table Styles */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.data-table th {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  background: var(--bg-secondary);
}

.data-table tr:last-child td {
  border-bottom: none;
}

.data-table tr:hover td {
  background: var(--bg-hover);
}

.attr-tag {
  display: inline-block;
  padding: 2px 8px;
  margin: 2px;
  border-radius: 4px;
  font-size: 11px;
  background: rgba(99,102,241,0.1);
  color: #6366f1;
}

.stride-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(139,92,246,0.15);
  color: #a78bfa;
}

.threat-cell {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.impact-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.impact-badge.critical { background: rgba(239,68,68,0.15); color: #ef4444; }
.impact-badge.high { background: rgba(245,158,11,0.15); color: #f59e0b; }
.impact-badge.medium { background: rgba(59,130,246,0.15); color: #3b82f6; }
.impact-badge.low { background: rgba(34,197,94,0.15); color: #22c55e; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

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

/* 可点击表格样式 */
.table-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.clickable-table tbody tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable-table tbody tr:hover td {
  background: rgba(59, 130, 246, 0.1);
}

.btn-view-detail {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-card);
  color: var(--brand-blue);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-view-detail:hover {
  background: var(--brand-blue);
  color: white;
  border-color: var(--brand-blue);
}

.btn-view-detail svg {
  width: 14px;
  height: 14px;
}

/* 威胁详情弹窗 */
.threat-modal {
  width: 800px;
  max-width: 90vw;
  max-height: 90vh;
}

.threat-detail-body {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--brand-blue);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
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
}

.detail-item.full {
  grid-column: span 2;
}

.detail-item .label {
  font-size: 12px;
  color: var(--text-muted);
}

.detail-item .value {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
}

.impact-value {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.impact-value.impact-high {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.impact-value.impact-medium {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.impact-value.impact-low {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.risk-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.risk-badge.risk-critical {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.risk-badge.risk-high {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.risk-badge.risk-medium {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.risk-badge.risk-low {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.risk-badge.risk-qm {
  background: rgba(107, 114, 128, 0.15);
  color: #6b7280;
}

/* 攻击树样式 */
.attack-trees-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.attack-tree-card {
  background: var(--bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s;
}

.attack-tree-card:hover {
  border-color: var(--brand-blue);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.1);
}

.attack-tree-card .attack-tree-header {
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--border-color);
}

.attack-tree-card .tree-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.attack-tree-card .tree-id {
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #a78bfa;
}

.attack-tree-card .tree-name {
  font-weight: 600;
  color: var(--text-primary);
}

.attack-tree-card .attack-tree-body {
  padding: 12px;
}

.attack-tree-card .tree-image {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.attack-tree-card .tree-image img {
  width: 100%;
  height: 220px;
  object-fit: contain;
  background: rgba(0, 0, 0, 0.2);
  transition: transform 0.3s;
}

.attack-tree-card .tree-image:hover img {
  transform: scale(1.02);
}

.attack-tree-card .image-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.attack-tree-card .tree-image:hover .image-overlay {
  opacity: 1;
}

.attack-tree-card .image-overlay svg {
  width: 32px;
  height: 32px;
  color: white;
}

.attack-tree-card .image-overlay span {
  font-size: 13px;
  color: white;
}

.attack-tree-card .tree-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 180px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  color: var(--text-muted);
}

.attack-tree-card .tree-placeholder svg {
  width: 40px;
  height: 40px;
  margin-bottom: 8px;
}

.attack-tree-card .tree-placeholder span {
  font-size: 13px;
}

.attack-tree-card .attack-tree-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.01);
}

.attack-tree-card .tree-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.attack-tree-card .tree-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

@media (max-width: 1000px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .detail-header {
    flex-direction: column;
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

/* 威胁详情弹窗增强样式 */
.threat-modal {
  width: 900px;
  max-width: 95vw;
  max-height: 90vh;
}

.threat-detail-body {
  max-height: 75vh;
  overflow-y: auto;
  padding: 20px;
}

.detail-grid.four-cols {
  grid-template-columns: repeat(4, 1fr);
}

.value.highlight {
  font-weight: 600;
  color: var(--brand-blue);
}

.value.small {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}

/* 攻击可行性等级 */
.feasibility-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.feasibility-badge.feasibility-very-high {
  background: rgba(220, 38, 38, 0.15);
  color: #dc2626;
}

.feasibility-badge.feasibility-high {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.feasibility-badge.feasibility-medium {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.feasibility-badge.feasibility-low {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.feasibility-badge.feasibility-very-low {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

/* 影响值样式 */
.impact-value.impact-severe {
  background: rgba(220, 38, 38, 0.15);
  color: #dc2626;
}

.impact-value.impact-major {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.impact-value.impact-moderate {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.impact-value.impact-negligible {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

/* 影响行样式 */
.impact-row {
  display: flex;
  gap: 16px;
  padding: 12px;
  margin-bottom: 8px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.impact-category {
  min-width: 140px;
  display: flex;
  align-items: center;
}

.category-label {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-secondary);
}

.impact-details {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.impact-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
  padding: 16px;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

/* 影响等级徽章 */
.impact-level-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.impact-level-badge.level-severe {
  background: rgba(220, 38, 38, 0.15);
  color: #dc2626;
}

.impact-level-badge.level-major {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.impact-level-badge.level-moderate {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.impact-level-badge.level-negligible {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.impact-level-badge.level-none {
  background: rgba(107, 114, 128, 0.15);
  color: #6b7280;
}

/* Excel风格表格 */
.excel-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-top: 12px;
}

.excel-table th,
.excel-table td {
  border: 1px solid var(--border-color);
  padding: 8px 10px;
  text-align: center;
  vertical-align: middle;
}

.excel-table th {
  background: linear-gradient(135deg, #4472C4, #2F5496);
  color: white;
  font-weight: 600;
  font-size: 11px;
  line-height: 1.3;
}

.excel-table th br {
  display: block;
}

.excel-table .sub-header th {
  background: #8EA9DB;
  color: #1a1a2e;
  font-size: 10px;
}

.excel-table td {
  background: var(--bg-card);
}

.excel-table td.text-left {
  text-align: left;
}

.excel-table td.note-cell {
  font-size: 10px;
  color: var(--text-muted);
  max-width: 120px;
  text-align: left;
}

.excel-table td.calc-value {
  font-family: 'Monaco', 'Consolas', monospace;
  color: var(--brand-blue);
  font-weight: 600;
}

.excel-table td.calc-value.highlight {
  background: rgba(59, 130, 246, 0.1);
  font-size: 14px;
}

.excel-table .stride-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
}

.excel-table .impact-value {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.excel-table .feasibility-badge,
.excel-table .impact-level-badge,
.excel-table .risk-badge {
  font-size: 11px;
  padding: 3px 8px;
}

/* 公式说明区域 */
.formula-section {
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  padding: 16px;
}

.formula-section h4 {
  border-bottom: none;
  margin-bottom: 12px;
}

.formula-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.formula-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.formula-label {
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 100px;
}

.formula-item code {
  background: var(--bg-tertiary);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 11px;
  color: var(--brand-blue);
}

/* 威胁弹窗宽度调整 */
.threat-modal {
  width: 1200px;
  max-width: 98vw;
}

.threat-detail-body {
  max-height: 80vh;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .detail-grid.four-cols {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .impact-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .impact-category {
    min-width: auto;
  }
  
  .impact-details {
    grid-template-columns: 1fr;
  }
  
  .impact-summary {
    grid-template-columns: 1fr;
  }
  
  .excel-table {
    font-size: 10px;
  }
  
  .excel-table th,
  .excel-table td {
    padding: 4px 6px;
  }
  
  .formula-item {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* 下载下拉菜单 */
.download-dropdown {
  position: relative;
}

.dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
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
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
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
</style>
