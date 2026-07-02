"""
Módulo de simulação operacional do Agro Leads Orchestrator.

Versão otimizada:
- carrega os leads em memória;
- simula as transições da State Machine no DataFrame;
- grava alterações no SQLite em lote no final;
- evita milhares de consultas e commits individuais.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class SimuladorOperacao:
    """
    Simulador de interações comerciais com leads agrícolas.
    """

    def __init__(
        self,
        orquestrador,
        semente: int = 42
    ):
        self.orquestrador = orquestrador
        self.gerador = np.random.default_rng(semente)

    @staticmethod
    def _agora() -> str:
        """
        Retorna timestamp atual formatado.
        """

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _data_futura(horas: int = 0, dias: int = 0) -> str:
        """
        Retorna data futura formatada.
        """

        data = datetime.now() + timedelta(hours=horas, days=dias)

        return data.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _calcular_score_linha(
        id_cliente: int,
        cultura: str,
        estagio_atual: str,
        status_atual: str
    ) -> float:
        """
        Calcula score de prioridade de um único lead.

        Mantém a mesma lógica do orquestrador, porém em Python,
        para evitar UPDATE massivo no SQLite durante a simulação.
        """

        score_base = 50 + (int(id_cliente) % 50)

        multiplicador_estagio = {
            "Plantio": 1.50,
            "Safra": 1.35,
            "Desenvolvimento": 1.00,
            "Entresafra": 0.70
        }.get(estagio_atual, 1.00)

        multiplicador_cultura = {
            "Cana": 1.10,
            "Soja": 1.00,
            "Milho": 0.95
        }.get(cultura, 1.00)

        multiplicador_status = {
            "Fila Prioritária": 1.80,
            "Disponível": 1.00,
            "Em Atendimento": 0.30,
            "Em Cooldown": 0.15,
            "Convertido": 0.00
        }.get(status_atual, 1.00)

        score = (
            score_base
            * multiplicador_estagio
            * multiplicador_cultura
            * multiplicador_status
        )

        return round(min(score, 250), 2)

    def _sortear_canal(self) -> str:
        """
        Sorteia canal da interação.
        """

        return self.gerador.choice(
            ["Robô", "Humano"],
            p=[0.65, 0.35]
        )

    def _sortear_resultado_robo(self) -> str:
        """
        Sorteia resultado da ligação do robô.
        """

        return self.gerador.choice(
            [
                "Não Atendido",
                "Atendido com Transferência",
                "Resposta WhatsApp"
            ],
            p=[0.65, 0.25, 0.10]
        )

    def _sortear_resultado_humano(self) -> str:
        """
        Sorteia resultado da interação humana.
        """

        return self.gerador.choice(
            [
                "Não Atendido",
                "Venda",
                "Resposta WhatsApp",
                "Atendido sem Venda"
            ],
            p=[0.50, 0.15, 0.10, 0.25]
        )

    def _escolher_lead_ponderado(
        self,
        dados_leads: pd.DataFrame
    ) -> pd.Series | None:
        """
        Escolhe um lead ponderando pelo score.
        """

        if dados_leads.empty:
            return None

        pesos = dados_leads["score_prioridade"].fillna(0).clip(lower=1)
        probabilidades = pesos / pesos.sum()

        indice_escolhido = self.gerador.choice(
            dados_leads.index,
            p=probabilidades
        )

        return dados_leads.loc[indice_escolhido]

    def simular_baseline_sem_orquestracao(
        self,
        quantidade_interacoes: int = 300
    ) -> pd.DataFrame:
        """
        Simula operação sem orquestrador.

        Nesse cenário, os leads são escolhidos com reposição,
        permitindo duplicidade de contato.
        """

        consulta_sql = """
        SELECT
            id_cliente,
            cultura,
            estagio_atual,
            status_atual,
            score_prioridade
        FROM leads
        WHERE status_atual <> 'Convertido';
        """

        dados_base = pd.read_sql_query(
            consulta_sql,
            self.orquestrador.conexao
        )

        registros = []

        for numero_interacao in range(1, quantidade_interacoes + 1):
            lead = dados_base.sample(
                n=1,
                replace=True,
                random_state=int(self.gerador.integers(0, 1_000_000))
            ).iloc[0]

            canal = self._sortear_canal()

            if canal == "Robô":
                resultado = self._sortear_resultado_robo()
            else:
                resultado = self._sortear_resultado_humano()

            registros.append({
                "cenario": "Sem Orquestrador",
                "numero_interacao": numero_interacao,
                "data_interacao": self._agora(),
                "id_cliente": int(lead["id_cliente"]),
                "canal": canal,
                "resultado": resultado,
                "cultura": lead["cultura"],
                "estagio_atual": lead["estagio_atual"],
                "status_antes": lead["status_atual"],
                "status_depois": lead["status_atual"],
                "score_prioridade": float(lead["score_prioridade"])
            })

        return pd.DataFrame(registros)

    def simular_dia_com_orquestracao(
        self,
        quantidade_interacoes: int = 300,
        limite_fila: int = 100
    ) -> pd.DataFrame:
        """
        Simula operação com orquestrador de forma otimizada.

        A lógica é executada em memória e persistida em lote no final.
        """

        consulta_sql = """
        SELECT
            id_cliente,
            nome,
            telefone,
            cultura,
            estagio_atual,
            status_atual,
            ultimo_contato,
            cooldown_ate,
            score_prioridade
        FROM leads
        WHERE status_atual <> 'Convertido';
        """

        dados_operacao = pd.read_sql_query(
            consulta_sql,
            self.orquestrador.conexao
        )

        dados_operacao = dados_operacao.set_index("id_cliente", drop=False)

        registros_logs = []
        registros_eventos = []
        ids_alterados = set()

        for numero_interacao in range(1, quantidade_interacoes + 1):
            canal = self._sortear_canal()

            if canal == "Robô":
                fila = dados_operacao[
                    dados_operacao["status_atual"] == "Disponível"
                ].sort_values(
                    by="score_prioridade",
                    ascending=False
                ).head(limite_fila)
            else:
                fila = dados_operacao[
                    dados_operacao["status_atual"].isin(
                        ["Fila Prioritária", "Disponível"]
                    )
                ].copy()

                fila["ordem_status"] = fila["status_atual"].map({
                    "Fila Prioritária": 1,
                    "Disponível": 2
                })

                fila = fila.sort_values(
                    by=["ordem_status", "score_prioridade"],
                    ascending=[True, False]
                ).head(limite_fila)

            lead = self._escolher_lead_ponderado(fila)

            if lead is None:
                continue

            id_cliente = int(lead["id_cliente"])
            cultura = lead["cultura"]
            estagio_atual = lead["estagio_atual"]
            status_antes = lead["status_atual"]
            score_antes = float(lead["score_prioridade"])

            data_evento = self._agora()
            cooldown_ate = None

            if canal == "Robô":
                resultado = self._sortear_resultado_robo()

                if resultado == "Não Atendido":
                    status_depois = "Em Cooldown"
                    cooldown_ate = self._data_futura(horas=48)

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Robô",
                        "Não Atendido",
                        "Lead colocado em cooldown por 48 horas."
                    ))

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Sistema",
                        "Cooldown Aplicado",
                        f"Cooldown válido até {cooldown_ate}."
                    ))

                elif resultado == "Atendido com Transferência":
                    status_depois = "Em Atendimento"

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Robô",
                        "Atendido",
                        "Cliente atendeu ligação do robô."
                    ))

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Sistema",
                        "Transferência Assistida",
                        "Chamada transferida automaticamente para vendedor humano."
                    ))

                else:
                    status_depois = "Fila Prioritária"

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "WhatsApp",
                        "Resposta WhatsApp",
                        "Cliente respondeu ao bot e entrou na fila prioritária."
                    ))

            else:
                resultado = self._sortear_resultado_humano()

                if resultado == "Não Atendido":
                    status_depois = "Em Cooldown"
                    cooldown_ate = self._data_futura(horas=48)

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Humano",
                        "Não Atendido",
                        "Lead colocado em cooldown por 48 horas."
                    ))

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Sistema",
                        "Cooldown Aplicado",
                        f"Cooldown válido até {cooldown_ate}."
                    ))

                elif resultado == "Venda":
                    status_depois = "Convertido"
                    cooldown_ate = self._data_futura(dias=30)

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Humano",
                        "Venda",
                        f"Venda realizada. Lead bloqueado até {cooldown_ate}."
                    ))

                elif resultado == "Resposta WhatsApp":
                    status_depois = "Fila Prioritária"

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "WhatsApp",
                        "Resposta WhatsApp",
                        "Cliente respondeu ao bot e entrou na fila prioritária."
                    ))

                else:
                    status_depois = "Em Atendimento"

                    registros_eventos.append((
                        id_cliente,
                        data_evento,
                        "Humano",
                        "Atendido",
                        "Cliente atendido por vendedor humano, sem venda imediata."
                    ))

            score_depois = self._calcular_score_linha(
                id_cliente=id_cliente,
                cultura=cultura,
                estagio_atual=estagio_atual,
                status_atual=status_depois
            )

            dados_operacao.at[id_cliente, "status_atual"] = status_depois
            dados_operacao.at[id_cliente, "ultimo_contato"] = data_evento
            dados_operacao.at[id_cliente, "cooldown_ate"] = cooldown_ate
            dados_operacao.at[id_cliente, "score_prioridade"] = score_depois

            ids_alterados.add(id_cliente)

            registros_logs.append({
                "cenario": "Com Orquestrador",
                "numero_interacao": numero_interacao,
                "data_interacao": data_evento,
                "id_cliente": id_cliente,
                "canal": canal,
                "resultado": resultado,
                "cultura": cultura,
                "estagio_atual": estagio_atual,
                "status_antes": status_antes,
                "status_depois": status_depois,
                "score_prioridade": score_depois,
                "score_antes": score_antes
            })

        self._persistir_alteracoes(
            dados_operacao=dados_operacao,
            ids_alterados=ids_alterados,
            registros_eventos=registros_eventos
        )

        return pd.DataFrame(registros_logs)

    def _persistir_alteracoes(
        self,
        dados_operacao: pd.DataFrame,
        ids_alterados: set[int],
        registros_eventos: list[tuple]
    ) -> None:
        """
        Persiste alterações da simulação no SQLite em lote.
        """

        if ids_alterados:
            dados_alterados = dados_operacao.loc[list(ids_alterados)]

            parametros_update = [
                (
                    linha["status_atual"],
                    linha["ultimo_contato"],
                    linha["cooldown_ate"],
                    float(linha["score_prioridade"]),
                    int(linha["id_cliente"])
                )
                for _, linha in dados_alterados.iterrows()
            ]

            consulta_update = """
            UPDATE leads
            SET
                status_atual = ?,
                ultimo_contato = ?,
                cooldown_ate = ?,
                score_prioridade = ?
            WHERE id_cliente = ?;
            """

            self.orquestrador.conexao.executemany(
                consulta_update,
                parametros_update
            )

        if registros_eventos:
            consulta_eventos = """
            INSERT INTO eventos_contato (
                id_cliente,
                data_evento,
                canal,
                resultado,
                observacao
            )
            VALUES (?, ?, ?, ?, ?);
            """

            self.orquestrador.conexao.executemany(
                consulta_eventos,
                registros_eventos
            )

        self.orquestrador.conexao.commit()


def calcular_metricas_duplicidade(
    logs_interacoes: pd.DataFrame
) -> pd.DataFrame:
    """
    Calcula métricas de duplicidade de contato por cenário.
    """

    contatos_por_cliente = (
        logs_interacoes
        .groupby(["cenario", "id_cliente"])
        .agg(
            quantidade_contatos=("numero_interacao", "count")
        )
        .reset_index()
    )

    resumo = (
        contatos_por_cliente
        .groupby("cenario")
        .agg(
            clientes_contatados=("id_cliente", "count"),
            clientes_com_duplicidade=(
                "quantidade_contatos",
                lambda x: (x > 1).sum()
            ),
            max_contatos_mesmo_cliente=("quantidade_contatos", "max"),
            media_contatos_por_cliente=("quantidade_contatos", "mean")
        )
        .reset_index()
    )

    resumo["percentual_clientes_duplicados"] = (
        resumo["clientes_com_duplicidade"]
        / resumo["clientes_contatados"]
        * 100
    )

    return resumo.round(2)


def calcular_metricas_eficiencia(
    logs_interacoes: pd.DataFrame
) -> pd.DataFrame:
    """
    Calcula métricas operacionais de eficiência.
    """

    dados = logs_interacoes.copy()

    dados["momento_agricola_critico"] = dados[
        "estagio_atual"
    ].isin(["Plantio", "Safra"])

    resumo = (
        dados
        .groupby("cenario")
        .agg(
            total_interacoes=("numero_interacao", "count"),
            interacoes_em_momento_critico=(
                "momento_agricola_critico",
                "sum"
            ),
            vendas=(
                "resultado",
                lambda x: (x == "Venda").sum()
            ),
            respostas_whatsapp=(
                "resultado",
                lambda x: (x == "Resposta WhatsApp").sum()
            ),
            nao_atendidos=(
                "resultado",
                lambda x: (x == "Não Atendido").sum()
            )
        )
        .reset_index()
    )

    resumo["percentual_momento_critico"] = (
        resumo["interacoes_em_momento_critico"]
        / resumo["total_interacoes"]
        * 100
    )

    resumo["taxa_venda"] = (
        resumo["vendas"]
        / resumo["total_interacoes"]
        * 100
    )

    resumo["taxa_whatsapp"] = (
        resumo["respostas_whatsapp"]
        / resumo["total_interacoes"]
        * 100
    )

    resumo["taxa_nao_atendido"] = (
        resumo["nao_atendidos"]
        / resumo["total_interacoes"]
        * 100
    )

    return resumo.round(2)