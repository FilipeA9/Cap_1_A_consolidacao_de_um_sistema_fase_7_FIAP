"""Pagina do servico da Fase 6: visao computacional YOLO."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.core.config import VISAO_BEST_PT, VISAO_DATASET, VISAO_SAIDA
from services.fase3_banco.db_manager import DatabaseManager

st.set_page_config(page_title="Visão Computacional (Fase 6)", page_icon="👁️",
                   layout="wide")
st.title("👁️ Visão Computacional — Fase 6")
st.caption("Detecção de maçãs (frutos) e garrafas (objetos estranhos/descarte "
           "irregular na lavoura) com YOLO, processando imagens estáticas de "
           "uma pasta — conforme permitido pelo enunciado.")

db = DatabaseManager()

# ----- Status do modelo -----
if VISAO_BEST_PT.exists():
    st.success("Modelo fine-tuned **best.pt** disponível (treinado com as 80 "
               "imagens da Fase 6).")
else:
    st.warning("`best.pt` ainda não gerado — a inferência usará o fallback "
               "YOLOv8n/COCO (classes apple e bottle). Para treinar o modelo "
               "da Fase 6 localmente, rode `python main.py treinar-yolo` "
               "(requer `pip install ultralytics`).")

# ----- Inferencia -----
st.subheader("🔎 Processar imagens estáticas")
pasta_padrao = str(VISAO_DATASET / "test" / "images")
pasta = st.text_input("Pasta de imagens", value=pasta_padrao)

if st.button("👁️ Detectar objetos", type="primary"):
    try:
        from services.fase6_visao.inferencia import processar_pasta
        with st.spinner("Executando YOLO nas imagens..."):
            deteccoes = processar_pasta(Path(pasta), db=db)
        if not deteccoes:
            st.info("Nenhum objeto detectado.")
        else:
            st.success(f"{len(deteccoes)} detecções registradas no banco.")
            st.dataframe(deteccoes, use_container_width=True, hide_index=True)
            garrafas = [d for d in deteccoes if d['classe'] == 'garrafa']
            if garrafas:
                st.error(f"⚠️ {len(garrafas)} objeto(s) estranho(s) detectado(s)! "
                         "Acionando motor de alertas...")
                from services.alertas.alert_engine import verificar_visao
                for r in verificar_visao(db):
                    st.warning(f"Alerta: {r['tipo']} — {r['status']}")
    except RuntimeError as e:
        st.error(str(e))
    except FileNotFoundError as e:
        st.error(str(e))

# ----- Galeria de resultados -----
saida = VISAO_SAIDA / "deteccoes"
if saida.exists():
    imagens = sorted(saida.glob("*.jpg")) + sorted(saida.glob("*.jpeg")) + \
              sorted(saida.glob("*.png"))
    if imagens:
        st.subheader("🖼️ Últimas imagens anotadas")
        cols = st.columns(4)
        for i, img in enumerate(imagens[-8:]):
            cols[i % 4].image(str(img), caption=img.name,
                              use_container_width=True)

# ----- Historico -----
st.subheader("📜 Histórico de detecções")
det = db.obter_deteccoes_visao(limite=100)
st.dataframe(det, use_container_width=True, hide_index=True)
