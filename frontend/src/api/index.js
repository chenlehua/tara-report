import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

// 图片上传
export async function uploadImage(file, imageType) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('image_type', imageType)
  
  const result = await api.post('/images/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  
  return {
    success: result.success,
    image_id: result.image_id,
    image_url: result.image_url,
    file: file
  }
}

// 批量上传JSON和图片文件，一键生成报告
export async function uploadAndGenerate(jsonFile, images = {}) {
  const formData = new FormData()
  formData.append('json_file', jsonFile)
  
  if (images.item_boundary) {
    formData.append('item_boundary_image', images.item_boundary)
  }
  if (images.system_architecture) {
    formData.append('system_architecture_image', images.system_architecture)
  }
  if (images.software_architecture) {
    formData.append('software_architecture_image', images.software_architecture)
  }
  if (images.dataflow) {
    formData.append('dataflow_image', images.dataflow)
  }
  
  // 添加攻击树图片
  if (images.attack_trees && images.attack_trees.length > 0) {
    images.attack_trees.forEach((file) => {
      formData.append('attack_tree_images', file)
    })
  }
  
  return api.post('/upload/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000 // 增加超时时间到2分钟
  })
}

// 生成报告
export async function generateReport(params) {
  const formData = new FormData()
  
  // 添加JSON数据
  if (params.jsonFile) {
    formData.append('json_file', params.jsonFile)
  } else if (params.jsonData) {
    formData.append('json_data', JSON.stringify(params.jsonData))
  }
  
  // 添加图片ID
  if (params.itemBoundaryImage) {
    formData.append('item_boundary_image', params.itemBoundaryImage)
  }
  if (params.systemArchitectureImage) {
    formData.append('system_architecture_image', params.systemArchitectureImage)
  }
  if (params.softwareArchitectureImage) {
    formData.append('software_architecture_image', params.softwareArchitectureImage)
  }
  if (params.dataflowImage) {
    formData.append('dataflow_image', params.dataflowImage)
  }
  if (params.attackTreeImages && params.attackTreeImages.length > 0) {
    formData.append('attack_tree_images', params.attackTreeImages.join(','))
  }
  
  return api.post('/reports/generate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 获取报告列表
export async function getReports() {
  return api.get('/reports')
}

// 获取报告详情
export async function getReport(reportId) {
  return api.get(`/reports/${reportId}`)
}

// 下载报告 (Excel)
export function getDownloadUrl(reportId) {
  return `/api/reports/${reportId}/download`
}

// 下载PDF报告
export function getPdfDownloadUrl(reportId) {
  return `/api/reports/${reportId}/download/pdf`
}

// 生成PDF报告
export async function generatePdf(reportId) {
  return api.post(`/reports/${reportId}/generate-pdf`)
}

// 删除报告
export async function deleteReport(reportId) {
  return api.delete(`/reports/${reportId}`)
}

// 获取图片URL
export function getImageUrl(imageId) {
  return `/api/images/${imageId}`
}

// 健康检查
export async function healthCheck() {
  return api.get('/health')
}

export default api
