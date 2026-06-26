# Agro Leads Orchestrator

Projeto de portfólio em Ciência de Dados, Engenharia de Dados e Engenharia de Software aplicado ao contexto de Agritechs.

O objetivo do projeto é desenvolver um **Orquestrador Omnichannel de Leads Agrícolas**, capaz de controlar contatos comerciais, evitar ligações duplicadas, aplicar regras de cooldown, priorizar clientes em momentos estratégicos de safra e organizar a operação comercial por meio de uma máquina de estados.

---

## 1. Problema de Negócio

Uma empresa de vendas de insumos e implementos agrícolas possui uma base com aproximadamente **950.000 leads** em nível nacional.

A operação comercial apresenta problemas graves:

* ausência de controle centralizado da base de clientes;
* vendedores humanos e robôs acessando a mesma lista sem coordenação;
* clientes recebendo múltiplas ligações no mesmo dia ou na mesma semana;
* robôs ligando para clientes que já foram abordados por vendedores;
* clientes sendo contatados mesmo após compra recente;
* aumento de reclamações em canais como Google e Reclame Aqui;
* queda na produtividade da equipe comercial;
* desgaste da marca e perda de oportunidades reais de venda.

---

## 2. Solução Proposta

A solução proposta é um **Orquestrador Omnichannel de Leads**, baseado em uma lógica de **State Machine**, ou Máquina de Estados.

O sistema controla o ciclo de vida de cada lead por meio dos seguintes status:

* Disponível;
* Em Cooldown;
* Fila Prioritária;
* Em Atendimento;
* Convertido.

A partir desses estados, o sistema decide se o cliente pode ser contatado, se deve aguardar uma janela de cooldown, se deve ser priorizado por um vendedor humano ou se deve ser retirado temporariamente da operação comercial.

---

## 3. Principais Regras de Negócio

### 3.1 Regra de Cooldown

Quando uma ligação humana ou automática resulta em **Não Atendido**, o lead entra em status **Em Cooldown** por 48 horas.

Durante esse período:

* robôs ficam proibidos de ligar para esse cliente;
* o cliente não retorna imediatamente para a fila genérica;
* o sistema reduz contatos repetitivos e inconvenientes.

---

### 3.2 Regra de WhatsApp

A empresa utiliza um bot de WhatsApp para mensagens automáticas.

Quando o cliente responde à mensagem:

* o lead muda imediatamente para **Fila Prioritária**;
* o cliente passa a ter prioridade de atendimento humano;
* o sistema entende que houve engajamento ativo.

---

### 3.3 Regra de Transferência Assistida

Quando o robô liga para um cliente disponível e o cliente atende:

* o sistema simula a transferência automática para um vendedor humano;
* o lead passa para o status **Em Atendimento**;
* a operação reduz perda de oportunidade comercial.

---

### 3.4 Regra de Safra e Plantio

Cada lead possui informações agrícolas importantes:

* cultura;
* estágio atual no campo;
* score de prioridade.

Culturas consideradas na simulação:

* Cana;
* Soja;
* Milho.

Estágios considerados:

* Plantio;
* Desenvolvimento;
* Safra;
* Entresafra.

Clientes em período de **Plantio** ou **Safra** recebem maior prioridade, pois estão em momentos comerciais mais relevantes para compra de insumos, fertilizantes, peças, manutenção ou implementos agrícolas.

---

## 4. Tecnologias Utilizadas

* Python;
* Pandas;
* NumPy;
* SQLite;
* Jupyter Notebook;
* Matplotlib;
* Scikit-learn;
* VS Code;
* Git e GitHub.

---

## 5. Estrutura do Projeto

```text
agro-leads-orchestrator/
│
├── dados/
│   └── agro_leads.db
│
├── notebooks/
│   └── 01_configuracao_banco_massa_sintetica.ipynb
│
├── src/
│   └── __init__.py
│
├── outputs/
│
├── docs/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## 6. Etapas do Projeto

### Parte 1 — Banco de Dados e Massa Sintética

Nesta etapa, o projeto cria um banco SQLite local chamado `agro_leads.db`.

A base sintética possui até **950.000 leads**, contendo informações como:

* id do cliente;
* nome;
* telefone;
* cultura agrícola;
* estágio atual;
* status operacional;
* último contato;
* data de liberação do cooldown;
* score de prioridade.

Também são criados índices SQL para garantir consultas rápidas em grande volume de dados.

---

### Parte 2 — Motor de Orquestração

A próxima etapa será a construção de uma engine em Python responsável por:

* calcular score de prioridade;
* buscar próximos leads para robô;
* aplicar cooldown de 48 horas;
* registrar resposta de WhatsApp;
* registrar venda;
* alterar status dos leads conforme a máquina de estados.

---

### Parte 3 — Simulador e Relatórios Analíticos

A etapa final irá simular um dia real de operação comercial com milhares de interações.

O objetivo será demonstrar:

* redução de ligações duplicadas;
* aumento da eficiência comercial;
* priorização de clientes em Safra e Plantio;
* impacto do WhatsApp na geração de oportunidades;
* visão analítica da operação.

---

## 7. Como Executar o Projeto

Clone o repositório:

```bash
git clone https://github.com/seu-usuario/agro-leads-orchestrator.git
```

Acesse a pasta:

```bash
cd agro-leads-orchestrator
```

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```bash
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Abra o VS Code:

```bash
code .
```

Execute o notebook:

```text
notebooks/01_configuracao_banco_massa_sintetica.ipynb
```

---

## 8. Principais Conceitos Aplicados

Este projeto demonstra conhecimentos em:

* modelagem de dados;
* banco de dados relacional;
* SQLite;
* geração de massa sintética;
* análise exploratória de dados;
* engenharia de dados local;
* regras de negócio;
* machine state;
* priorização por score;
* otimização com índices SQL;
* simulação operacional;
* análise de funil comercial;
* automação de processos;
* tomada de decisão orientada por dados.

---

## 9. Objetivo de Portfólio

Este projeto foi desenvolvido para demonstrar uma solução ponta a ponta envolvendo dados, negócio e tecnologia.

Ele combina contexto realista do agronegócio com práticas de engenharia de software, ciência de dados e engenharia de dados, criando uma solução aplicável a operações comerciais de Agritechs, revendas agrícolas, empresas de insumos, máquinas, implementos e tecnologia agrícola.

---

## 10. Status do Projeto

Em desenvolvimento.

* [x] Estrutura inicial do projeto;
* [x] Criação do banco SQLite;
* [x] Geração de massa sintética;
* [x] Criação de índices de performance;
* [ ] Motor de orquestração;
* [ ] Simulador de operação diária;
* [ ] Relatórios analíticos;
* [ ] Visualizações finais;
* [ ] Documentação técnica completa.
