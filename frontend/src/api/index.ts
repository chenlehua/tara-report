import axios from 'axios'
import type { ReportInfo, PreviewData, ApiResponse } from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000, // 增加超时时间到2分钟
  headers: {
    'Content-Type': 'application/json'
  },
  maxContentLength: Infinity,
  maxBodyLength: Infinity
})

// 获取报告列表
export async function getReports(page = 1, limit = 10): Promise<{ success: boolean; reports: ReportInfo[]; total: number }> {
  const response = await api.get('/reports', { params: { page, page_size: limit } })
  // 返回后端原始格式 { success, reports, total, page, page_size }
  return response.data
}

// 生成报告 (JSON数据)
export async function generateReport(data: any): Promise<ReportInfo> {
  const response = await api.post('/reports/generate', data)
  return response.data
}

// 上传JSON文件和图片批量生成
export async function uploadAndGenerate(
  jsonFile: File,
  images?: {
    item_boundary?: File
    system_architecture?: File
    software_architecture?: File
    dataflow?: File
    attack_trees?: File[]
  }
): Promise<{ success: boolean; message: string; report_info: ReportInfo }> {
  const formData = new FormData()
  formData.append('json_file', jsonFile)
  
  if (images?.item_boundary) {
    formData.append('item_boundary_image', images.item_boundary)
  }
  if (images?.system_architecture) {
    formData.append('system_architecture_image', images.system_architecture)
  }
  if (images?.software_architecture) {
    formData.append('software_architecture_image', images.software_architecture)
  }
  if (images?.dataflow) {
    formData.append('dataflow_image', images.dataflow)
  }
  
  // 添加攻击树图片
  if (images?.attack_trees && images.attack_trees.length > 0) {
    images.attack_trees.forEach((file) => {
      formData.append('attack_tree_images', file)
    })
  }
  
  const response = await api.post('/upload/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000 // 增加超时时间到2分钟
  })
  return response.data
}

// 获取报告预览数据
export async function getReportPreview(reportId: string): Promise<PreviewData> {
  const response = await api.get(`/reports/${reportId}/preview`)
  return response.data
}

// 下载报告
export async function downloadReport(reportId: string): Promise<Blob> {
  const response = await api.get(`/reports/${reportId}/download`, {
    responseType: 'blob'
  })
  return response.data
}

// 下载PDF报告
export async function downloadPdfReport(reportId: string): Promise<Blob> {
  const response = await api.get(`/reports/${reportId}/download/pdf`, {
    responseType: 'blob'
  })
  return response.data
}

// 获取Excel下载URL
export function getDownloadUrl(reportId: string): string {
  return `/api/v1/reports/${reportId}/download`
}

// 获取PDF下载URL
export function getPdfDownloadUrl(reportId: string): string {
  return `/api/v1/reports/${reportId}/download/pdf`
}

// 生成PDF报告
export async function generatePdf(reportId: string): Promise<{ success: boolean; download_url: string }> {
  const response = await api.post(`/reports/${reportId}/generate-pdf`)
  return response.data
}

// 删除报告
export async function deleteReport(reportId: string): Promise<void> {
  await api.delete(`/reports/${reportId}`)
}

// 上传单个图片
export async function uploadImage(file: File, type: string): Promise<{ filename: string; url: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)
  
  const response = await api.post('/images/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

// 获取图片URL
export function getImageUrl(filename: string): string {
  return `/api/v1/images/${filename}`
}

export default api
