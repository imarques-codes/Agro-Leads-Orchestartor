"""
Módulo de estatísticas, qualidade de dados e engenharia de atributos.

Este módulo apoia o notebook 02_engenharia_dados.ipynb.
"""

import pandas as pd


def calcular_percentual_nulos(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula quantidade e percentual de valores nulos por coluna.
    """

    total_linhas = len(dados)

    resultado = pd.DataFrame({
        "coluna": dados.columns,
        "quantidade_nulos": dados.isna().sum().values,
        "percentual_nulos": (dados.isna().sum().values / total_linhas) * 100
    })

    resultado["percentual_nulos"] = resultado["percentual_nulos"].round(2)

    return resultado.sort_values(
        by="percentual_nulos",
        ascending=False
    )


def calcular_duplicidades(
    dados: pd.DataFrame,
    coluna: str
) -> dict:
    """
    Calcula duplicidades em uma coluna específica.
    """

    total_registros = len(dados)
    total_unicos = dados[coluna].nunique()
    total_duplicados = total_registros - total_unicos

    return {
        "coluna": coluna,
        "total_registros": total_registros,
        "total_unicos": total_unicos,
        "total_duplicados": total_duplicados,
        "percentual_duplicados": round(
            (total_duplicados / total_registros) * 100,
            2
        )
    }


def calcular_estatisticas_score(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estatísticas descritivas do score de prioridade.
    """

    estatisticas = dados["score_prioridade"].describe(
        percentiles=[0.25, 0.50, 0.75, 0.90, 0.95]
    ).to_frame()

    estatisticas.columns = ["score_prioridade"]

    return estatisticas.round(2)


def detectar_outliers_iqr(
    dados: pd.DataFrame,
    coluna: str
) -> pd.DataFrame:
    """
    Detecta outliers usando o método IQR.

    IQR = Q3 - Q1
    Limite inferior = Q1 - 1.5 * IQR
    Limite superior = Q3 + 1.5 * IQR
    """

    q1 = dados[coluna].quantile(0.25)
    q3 = dados[coluna].quantile(0.75)

    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    outliers = dados[
        (dados[coluna] < limite_inferior)
        | (dados[coluna] > limite_superior)
    ].copy()

    outliers["limite_inferior"] = limite_inferior
    outliers["limite_superior"] = limite_superior

    return outliers


def criar_faixa_score(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Cria uma coluna categórica com faixas de score.
    """

    dados = dados.copy()

    dados["faixa_score"] = pd.cut(
        dados["score_prioridade"],
        bins=[-1, 30, 60, 90, 130, 250],
        labels=[
            "Muito Baixo",
            "Baixo",
            "Médio",
            "Alto",
            "Prioridade Máxima"
        ]
    )

    return dados


def criar_indicadores_operacionais(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Cria indicadores derivados para apoiar análises futuras.
    """

    dados = dados.copy()

    dados["lead_em_momento_agricola_critico"] = dados[
        "estagio_atual"
    ].isin(["Plantio", "Safra"])

    dados["lead_disponivel_para_contato"] = dados[
        "status_atual"
    ].eq("Disponível")

    dados["lead_engajado_whatsapp"] = dados[
        "status_atual"
    ].eq("Fila Prioritária")

    dados["lead_bloqueado"] = dados[
        "status_atual"
    ].isin(["Em Cooldown", "Convertido"])

    return dados