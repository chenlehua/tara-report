"""
Report generators module
"""
from app.generators.excel_generator import generate_tara_excel_from_json
from app.generators.pdf_generator import generate_tara_pdf_from_json

__all__ = ["generate_tara_excel_from_json", "generate_tara_pdf_from_json"]
