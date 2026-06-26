import numpy as np


def calcular_score_inicial(
    culturas: np.ndarray,
    estagios: np.ndarray,
    status: np.ndarray,
    gerador: np.random.Generator
) -> np.ndarray:
    """
    Calcula o score inicial de prioridade comercial dos leads.

    A lógica considera:
    - Estágio agrícola do cliente;
    - Tipo de cultura;
    - Status atual dentro da máquina de estados;
    - Variação estatística simulada.

    Clientes em Plantio ou Safra recebem maior prioridade.
    """

    score_base = gerador.normal(
        loc=50,
        scale=15,
        size=len(culturas)
    )

    score_base = np.clip(score_base, 1, 100)

    multiplicador_estagio = np.select(
        [
            estagios == "Plantio",
            estagios == "Safra",
            estagios == "Desenvolvimento",
            estagios == "Entresafra"
        ],
        [
            1.50,
            1.35,
            1.00,
            0.70
        ],
        default=1.00
    )

    multiplicador_cultura = np.select(
        [
            culturas == "Cana",
            culturas == "Soja",
            culturas == "Milho"
        ],
        [
            1.10,
            1.00,
            0.95
        ],
        default=1.00
    )

    multiplicador_status = np.select(
        [
            status == "Fila Prioritária",
            status == "Disponível",
            status == "Em Atendimento",
            status == "Em Cooldown",
            status == "Convertido"
        ],
        [
            1.80,
            1.00,
            0.30,
            0.15,
            0.00
        ],
        default=1.00
    )

    score_final = (
        score_base
        * multiplicador_estagio
        * multiplicador_cultura
        * multiplicador_status
    )

    score_final = np.clip(score_final, 0, 250)

    return np.round(score_final, 2)