"""
TARA calculation utilities
TARA分析计算工具

This module contains all the calculation functions for TARA analysis derived columns,
including attack feasibility, impact level, risk level, and other derived values.
"""
from typing import Dict, Any, Optional

# ==================== Attack Feasibility Calculations ====================

# 攻击向量指标值映射 (M列)
ATTACK_VECTOR_VALUES = {
    '网络': 0.85,
    '邻居': 0.62,
    '本地': 0.55,
    '物理': 0.2
}

# 攻击复杂度指标值映射 (O列)
ATTACK_COMPLEXITY_VALUES = {
    '低': 0.77,
    '高': 0.44
}

# 权限要求指标值映射 (Q列)
PRIVILEGES_REQUIRED_VALUES = {
    '无': 0.85,
    '低': 0.62,
    '高': 0.27
}

# 用户交互指标值映射 (S列)
USER_INTERACTION_VALUES = {
    '不需要': 0.85,
    '需要': 0.62
}

# 影响值映射 (X/AA/AD/AG列)
IMPACT_VALUES = {
    '可忽略不计的': 0,
    '中等的': 1,
    '重大的': 10,
    '严重的': 1000
}

# 影响注释映射
SAFETY_NOTES = {
    '可忽略不计的': '没有受伤',
    '中等的': '轻伤和中等伤害',
    '重大的': '严重伤害(生存概率高)',
    '严重的': '危及生命(生存概率不确定)或致命伤害'
}

FINANCIAL_NOTES = {
    '可忽略不计的': '财务损失不会产生任何影响',
    '中等的': '财务损失会产生中等影响',
    '重大的': '财务损失会产生重大影响',
    '严重的': '财务损失会产生严重影响'
}

OPERATIONAL_NOTES = {
    '可忽略不计的': '操作损坏不会导致车辆功能减少',
    '中等的': '操作损坏会导致车辆功能中等减少',
    '重大的': '操作损坏会导致车辆功能重大减少',
    '严重的': '操作损坏会导致车辆功能丧失'
}

PRIVACY_NOTES = {
    '可忽略不计的': '隐私危害不会产生任何影响',
    '中等的': '隐私危害会产生中等影响',
    '重大的': '隐私危害会产生重大影响',
    '严重的': '隐私危害会产生严重影响'
}

# WP29控制映射
WP29_CONTROL_MAPPING = {
    'T篡改': 'M10',
    'D拒绝服务': 'M13',
    'I信息泄露': 'M11',
    'S欺骗': 'M23',
    'R抵赖': 'M24',
    'E权限提升': 'M16'
}


def calc_attack_vector_value(attack_vector: Optional[str]) -> float:
    """
    计算攻击向量指标值 (M列)
    
    Args:
        attack_vector: 攻击向量 (网络/邻居/本地/物理)
    
    Returns:
        指标值
    """
    if not attack_vector:
        return 0.0
    return ATTACK_VECTOR_VALUES.get(attack_vector, 0.0)


def calc_attack_complexity_value(attack_complexity: Optional[str]) -> float:
    """
    计算攻击复杂度指标值 (O列)
    
    Args:
        attack_complexity: 攻击复杂度 (低/高)
    
    Returns:
        指标值
    """
    if not attack_complexity:
        return 0.0
    return ATTACK_COMPLEXITY_VALUES.get(attack_complexity, 0.0)


def calc_privileges_value(privileges_required: Optional[str]) -> float:
    """
    计算权限要求指标值 (Q列)
    
    Args:
        privileges_required: 权限要求 (无/低/高)
    
    Returns:
        指标值
    """
    if not privileges_required:
        return 0.0
    return PRIVILEGES_REQUIRED_VALUES.get(privileges_required, 0.0)


def calc_user_interaction_value(user_interaction: Optional[str]) -> float:
    """
    计算用户交互指标值 (S列)
    
    Args:
        user_interaction: 用户交互 (不需要/需要)
    
    Returns:
        指标值
    """
    if not user_interaction:
        return 0.0
    return USER_INTERACTION_VALUES.get(user_interaction, 0.0)


def calc_attack_feasibility_value(
    attack_vector: Optional[str],
    attack_complexity: Optional[str],
    privileges_required: Optional[str],
    user_interaction: Optional[str]
) -> float:
    """
    计算攻击可行性计算值 (T列)
    
    公式: 8.22 × 攻击向量值 × 攻击复杂度值 × 权限要求值 × 用户交互值
    
    Args:
        attack_vector: 攻击向量
        attack_complexity: 攻击复杂度
        privileges_required: 权限要求
        user_interaction: 用户交互
    
    Returns:
        攻击可行性计算值
    """
    av = calc_attack_vector_value(attack_vector)
    ac = calc_attack_complexity_value(attack_complexity)
    pr = calc_privileges_value(privileges_required)
    ui = calc_user_interaction_value(user_interaction)
    
    return round(8.22 * av * ac * pr * ui, 2)


