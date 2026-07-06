"""
Módulo de modelagem preditiva do Agro Leads Orchestrator.

Responsável por:
- preparar base de machine learning;
- criar variável alvo;
- separar treino e teste;
- treinar modelos;
- avaliar desempenho;
- extrair importância de variáveis.
"""

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def criar_base_modelagem(logs_simulacao: pd.DataFrame) -> pd.DataFrame:
    """
    Cria a base de modelagem a partir dos logs de simulação.

    A variável alvo será:
    - 1 para interações com resultado Venda;
    - 0 para demais resultados.
    """

    dados = logs_simulacao.copy()

    dados["converteu"] = dados["resultado"].eq("Venda").astype(int)

    colunas_necessarias = [
        "cenario",
        "canal",
        "cultura",
        "estagio_atual",
        "status_antes",
        "score_prioridade",
        "converteu"
    ]

    dados = dados[colunas_necessarias].copy()

    dados = dados.dropna(subset=[
        "cenario",
        "canal",
        "cultura",
        "estagio_atual",
        "status_antes",
        "score_prioridade",
        "converteu"
    ])

    return dados


def separar_variaveis(
    dados_modelagem: pd.DataFrame
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Separa variáveis explicativas e variável alvo.
    """

    variaveis_explicativas = dados_modelagem.drop(columns=["converteu"])
    variavel_alvo = dados_modelagem["converteu"]

    return variaveis_explicativas, variavel_alvo


def criar_preprocessador() -> ColumnTransformer:
    """
    Cria o pré-processador com:
    - OneHotEncoder para variáveis categóricas;
    - StandardScaler para variável numérica.
    """

    colunas_categoricas = [
        "cenario",
        "canal",
        "cultura",
        "estagio_atual",
        "status_antes"
    ]

    colunas_numericas = [
        "score_prioridade"
    ]

    preprocessador = ColumnTransformer(
        transformers=[
            (
                "categoricas",
                OneHotEncoder(handle_unknown="ignore"),
                colunas_categoricas
            ),
            (
                "numericas",
                StandardScaler(),
                colunas_numericas
            )
        ]
    )

    return preprocessador


def criar_pipeline_regressao_logistica() -> Pipeline:
    """
    Cria pipeline com Regressão Logística.
    """

    preprocessador = criar_preprocessador()

    modelo = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessador", preprocessador),
            ("modelo", modelo)
        ]
    )

    return pipeline


def criar_pipeline_random_forest() -> Pipeline:
    """
    Cria pipeline com Random Forest.
    """

    preprocessador = criar_preprocessador()

    modelo = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessador", preprocessador),
            ("modelo", modelo)
        ]
    )

    return pipeline


def avaliar_modelo(
    modelo: Pipeline,
    x_teste: pd.DataFrame,
    y_teste: pd.Series,
    nome_modelo: str
) -> dict:
    """
    Avalia um modelo de classificação.
    """

    predicoes = modelo.predict(x_teste)

    if hasattr(modelo, "predict_proba"):
        probabilidades = modelo.predict_proba(x_teste)[:, 1]
    else:
        probabilidades = predicoes

    metricas = {
        "modelo": nome_modelo,
        "acuracia": accuracy_score(y_teste, predicoes),
        "precisao": precision_score(y_teste, predicoes, zero_division=0),
        "recall": recall_score(y_teste, predicoes, zero_division=0),
        "f1_score": f1_score(y_teste, predicoes, zero_division=0)
    }

    if y_teste.nunique() > 1:
        metricas["roc_auc"] = roc_auc_score(y_teste, probabilidades)
    else:
        metricas["roc_auc"] = None

    return metricas


def obter_matriz_confusao(
    modelo: Pipeline,
    x_teste: pd.DataFrame,
    y_teste: pd.Series
) -> pd.DataFrame:
    """
    Retorna matriz de confusão como DataFrame.
    """

    predicoes = modelo.predict(x_teste)

    matriz = confusion_matrix(y_teste, predicoes)

    return pd.DataFrame(
        matriz,
        index=["Real Não Venda", "Real Venda"],
        columns=["Previsto Não Venda", "Previsto Venda"]
    )


def obter_relatorio_classificacao(
    modelo: Pipeline,
    x_teste: pd.DataFrame,
    y_teste: pd.Series
) -> pd.DataFrame:
    """
    Retorna classification report como DataFrame.
    """

    predicoes = modelo.predict(x_teste)

    relatorio = classification_report(
        y_teste,
        predicoes,
        output_dict=True,
        zero_division=0
    )

    return pd.DataFrame(relatorio).transpose()


def obter_importancia_variaveis_random_forest(
    modelo: Pipeline
) -> pd.DataFrame:
    """
    Extrai importância das variáveis de um pipeline com Random Forest.
    """

    preprocessador = modelo.named_steps["preprocessador"]
    classificador = modelo.named_steps["modelo"]

    nomes_variaveis = preprocessador.get_feature_names_out()

    importancias = classificador.feature_importances_

    dados_importancia = pd.DataFrame({
        "variavel": nomes_variaveis,
        "importancia": importancias
    })

    dados_importancia = dados_importancia.sort_values(
        by="importancia",
        ascending=False
    )

    return dados_importancia