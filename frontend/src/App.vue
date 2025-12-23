<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div class="logo-text">
            <div class="logo-title">TARA Pro</div>
            <div class="logo-subtitle">智能安全分析</div>
          </div>
        </div>
      </div>

      <nav class="nav-menu">
        <router-link 
          to="/generator" 
          class="nav-item"
          :class="{ active: $route.path === '/generator' }"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/>
          </svg>
          <span>一键生成报告</span>
          <span class="badge-ai">AI</span>
        </router-link>

        <router-link 
          to="/reports" 
          class="nav-item"
          :class="{ active: $route.path.startsWith('/reports') }"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <path d="M14 2v6h6"/>
            <path d="M16 13H8"/>
            <path d="M16 17H8"/>
            <path d="M10 9H8"/>
          </svg>
          <span>报告中心</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="version">v1.0.0</div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  display: flex;
  flex-direction: column;
  background: rgba(15,23,42,0.85);
  backdrop-filter: blur(24px);
  border-right: 1px solid var(--border-color);
}

.sidebar-header {
  height: 68px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--brand-blue) 0%, var(--brand-purple) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(59,130,246,0.3);
}

.logo-icon svg {
  width: 22px;
  height: 22px;
  color: white;
}

.logo-title {
  font-weight: 700;
  font-size: 18px;
  color: var(--text-primary);
}

.logo-subtitle {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(59,130,246,0.15) 0%, rgba(139,92,246,0.08) 100%);
  color: var(--text-primary);
}

.nav-item svg {
  width: 20px;
  height: 20px;
}

.badge-ai {
  margin-left: auto;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 4px;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  color: white;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.version {
  font-size: 12px;
  color: var(--text-muted);
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}
</style>
