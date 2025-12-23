import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ReportInfo, PreviewData } from '@/types'
import * as api from '@/api'

export const useReportStore = defineStore('report', () => {
  // State
  const reports = ref<ReportInfo[]>([])
  const currentReport = ref<ReportInfo | null>(null)
  const previewData = ref<PreviewData | null>(null)
  const loading = ref(false)
  const generating = ref(false)
  const total = ref(0)

  // Actions
  async function fetchReports(page = 1, limit = 10) {
    loading.value = true
    try {
      const result = await api.getReports(page, limit)
      reports.value = result.items
      total.value = result.total
    } catch (error) {
      console.error('Failed to fetch reports:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function generateReport(
    jsonFile: File,
    images?: {
      item_boundary_image?: File
      system_architecture_image?: File
      software_architecture_image?: File
      dataflow_image?: File
      attack_tree_images?: File[]
    }
  ): Promise<{ success: boolean; message: string; report_info?: ReportInfo }> {
    generating.value = true
    try {
      const result = await api.uploadAndGenerate(jsonFile, {
        item_boundary: images?.item_boundary_image,
        system_architecture: images?.system_architecture_image,
        software_architecture: images?.software_architecture_image,
        dataflow: images?.dataflow_image,
        attack_trees: images?.attack_tree_images
      })
      if (result.success && result.report_info) {
        currentReport.value = result.report_info
        // 刷新列表
        await fetchReports()
      }
      return result
    } catch (error: any) {
      console.error('Failed to generate report:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || error.message || '报告生成失败' 
      }
    } finally {
      generating.value = false
    }
  }

  async function uploadAndGenerate(
    jsonFile: File,
    images?: {
      item_boundary?: File
      system_architecture?: File
      software_architecture?: File
      dataflow?: File
    }
  ): Promise<ReportInfo> {
    generating.value = true
    try {
      const report = await api.uploadAndGenerate(jsonFile, images)
      currentReport.value = report
      // 刷新列表
      await fetchReports()
      return report
    } catch (error) {
      console.error('Failed to upload and generate:', error)
      throw error
    } finally {
      generating.value = false
    }
  }

  async function fetchPreview(reportId: string) {
    loading.value = true
    try {
      previewData.value = await api.getReportPreview(reportId)
    } catch (error) {
      console.error('Failed to fetch preview:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function downloadReport(reportId: string, filename: string) {
    try {
      const blob = await api.downloadReport(reportId)
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download report:', error)
      throw error
    }
  }

  async function deleteReport(reportId: string) {
    try {
      await api.deleteReport(reportId)
      // 刷新列表
      await fetchReports()
    } catch (error) {
      console.error('Failed to delete report:', error)
      throw error
    }
  }

  function clearPreview() {
    previewData.value = null
  }

  function clearCurrent() {
    currentReport.value = null
  }

  return {
    // State
    reports,
    currentReport,
    previewData,
    loading,
    generating,
    total,
    // Actions
    fetchReports,
    generateReport,
    uploadAndGenerate,
    fetchPreview,
    downloadReport,
    deleteReport,
    clearPreview,
    clearCurrent
  }
})
