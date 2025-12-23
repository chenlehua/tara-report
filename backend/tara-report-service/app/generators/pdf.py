"""
TARA PDF报告生成器
用于生成车载信息娱乐系统(IVI)的威胁分析和风险评估报告 (PDF格式)
"""
import os
import glob
import tempfile
from typing import Dict, Any, Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from PIL import Image as PILImage
from reportlab.platypus import Image


# ==================== 中文字体注册 ====================
FONT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')


def find_chinese_fonts():
    """查找系统中可用的中文字体"""
    font_candidates = []
    
    # Linux字体路径
    linux_fonts = [
        ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WenQuanYi', 0),
        ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 'WenQuanYiMicroHei', 0),
        ('/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc', 'WenQuanYi', 0),
        ('/usr/share/fonts/wqy-microhei/wqy-microhei.ttc', 'WenQuanYiMicroHei', 0),
        ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
        ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans', None),
    ]
    
    # Windows字体路径
    windows_fonts = [
        ('C:/Windows/Fonts/msyh.ttc', 'MicrosoftYaHei', 0),
        ('C:/Windows/Fonts/simsun.ttc', 'SimSun', 0),
        ('C:/Windows/Fonts/simhei.ttf', 'SimHei', None),
    ]
    
    # macOS字体路径
    mac_fonts = [
        ('/System/Library/Fonts/PingFang.ttc', 'PingFang', 0),
        ('/Library/Fonts/Songti.ttc', 'Songti', 0),
    ]
    
    font_candidates.extend(linux_fonts)
    font_candidates.extend(windows_fonts)
    font_candidates.extend(mac_fonts)
    
    # 检查本地缓存目录
    if os.path.exists(FONT_CACHE_DIR):
        for ttf_file in glob.glob(os.path.join(FONT_CACHE_DIR, '*.ttf')):
            font_name = os.path.splitext(os.path.basename(ttf_file))[0]
            font_candidates.append((ttf_file, font_name, None))
        for ttc_file in glob.glob(os.path.join(FONT_CACHE_DIR, '*.ttc')):
            font_name = os.path.splitext(os.path.basename(ttc_file))[0]
            font_candidates.append((ttc_file, font_name, 0))
    
    return font_candidates


def register_chinese_fonts():
    """注册中文字体"""
    registered_fonts = []
    font_candidates = find_chinese_fonts()
    
    for font_info in font_candidates:
        font_path, font_name = font_info[0], font_info[1]
        font_index = font_info[2] if len(font_info) > 2 else None
        
        if os.path.exists(font_path):
            try:
                if font_index is not None:
                    pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=font_index))
                else:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                registered_fonts.append(font_name)
                print(f"成功注册字体: {font_name}")
                if len(registered_fonts) >= 1:
                    break
            except Exception as e:
                print(f"注册字体失败 {font_name}: {e}")
    
    if not registered_fonts:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            registered_fonts.append('STSong-Light')
            print("使用内置CID字体: STSong-Light")
        except Exception:
            pass
    
    if not registered_fonts:
        return 'Helvetica'
    
    return registered_fonts[0]


# 注册字体
CHINESE_FONT = register_chinese_fonts()
CHINESE_FONT_BOLD = CHINESE_FONT


# ==================== 颜色定义 ====================
class TARAColors:
    """TARA报告颜色常量"""
    DARK_BLUE = colors.HexColor('#2F5496')
    MEDIUM_BLUE = colors.HexColor('#4472C4')
    LIGHT_BLUE = colors.HexColor('#8EA9DB')
    WHITE = colors.white
    BLACK = colors.black
    GRAY = colors.HexColor('#808080')
    LIGHT_GRAY = colors.HexColor('#F2F2F2')
    
    RISK_CRITICAL = colors.HexColor('#FF0000')
    RISK_HIGH = colors.HexColor('#FF6600')
    RISK_MEDIUM = colors.HexColor('#FFCC00')
    RISK_LOW = colors.HexColor('#92D050')
    RISK_QM = colors.HexColor('#00B050')


