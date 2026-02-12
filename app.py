import streamlit as st
from PIL import Image
import io
import zipfile

# --- Configurações da Página ---
st.set_page_config(page_title="Otimizador de Imagens", layout="centered")

st.title("🚀 Otimizador de Imagens")
st.write("""
**Regras aplicadas:**
1. Largura: **Máximo 1440px** (Se for menor, mantém o original. Se maior, reduz).
2. Peso: **< 95KB** (Margem de segurança para o limite de 100KB).
3. Formato: **WebP**.
4. Fundo: **Preto** (Substitui transparência).
""")

# --- Função de Processamento ---
def processar_imagem(image_file):
    # Carregar imagem na memória
    img = Image.open(image_file)
    nome_original = image_file.name.rsplit('.', 1)[0]
    
    # 1. Redimensionar Inteligente (Sem Upscaling)
    target_width = 1440
    
    # Só redimensiona se a largura original for MAIOR que 1440px
    if img.size[0] > target_width:
        w_percent = (target_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
    
    # 2. Fundo Preto (Remover transparência)
    # Importante fazer isso mesmo se a imagem for pequena
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (0, 0, 0))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[3])
        img = background
    else:
        img = img.convert('RGB')
        
    # 3. Compressão Loop com Margem de Segurança (95KB)
    max_size_bytes = 95 * 1024 
    quality = 95
    step = 2
    output_buffer = io.BytesIO()
    
    # Loop para encontrar a melhor qualidade que caiba em 95KB
    while quality > 5:
        output_buffer.seek(0)
        output_buffer.truncate(0)
        # method=6 garante a melhor compactação possível do WebP
        img.save(output_buffer, format="WEBP", quality=quality, method=6)
        size = output_buffer.tell()
        
        if size <= max_size_bytes:
            break
        
        quality -= step
        
    return output_buffer.getvalue(), f"{nome_original}.webp", size, quality, img.size[0]

# --- Interface de Upload ---
uploaded_files = st.file_uploader("Arraste suas imagens aqui (JPG, PNG, WEBP)", 
                                  accept_multiple_files=True, 
                                  type=['png', 'jpg', 'jpeg', 'webp'])

if uploaded_files:
    if st.button("Processar Imagens"):
        zip_buffer = io.BytesIO()
        progresso = st.progress(0)
        status_text = st.empty()
        
        # Área de resultados visuais
        result_container = st.container()

        # Criar ZIP
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            total = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Feedback visual
                status_text.text(f"Otimizando {uploaded_file.name}...")
                
                # Processar
                img_data, novo_nome, tamanho, q_final, largura_final = processar_imagem(uploaded_file)
                
                # Adicionar ao ZIP
                zip_file.writestr(novo_nome, img_data)
                
                # Atualizar barra
                progresso.progress((i + 1) / total)
                
                # Mostrar resultado na lista
                kb_size = tamanho / 1024
                cor = "✅" if kb_size <= 96 else "⚠️" 
                
                with result_container:
                    st.text(f"{cor} {novo_nome} | {kb_size:.2f} KB | Largura: {largura_final}px | Q: {q_final}%")

        status_text.text("Concluído!")
        progresso.progress(100)

        # Botão de Download Final
        st.markdown("---")
        st.success("Processamento finalizado! Baixe seus arquivos abaixo:")
        
        st.download_button(
            label="⬇️ Baixar Imagens Otimizadas (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="imagens_otimizadas_rtx.zip",
            mime="application/zip",
            type="primary"
        )
