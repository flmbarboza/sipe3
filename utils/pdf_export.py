"""
Geração simples de PDF do Relatório Completo, usando fpdf2.
Recebe o texto em Markdown "leve" (títulos com #, ## e listas com -)
e converte em um PDF básico, mas legível.
"""

from fpdf import FPDF
from analytics import pdf_generated


pdf_generated(
    pages=25
)

class RelatorioPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def _clean(text: str) -> str:
    # fpdf2 (helvetica) não suporta todos os unicode; troca caracteres problemáticos
    return (
        text.replace("—", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


def markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    pdf = RelatorioPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    for raw_line in markdown_text.split("\n"):
        line = _clean(raw_line.rstrip())

        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(4)
            pdf.multi_cell(0, 10, line[2:])
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(37, 99, 235)
            pdf.ln(3)
            pdf.multi_cell(0, 8, line[3:])
            pdf.ln(1)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(0, 7, line[4:])
        elif line.startswith("- "):
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(0, 6, f"  •  {line[2:]}")
        elif line.strip() == "":
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(0, 6, line)

    return bytes(pdf.output())
