"""
Módulo principal da máquina de estados do Agro Leads Orchestrator.

Responsável por:
- controlar status dos leads;
- aplicar cooldown;
- priorizar respostas de WhatsApp;
- simular transferência assistida;
- registrar vendas;
- consultar próximos leads para robôs e vendedores.

Versão otimizada:
- não recalcula score da base inteira a cada interação;
- recalcula apenas o lead afetado pela mudança de estado;
- reduz o tempo de execução do simulador operacional.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


class OrquestradorOmnichannelLeads:
    """
    Engine principal de orquestração omnichannel de leads agrícolas.
    """

    def __init__(self, caminho_banco: Path):
        self.caminho_banco = caminho_banco
        self.conexao = sqlite3.connect(caminho_banco)
        self.conexao.row_factory = sqlite3.Row
        self._configurar_conexao()

    def _configurar_conexao(self) -> None:
        """
        Aplica configurações básicas de performance e integridade.
        """

        self.conexao.execute("PRAGMA foreign_keys = ON;")
        self.conexao.execute("PRAGMA journal_mode = WAL;")
        self.conexao.execute("PRAGMA synchronous = NORMAL;")
        self.conexao.execute("PRAGMA temp_store = MEMORY;")

    @staticmethod
    def _agora() -> str:
        """
        Retorna timestamp atual formatado para SQLite.
        """

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _data_futura(horas: int = 0, dias: int = 0) -> str:
        """
        Retorna uma data futura formatada para SQLite.
        """

        data = datetime.now() + timedelta(hours=horas, days=dias)

        return data.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _expressao_score_sql() -> str:
        """
        Retorna a expressão SQL usada para cálculo do score.

        A expressão é centralizada para evitar duplicidade entre:
        - recálculo da base inteira;
        - recálculo individual de um lead.
        """

        return """
        ROUND(
            MIN(
                250,
                (
                    50 + (id_cliente % 50)
                )
                *
                CASE
                    WHEN estagio_atual = 'Plantio' THEN 1.50
                    WHEN estagio_atual = 'Safra' THEN 1.35
                    WHEN estagio_atual = 'Desenvolvimento' THEN 1.00
                    WHEN estagio_atual = 'Entresafra' THEN 0.70
                    ELSE 1.00
                END
                *
                CASE
                    WHEN cultura = 'Cana' THEN 1.10
                    WHEN cultura = 'Soja' THEN 1.00
                    WHEN cultura = 'Milho' THEN 0.95
                    ELSE 1.00
                END
                *
                CASE
                    WHEN status_atual = 'Fila Prioritária' THEN 1.80
                    WHEN status_atual = 'Disponível' THEN 1.00
                    WHEN status_atual = 'Em Atendimento' THEN 0.30
                    WHEN status_atual = 'Em Cooldown' THEN 0.15
                    WHEN status_atual = 'Convertido' THEN 0.00
                    ELSE 1.00
                END
            ),
            2
        )
        """

    def fechar_conexao(self) -> None:
        """
        Fecha conexão com o banco.
        """

        self.conexao.close()

    def registrar_evento(
        self,
        id_cliente: int,
        canal: str,
        resultado: str,
        observacao: str | None = None
    ) -> None:
        """
        Registra evento na tabela eventos_contato.

        Este método público faz commit.
        """

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal=canal,
            resultado=resultado,
            observacao=observacao
        )

        self.conexao.commit()

    def _registrar_evento_sem_commit(
        self,
        id_cliente: int,
        canal: str,
        resultado: str,
        observacao: str | None = None
    ) -> None:
        """
        Registra evento sem realizar commit imediato.

        Usado internamente para reduzir quantidade de commits no SQLite.
        """

        consulta_sql = """
        INSERT INTO eventos_contato (
            id_cliente,
            data_evento,
            canal,
            resultado,
            observacao
        )
        VALUES (?, ?, ?, ?, ?);
        """

        self.conexao.execute(
            consulta_sql,
            (
                id_cliente,
                self._agora(),
                canal,
                resultado,
                observacao
            )
        )

    def obter_lead_por_id(self, id_cliente: int) -> dict | None:
        """
        Busca um lead pelo id_cliente.
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
        WHERE id_cliente = ?;
        """

        cursor = self.conexao.execute(consulta_sql, (id_cliente,))
        resultado = cursor.fetchone()

        if resultado is None:
            return None

        return dict(resultado)

    def calcular_score_prioridade(self) -> None:
        """
        Recalcula o score de prioridade da base inteira.

        Use este método apenas em momentos controlados, por exemplo:
        - início do dia;
        - fim da simulação;
        - rotina batch.

        Evite chamar este método dentro de loops operacionais.
        """

        consulta_sql = f"""
        UPDATE leads
        SET score_prioridade = {self._expressao_score_sql()};
        """

        self.conexao.execute(consulta_sql)
        self.conexao.commit()

    def recalcular_score_cliente(self, id_cliente: int) -> None:
        """
        Recalcula o score de prioridade de apenas um cliente.
        """

        self._recalcular_score_cliente_sem_commit(id_cliente)
        self.conexao.commit()

    def _recalcular_score_cliente_sem_commit(self, id_cliente: int) -> None:
        """
        Recalcula o score de prioridade de apenas um cliente sem commit imediato.
        """

        consulta_sql = f"""
        UPDATE leads
        SET score_prioridade = {self._expressao_score_sql()}
        WHERE id_cliente = ?;
        """

        self.conexao.execute(consulta_sql, (id_cliente,))

    def liberar_cooldowns_expirados(self) -> int:
        """
        Libera leads cujo cooldown já expirou.

        Leads em cooldown vencido voltam para o status Disponível.
        Apenas os leads liberados têm score recalculado.
        """

        agora = self._agora()

        consulta_select = """
        SELECT id_cliente
        FROM leads
        WHERE status_atual = 'Em Cooldown'
        AND cooldown_ate <= ?;
        """

        cursor = self.conexao.execute(consulta_select, (agora,))
        ids_liberados = [linha["id_cliente"] for linha in cursor.fetchall()]

        if not ids_liberados:
            return 0

        consulta_update = """
        UPDATE leads
        SET
            status_atual = 'Disponível',
            cooldown_ate = NULL
        WHERE id_cliente = ?;
        """

        self.conexao.executemany(
            consulta_update,
            [(id_cliente,) for id_cliente in ids_liberados]
        )

        for id_cliente in ids_liberados:
            self._recalcular_score_cliente_sem_commit(id_cliente)

        self.conexao.commit()

        return len(ids_liberados)

    def obter_proximos_leads_robo(self, limite: int = 20) -> pd.DataFrame:
        """
        Retorna os próximos leads que podem ser acionados por robô.

        Regra:
        - libera cooldowns expirados;
        - busca apenas leads Disponíveis;
        - ordena por maior score;
        - não recalcula a base inteira.
        """

        self.liberar_cooldowns_expirados()

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
        WHERE status_atual = 'Disponível'
        ORDER BY score_prioridade DESC
        LIMIT ?;
        """

        return pd.read_sql_query(
            consulta_sql,
            self.conexao,
            params=(limite,)
        )

    def obter_proximos_leads_humano(self, limite: int = 20) -> pd.DataFrame:
        """
        Retorna os próximos leads para atendimento humano.

        Regra:
        - prioriza Fila Prioritária;
        - depois considera leads Disponíveis;
        - ordena por score;
        - não recalcula a base inteira.
        """

        self.liberar_cooldowns_expirados()

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
        WHERE status_atual IN ('Fila Prioritária', 'Disponível')
        ORDER BY
            CASE
                WHEN status_atual = 'Fila Prioritária' THEN 1
                WHEN status_atual = 'Disponível' THEN 2
                ELSE 3
            END,
            score_prioridade DESC
        LIMIT ?;
        """

        return pd.read_sql_query(
            consulta_sql,
            self.conexao,
            params=(limite,)
        )

    def registrar_evento_nao_atendido(
        self,
        id_cliente: int,
        canal: str = "Robô"
    ) -> None:
        """
        Aplica regra de não atendido.

        O lead entra em cooldown por 48 horas.
        """

        agora = self._agora()
        cooldown_ate = self._data_futura(horas=48)

        consulta_sql = """
        UPDATE leads
        SET
            status_atual = 'Em Cooldown',
            ultimo_contato = ?,
            cooldown_ate = ?
        WHERE id_cliente = ?;
        """

        self.conexao.execute(
            consulta_sql,
            (
                agora,
                cooldown_ate,
                id_cliente
            )
        )

        self._recalcular_score_cliente_sem_commit(id_cliente)

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal=canal,
            resultado="Não Atendido",
            observacao="Lead colocado em cooldown por 48 horas."
        )

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal="Sistema",
            resultado="Cooldown Aplicado",
            observacao=f"Cooldown válido até {cooldown_ate}."
        )

        self.conexao.commit()

    def registrar_resposta_whatsapp(self, id_cliente: int) -> None:
        """
        Registra resposta de WhatsApp.

        O lead entra imediatamente em Fila Prioritária.
        """

        agora = self._agora()

        consulta_sql = """
        UPDATE leads
        SET
            status_atual = 'Fila Prioritária',
            ultimo_contato = ?,
            cooldown_ate = NULL
        WHERE id_cliente = ?;
        """

        self.conexao.execute(
            consulta_sql,
            (
                agora,
                id_cliente
            )
        )

        self._recalcular_score_cliente_sem_commit(id_cliente)

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal="WhatsApp",
            resultado="Resposta WhatsApp",
            observacao="Cliente respondeu ao bot e entrou na fila prioritária."
        )

        self.conexao.commit()

    def registrar_atendimento_robo_atendido(self, id_cliente: int) -> None:
        """
        Registra cenário em que o robô ligou e o cliente atendeu.

        O sistema simula transferência assistida para vendedor humano.
        """

        agora = self._agora()

        consulta_sql = """
        UPDATE leads
        SET
            status_atual = 'Em Atendimento',
            ultimo_contato = ?,
            cooldown_ate = NULL
        WHERE id_cliente = ?;
        """

        self.conexao.execute(
            consulta_sql,
            (
                agora,
                id_cliente
            )
        )

        self._recalcular_score_cliente_sem_commit(id_cliente)

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal="Robô",
            resultado="Atendido",
            observacao="Cliente atendeu ligação do robô."
        )

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal="Sistema",
            resultado="Transferência Assistida",
            observacao="Chamada transferida automaticamente para vendedor humano."
        )

        self.conexao.commit()

    def registrar_atendimento_humano_sem_venda(self, id_cliente: int) -> None:
        """
        Registra atendimento humano sem venda imediata.

        O lead entra em Em Atendimento.
        """

        agora = self._agora()

        consulta_sql = """
        UPDATE leads
        SET
            status_atual = 'Em Atendimento',
            ultimo_contato = ?,
            cooldown_ate = NULL
        WHERE id_cliente = ?;
        """

        self.conexao.execute(
            consulta_sql,
            (
                agora,
                id_cliente
            )
        )

        self._recalcular_score_cliente_sem_commit(id_cliente)

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal="Humano",
            resultado="Atendido",
            observacao="Cliente atendido por vendedor humano, sem venda imediata."
        )

        self.conexao.commit()

    def registrar_sucesso_venda(self, id_cliente: int) -> None:
        """
        Registra venda realizada.

        O lead é convertido e fica fora da régua comercial por 30 dias.
        """

        agora = self._agora()
        bloqueio_ate = self._data_futura(dias=30)

        consulta_sql = """
        UPDATE leads
        SET
            status_atual = 'Convertido',
            ultimo_contato = ?,
            cooldown_ate = ?,
            score_prioridade = 0
        WHERE id_cliente = ?;
        """

        self.conexao.execute(
            consulta_sql,
            (
                agora,
                bloqueio_ate,
                id_cliente
            )
        )

        self._registrar_evento_sem_commit(
            id_cliente=id_cliente,
            canal="Humano",
            resultado="Venda",
            observacao=f"Venda realizada. Lead bloqueado até {bloqueio_ate}."
        )

        self.conexao.commit()

    def obter_resumo_status(self) -> pd.DataFrame:
        """
        Retorna resumo por status da base.
        """

        consulta_sql = """
        SELECT
            status_atual,
            COUNT(*) AS quantidade,
            ROUND(AVG(score_prioridade), 2) AS score_medio
        FROM leads
        GROUP BY status_atual
        ORDER BY quantidade DESC;
        """

        return pd.read_sql_query(consulta_sql, self.conexao)

    def obter_historico_cliente(self, id_cliente: int) -> pd.DataFrame:
        """
        Retorna histórico de eventos de um cliente.
        """

        consulta_sql = """
        SELECT
            id_evento,
            id_cliente,
            data_evento,
            canal,
            resultado,
            observacao
        FROM eventos_contato
        WHERE id_cliente = ?
        ORDER BY id_evento DESC;
        """

        return pd.read_sql_query(
            consulta_sql,
            self.conexao,
            params=(id_cliente,)
        )