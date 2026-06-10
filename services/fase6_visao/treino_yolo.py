"""
FarmTech Solutions - Fase 6 - Treinamento local do YOLO.

Reproduz localmente o fine-tuning que a Fase 6 fazia no Colab (la com
YOLOv5; aqui com ultralytics/YOLOv8, API mais simples e mesmo formato de
labels). Ao final copia o melhor peso para services/fase6_visao/best.pt,
que e o arquivo consumido pela inferencia da dashboard.

Requisitos: pip install ultralytics  (instalacao pesada - inclui PyTorch)
Execucao:   python main.py treinar-yolo [--epocas 60]
"""

import shutil
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import VISAO_DIR, VISAO_BEST_PT

DATA_YAML = VISAO_DIR / "data.yaml"


def treinar(epocas: int = 60, imgsz: int = 640, modelo_base: str = "yolov8n.pt"):
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics nao instalado. Rode: pip install ultralytics")
        sys.exit(1)

    print(f"Treinando YOLO ({modelo_base}) por {epocas} epocas...")
    print("Dica da Fase 6: treine tambem com 30 epocas e compare métricas.")

    modelo = YOLO(modelo_base)
    resultados = modelo.train(
        data=str(DATA_YAML),
        epochs=epocas,
        imgsz=imgsz,
        project=str(VISAO_DIR / "runs"),
        name=f"treino_{epocas}ep",
        exist_ok=True,
        patience=20,
    )

    # Copia o melhor peso para o local padrao consumido pela inferencia
    best = Path(resultados.save_dir) / "weights" / "best.pt"
    if best.exists():
        shutil.copy(best, VISAO_BEST_PT)
        print(f"\nMelhor peso copiado para {VISAO_BEST_PT}")
    else:
        print("\nAviso: best.pt nao encontrado no diretorio de treino.")

    # Validacao no conjunto de teste (mesma pratica do notebook da Fase 6)
    metricas = modelo.val(data=str(DATA_YAML), split="test")
    print(f"mAP50 (teste): {metricas.box.map50:.4f}")
    return resultados


if __name__ == "__main__":
    epocas = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    treinar(epocas=epocas)
