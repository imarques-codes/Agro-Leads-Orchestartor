import sqlite3
from pathlib import Path


def criar_conexao(caminho_banco: Path) -> sqlite3.Connection:
    """
    Cria conexão SQLite com ajustes básicos de performance.
    """

    conexao = sqlite3.connect(caminho_banco)

    conexao.execute("PRAGMA journal_mode = WAL;")
    conexao.execute("PRAGMA synchronous = NORMAL;")
    conexao.execute("PRAGMA temp_store = MEMORY;")
    conexao.execute("PRAGMA cache_size = -200000;")
    conexao.execute("PRAGMA foreign_keys = ON;")

    return conexao


def remover_banco_existente(caminho_banco: Path) -> None:
    """
    Remove banco SQLite anterior, caso exista.
    """

    if caminho_banco.exists():
        caminho_banco.unlink()
        print(f"Banco anterior removido: {caminho_banco}")


def criar_tabela_leads(conexao: sqlite3.Connection) -> None:
    """
    Cria a tabela principal de leads.
    """

    consulta_sql = """
    CREATE TABLE IF NOT EXISTS leads (
        id_cliente INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL UNIQUE,

        cultura TEXT NOT NULL CHECK (
            cultura IN ('Cana', 'Soja', 'Milho')
        ),

        estagio_atual TEXT NOT NULL CHECK (
            estagio_atual IN (
                'Plantio',
                'Desenvolvimento',
                'Safra',
                'Entresafra'
            )
        ),

        status_atual TEXT NOT NULL CHECK (
            status_atual IN (
                'Disponível',
                'Em Cooldown',
                'Fila Prioritária',
                'Em Atendimento',
                'Convertido'
            )
        ),

        ultimo_contato TEXT,
        cooldown_ate TEXT,
        score_prioridade REAL NOT NULL
    );
    """

    conexao.execute(consulta_sql)
    conexao.commit()


def criar_tabela_eventos_contato(conexao: sqlite3.Connection) -> None:
    """
    Cria a tabela de eventos de contato.
    """

    consulta_sql = """
    CREATE TABLE IF NOT EXISTS eventos_contato (
        id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,

        data_evento TEXT NOT NULL,

        canal TEXT NOT NULL CHECK (
            canal IN ('Robô', 'Humano', 'WhatsApp', 'Sistema')
        ),

        resultado TEXT NOT NULL CHECK (
            resultado IN (
                'Atendido',
                'Não Atendido',
                'Venda',
                'Resposta WhatsApp',
                'Transferência Assistida',
                'Cooldown Aplicado',
                'Lead Gerado'
            )
        ),

        observacao TEXT,

        FOREIGN KEY (id_cliente) REFERENCES leads(id_cliente)
    );
    """

    conexao.execute(consulta_sql)
    conexao.commit()


def criar_schema(conexao: sqlite3.Connection) -> None:
    """
    Cria todas as tabelas do projeto.
    """

    criar_tabela_leads(conexao)
    criar_tabela_eventos_contato(conexao)

    print("Schema criado com sucesso.")


def criar_indices(conexao: sqlite3.Connection) -> None:
    """
    Cria índices para otimizar consultas da engine de orquestração.
    """

    indices_sql = [
        """
        CREATE INDEX IF NOT EXISTS idx_leads_status_score
        ON leads (status_atual, score_prioridade DESC);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_leads_status_cooldown
        ON leads (status_atual, cooldown_ate);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_leads_cultura_estagio
        ON leads (cultura, estagio_atual);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_leads_cooldown_ate
        ON leads (cooldown_ate);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_leads_telefone
        ON leads (telefone);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_leads_disponiveis_score
        ON leads (score_prioridade DESC)
        WHERE status_atual = 'Disponível';
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_leads_fila_prioritaria_score
        ON leads (score_prioridade DESC)
        WHERE status_atual = 'Fila Prioritária';
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_leads_cooldown_expiracao
        ON leads (cooldown_ate)
        WHERE status_atual = 'Em Cooldown';
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_eventos_cliente_data
        ON eventos_contato (id_cliente, data_evento);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_eventos_canal_resultado
        ON eventos_contato (canal, resultado);
        """
    ]

    for indice in indices_sql:
        conexao.execute(indice)

    conexao.commit()

    conexao.execute("ANALYZE;")
    conexao.execute("PRAGMA optimize;")
    conexao.commit()

    print("Índices criados e banco otimizado.")