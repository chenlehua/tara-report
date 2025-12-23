"""
TARA PDF报告生成器
用于生成车载信息娱乐系统(IVI)的威胁分析和风险评估报告 (PDF格式)
与Excel报告保持内容一致
"""

import os
from typing import Dict, List, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.graphics.shapes import Drawing, Line
from PIL import Image as PILImage


# ==================== 中文字体注册 ====================
import urllib.request
import tempfile
import glob

# 字体目录（用于存放下载的字体）
FONT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')

def find_chinese_fonts():
    """
    查找系统中可用的中文字体
    返回: [(font_path, font_name, subfont_index), ...]
    """
    font_candidates = []
    
    # Windows字体路径
    windows_fonts = [
        ('C:/Windows/Fonts/msyh.ttc', 'MicrosoftYaHei', 0),       # 微软雅黑
        ('C:/Windows/Fonts/msyhbd.ttc', 'MicrosoftYaHeiBold', 0), # 微软雅黑粗体
        ('C:/Windows/Fonts/simsun.ttc', 'SimSun', 0),             # 宋体
        ('C:/Windows/Fonts/simhei.ttf', 'SimHei', None),          # 黑体
        ('C:/Windows/Fonts/simkai.ttf', 'KaiTi', None),           # 楷体
        ('C:/Windows/Fonts/STKAITI.TTF', 'STKaiti', None),        # 华文楷体
        ('C:/Windows/Fonts/STSONG.TTF', 'STSong', None),          # 华文宋体
        ('C:/Windows/Fonts/STFANGSO.TTF', 'STFangsong', None),    # 华文仿宋
    ]
    
    # macOS字体路径
    mac_fonts = [
        ('/System/Library/Fonts/PingFang.ttc', 'PingFang', 0),                      # 苹方
        ('/System/Library/Fonts/STHeiti Light.ttc', 'STHeitiLight', 0),             # 华文黑体
        ('/System/Library/Fonts/STHeiti Medium.ttc', 'STHeitiMedium', 0),           # 华文黑体中等
        ('/Library/Fonts/Songti.ttc', 'Songti', 0),                                  # 宋体
        ('/Library/Fonts/Kaiti.ttc', 'Kaiti', 0),                                    # 楷体
        ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 'ArialUnicode', None),
        ('/Library/Fonts/Arial Unicode.ttf', 'ArialUnicode', None),
    ]
    
    # Linux字体路径
    linux_fonts = [
        # 文泉驿字体
        ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WenQuanYi', 0),
        ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 'WenQuanYiMicroHei', 0),
        ('/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc', 'WenQuanYi', 0),
        ('/usr/share/fonts/wqy-microhei/wqy-microhei.ttc', 'WenQuanYiMicroHei', 0),
        # Noto字体
        ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
        ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
        ('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
        ('/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
        # 思源字体
        ('/usr/share/fonts/adobe-source-han-sans/SourceHanSansCN-Regular.otf', 'SourceHanSans', None),
        ('/usr/share/fonts/truetype/source-han-sans/SourceHanSansCN-Regular.otf', 'SourceHanSans', None),
        # AR PL 字体
        ('/usr/share/fonts/truetype/arphic/uming.ttc', 'ARPLUMing', 0),
        ('/usr/share/fonts/truetype/arphic/ukai.ttc', 'ARPLUKai', 0),
        # DejaVu (作为最后的备选)
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans', None),
    ]
    
    # 合并所有候选字体
    font_candidates.extend(windows_fonts)
    font_candidates.extend(mac_fonts)
    font_candidates.extend(linux_fonts)
    
    # 检查本地缓存目录
    if os.path.exists(FONT_CACHE_DIR):
        for ttf_file in glob.glob(os.path.join(FONT_CACHE_DIR, '*.ttf')):
            font_name = os.path.splitext(os.path.basename(ttf_file))[0]
            font_candidates.append((ttf_file, font_name, None))
        for ttc_file in glob.glob(os.path.join(FONT_CACHE_DIR, '*.ttc')):
            font_name = os.path.splitext(os.path.basename(ttc_file))[0]
            font_candidates.append((ttc_file, font_name, 0))
    
    return font_candidates


def download_noto_font():
    """
    下载 Noto Sans SC 字体（开源中文字体）
    返回: 字体文件路径，如果下载失败返回None
    """
    # 创建字体缓存目录
    os.makedirs(FONT_CACHE_DIR, exist_ok=True)
    
    font_path = os.path.join(FONT_CACHE_DIR, 'NotoSansSC-Regular.ttf')
    
    # 如果已经下载过，直接返回
    if os.path.exists(font_path):
        return font_path
    
    # Noto Sans SC 下载链接（Google Fonts）
    font_urls = [
        'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf',
        'https://github.com/notofonts/noto-cjk/releases/download/Sans2.004/03_NotoSansCJKsc-OTF.zip',
    ]
    
    print("尝试下载中文字体...")
    # 注意：由于网络限制，这里只是预留接口，实际下载可能不可用
    # 用户应该手动将中文字体放到 fonts 目录
    
    return None


def register_chinese_fonts():
    """
    注册中文字体，解决乱码问题
    优先级：系统字体 > 本地缓存字体 > CID字体
    """
    registered_fonts = []
    registered_bold = None
    
    # 1. 尝试注册系统字体
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
                print(f"成功注册字体: {font_name} ({font_path})")
                
                # 只需要注册一个即可
                if len(registered_fonts) >= 1:
                    break
            except Exception as e:
                print(f"注册字体失败 {font_name}: {e}")
    
    # 2. 如果没有找到系统字体，尝试使用CID字体
    if not registered_fonts:
        try:
            # STSong-Light 是 reportlab 内置的 CID 字体，支持中文
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            registered_fonts.append('STSong-Light')
            print("使用内置CID字体: STSong-Light")
        except Exception as e:
            print(f"注册CID字体失败: {e}")
    
    # 3. 如果仍然没有字体，尝试注册 HeiseiMin-W3（另一个CID字体）
    if not registered_fonts:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
            registered_fonts.append('HeiseiMin-W3')
            print("使用内置CID字体: HeiseiMin-W3")
        except Exception as e:
            print(f"注册HeiseiMin字体失败: {e}")
    
    # 4. 最后的备选：提示用户安装字体
    if not registered_fonts:
        print("=" * 60)
        print("警告：未找到可用的中文字体！")
        print("请安装中文字体以解决PDF乱码问题：")
        print("")
        print("Linux (Ubuntu/Debian):")
        print("  sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei")
        print("")
        print("Linux (CentOS/RHEL):")
        print("  sudo yum install wqy-zenhei-fonts wqy-microhei-fonts")
        print("")
        print("或者将中文字体文件（.ttf/.ttc）放到以下目录：")
        print(f"  {FONT_CACHE_DIR}")
        print("=" * 60)
        return 'Helvetica'
    
    return registered_fonts[0]


def get_font_name():
    """获取已注册的中文字体名称"""
    return CHINESE_FONT


# 注册字体并获取默认中文字体名
CHINESE_FONT = register_chinese_fonts()
CHINESE_FONT_BOLD = CHINESE_FONT  # 大多数中文字体没有独立的粗体，使用相同字体


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
    
    # 风险等级颜色
    RISK_CRITICAL = colors.HexColor('#FF0000')
    RISK_HIGH = colors.HexColor('#FF6600')
    RISK_MEDIUM = colors.HexColor('#FFCC00')
    RISK_LOW = colors.HexColor('#92D050')
    RISK_QM = colors.HexColor('#00B050')


# ==================== 样式定义 ====================
def get_tara_styles():
    """获取TARA报告样式"""
    styles = getSampleStyleSheet()
    
    # 主标题样式
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
    
    # 副标题样式
    styles.add(ParagraphStyle(
        name='TARASubTitle',
        fontName=CHINESE_FONT,
        fontSize=14,
        textColor=TARAColors.DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=8,
        leading=18
    ))
    
    # 章节标题样式
    styles.add(ParagraphStyle(
        name='TARASectionHeader',
        fontName=CHINESE_FONT_BOLD,
        fontSize=12,
        textColor=TARAColors.WHITE,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        leading=16,
        backColor=TARAColors.DARK_BLUE,
        leftIndent=6,
        rightIndent=6,
        borderPadding=4
    ))
    
    # 子章节标题
    styles.add(ParagraphStyle(
        name='TARASubSection',
        fontName=CHINESE_FONT_BOLD,
        fontSize=11,
        textColor=TARAColors.WHITE,
        alignment=TA_LEFT,
        spaceBefore=8,
        spaceAfter=4,
        leading=14,
        backColor=TARAColors.MEDIUM_BLUE,
        leftIndent=4,
        borderPadding=3
    ))
    
    # 正文样式
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
    
    # 表格内容样式
    styles.add(ParagraphStyle(
        name='TARATableCell',
        fontName=CHINESE_FONT,
        fontSize=8,
        textColor=TARAColors.BLACK,
        alignment=TA_LEFT,
        leading=10,
        wordWrap='CJK'
    ))
    
    # 表格标题样式
    styles.add(ParagraphStyle(
        name='TARATableHeader',
        fontName=CHINESE_FONT_BOLD,
        fontSize=8,
        textColor=TARAColors.WHITE,
        alignment=TA_CENTER,
        leading=10
    ))
    
    # 封面信息样式
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
def safe_paragraph(text: str, style, max_width: Optional[float] = None) -> Paragraph:
    """安全创建段落，处理特殊字符"""
    if text is None:
        text = ''
    # 转义HTML特殊字符
    text = str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # 保留换行
    text = text.replace('\n', '<br/>')
    return Paragraph(text, style)


def load_image_safe(image_path: str, max_width: float = 450, max_height: float = 300) -> Optional[Image]:
    """安全加载图片，自动缩放"""
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        # 使用PIL获取图片尺寸
        with PILImage.open(image_path) as img:
            orig_width, orig_height = img.size
        
        # 计算缩放比例
        width_ratio = max_width / orig_width
        height_ratio = max_height / orig_height
        ratio = min(width_ratio, height_ratio, 1.0)  # 不放大
        
        new_width = orig_width * ratio
        new_height = orig_height * ratio
        
        return Image(image_path, width=new_width, height=new_height)
    except Exception as e:
        print(f"Failed to load image {image_path}: {e}")
        return None


def create_section_header(title: str, styles) -> Table:
    """创建章节标题（带背景色）"""
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


# ==================== 封面页 ====================
def create_cover_page(data: Dict[str, Any], styles) -> List:
    """创建封面页"""
    elements = []
    
    # 顶部空白
    elements.append(Spacer(1, 60))
    
    # 数据等级信息（右上角）
    info_data = [
        [f"数据等级：{data.get('data_level', '秘密')}", ""],
        [f"Data level: Confidential", ""],
        [f"编号：{data.get('document_number', '')}", ""],
        [f"Number: {data.get('document_number', '')}", ""],
        [f"版本：{data.get('version', '')}", ""],
        [f"Version: {data.get('version', '')}", ""],
    ]
    info_table = Table(info_data, colWidths=[300, 200])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    
    elements.append(Spacer(1, 80))
    
    # 主标题
    title = data.get('report_title', '威胁分析和风险评估报告')
    title_en = data.get('report_title_en', 'Threat Analysis And Risk Assessment Report')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Paragraph(title_en, styles['TARASubTitle']))
    
    elements.append(Spacer(1, 20))
    
    # 项目名称
    project_name = data.get('project_name', '')
    if project_name:
        elements.append(Paragraph(project_name, styles['TARATitle']))
    
    elements.append(Spacer(1, 100))
    
    # 签署信息表格
    sign_data = [
        ['编制/日期：', data.get('author_date', ''), 'Author/Date:', data.get('author_date', '')],
        ['审核/日期：', data.get('review_date', ''), 'Review/Date:', data.get('review_date', '')],
        ['会签/日期：', data.get('sign_date', ''), 'Signature/Date:', data.get('sign_date', '')],
        ['批准/日期：', data.get('approve_date', ''), 'Approve/Date:', data.get('approve_date', '')],
    ]
    
    sign_table = Table(sign_data, colWidths=[80, 100, 90, 100])
    sign_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sign_table)
    
    elements.append(PageBreak())
    return elements


