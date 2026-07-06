"""
Módulo de apoio ao dashboard final do projeto Agro Leads Orchestrator.

Responsável por:
- carregar arquivos analíticos;
- calcular indicadores executivos;
- preparar tabelas consolidadas;
- apoiar o notebook 07_dashboard_final.ipynb.
"""

from pathlib import Path

import pandas as pd


def carregar_csv(caminho_arquivo: Path) -> pd.DataFrame:
    """
    Carrega um arquivo CSV validando sua existência.
    """

    if not caminho_arquivo.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_arquivo}"
        )

    return pd.read_csv(caminho_arquivo)


def calcular_reducao_percentual(
    valor_antes: float,
    valor_depois: float
) -> float:
    """
    Calcula redução percentual entre dois valores.
    """

    if valor_antes == 0:
        return 0.0

    reducao = ((valor_antes - valor_depois) / valor_antes) * 100

    return round(reducao, 2)


def obter_valor_metrica(
    dados: pd.DataFrame,
    cenario: str,
    coluna: str
) -> float:
    """
    Obtém uma métrica específica para determinado cenário.
    """

    valor = dados.loc[
        dados["cenario"] == cenario,
        coluna
    ].iloc[0]

    return float(valor)


def criar_resumo_executivo(
    metricas_duplicidade: pd.DataFrame,
    metricas_eficiencia: pd.DataFrame,
    comparativo_modelos: pd.DataFrame
) -> dict:
    """
    Cria um dicionário com os principais indicadores do projeto.
    """

    duplicidade_sem = obter_valor_metrica(
        metricas_duplicidade,
        "Sem Orquestrador",
        "percentual_clientes_duplicados"
    )

    duplicidade_com = obter_valor_metrica(
        metricas_duplicidade,
        "Com Orquestrador",
        "percentual_clientes_duplicados"
    )

    reducao_duplicidade = calcular_reducao_percentual(
        duplicidade_sem,
        duplicidade_com
    )

    momento_critico_sem = obter_valor_metrica(
        metricas_eficiencia,
        "Sem Orquestrador",
        "percentual_momento_critico"
    )

    momento_critico_com = obter_valor_metrica(
        metricas_eficiencia,
        "Com Orquestrador",
        "percentual_momento_critico"
    )

    melhor_modelo = comparativo_modelos.sort_values(
        by="f1_score",
        ascending=False
    ).iloc[0]

    resumo = {
        "duplicidade_sem_orquestrador_%": duplicidade_sem,
        "duplicidade_com_orquestrador_%": duplicidade_com,
        "reducao_duplicidade_%": reducao_duplicidade,
        "momento_critico_sem_orquestrador_%": momento_critico_sem,
        "momento_critico_com_orquestrador_%": momento_critico_com,
        "melhor_modelo_ml": melhor_modelo["modelo"],
        "melhor_f1_score": round(float(melhor_modelo["f1_score"]), 4),
        "melhor_recall": round(float(melhor_modelo["recall"]), 4)
    }

    return resumo


def criar_tabela_indicadores(resumo: dict) -> pd.DataFrame:
    """
    Transforma o resumo executivo em tabela analítica.
    """

    tabela = pd.DataFrame(
        list(resumo.items()),
        columns=["indicador", "valor"]
    )

    return tabela