"""
报告生成器模块
"""
from .excel_generator import generate_tara_excel, generate_tara_excel_from_json
from .pdf_generator import generate_tara_pdf, generate_tara_pdf_from_json

__all__ = [
    "generate_tara_excel", "generate_tara_excel_from_json",
    "generate_tara_pdf", "generate_tara_pdf_from_json"
]