# ==================== 相关定义页 ====================
def create_definitions_page(data: Dict[str, Any], styles) -> List:
    """创建相关定义页"""
    elements = []
    
    # 页面标题
    title = data.get('title', 'TARA分析报告 - 相关定义')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 12))
    
    # 1. 功能描述
    elements.append(create_section_header('1. 功能描述 Functional Description', styles))
    elements.append(Spacer(1, 6))
    
    func_desc = data.get('functional_description', '')
    if func_desc:
        elements.append(Paragraph(func_desc, styles['TARABody']))
    elements.append(Spacer(1, 12))
    
    # 2. 项目边界图
    elements.append(create_section_header('2. 项目边界 Item Boundary', styles))
    elements.append(Spacer(1, 6))
    
    boundary_img = load_image_safe(data.get('item_boundary_image', ''), max_width=480, max_height=280)
    if boundary_img:
        elements.append(boundary_img)
    else:
        elements.append(Paragraph('[项目边界图]', styles['TARABody']))
    elements.append(Spacer(1, 12))
    
    # 3. 系统架构图
    elements.append(create_section_header('3. 系统架构图 System Architecture', styles))
    elements.append(Spacer(1, 6))
    
    sys_arch_img = load_image_safe(data.get('system_architecture_image', ''), max_width=480, max_height=280)
    if sys_arch_img:
        elements.append(sys_arch_img)
    else:
        elements.append(Paragraph('[系统架构图]', styles['TARABody']))
    elements.append(Spacer(1, 12))
    
    # 4. 软件架构图
    elements.append(create_section_header('4. 软件架构图 Software Architecture', styles))
    elements.append(Spacer(1, 6))
    
    sw_arch_img = load_image_safe(data.get('software_architecture_image', ''), max_width=480, max_height=280)
    if sw_arch_img:
        elements.append(sw_arch_img)
    else:
        elements.append(Paragraph('[软件架构图]', styles['TARABody']))
    elements.append(Spacer(1, 12))
    
    # 5. 相关项假设
    elements.append(create_section_header('5. 相关项假设 Item Assumptions', styles))
    elements.append(Spacer(1, 6))
    
    assumptions = data.get('assumptions', [])
    if assumptions:
        # 表头
        header = ['假设编号\nAssumption ID', '假设描述\nAssumption Description']
        table_data = [header]
        
        for asm in assumptions:
            row = [
                asm.get('id', ''),
                asm.get('description', '')
            ]
            table_data.append(row)
        
        asm_table = Table(table_data, colWidths=[80, 420])
        asm_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(asm_table)
    elements.append(Spacer(1, 12))
    
    # 6. 术语表
    elements.append(create_section_header('6. 术语表 Terminology', styles))
    elements.append(Spacer(1, 6))
    
    terminology = data.get('terminology', [])
    if terminology:
        header = ['缩写\nAbbreviation', '英文全称\nEnglish Full Name', '中文全称\nChinese Name']
        table_data = [header]
        
        for term in terminology:
            row = [
                term.get('abbreviation', ''),
                term.get('english', ''),
                term.get('chinese', '')
            ]
            table_data.append(row)
        
        term_table = Table(table_data, colWidths=[80, 220, 200])
        term_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(term_table)
    
    elements.append(PageBreak())
    return elements