def calc_attack_feasibility_level(feasibility_value: float) -> str:
    """
    计算攻击可行性等级 (U列)
    
    Args:
        feasibility_value: 攻击可行性计算值
    
    Returns:
        攻击可行性等级 (很低/低/中/高/很高)
    """
    if feasibility_value <= 1.05:
        return '很低'
    elif feasibility_value <= 1.99:
        return '低'
    elif feasibility_value <= 2.99:
        return '中'
    elif feasibility_value <= 3.99:
        return '高'
    else:
        return '很高'


# ==================== Impact Calculations ====================

def calc_impact_value(impact: Optional[str]) -> int:
    """
    计算影响指标值 (X/AA/AD/AG列)
    
    Args:
        impact: 影响等级 (可忽略不计的/中等的/重大的/严重的)
    
    Returns:
        影响指标值
    """
    if not impact:
        return 0
    return IMPACT_VALUES.get(impact, 0)


def calc_total_impact_value(
    safety_impact: Optional[str],
    financial_impact: Optional[str],
    operational_impact: Optional[str],
    privacy_impact: Optional[str]
) -> int:
    """
    计算影响总计算值 (AH列)
    
    公式: 安全指标值 + 经济指标值 + 操作指标值 + 隐私指标值
    
    Args:
        safety_impact: 安全影响
        financial_impact: 经济影响
        operational_impact: 操作影响
        privacy_impact: 隐私影响
    
    Returns:
        影响总计算值
    """
    safety = calc_impact_value(safety_impact)
    financial = calc_impact_value(financial_impact)
    operational = calc_impact_value(operational_impact)
    privacy = calc_impact_value(privacy_impact)
    
    return safety + financial + operational + privacy


def calc_impact_level(total_impact_value: int) -> str:
    """
    计算影响等级 (AI列)
    
    Args:
        total_impact_value: 影响总计算值
    
    Returns:
        影响等级
    """
    if total_impact_value >= 1000:
        return '严重的'
    elif total_impact_value >= 100:
        return '重大的'
    elif total_impact_value >= 10:
        return '中等的'
    elif total_impact_value >= 1:
        return '可忽略不计的'
    else:
        return '无影响'


# ==================== Risk Assessment Calculations ====================

def calc_risk_level(impact_level: str, feasibility_level: str) -> str:
    """
    计算风险等级 (AJ列)
    
    Args:
        impact_level: 影响等级
        feasibility_level: 攻击可行性等级
    
    Returns:
        风险等级 (QM/Low/Medium/High/Critical)
    """
    # QM条件
    if impact_level == '无影响' and feasibility_level == '无':
        return 'QM'
    
    # Low条件
    if impact_level == '无影响' and feasibility_level != '无':
        return 'Low'
    if impact_level == '可忽略不计的' and feasibility_level in ['很低', '低', '中']:
        return 'Low'
    if impact_level == '中等的' and feasibility_level in ['很低', '低']:
        return 'Low'
    if impact_level == '重大的' and feasibility_level == '很低':
        return 'Low'
    
    # Medium条件
    if impact_level == '可忽略不计的' and feasibility_level in ['高', '很高']:
        return 'Medium'
    if impact_level == '中等的' and feasibility_level == '中':
        return 'Medium'
    if impact_level == '重大的' and feasibility_level == '低':
        return 'Medium'
    if impact_level == '严重的' and feasibility_level == '很低':
        return 'Medium'
    
    # High条件
    if impact_level == '中等的' and feasibility_level in ['高', '很高']:
        return 'High'
    if impact_level == '重大的' and feasibility_level == '中':
        return 'High'
    if impact_level == '严重的' and feasibility_level == '低':
        return 'High'
    
    # Critical条件
    return 'Critical'


def calc_risk_treatment(risk_level: str) -> str:
    """
    计算风险处置决策 (AK列)
    
    Args:
        risk_level: 风险等级
    
    Returns:
        风险处置决策
    """
    if risk_level in ['QM', 'Low']:
        return '保留风险'
    elif risk_level == 'Medium':
        return '降低风险'
    else:
        return '降低风险/规避风险/转移风险'


def calc_security_goal(risk_treatment: str, security_goal: Optional[str] = None) -> str:
    """
    计算安全目标 (AL列)
    
    Args:
        risk_treatment: 风险处置决策
        security_goal: 原有安全目标（如果有）
    
    Returns:
        安全目标
    """
    if risk_treatment == '保留风险':
        return '/'
    # 如果有原始安全目标，返回原始值；否则返回默认值
    if security_goal and security_goal.strip():
        return security_goal
    return '需要定义安全目标'


