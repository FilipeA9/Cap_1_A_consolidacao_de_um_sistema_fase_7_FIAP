"""
FarmTech Solutions - Fase 6 - Inferencia de visao computacional.

Processa imagens estaticas de uma pasta (conforme permitido pelo
enunciado: "voce pode usar imagens estaticas e salvas em uma pasta"),
detectando macas (frutos) e garrafas (objetos estranhos/descarte
irregular na lavoura). Cada deteccao e gravada na tabela
`deteccoes_visao`; garrafas disparam alerta corretivo via alert_engine.

Modelo: services/fase6_visao/best.pt (gerado por treino_yolo.py).
Fallback: se best.pt nao existir, usa YOLOv8n pre-treinado na COCO
(classes 47=apple e 39=bottle), mapeadas para maca/garrafa - util para
demonstracao antes do primeiro treino.

Execucao: python main.py visao [--pasta caminho/das/imagens]
"""

import sys
import os
from pathlib import Path
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import (VISAO_BEST_PT, VISAO_DATASET, VISAO_SAIDA)
from services.fase3_banco.db_manager import DatabaseManager

# Mapeamento do fallback COCO -> classes do projeto
COCO_MAP = {47: "maca", 39: "garrafa"}
CONFIANCA_MINIMA = 0.30


def _carregar_modelo():
    try:
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError(
            "ultralytics nao instalado. Rode: pip install ultralytics")

    if VISAO_BEST_PT.exists():
        return YOLO(str(VISAO_BEST_PT)), "best.pt (fine-tuned Fase 6)", None
    # Fallback: modelo COCO pre-treinado com filtro de classes
    return YOLO("yolov8n.pt"), "yolov8n COCO (fallback)", list(COCO_MAP.keys())


def processar_pasta(pasta: Path = None, db: DatabaseManager = None,
                    salvar_anotadas: bool = True) -> List[Dict]:
    """Roda a deteccao em todas as imagens da pasta informada."""
    pasta = Path(pasta or (VISAO_DATASET / "test" / "images"))
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta de imagens nao encontrada: {pasta}")

    modelo, nome_modelo, filtro_classes = _carregar_modelo()
    db = db or DatabaseManager()
    VISAO_SAIDA.mkdir(parents=True, exist_ok=True)

    kwargs = dict(conf=CONFIANCA_MINIMA, verbose=False)
    if filtro_classes:
        kwargs["classes"] = filtro_classes
    if salvar_anotadas:
        kwargs.update(save=True, project=str(VISAO_SAIDA), name="deteccoes",
                      exist_ok=True)

    resultados = modelo.predict(source=str(pasta), **kwargs)

    deteccoes = []
    for r in resultados:
        nome_imagem = Path(r.path).name
        for box in r.boxes:
            classe_id = int(box.cls[0])
            conf = float(box.conf[0])
            if filtro_classes:  # fallback COCO
                classe = COCO_MAP.get(classe_id, f"coco_{classe_id}")
            else:               # modelo fine-tuned (0=maca, 1=garrafa)
                classe = r.names.get(classe_id, str(classe_id))
            db.inserir_deteccao_visao(nome_imagem, classe, conf, nome_modelo)
            deteccoes.append({
                'imagem': nome_imagem,
                'classe': classe,
                'confianca': round(conf, 3),
                'modelo': nome_modelo,
            })

    return deteccoes


def executar_cli(pasta: str = None):
    print("=" * 60)
    print("VISAO COMPUTACIONAL (Fase 6) - deteccao em imagens estaticas")
    print("=" * 60)
    deteccoes = processar_pasta(Path(pasta) if pasta else None)
    if not deteccoes:
        print("Nenhum objeto detectado.")
        return
    for d in deteccoes:
        print(f"  {d['imagem']:30s} {d['classe']:10s} conf={d['confianca']}")
    garrafas = [d for d in deteccoes if d['classe'] == 'garrafa']
    print(f"\n{len(deteccoes)} deteccoes gravadas no banco "
          f"({len(garrafas)} objetos estranhos).")
    if garrafas:
        print("Disparando verificacao de alertas (objeto estranho na lavoura)...")
        from services.alertas.alert_engine import verificar_visao
        verificar_visao()
    print(f"Imagens anotadas salvas em: {VISAO_SAIDA / 'deteccoes'}")


if __name__ == "__main__":
    executar_cli(sys.argv[1] if len(sys.argv) > 1 else None)
