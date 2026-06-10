"""
FarmTech Solutions - Fase 1 - Ponte para a analise estatistica em R.

A entrega original da Fase 1 incluia o script `clima.R` (estatisticas de
areas + consulta a API meteorologica via httr2). Este modulo dispara o
script via Rscript quando o R esta instalado; caso contrario, executa um
fallback em Python (mesmas estatisticas + consulta Open-Meteo, que nao
exige chave de API) para que a dashboard nunca quebre.
"""

import shutil
import statistics
import subprocess
from pathlib import Path

SCRIPT_R = Path(__file__).parent / "clima.R"

AREAS_CAFE = [10.5, 12.3, 8.8, 15.1, 9.7]
AREAS_CANA = [35.2, 41.5, 38.9, 45.0, 32.1]


def r_disponivel() -> bool:
    return shutil.which("Rscript") is not None


def executar_script_r(timeout: int = 120) -> str:
    """Executa o clima.R original e devolve a saida de texto."""
    resultado = subprocess.run(
        ["Rscript", str(SCRIPT_R)],
        capture_output=True, text=True, timeout=timeout,
    )
    saida = resultado.stdout
    if resultado.returncode != 0:
        saida += f"\n[ERRO Rscript]\n{resultado.stderr}"
    return saida


def estatisticas_python() -> str:
    """Fallback: replica a analise estatistica do clima.R em Python."""
    linhas = ["### Analise Estatistica (fallback Python) ###", ""]
    for nome, areas in [("Cafe", AREAS_CAFE), ("Cana-de-acucar", AREAS_CANA)]:
        linhas += [
            f"--- {nome} ---",
            f"Media de area: {statistics.mean(areas):.2f} ha",
            f"Desvio padrao: {statistics.stdev(areas):.2f} ha",
            f"Minimo/Maximo: {min(areas):.2f} / {max(areas):.2f} ha",
            "",
        ]
    return "\n".join(linhas)


def clima_python(cidade_lat: float = -23.55, cidade_lon: float = -46.63) -> str:
    """Fallback: consulta a API publica Open-Meteo (sem chave) e formata."""
    try:
        import requests
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={cidade_lat}&longitude={cidade_lon}"
            "&current=temperature_2m,relative_humidity_2m,precipitation"
            "&timezone=America%2FSao_Paulo"
        )
        dados = requests.get(url, timeout=10).json().get("current", {})
        return (
            "### Clima atual (Open-Meteo, Sao Paulo) ###\n"
            f"Temperatura: {dados.get('temperature_2m', '?')} C\n"
            f"Umidade relativa: {dados.get('relative_humidity_2m', '?')} %\n"
            f"Precipitacao: {dados.get('precipitation', '?')} mm\n"
        )
    except Exception as e:  # rede indisponivel nao deve quebrar o servico
        return f"[Clima indisponivel: {e}]"


def executar(preferir_r: bool = True) -> str:
    """Ponto de entrada usado pela dashboard e pelo main.py."""
    if preferir_r and r_disponivel():
        return executar_script_r()
    return estatisticas_python() + "\n" + clima_python()


if __name__ == "__main__":
    print(executar())
