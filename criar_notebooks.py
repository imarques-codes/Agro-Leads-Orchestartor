from pathlib import Path
import nbformat as nbf

pasta_notebooks = Path("notebooks")
pasta_notebooks.mkdir(exist_ok=True)

notebooks = [
    ("01_configuracao_projeto.ipynb", "01 - Configuração do Projeto"),
    ("02_engenharia_dados.ipynb", "02 - Engenharia de Dados"),
    ("03_analise_exploratoria.ipynb", "03 - Análise Exploratória"),
    ("04_state_machine.ipynb", "04 - State Machine"),
    ("05_simulador_operacao.ipynb", "05 - Simulador de Operação"),
    ("06_machine_learning.ipynb", "06 - Machine Learning"),
    ("07_dashboard_final.ipynb", "07 - Dashboard Final"),
]

for nome_arquivo, titulo in notebooks:
    caminho_notebook = pasta_notebooks / nome_arquivo

    if caminho_notebook.exists():
        print(f"Notebook já existe: {caminho_notebook}")
        continue

    notebook = nbf.v4.new_notebook()

    notebook.cells = [
        nbf.v4.new_markdown_cell(
            f"# {titulo}\n\n"
            "Notebook criado para o projeto Agro Leads Orchestrator."
        )
    ]

    nbf.write(notebook, caminho_notebook)
    print(f"Notebook criado: {caminho_notebook}")

print("\nProcesso finalizado.")
