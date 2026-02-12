import streamlit as st
from PIL import Image
import io
import zipfile

# --- Configurações da Página ---
st.set_page_config(page_title="Otimizador de Imagens RTX", layout="centered")

st.title("🚀 Otimizador de Imagens (Padrão RTX)")
st.write("""
**Regras aplicadas:**
1. Largura: **1440px** (proporcional)
2. Tamanho Máximo: **100KB**
3. Formato: **WebP**
4. Fundo: **Preto** (remove transparência)
""")

# --- Função de Processamento ---
def processar_imagem(image_file):
    # Carregar imagem na memória
    img = Image.open(image_file)
    nome_original = image_file.name.rsplit('.', 1)[0]
    
    # 1. Redimensionar (LANCZOS)
    target_width = 1440
    w_percent = (target_width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
    
    # 2. Fundo Preto
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (0, 0, 0))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[3])
        img = background
    else:
        img = img.convert('RGB')
        
    # 3. Compressão Loop
    max_size_bytes = 100 * 1024 # 100KB
    quality = 95
    step = 2
    output_buffer = io.BytesIO()
    
    while quality > 5:
        output_buffer.seek(0)
        output_buffer.truncate(0)
        img.save(output_buffer, format="WEBP", quality=quality, method=6)
        size = output_buffer.tell()
        if size <= max_size_bytes:
            break
        quality -= step
        
    return output_buffer.getvalue(), f"{nome_original}.webp", size, quality

# --- Interface de Upload ---
uploaded_files = st.file_uploader("Arraste suas imagens aqui (JPG, PNG, WEBP)", 
                                  accept_multiple_files=True, 
                                  type=['png', 'jpg', 'jpeg', 'webp'])

if uploaded_files:
    if st.button("Processar Imagens"):
        zip_buffer = io.BytesIO()
        progresso = st.progress(0)
        status_text = st.empty()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            total = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Processar
                status_text.text(f"Processando {uploaded_file.name}...")
                img_data, novo_nome, tamanho, q_final = processar_imagem(uploaded_file)
                
                # Adicionar ao ZIP
                zip_file.writestr(novo_nome, img_data)
                
                # Atualizar barra
                progresso.progress((i + 1) / total)
                
                # Mostrar resultado na tela (opcional)
                st.success(f"✅ {novo_nome} | {tamanho/1024:.1f} KB | Q: {q_final}%")

        # Botão de Download Final
        st.markdown("---")
        st.write("### Tudo pronto!")
        st.download_button(
            label="⬇️ Baixar Todas as Imagens (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="imagens_otimizadas.zip",
            mime="application/zip",
            type="primary"
        )