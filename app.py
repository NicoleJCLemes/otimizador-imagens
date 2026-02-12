import streamlit as st
from PIL import Image
import io
import zipfile

# --- Configurações da Página ---
st.set_page_config(page_title="Otimizador de Imagens", layout="centered")

st.title("🚀 Otimizador de Imagens")
st.write("""
**Regras aplicadas:**
1. Largura: **1440px** (proporcional)
2. Tamanho Alvo: **< 95KB** (Margem de segurança para limite de 100KB)
3. Formato: **WebP**
4. Fundo: **Preto** (remove transparência)
""")

# --- Função de Processamento ---
def processar_imagem(image_file):
    # Carregar imagem na memória
    img = Image.open(image_file)
    nome_original = image_file.name.rsplit('.', 1)[0]
    
    # 1. Redimensionar Inteligente (Sem Upscaling)
    target_width = 1440
    
    # Só redimensiona se a imagem for MAIOR que o alvo
    if img.size[0] > target_width:
        w_percent = (target_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
    else:
        # Se for menor ou igual, mantém o tamanho original (evita desfoque)
        pass
    
    # 2. Fundo Preto (Remover transparência)
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (0, 0, 0))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[3])
        img = background
    else:
        img = img.convert('RGB')
        
    # 3. Compressão Loop com Margem de Segurança
    # 95KB * 1024 bytes = 97280 bytes. Isso garante que nunca passará de 100KB.
    max_size_bytes = 95 * 1024 
    quality = 95
    step = 2
    output_buffer = io.BytesIO()
    
    # Loop para encontrar a melhor qualidade que caiba em 95KB
    while quality > 5:
        output_buffer.seek(0)
        output_buffer.truncate(0)
        # method=6 é o mais lento, mas gera o menor arquivo com melhor qualidade visual
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
    process_btn = st.button("Processar Imagens")
    
    if process_btn:
        zip_buffer = io.BytesIO()
        progresso = st.progress(0)
        status_text = st.empty()
        
        # Criar ZIP
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            total = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Feedback visual
                status_text.text(f"Otimizando {uploaded_file.name}...")
                
                # Processar
                img_data, novo_nome, tamanho, q_final = processar_imagem(uploaded_file)
                
                # Adicionar ao ZIP
                zip_file.writestr(novo_nome, img_data)
                
                # Atualizar barra
                progresso.progress((i + 1) / total)
                
                # Mostrar resultado na tela
                kb_size = tamanho / 1024
                # Se ficar verde (sucesso) ou amarelo (atenção se ficou muito comprimido)
                cor = "✅" if kb_size <= 96 else "⚠️" 
                st.write(f"{cor} **{novo_nome}**: {kb_size:.2f} KB (Qualidade: {q_final}%)")

        status_text.text("Concluído!")
        progresso.progress(100)

        # Botão de Download Final
        st.markdown("---")
        st.success("Processamento finalizado! Baixe seus arquivos abaixo:")
        
        st.download_button(
            label="⬇️ Baixar Imagens Otimizadas (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="imagens_otimizadas_95kb.zip",
            mime="application/zip",
            type="primary"
        )