# ==================== 样式定义 ====================
def get_tara_styles():
    """获取TARA报告样式"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='TARATitle',
        fontName=CHINESE_FONT_BOLD,
        fontSize=18,
        textColor=TARAColors.DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=12,
        spaceBefore=6,
        leading=24
    ))
    
    styles.add(ParagraphStyle(
        name='TARASubTitle',
        fontName=CHINESE_FONT,
        fontSize=14,
        textColor=TARAColors.DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=8,
        leading=18
    ))
    
    styles.add(ParagraphStyle(
        name='TARABody',
        fontName=CHINESE_FONT,
        fontSize=10,
        textColor=TARAColors.BLACK,
        alignment=TA_LEFT,
        spaceBefore=4,
        spaceAfter=4,
        leading=14,
        firstLineIndent=0
    ))
    
    styles.add(ParagraphStyle(
        name='TARATableHeader',
        fontName=CHINESE_FONT_BOLD,
        fontSize=8,
        textColor=TARAColors.WHITE,
        alignment=TA_CENTER,
        leading=10
    ))
    
    styles.add(ParagraphStyle(
        name='TARACoverInfo',
        fontName=CHINESE_FONT,
        fontSize=11,
        textColor=TARAColors.BLACK,
        alignment=TA_LEFT,
        spaceBefore=4,
        spaceAfter=4,
        leading=16
    ))
    
    return styles


# ==================== 辅助函数 ====================
def safe_paragraph(text: str, style) -> Paragraph:
    """安全创建段落"""
    if text is None:
        text = ''
    text = str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('\n', '<br/>')
    return Paragraph(text, style)


def load_image_safe(image_path: str, max_width: float = 450, max_height: float = 300) -> Optional[Image]:
    """安全加载图片"""
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        with PILImage.open(image_path) as img:
            orig_width, orig_height = img.size
        
        width_ratio = max_width / orig_width
        height_ratio = max_height / orig_height
        ratio = min(width_ratio, height_ratio, 1.0)
        
        new_width = orig_width * ratio
        new_height = orig_height * ratio
        
        return Image(image_path, width=new_width, height=new_height)
    except Exception as e:
        print(f"Failed to load image {image_path}: {e}")
        return None


def create_section_header(title: str, styles) -> Table:
    """创建章节标题"""
    data = [[safe_paragraph(title, styles['TARATableHeader'])]]
    table = Table(data, colWidths=[500])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), TARAColors.DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, -1), TARAColors.WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def get_risk_color(risk_level: str) -> colors.Color:
    """根据风险等级返回对应颜色"""
    risk_colors = {
        'Critical': TARAColors.RISK_CRITICAL,
        'High': TARAColors.RISK_HIGH,
        'Medium': TARAColors.RISK_MEDIUM,
        'Low': TARAColors.RISK_LOW,
        'QM': TARAColors.RISK_QM,
    }
    return risk_colors.get(risk_level, TARAColors.GRAY)


# ==================== 计算函数 ====================
def calculate_attack_vector_value(attack_vector: str) -> float:
    values = {'网络': 0.85, '邻居': 0.62, '本地': 0.55, '物理': 0.2}
    return values.get(attack_vector, 0)


def calculate_attack_complexity_value(complexity: str) -> float:
    values = {'低': 0.77, '高': 0.44}
    return values.get(complexity, 0)


def calculate_privileges_value(privileges: str) -> float:
    values = {'无': 0.85, '低': 0.62, '高': 0.27}
    return values.get(privileges, 0)


def calculate_user_interaction_value(interaction: str) -> float:
    values = {'不需要': 0.85, '需要': 0.62}
    return values.get(interaction, 0)


def calculate_attack_feasibility(av: float, ac: float, pr: float, ui: float) -> tuple:
    calc_value = 8.22 * av * ac * pr * ui
    if calc_value <= 1.05:
        level = '很低'
    elif calc_value <= 1.99:
        level = '低'
    elif calc_value <= 2.99:
        level = '中'
    elif calc_value <= 3.99:
        level = '高'
    else:
        level = '很高'
    return round(calc_value, 2), level


def calculate_impact_value(impact: str) -> int:
    values = {'可忽略不计的': 0, '中等的': 1, '重大的': 10, '严重的': 1000}
    return values.get(impact, 0)


def calculate_impact_level(total: int) -> str:
    if total >= 1000:
        return '严重的'
    elif total >= 100:
        return '重大的'
    elif total >= 10:
        return '中等的'
    elif total >= 1:
        return '可忽略不计的'
    return '无影响'


def calculate_risk_level(impact_level: str, feasibility_level: str) -> str:
    if impact_level == '无影响' and feasibility_level == '无':
        return 'QM'
    low_conditions = [
        (impact_level == '无影响' and feasibility_level != '无'),
        (impact_level == '可忽略不计的' and feasibility_level in ['很低', '低', '中']),
        (impact_level == '中等的' and feasibility_level in ['很低', '低']),
        (impact_level == '重大的' and feasibility_level == '很低')
    ]
    if any(low_conditions):
        return 'Low'
    medium_conditions = [
        (impact_level == '可忽略不计的' and feasibility_level in ['高', '很高']),
        (impact_level == '中等的' and feasibility_level == '中'),
        (impact_level == '重大的' and feasibility_level == '低'),
        (impact_level == '严重的' and feasibility_level == '很低')
    ]
    if any(medium_conditions):
        return 'Medium'
    high_conditions = [
        (impact_level == '中等的' and feasibility_level in ['高', '很高']),
        (impact_level == '重大的' and feasibility_level == '中'),
        (impact_level == '严重的' and feasibility_level == '低')
    ]
    if any(high_conditions):
        return 'High'
    return 'Critical'


def get_risk_treatment(risk_level: str) -> str:
    if risk_level in ['QM', 'Low']:
        return '保留风险'
    elif risk_level == 'Medium':
        return '降低风险'
    return '降低风险/规避风险/转移风险'


def get_wp29_control(stride_model: str) -> str:
    mapping = {
        'T篡改': 'M10',
        'D拒绝服务': 'M13',
        'I信息泄露': 'M11',
        'S欺骗': 'M23',
        'R抵赖': 'M24',
        'E权限提升': 'M16'
    }
    return mapping.get(stride_model, '')


# ==================== 页面生成函数 ====================
def create_cover_page(data: Dict[str, Any], styles) -> List:
    """创建封面页"""
    elements = []
    elements.append(Spacer(1, 60))
    
    info_data = [
        [f"数据等级：{data.get('data_level', '秘密')}", ""],
        [f"编号：{data.get('document_number', '')}", ""],
        [f"版本：{data.get('version', '')}", ""],
    ]
    info_table = Table(info_data, colWidths=[300, 200])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 80))
    
    title = data.get('report_title', '威胁分析和风险评估报告')
    title_en = data.get('report_title_en', 'Threat Analysis And Risk Assessment Report')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Paragraph(title_en, styles['TARASubTitle']))
    elements.append(Spacer(1, 20))
    
    project_name = data.get('project_name', '')
    if project_name:
        elements.append(Paragraph(project_name, styles['TARATitle']))
    
    elements.append(Spacer(1, 100))
    
    sign_data = [
        ['编制/日期：', data.get('author_date', '')],
        ['审核/日期：', data.get('review_date', '')],
        ['会签/日期：', data.get('sign_date', '')],
        ['批准/日期：', data.get('approve_date', '')],
    ]
    sign_table = Table(sign_data, colWidths=[100, 150])
    sign_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sign_table)
    elements.append(PageBreak())
    return elements


def create_definitions_page(data: Dict[str, Any], styles) -> List:
    """创建相关定义页"""
    elements = []
    
    title = data.get('title', 'TARA分析报告 - 相关定义')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 12))
    
    elements.append(create_section_header('1. 功能描述 Functional Description', styles))
    elements.append(Spacer(1, 6))
    func_desc = data.get('functional_description', '')
    if func_desc:
        elements.append(Paragraph(func_desc, styles['TARABody']))
    elements.append(Spacer(1, 12))
    
    # 图片部分
    for section_num, section_name, image_key in [
        ('2', '项目边界 Item Boundary', 'item_boundary_image'),
        ('3', '系统架构图 System Architecture', 'system_architecture_image'),
        ('4', '软件架构图 Software Architecture', 'software_architecture_image'),
    ]:
        elements.append(create_section_header(f'{section_num}. {section_name}', styles))
        elements.append(Spacer(1, 6))
        img = load_image_safe(data.get(image_key, ''), max_width=480, max_height=280)
        if img:
            elements.append(img)
        else:
            elements.append(Paragraph(f'[{section_name}图]', styles['TARABody']))
        elements.append(Spacer(1, 12))
    
    # 假设
    elements.append(create_section_header('5. 相关项假设 Item Assumptions', styles))
    elements.append(Spacer(1, 6))
    assumptions = data.get('assumptions', [])
    if assumptions:
        header = ['假设编号', '假设描述']
        table_data = [header]
        for asm in assumptions:
            table_data.append([asm.get('id', ''), asm.get('description', '')])
        asm_table = Table(table_data, colWidths=[80, 420])
        asm_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(asm_table)
    elements.append(Spacer(1, 12))
    
    # 术语
    elements.append(create_section_header('6. 术语表 Terminology', styles))
    elements.append(Spacer(1, 6))
    terminology = data.get('terminology', [])
    if terminology:
        header = ['缩写', '英文全称', '中文全称']
        table_data = [header]
        for term in terminology:
            table_data.append([term.get('abbreviation', ''), term.get('english', ''), term.get('chinese', '')])
        term_table = Table(table_data, colWidths=[80, 220, 200])
        term_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
        ]))
        elements.append(term_table)
    
    elements.append(PageBreak())
    return elements


def create_assets_page(data: Dict[str, Any], styles) -> List:
    """创建资产列表页"""
    elements = []
    
    title = data.get('title', '资产列表 Asset List')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 12))
    
    assets = data.get('assets', [])
    if assets:
        header = ['资产ID', '资产名称', '分类', '备注', '真', '完', '不抵', '密', '可用', '权']
        table_data = [header]
        for asset in assets:
            remarks = asset.get('remarks', '')[:30] + '...' if len(asset.get('remarks', '')) > 30 else asset.get('remarks', '')
            table_data.append([
                asset.get('id', ''),
                asset.get('name', ''),
                asset.get('category', ''),
                remarks,
                '√' if asset.get('authenticity') else '',
                '√' if asset.get('integrity') else '',
                '√' if asset.get('non_repudiation') else '',
                '√' if asset.get('confidentiality') else '',
                '√' if asset.get('availability') else '',
                '√' if asset.get('authorization') else ''
            ])
        
        col_widths = [40, 60, 50, 120, 25, 25, 30, 25, 30, 25]
        asset_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        asset_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
        ]))
        elements.append(asset_table)
    
    # 数据流图
    elements.append(Spacer(1, 20))
    elements.append(create_section_header('数据流图 Data Flow Diagram', styles))
    elements.append(Spacer(1, 6))
    dataflow_img = load_image_safe(data.get('dataflow_image', ''), max_width=480, max_height=300)
    if dataflow_img:
        elements.append(dataflow_img)
    else:
        elements.append(Paragraph('[数据流图]', styles['TARABody']))
    
    elements.append(PageBreak())
    return elements


def create_attack_trees_page(data: Dict[str, Any], styles) -> List:
    """创建攻击树页"""
    elements = []
    
    title = data.get('title', '攻击树分析 Attack Tree Analysis')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 12))
    
    attack_trees = data.get('attack_trees', [])
    for i, tree in enumerate(attack_trees):
        tree_title = tree.get('title', f'攻击树 {i+1}')
        elements.append(create_section_header(tree_title, styles))
        elements.append(Spacer(1, 6))
        
        tree_img = load_image_safe(tree.get('image', ''), max_width=480, max_height=350)
        if tree_img:
            elements.append(tree_img)
        else:
            elements.append(Paragraph(f'[攻击树图: {tree_title}]', styles['TARABody']))
        elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    return elements


def create_tara_results_page(data: Dict[str, Any], styles) -> List:
    """创建TARA分析结果页"""
    elements = []
    
    title = data.get('title', 'TARA分析结果 TARA Analysis Results')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 8))
    
    results = data.get('results', [])
    if not results:
        elements.append(Paragraph('无分析结果', styles['TARABody']))
        return elements
    
    for idx, result in enumerate(results):
        threat_title = f"威胁 {idx+1}: {result.get('asset_name', '')} - {result.get('stride_model', '')}"
        elements.append(create_section_header(threat_title, styles))
        elements.append(Spacer(1, 4))
        
        # 基本信息
        basic_data = [
            ['资产ID', result.get('asset_id', ''), '资产名称', result.get('asset_name', '')],
            ['分类', result.get('category', ''), 'STRIDE模型', result.get('stride_model', '')],
        ]
        basic_table = Table(basic_data, colWidths=[60, 170, 60, 180])
        basic_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), TARAColors.LIGHT_BLUE),
            ('BACKGROUND', (2, 0), (2, -1), TARAColors.LIGHT_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
        ]))
        elements.append(basic_table)
        elements.append(Spacer(1, 4))
        
        # 威胁场景
        elements.append(Paragraph(f"<b>潜在威胁场景:</b> {result.get('threat_scenario', '')}", styles['TARABody']))
        
        # 计算风险
        av_value = calculate_attack_vector_value(result.get('attack_vector', '本地'))
        ac_value = calculate_attack_complexity_value(result.get('attack_complexity', '低'))
        pr_value = calculate_privileges_value(result.get('privileges_required', '低'))
        ui_value = calculate_user_interaction_value(result.get('user_interaction', '不需要'))
        _, feasibility_level = calculate_attack_feasibility(av_value, ac_value, pr_value, ui_value)
        
        safety_value = calculate_impact_value(result.get('safety_impact', '中等的'))
        financial_value = calculate_impact_value(result.get('financial_impact', '中等的'))
        operational_value = calculate_impact_value(result.get('operational_impact', '重大的'))
        privacy_value = calculate_impact_value(result.get('privacy_impact', '可忽略不计的'))
        impact_total = safety_value + financial_value + operational_value + privacy_value
        impact_level = calculate_impact_level(impact_total)
        
        risk_level = calculate_risk_level(impact_level, feasibility_level)
        risk_treatment = get_risk_treatment(risk_level)
        
        risk_data = [
            ['攻击可行性', feasibility_level, '影响等级', impact_level],
            ['风险等级', risk_level, '风险处置', risk_treatment],
        ]
        risk_table = Table(risk_data, colWidths=[80, 150, 80, 160])
        risk_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), TARAColors.LIGHT_BLUE),
            ('BACKGROUND', (2, 0), (2, -1), TARAColors.LIGHT_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(risk_table)
        elements.append(Spacer(1, 16))
        
        if (idx + 1) % 3 == 0 and idx < len(results) - 1:
            elements.append(PageBreak())
    
    return elements


def create_risk_summary_page(data: Dict[str, Any], styles) -> List:
    """创建风险汇总页"""
    elements = []
    
    elements.append(create_section_header('风险评估汇总 Risk Assessment Summary', styles))
    elements.append(Spacer(1, 12))
    
    results = data.get('results', [])
    if not results:
        elements.append(Paragraph('无分析结果', styles['TARABody']))
        return elements
    
    summary_header = ['序号', '资产', 'STRIDE', '风险等级', '风险处置']
    table_data = [summary_header]
    
    risk_stats = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'QM': 0}
    
    for idx, result in enumerate(results):
        av_value = calculate_attack_vector_value(result.get('attack_vector', '本地'))
        ac_value = calculate_attack_complexity_value(result.get('attack_complexity', '低'))
        pr_value = calculate_privileges_value(result.get('privileges_required', '低'))
        ui_value = calculate_user_interaction_value(result.get('user_interaction', '不需要'))
        _, feasibility_level = calculate_attack_feasibility(av_value, ac_value, pr_value, ui_value)
        
        safety_value = calculate_impact_value(result.get('safety_impact', '中等的'))
        financial_value = calculate_impact_value(result.get('financial_impact', '中等的'))
        operational_value = calculate_impact_value(result.get('operational_impact', '重大的'))
        privacy_value = calculate_impact_value(result.get('privacy_impact', '可忽略不计的'))
        impact_total = safety_value + financial_value + operational_value + privacy_value
        impact_level = calculate_impact_level(impact_total)
        
        risk_level = calculate_risk_level(impact_level, feasibility_level)
        risk_treatment = get_risk_treatment(risk_level)
        
        risk_stats[risk_level] = risk_stats.get(risk_level, 0) + 1
        
        table_data.append([
            str(idx + 1),
            result.get('asset_name', ''),
            result.get('stride_model', ''),
            risk_level,
            risk_treatment[:10]
        ])
    
    col_widths = [30, 100, 60, 60, 100]
    summary_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TARAColors.DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
    ]))
    elements.append(summary_table)
    
    # 统计
    elements.append(Spacer(1, 20))
    elements.append(Paragraph('<b>风险统计</b>', styles['TARABody']))
    stats_data = [
        ['风险等级', 'Critical', 'High', 'Medium', 'Low', 'QM', '合计'],
        ['数量', str(risk_stats['Critical']), str(risk_stats['High']),
         str(risk_stats['Medium']), str(risk_stats['Low']), str(risk_stats['QM']),
         str(sum(risk_stats.values()))]
    ]
    stats_table = Table(stats_data, colWidths=[60, 60, 60, 60, 60, 60, 60])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
    ]))
    elements.append(stats_table)
    
    return elements


# ==================== 主生成函数 ====================
def generate_tara_pdf(
    output_path: str,
    cover_data: Dict[str, Any],
    definitions_data: Dict[str, Any],
    assets_data: Dict[str, Any],
    attack_trees_data: Dict[str, Any],
    tara_results_data: Dict[str, Any]
) -> str:
    """生成TARA分析报告PDF文件"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    styles = get_tara_styles()
    elements = []
    
    elements.extend(create_cover_page(cover_data, styles))
    elements.extend(create_definitions_page(definitions_data, styles))
    elements.extend(create_assets_page(assets_data, styles))
    
    if attack_trees_data.get('attack_trees'):
        elements.extend(create_attack_trees_page(attack_trees_data, styles))
    
    elements.extend(create_tara_results_page(tara_results_data, styles))
    elements.append(PageBreak())
    elements.extend(create_risk_summary_page(tara_results_data, styles))
    
    doc.build(elements)
    return output_path


def generate_tara_pdf_from_json(
    output_path: str,
    json_data: Dict[str, Any]
) -> str:
    """从JSON数据生成TARA分析报告PDF文件"""
    return generate_tara_pdf(
        output_path=output_path,
        cover_data=json_data.get('cover', {}),
        definitions_data=json_data.get('definitions', {}),
        assets_data=json_data.get('assets', {}),
        attack_trees_data=json_data.get('attack_trees', {}),
        tara_results_data=json_data.get('tara_results', {})
    )
