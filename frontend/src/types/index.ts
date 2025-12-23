// TARA Report Types

export interface CoverData {
  project_name: string
  document_number: string
  version: string
  data_level: string
  applicability: string
  prepared_by: string
  prepared_date: string
  reviewed_by: string
  reviewed_date: string
  approved_by: string
  approved_date: string
}

export interface DefinitionsData {
  functional_description: string
  item_boundary_image?: string
  system_architecture_image?: string
  software_architecture_image?: string
  assumptions: string[]
  terminology: Array<{ term: string; definition: string }>
}

export interface Asset {
  id: string
  name: string
  category: string
  remarks: string
  authenticity: boolean
  integrity: boolean
  availability: boolean
  confidentiality: boolean
}

export interface AssetsData {
  dataflow_image?: string
  assets: Asset[]
}

export interface AttackTree {
  asset_id: string
  asset_name: string
  attack_tree_image: string
}

export interface AttackTreesData {
  attack_trees: AttackTree[]
}

export interface TaraResult {
  asset_id: string
  asset_name: string
  stride_model: string
  threat_id: string
  threat_scenario: string
  damage_scenario: string
  attack_path: string
  attack_vector: string
  attack_complexity: string
  privilege_required: string
  user_interaction: string
  safety_impact: number
  financial_impact: number
  operational_impact: number
  privacy_impact: number
  security_measure: string
  effectiveness: string
  security_goal: string
  residual_risk: string
}

export interface TARAResultsData {
  results: TaraResult[]
}

export interface ReportInputData {
  cover: CoverData
  definitions: DefinitionsData
  assets: AssetsData
  attack_trees: AttackTreesData
  tara_results: TARAResultsData
}

export interface Statistics {
  total_assets: number
  total_threats: number
  high_risk_count: number
  risk_distribution: Record<string, number>
  stride_distribution: Record<string, number>
}

export interface ReportInfo {
  id: string
  name: string
  version: string
  created_at: string
  file_path: string
  file_size: number
  statistics: Statistics
}

export interface PreviewData {
  report_info: {
    id: string
    name: string
    version: string
    created_at: string
    file_path: string
    file_size: number
    statistics: Statistics
  }
  cover: CoverData
  definitions: DefinitionsData & {
    item_boundary_image?: string
    system_architecture_image?: string
    software_architecture_image?: string
  }
  assets: Asset[]
  dataflow_image?: string
  attack_trees: AttackTree[]
  tara_results: TaraResult[]
  statistics: Statistics
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}