def calc_wp29_control_mapping(stride_model: Optional[str]) -> str:
    """
    计算WP29控制映射 (AN列)
    
    Args:
        stride_model: STRIDE模型
    
    Returns:
        WP29控制映射
    """
    if not stride_model:
        return '-'
    return WP29_CONTROL_MAPPING.get(stride_model, '-')


def get_safety_note(safety_impact: Optional[str]) -> str:
    """获取安全影响注释"""
    if not safety_impact:
        return '-'
    return SAFETY_NOTES.get(safety_impact, '-')


def get_financial_note(financial_impact: Optional[str]) -> str:
    """获取经济影响注释"""
    if not financial_impact:
        return '-'
    return FINANCIAL_NOTES.get(financial_impact, '-')


def get_operational_note(operational_impact: Optional[str]) -> str:
    """获取操作影响注释"""
    if not operational_impact:
        return '-'
    return OPERATIONAL_NOTES.get(operational_impact, '-')


def get_privacy_note(privacy_impact: Optional[str]) -> str:
    """获取隐私影响注释"""
    if not privacy_impact:
        return '-'
    return PRIVACY_NOTES.get(privacy_impact, '-')


def calculate_tara_derived_columns(tara_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算TARA结果的所有派生列
    
    Args:
        tara_result: TARA结果数据字典
    
    Returns:
        包含派生列的TARA结果数据字典
    """
    # 提取原始数据
    attack_vector = tara_result.get('attack_vector')
    attack_complexity = tara_result.get('attack_complexity')
    privileges_required = tara_result.get('privileges_required')
    user_interaction = tara_result.get('user_interaction')
    
    safety_impact = tara_result.get('safety_impact')
    financial_impact = tara_result.get('financial_impact')
    operational_impact = tara_result.get('operational_impact')
    privacy_impact = tara_result.get('privacy_impact')
    
    stride_model = tara_result.get('stride_model')
    original_security_goal = tara_result.get('security_goal')
    
    # 攻击可行性计算
    attack_vector_value = calc_attack_vector_value(attack_vector)
    attack_complexity_value = calc_attack_complexity_value(attack_complexity)
    privileges_required_value = calc_privileges_value(privileges_required)
    user_interaction_value = calc_user_interaction_value(user_interaction)
    attack_feasibility_value = calc_attack_feasibility_value(
        attack_vector, attack_complexity, privileges_required, user_interaction
    )
    attack_feasibility_level = calc_attack_feasibility_level(attack_feasibility_value)
    
    # 影响计算
    safety_impact_value = calc_impact_value(safety_impact)
    financial_impact_value = calc_impact_value(financial_impact)
    operational_impact_value = calc_impact_value(operational_impact)
    privacy_impact_value = calc_impact_value(privacy_impact)
    total_impact_value = calc_total_impact_value(
        safety_impact, financial_impact, operational_impact, privacy_impact
    )
    impact_level = calc_impact_level(total_impact_value)
    
    # 风险评估
    risk_level = calc_risk_level(impact_level, attack_feasibility_level)
    risk_treatment = calc_risk_treatment(risk_level)
    security_goal = calc_security_goal(risk_treatment, original_security_goal)
    wp29_control_mapping = calc_wp29_control_mapping(stride_model)
    
    # 影响注释
    safety_note = get_safety_note(safety_impact)
    financial_note = get_financial_note(financial_impact)
    operational_note = get_operational_note(operational_impact)
    privacy_note = get_privacy_note(privacy_impact)
    
    # 构建结果（保留原有字段，添加计算字段）
    result = dict(tara_result)
    
    # 添加攻击可行性计算字段
    result['attack_vector_value'] = attack_vector_value
    result['attack_complexity_value'] = attack_complexity_value
    result['privileges_required_value'] = privileges_required_value
    result['user_interaction_value'] = user_interaction_value
    result['attack_feasibility_value'] = attack_feasibility_value
    result['attack_feasibility_level'] = attack_feasibility_level
    
    # 添加影响计算字段
    result['safety_impact_value'] = safety_impact_value
    result['financial_impact_value'] = financial_impact_value
    result['operational_impact_value'] = operational_impact_value
    result['privacy_impact_value'] = privacy_impact_value
    result['total_impact_value'] = total_impact_value
    result['impact_level'] = impact_level
    
    # 添加影响注释字段
    result['safety_note'] = safety_note
    result['financial_note'] = financial_note
    result['operational_note'] = operational_note
    result['privacy_note'] = privacy_note
    
    # 添加风险评估字段
    result['risk_level'] = risk_level
    result['risk_treatment'] = risk_treatment
    result['calculated_security_goal'] = security_goal
    result['wp29_control_mapping'] = wp29_control_mapping
    
    return result
