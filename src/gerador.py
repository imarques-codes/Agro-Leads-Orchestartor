"""
Módulo responsável pela geração de dados sintéticos de leads agrícolas.
"""

import time

import numpy as np
import pandas as pd

from src.score import calcular_score_inicial


NOMES = np.array([
    "João", "José", "Carlos", "Marcos", "Paulo", "Lucas",
    "Mateus", "Rafael", "Fernando", "Bruno", "Ricardo",
    "André", "Gustavo", "Roberto", "Eduardo", "Henrique",
    "Igor", "Daniel", "Felipe", "Luiz", "Marcelo"
])

SOBRENOMES = np.array([
    "Silva", "Santos", "Oliveira", "Souza", "Pereira",
    "Costa", "Rodrigues", "Almeida", "Nascimento",
    "Lima", "Araújo", "Fernandes", "Carvalho", "Gomes",
    "Martins", "Barbosa", "Ribeiro", "Moura"
])

DDDS = np.array([
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    34, 35, 43, 44, 62, 64, 65, 66, 67
])


def gerar_nomes(
    quantidade: int,
    gerador: np.random.Generator
) -> np.ndarray:
    """
    Gera nomes sintéticos de clientes.
    """

    primeiros_nomes = gerador.choice(NOMES, size=quantidade)
    sobrenomes = gerador.choice(SOBRENOMES, size=quantidade)

    nomes_completos = np.char.add(
        np.char.add(primeiros_nomes.astype(str), " "),
        sobrenomes.astype(str)
    )

    return nomes_completos


def gerar_telefones_unicos(
    ids_clientes: np.ndarray,
    gerador: np.random.Generator
) -> list[str]:
    """
    Gera telefones únicos usando o id_cliente como parte do número.
    """

    ddds = gerador.choice(DDDS, size=len(ids_clientes))

    telefones = [
        f"55{ddd}9{id_cliente:08d}"
        for ddd, id_cliente in zip(ddds, ids_clientes)
    ]

    return telefones


def gerar_perfil_agricola(
    quantidade: int,
    gerador: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Gera cultura agrícola e estágio atual do cliente.
    """

    culturas = gerador.choice(
        ["Cana", "Soja", "Milho"],
        size=quantidade,
        p=[0.45, 0.35, 0.20]
    )

    estagios = gerador.choice(
        ["Plantio", "Desenvolvimento", "Safra", "Entresafra"],
        size=quantidade,
        p=[0.25, 0.30, 0.25, 0.20]
    )

    return culturas, estagios


def gerar_status_leads(
    quantidade: int,
    gerador: np.random.Generator
) -> np.ndarray:
    """
    Gera status inicial dos leads na máquina de estados.
    """

    status = gerador.choice(
        [
            "Disponível",
            "Em Cooldown",
            "Fila Prioritária",
            "Em Atendimento",
            "Convertido"
        ],
        size=quantidade,
        p=[0.72, 0.12, 0.06, 0.04, 0.06]
    )

    return status


def gerar_datas_operacionais(
    status: np.ndarray,
    gerador: np.random.Generator
) -> tuple[pd.Series, pd.Series]:
    """
    Gera datas de último contato e cooldown.
    """

    quantidade = len(status)
    agora = pd.Timestamp.now().floor("s")

    minutos_desde_ultimo_contato = gerador.integers(
        low=0,
        high=60 * 24 * 30,
        size=quantidade
    )

    ultimo_contato = agora - pd.to_timedelta(
        minutos_desde_ultimo_contato,
        unit="m"
    )

    ultimo_contato = pd.Series(ultimo_contato).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    sem_contato_anterior = gerador.random(quantidade) < 0.18
    ultimo_contato.loc[sem_contato_anterior] = None

    cooldown_ate = pd.Series([None] * quantidade, dtype="object")

    mascara_cooldown = status == "Em Cooldown"

    horas_cooldown = gerador.integers(
        low=1,
        high=48,
        size=mascara_cooldown.sum()
    )

    cooldown_ate.loc[mascara_cooldown] = (
        agora + pd.to_timedelta(horas_cooldown, unit="h")
    ).strftime("%Y-%m-%d %H:%M:%S")

    mascara_convertido = status == "Convertido"

    cooldown_ate.loc[mascara_convertido] = (
        agora + pd.Timedelta(days=30)
    ).strftime("%Y-%m-%d %H:%M:%S")

    return ultimo_contato, cooldown_ate


def gerar_lote_leads(
    id_inicial: int,
    quantidade_lote: int,
    gerador: np.random.Generator
) -> pd.DataFrame:
    """
    Gera um lote de leads sintéticos.
    """

    ids_clientes = np.arange(
        id_inicial,
        id_inicial + quantidade_lote
    )

    nomes = gerar_nomes(
        quantidade=quantidade_lote,
        gerador=gerador
    )

    telefones = gerar_telefones_unicos(
        ids_clientes=ids_clientes,
        gerador=gerador
    )

    culturas, estagios = gerar_perfil_agricola(
        quantidade=quantidade_lote,
        gerador=gerador
    )

    status = gerar_status_leads(
        quantidade=quantidade_lote,
        gerador=gerador
    )

    ultimo_contato, cooldown_ate = gerar_datas_operacionais(
        status=status,
        gerador=gerador
    )

    score_prioridade = calcular_score_inicial(
        culturas=culturas,
        estagios=estagios,
        status=status,
        gerador=gerador
    )

    dados_lote = pd.DataFrame({
        "id_cliente": ids_clientes,
        "nome": nomes,
        "telefone": telefones,
        "cultura": culturas,
        "estagio_atual": estagios,
        "status_atual": status,
        "ultimo_contato": ultimo_contato,
        "cooldown_ate": cooldown_ate,
        "score_prioridade": score_prioridade
    })

    return dados_lote


def inserir_leads_em_lotes(
    conexao,
    quantidade_total: int,
    tamanho_lote: int,
    gerador: np.random.Generator
) -> None:
    """
    Insere leads no banco SQLite em lotes.
    """

    inicio = time.time()

    total_inserido = 0
    id_atual = 1

    while total_inserido < quantidade_total:
        quantidade_restante = quantidade_total - total_inserido
        quantidade_lote_atual = min(tamanho_lote, quantidade_restante)

        print(
            f"Gerando registros "
            f"{total_inserido + 1:,} até "
            f"{total_inserido + quantidade_lote_atual:,}"
        )

        dados_lote = gerar_lote_leads(
            id_inicial=id_atual,
            quantidade_lote=quantidade_lote_atual,
            gerador=gerador
        )

        dados_lote.to_sql(
            name="leads",
            con=conexao,
            if_exists="append",
            index=False,
            chunksize=50_000
        )

        total_inserido += quantidade_lote_atual
        id_atual += quantidade_lote_atual

        print(f"Total inserido: {total_inserido:,}")

    conexao.commit()

    tempo_total = time.time() - inicio

    print("\nCarga concluída.")
    print(f"Total inserido: {total_inserido:,}")
    print(f"Tempo total: {tempo_total:.2f} segundos")