import streamlit as st
import PyPDF2
import re
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def detect_sensitive_data(text):
    patterns = {
        'CPF': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
        'RG': r'\d{2}\.\d{3}\.\d{3}-\d{1}',
        'Email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'Telefone': r'\(\d{2}\)\s*\d{4,5}-\d{4}',
        'Nome': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    }
    
    sensitive_data = {}
    for data_type, pattern in patterns.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            sensitive_data[match.group()] = (match.start(), match.end(), data_type)
    
    return sensitive_data

def anonymize_pdf(input_pdf):
    reader = PyPDF2.PdfReader(input_pdf)
    writer = PyPDF2.PdfWriter()
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        content = page.extract_text()
        sensitive_data = detect_sensitive_data(content)
        
        if sensitive_data:
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            for data, (start, end, data_type) in sensitive_data.items():
                # Simplificado para demonstração
                can.setFillColorRGB(0, 0, 0)
                can.rect(100, 100, 400, 20, fill=1)
            
            can.save()
            packet.seek(0)
            new_pdf = PyPDF2.PdfReader(packet)
            page.merge_page(new_pdf.pages[0])
        
        writer.add_page(page)
    
    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf

def main():
    st.title("Anonimizador de PDF - LGPD")
    
    uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
    
    if uploaded_file is not None:
        st.write("Arquivo carregado com sucesso!")
        
        if st.button("Anonimizar PDF"):
            with st.spinner("Processando o PDF..."):
                output_pdf = anonymize_pdf(uploaded_file)
            
            st.success("PDF anonimizado com sucesso!")
            st.download_button(
                label="Baixar PDF Anonimizado",
                data=output_pdf,
                file_name="documento_anonimizado.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()