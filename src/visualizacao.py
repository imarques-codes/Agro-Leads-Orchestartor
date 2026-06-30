"""
Módulo de visualização do projeto Agro Leads Orchestrator.

Centraliza funções gráficas utilizadas nos notebooks de análise.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def salvar_grafico(caminho_saida: Path) -> None:
    """
    Salva o gráfico atual em arquivo PNG.
    """

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout()
    plt.savefig(
        caminho_saida,
        dpi=150,
        bbox_inches="tight"
    )


def grafico_barras_contagem(
    dados: pd.DataFrame,
    coluna: str,
    titulo: str,
    nome_eixo_x: str,
    nome_eixo_y: str,
    caminho_saida: Path | None = None
) -> None:
    """
    Cria gráfico de barras com contagem de registros por categoria.
    """

    contagem = (
        dados[coluna]
        .value_counts()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(10, 5))
    plt.bar(contagem.index.astype(str), contagem.values)

    plt.title(titulo)
    plt.xlabel(nome_eixo_x)
    plt.ylabel(nome_eixo_y)
    plt.xticks(rotation=30, ha="right")

    if caminho_saida:
        salvar_grafico(caminho_saida)

    plt.show()


def grafico_histograma_score(
    dados: pd.DataFrame,
    coluna_score: str,
    titulo: str,
    caminho_saida: Path | None = None
) -> None:
    """
    Cria histograma para análise de distribuição do score.
    """

    plt.figure(figsize=(10, 5))
    plt.hist(
        dados[coluna_score],
        bins=40
    )

    plt.title(titulo)
    plt.xlabel("Score de Prioridade")
    plt.ylabel("Quantidade de Leads")

    if caminho_saida:
        salvar_grafico(caminho_saida)

    plt.show()


def grafico_barras_agregado(
    dados: pd.DataFrame,
    coluna_categoria: str,
    coluna_valor: str,
    titulo: str,
    nome_eixo_x: str,
    nome_eixo_y: str,
    caminho_saida: Path | None = None
) -> None:
    """
    Cria gráfico de barras usando média agregada por categoria.
    """

    dados_agregados = (
        dados
        .groupby(coluna_categoria)[coluna_valor]
        .mean()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(10, 5))
    plt.bar(dados_agregados.index.astype(str), dados_agregados.values)

    plt.title(titulo)
    plt.xlabel(nome_eixo_x)
    plt.ylabel(nome_eixo_y)
    plt.xticks(rotation=30, ha="right")

    if caminho_saida:
        salvar_grafico(caminho_saida)

    plt.show()


def grafico_boxplot_score_por_categoria(
    dados: pd.DataFrame,
    coluna_categoria: str,
    coluna_score: str,
    titulo: str,
    caminho_saida: Path | None = None
) -> None:
    """
    Cria boxplot do score por categoria.
    """

    categorias = dados[coluna_categoria].dropna().unique()

    dados_plot = [
        dados.loc[dados[coluna_categoria] == categoria, coluna_score]
        for categoria in categorias
    ]

    plt.figure(figsize=(10, 5))
    plt.boxplot(
        dados_plot,
        tick_labels=categorias
    )

    plt.title(titulo)
    plt.xlabel(coluna_categoria)
    plt.ylabel(coluna_score)
    plt.xticks(rotation=30, ha="right")

    if caminho_saida:
        salvar_grafico(caminho_saida)

    plt.show()


def grafico_matriz_cultura_estagio(
    matriz: pd.DataFrame,
    titulo: str,
    caminho_saida: Path | None = None
) -> None:
    """
    Cria visualização tipo matriz para cultura x estágio agrícola.
    """

    plt.figure(figsize=(10, 6))
    plt.imshow(matriz.values, aspect="auto")

    plt.title(titulo)
    plt.xlabel("Estágio Atual")
    plt.ylabel("Cultura")

    plt.xticks(
        ticks=range(len(matriz.columns)),
        labels=matriz.columns,
        rotation=30,
        ha="right"
    )

    plt.yticks(
        ticks=range(len(matriz.index)),
        labels=matriz.index
    )

    plt.colorbar(label="Quantidade de Leads")

    if caminho_saida:
        salvar_grafico(caminho_saida)

    plt.show()