# ==================== 资产列表页 ====================
def create_assets_page(data: Dict[str, Any], styles) -> List:
    """创建资产列表页"""
    elements = []
    
    # 页面标题
    title = data.get('title', '资产列表 Asset List')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 12))
    
    assets = data.get('assets', [])
    if assets:
        # 创建表头（两行）
        header1 = ['Asset Identification 资产识别', '', '', '', 'Cybersecurity Attributes 网络安全属性', '', '', '', '', '']
        header2 = [
            '资产ID\nAsset ID',
            '资产名称\nAsset Name',
            '分类\nCategory',
            '备注\nRemarks',
            '真实性\nAuth.',
            '完整性\nInteg.',
            '不可抵赖\nNon-rep.',
            '机密性\nConf.',
            '可用性\nAvail.',
            '权限\nAuthor.'
        ]
        
        table_data = [header2]
        
        for asset in assets:
            row = [
                asset.get('id', ''),
                asset.get('name', ''),
                asset.get('category', ''),
                asset.get('remarks', '')[:50] + '...' if len(asset.get('remarks', '')) > 50 else asset.get('remarks', ''),
                '√' if asset.get('authenticity') else '',
                '√' if asset.get('integrity') else '',
                '√' if asset.get('non_repudiation') else '',
                '√' if asset.get('confidentiality') else '',
                '√' if asset.get('availability') else '',
                '√' if asset.get('authorization') else ''
            ]
            table_data.append(row)
        
        # 列宽
        col_widths = [40, 60, 50, 120, 35, 35, 40, 35, 35, 35]
        asset_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        asset_table.setStyle(TableStyle([
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT_BOLD),
            # 数据行样式
            ('FONTNAME', (0, 1), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            # 备注列左对齐
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),
            # 交替行背景色
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [TARAColors.WHITE, TARAColors.LIGHT_GRAY]),
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


# ==================== 攻击树页 ====================
def create_attack_trees_page(data: Dict[str, Any], styles) -> List:
    """创建攻击树页"""
    elements = []
    
    # 页面标题
    title = data.get('title', '攻击树分析 Attack Tree Analysis')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 12))
    
    attack_trees = data.get('attack_trees', [])
    for i, tree in enumerate(attack_trees):
        # 攻击树标题
        tree_title = tree.get('title', f'攻击树 {i+1}')
        elements.append(create_section_header(tree_title, styles))
        elements.append(Spacer(1, 6))
        
        # 攻击树图片
        tree_img = load_image_safe(tree.get('image', ''), max_width=480, max_height=350)
        if tree_img:
            elements.append(tree_img)
        else:
            elements.append(Paragraph(f'[攻击树图: {tree_title}]', styles['TARABody']))
        
        elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    return elements


