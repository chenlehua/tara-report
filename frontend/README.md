# TARA Report Frontend

TARA威胁分析和风险评估报告生成系统前端。

## 功能特性

- 📁 JSON文件上传和预览
- 🖼️ 架构图片上传（项目边界图、系统架构图、软件架构图、数据流图）
- 🚀 一键生成TARA报告
- 📊 报告中心管理
- 👁️ 报告预览（包含图片展示）
- ⬇️ 报告下载

## 技术栈

- Vue 3 + Composition API
- Vue Router 4
- Pinia
- Vite 5
- Tailwind CSS
- Axios

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

开发服务器将在 http://localhost:3000 启动。

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录。

## 项目结构

```
frontend/
├── index.html              # HTML入口
├── vite.config.js          # Vite配置
├── tailwind.config.js      # Tailwind配置
├── package.json            # 项目配置
├── src/
│   ├── main.js             # 应用入口
│   ├── App.vue             # 根组件
│   ├── api/
│   │   └── index.js        # API服务
│   ├── assets/
│   │   └── main.css        # 全局样式
│   ├── components/
│   │   └── ImageUploader.vue   # 图片上传组件
│   └── views/
│       ├── GeneratorView.vue   # 生成报告页面
│       ├── ReportsView.vue     # 报告列表页面
│       └── ReportDetailView.vue # 报告详情页面
└── README.md
```

## 页面说明

### 一键生成报告 (`/generator`)

1. 上传JSON数据文件（必需）
2. 上传相关图片（可选）
   - 项目边界图
   - 系统架构图
   - 软件架构图
   - 数据流图
3. 点击"一键生成TARA报告"
4. 查看生成结果并下载

### 报告中心 (`/reports`)

- 查看所有已生成的报告列表
- 预览报告内容
- 下载报告文件
- 删除报告

### 报告详情 (`/reports/:id`)

- 查看报告统计信息
- 预览架构图片
- 查看资产列表
- 查看威胁分析结果
- 下载报告

## API配置

前端通过Vite代理与后端API通信，代理配置在 `vite.config.js`:

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 开发说明

### 添加新页面

1. 在 `src/views/` 创建新的Vue组件
2. 在 `src/main.js` 中添加路由配置

### 添加新组件

在 `src/components/` 创建可复用的组件

### 修改样式

- 全局样式: `src/assets/main.css`
- 组件样式: 在Vue组件的 `<style scoped>` 中
- Tailwind类: 直接在模板中使用

## License

MIT License
