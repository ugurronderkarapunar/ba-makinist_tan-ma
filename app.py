import streamlit as st
from pdf2image import convert_from_bytes
import pytesseract
import re

# 1. Genişletilmiş Unvan Hiyerarşisi
UNVAN_HIYERARSI = {
    "UZAKYOL BAŞMAKİNİST": 110,
    "BAŞMAKİNİST": 100,
    "ÇARKÇIBAŞI": 100,
    "CHIEF ENGINEER": 100,
    "UZAKYOL İKİNCİ MAKİNİST": 90,
    "İKİNCİ MAKİNİST": 85,
    "2. MAKİNİST": 80,
    "3. MAKİNİST": 60,
    "4. MAKİNİST": 40,
    "SINIRLI BAŞMAKİNİST": 35,
    "RESTRICTED CHIEF ENGINEER": 35,
    "SINIRLI MAKİNİST": 30,
    "MAKİNE LOSTROMOSU": 25,
    "YAĞCI": 15,
    "OILER": 15,
    "SİLİCİ": 5
}

def ocr_ile_oku(pdf_file):
    # PDF sayfalarını görsele çevir
    pages = convert_from_bytes(pdf_file.read())
    full_text = ""
    for page in pages:
        # Görseldeki metni Türkçe ve İngilizce olarak oku
        text = pytesseract.image_to_string(page, lang='tur+eng')
        full_text += text + " "
    return full_text

def unvan_analiz(text):
    # Metni temizle: Boşlukları normalize et ve büyük harfe çevir
    temiz_metin = " ".join(text.split()).upper()
    bulunanlar = []

    for unvan, puan in UNVAN_HIYERARSI.items():
        # Belgedeki "SINIRLI BAŞMAKİNİST" gibi tam eşleşmeleri arar
        if unvan in temiz_metin:
            bulunanlar.append((unvan, puan))
    
    if not bulunanlar:
        return None
    
    # En yüksek puanlı unvanı seç
    return max(bulunanlar, key=lambda x: x[1])

# --- Streamlit Arayüzü ---
st.title("🚢 Taranmış Cüzdan Analiz Sistemi (OCR)")
st.write("Taranmış PDF veya fotoğraf halindeki belgeleri analiz eder.")

uploaded_file = st.file_uploader("Cüzdan PDF veya Görselini Yükleyin", type=["pdf", "jpg", "png"])

if uploaded_file:
    with st.spinner('Görüntü işleniyor ve metin okunuyor... (Bu işlem biraz sürebilir)'):
        try:
            # Metin çıkarma
            extracted_text = ocr_ile_oku(uploaded_file)
            
            # Unvan analizi
            sonuc = unvan_analiz(extracted_text)
            
            if sonuc:
                unvan, puan = sonuc
                st.success(f"### Tespit Edilen En Yüksek Yeterlilik: **{unvan}**")
                st.progress(puan / 110)
            else:
                st.warning("Belgede tanımlı bir unvan tespit edilemedi.")
            
            with st.expander("OCR Tarafından Okunan Ham Metin"):
                st.text(extracted_text)
                
        except Exception as e:
            st.error(f"Hata oluştu: {e}. Lütfen sistemde Tesseract ve Poppler yüklü olduğundan emin olun.")