# ==================== TARA分析结果页（横向） ====================
def create_tara_results_page(data: Dict[str, Any], styles) -> List:
    """创建TARA分析结果页 - 使用简化表格"""
    elements = []
    
    # 页面标题
    title = data.get('title', 'TARA分析结果 TARA Analysis Results')
    elements.append(Paragraph(title, styles['TARATitle']))
    elements.append(Spacer(1, 8))
    
    results = data.get('results', [])
    if not results:
        elements.append(Paragraph('无分析结果', styles['TARABody']))
        return elements
    
    # 为每条结果创建详细卡片
    for idx, result in enumerate(results):
        # 威胁标题
        threat_title = f"威胁 {idx+1}: {result.get('asset_name', '')} - {result.get('stride_model', '')}"
        elements.append(create_section_header(threat_title, styles))
        elements.append(Spacer(1, 4))
        
        # 基本信息表
        basic_data = [
            ['资产ID', result.get('asset_id', ''), '资产名称', result.get('asset_name', '')],
            ['分类', result.get('category', ''), '安全属性', result.get('security_attribute', '').replace('\n', ' ')],
            ['STRIDE模型', result.get('stride_model', ''), 'WP29映射', result.get('wp29_mapping', '').replace('\n', ', ')],
        ]
        
        basic_table = Table(basic_data, colWidths=[60, 170, 60, 180])
        basic_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), TARAColors.LIGHT_BLUE),
            ('BACKGROUND', (2, 0), (2, -1), TARAColors.LIGHT_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(basic_table)
        elements.append(Spacer(1, 4))
        
        # 威胁场景
        elements.append(Paragraph(f"<b>威胁场景:</b> {result.get('threat_scenario', '')}", styles['TARABody']))
        
        # 攻击路径
        attack_path = result.get('attack_path', '')
        if attack_path:
            elements.append(Paragraph(f"<b>攻击路径:</b> {attack_path[:200]}{'...' if len(attack_path) > 200 else ''}", styles['TARABody']))
        elements.append(Spacer(1, 4))
        
        # 威胁分析表
        threat_analysis_data = [
            ['攻击向量', '攻击复杂度', '权限要求', '用户交互'],
            [
                result.get('attack_vector', ''),
                result.get('attack_complexity', ''),
                result.get('privileges_required', ''),
                result.get('user_interaction', '')
            ]
        ]
        
        threat_table = Table(threat_analysis_data, colWidths=[120, 120, 120, 120])
        threat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(threat_table)
        elements.append(Spacer(1, 4))
        
        # 影响分析表
        impact_data = [
            ['安全影响', '经济影响', '操作影响', '隐私影响'],
            [
                result.get('safety_impact', ''),
                result.get('financial_impact', ''),
                result.get('operational_impact', ''),
                result.get('privacy_impact', '')
            ]
        ]
        
        impact_table = Table(impact_data, colWidths=[120, 120, 120, 120])
        impact_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TARAColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(impact_table)
        elements.append(Spacer(1, 4))
        
        # 风险评估和安全需求
        security_req = result.get('security_requirement', '')
        risk_data = [
            ['安全需求', security_req[:100] + '...' if len(security_req) > 100 else security_req]
        ]
        
        req_table = Table(risk_data, colWidths=[60, 420])
        req_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), TARAColors.LIGHT_BLUE),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(req_table)
        
        elements.append(Spacer(1, 16))
        
        # 每3条记录分页
        if (idx + 1) % 3 == 0 and idx < len(results) - 1:
            elements.append(PageBreak())
    
    return elements


