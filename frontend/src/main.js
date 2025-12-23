import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from './App.vue'
import './assets/main.css'

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/generator'
  },
  {
    path: '/generator',
    name: 'Generator',
    component: () => import('./views/GeneratorView.vue')
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('./views/ReportsView.vue')
  },
  {
    path: '/reports/:id',
    name: 'ReportDetail',
    component: () => import('./views/ReportDetailView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const pinia = createPinia()
const app = createApp(App)

app.use(router)
app.use(pinia)
app.mount('#app')