# ==================== 风险汇总页 ====================
def create_risk_summary_page(data: Dict[str, Any], styles) -> List:
    """创建风险汇总页"""
    elements = []
    
    elements.append(create_section_header('风险评估汇总 Risk Assessment Summary', styles))
    elements.append(Spacer(1, 12))
    
    results = data.get('results', [])
    if not results:
        elements.append(Paragraph('无分析结果', styles['TARABody']))
        return elements
    
    # 汇总表
    summary_header = ['序号', '资产', 'STRIDE', '攻击向量', '安全影响', '操作影响', '安全需求']
    table_data = [summary_header]
    
    for idx, result in enumerate(results):
        row = [
            str(idx + 1),
            result.get('asset_name', ''),
            result.get('stride_model', ''),
            result.get('attack_vector', ''),
            result.get('safety_impact', ''),
            result.get('operational_impact', ''),
            result.get('security_requirement', '')[:30] + '...' if len(result.get('security_requirement', '')) > 30 else result.get('security_requirement', '')
        ]
        table_data.append(row)
    
    col_widths = [30, 70, 50, 50, 60, 60, 160]
    summary_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TARAColors.DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), TARAColors.WHITE),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, TARAColors.GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [TARAColors.WHITE, TARAColors.LIGHT_GRAY]),
    ]))
    elements.append(summary_table)
    
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
    """
    生成TARA分析报告PDF文件
    
    参数:
        output_path: 输出文件路径
        cover_data: 封面数据
        definitions_data: 相关定义数据
        assets_data: 资产列表数据
        attack_trees_data: 攻击树数据
        tara_results_data: TARA分析结果数据
    
    返回:
        str: 生成的文件路径
    """
    # 创建PDF文档
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    # 获取样式
    styles = get_tara_styles()
    
    # 构建内容
    elements = []
    
    # 1. 封面
    elements.extend(create_cover_page(cover_data, styles))
    
    # 2. 相关定义
    elements.extend(create_definitions_page(definitions_data, styles))
    
    # 3. 资产列表
    elements.extend(create_assets_page(assets_data, styles))
    
    # 4. 攻击树
    if attack_trees_data.get('attack_trees'):
        elements.extend(create_attack_trees_page(attack_trees_data, styles))
    
    # 5. TARA分析结果
    elements.extend(create_tara_results_page(tara_results_data, styles))
    
    # 6. 风险汇总
    elements.append(PageBreak())
    elements.extend(create_risk_summary_page(tara_results_data, styles))
    
    # 构建PDF
    doc.build(elements)
    
    return output_path


def generate_tara_pdf_from_json(
    output_path: str,
    json_data: Dict[str, Any]
) -> str:
    """
    从JSON数据生成TARA分析报告PDF文件
    
    参数:
        output_path: 输出文件路径
        json_data: 包含所有数据的JSON对象
    
    返回:
        str: 生成的文件路径
    """
    return generate_tara_pdf(
        output_path=output_path,
        cover_data=json_data.get('cover', {}),
        definitions_data=json_data.get('definitions', {}),
        assets_data=json_data.get('assets', {}),
        attack_trees_data=json_data.get('attack_trees', {}),
        tara_results_data=json_data.get('tara_results', {})
    )


if __name__ == "__main__":
    # 测试用例
    sample_data = {
        "cover": {
            "report_title": "威胁分析和风险评估报告",
            "report_title_en": "Threat Analysis And Risk Assessment Report",
            "project_name": "——DiLink150中控主机平台",
            "data_level": "秘密",
            "document_number": "IPC0011_JF_A30-44003",
            "version": "V1.0",
            "author_date": "2025.11",
            "review_date": "2025.12"
        },
        "definitions": {
            "title": "MY25 EV平台中控主机 TARA分析报告 - 相关定义",
            "functional_description": "车载信息娱乐系统(In-Vehicle Infotainment, IVI)是一种集成多媒体娱乐、导航、蓝牙通信、车辆控制等功能的智能车载终端系统。它通过触摸屏、语音识别和物理按键为驾驶员和乘客提供便捷的人机交互体验。",
            "assumptions": [
                {"id": "ASM-01", "description": "IVI系统运行在独立的电子控制单元上"},
                {"id": "ASM-02", "description": "IVI系统与车身域控制器通过CAN网关进行通信"}
            ],
            "terminology": [
                {"abbreviation": "IVI", "english": "In-Vehicle Infotainment", "chinese": "车载信息娱乐系统"},
                {"abbreviation": "TARA", "english": "Threat Analysis and Risk Assessment", "chinese": "威胁分析与风险评估"},
                {"abbreviation": "STRIDE", "english": "Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege", "chinese": "欺骗、篡改、抵赖、信息泄露、拒绝服务、权限提升"}
            ]
        },
        "assets": {
            "title": "MY25 EV平台中控主机 - 资产列表 Asset List",
            "assets": [
                {
                    "id": "P001", "name": "SOC", "category": "内部实体",
                    "remarks": "主处理器芯片，运行Android Automotive OS",
                    "authenticity": True, "integrity": True, "availability": True
                },
                {
                    "id": "P002", "name": "MCU", "category": "内部实体",
                    "remarks": "微控制器，处理CAN通信",
                    "authenticity": True, "integrity": True, "confidentiality": True
                }
            ]
        },
        "attack_trees": {
            "title": "MY25 EV平台中控主机 - 攻击树分析",
            "attack_trees": [
                {"title": "攻击树1: 远程入侵IVI系统", "image": ""},
                {"title": "攻击树2: 物理接口攻击", "image": ""}
            ]
        },
        "tara_results": {
            "title": "MY25 EV平台中控主机_TARA分析结果",
            "results": [
                {
                    "asset_id": "P001", "asset_name": "车载多媒体SOC",
                    "subdomain1": "系统实体", "subdomain2": "N/A", "subdomain3": "SOC",
                    "category": "内部实体", "security_attribute": "Authenticity\n真实性",
                    "stride_model": "S欺骗", 
                    "threat_scenario": "黑客仿冒SOC模块发送恶意指令，绕过身份验证机制",
                    "attack_path": "1.攻击者锁定目标车辆\n2.通过OTA漏洞植入恶意代码\n3.获取系统控制权限",
                    "wp29_mapping": "4.1\n5.1",
                    "attack_vector": "网络", "attack_complexity": "高",
                    "privileges_required": "低", "user_interaction": "不需要",
                    "safety_impact": "中等的", "financial_impact": "中等的",
                    "operational_impact": "重大的", "privacy_impact": "可忽略不计的",
                    "security_requirement": "1.应实现安全启动机制\n2.应对通信进行加密认证"
                },
                {
                    "asset_id": "P002", "asset_name": "CAN通信MCU",
                    "subdomain1": "系统实体", "subdomain2": "N/A", "subdomain3": "MCU",
                    "category": "内部实体", "security_attribute": "Integrity\n完整性",
                    "stride_model": "T篡改",
                    "threat_scenario": "攻击者篡改CAN总线上的消息，发送伪造的控制指令",
                    "attack_path": "1.物理接触OBD-II接口\n2.接入CAN总线\n3.注入恶意报文",
                    "wp29_mapping": "6.2\n7.1",
                    "attack_vector": "物理", "attack_complexity": "低",
                    "privileges_required": "无", "user_interaction": "不需要",
                    "safety_impact": "严重的", "financial_impact": "重大的",
                    "operational_impact": "严重的", "privacy_impact": "中等的",
                    "security_requirement": "1.应实现CAN消息认证\n2.应对异常消息进行检测"
                }
            ]
        }
    }
    
    output_file = "/tmp/tara_report_test.pdf"
    generate_tara_pdf_from_json(output_file, sample_data)
    print(f"测试报告已生成: {output_file}")
