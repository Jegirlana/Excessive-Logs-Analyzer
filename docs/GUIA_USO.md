# Guia de Uso - Excessive Logs Analyzer

Guia completo para utilizar a ferramenta de análise de logs excessivos.

---

## 📋 Índice

1. [Instalação](#instalação)
2. [Como Funciona](#como-funciona)
3. [Iniciando a Interface Gráfica](#iniciando-a-interface-gráfica)
4. [Configuração](#configuração)
5. [Interpretação de Resultados](#interpretação-de-resultados)
6. [Exemplos Práticos](#exemplos-práticos)
7. [Troubleshooting](#troubleshooting)

---

## Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Node.js 18 ou superior (apenas para usar Claude/ChatGPT via Puter)

### Instalando os Pré-requisitos

Se você ainda não tem Python ou Node.js instalados, siga as instruções abaixo para o seu sistema operacional.

#### Linux (Ubuntu/Debian)

```bash
# Atualizar lista de pacotes
sudo apt update

# Instalar Python 3 e pip
sudo apt install -y python3 python3-pip python3-venv

# Verificar instalação
python3 --version
pip3 --version

# Instalar Node.js 18+ via NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar instalação
node --version
npm --version
```

#### Linux (Fedora/RHEL/CentOS)

```bash
# Instalar Python 3 e pip
sudo dnf install -y python3 python3-pip

# Instalar Node.js 18+
sudo dnf install -y nodejs npm

# Verificar instalação
python3 --version
node --version
```

#### macOS

```bash
# Instalar Homebrew (se ainda não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python 3
brew install python

# Instalar Node.js 18+
brew install node@18

# Verificar instalação
python3 --version
pip3 --version
node --version
npm --version
```

#### Windows

Baixe e instale os instaladores oficiais:

1. **Python 3.8+:**
   - Acesse https://www.python.org/downloads/windows/
   - Baixe o instalador da versão mais recente (Python 3.x.x)
   - Execute o instalador e **marque a opção "Add Python to PATH"** antes de clicar em "Install Now"
   - Abra o Prompt de Comando e verifique:
     ```bat
     python --version
     pip --version
     ```

2. **Node.js 18+:**
   - Acesse https://nodejs.org/en/download/
   - Baixe o instalador LTS para Windows (`.msi`)
   - Execute o instalador com as opções padrão
   - Abra o Prompt de Comando e verifique:
     ```bat
     node --version
     npm --version
     ```

> **Dica:** Após instalar, feche e reabra o Prompt de Comando para que as variáveis de ambiente sejam atualizadas.

---

### Passos de Instalação

**Linux/Mac:**
```bash
# 1. Navegue até o diretório do projeto
cd Application

# 2. Crie um ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o Puter Bridge (para Claude e ChatGPT gratuitos)
cd puter-bridge
npm install
npm run auth
cd ..
```

**Windows:**
```bat
:: 1. Navegue até o diretório do projeto
cd Application

:: 2. Crie um ambiente virtual
python -m venv venv
venv\Scripts\activate

:: 3. Instale as dependências
pip install -r requirements.txt

:: 4. Configure o Puter Bridge (para Claude e ChatGPT gratuitos)
cd puter-bridge
npm install
npm run auth
cd ..
```

## Iniciando a Interface Gráfica

Com a instalação concluída, use a  interface gráfica para utilizar a ferramenta. Ela roda no navegador e não requer nenhum conhecimento de linha de comando além de um único comando para iniciá-la.

### Linux/Mac

**1. Abra um terminal na pasta do projeto.**

**2. Inicie a interface:**

```bash
./start_ui.sh
```

O script verifica o ambiente virtual, instala o Streamlit se necessário e inicia o servidor.

**3. Acesse no navegador:**

Abra `http://127.0.0.1:8501`. A tela inicial exibe um preview dos primeiros 10 logs do dataset padrão.

**4. (Opcional) Ative Claude e ChatGPT via Puter:**

Em um segundo terminal, execute:

```bash
./start_puter.sh
```

A interface detecta automaticamente o Puter Bridge e habilita os provedores Claude e ChatGPT.

**5. Para encerrar:**

Pressione `Ctrl+C` no terminal onde o `start_ui.sh` está rodando.

---

### Windows

**1. Abra o Explorador de Arquivos na pasta do projeto.**

**2. Dê duplo clique em `start_ui.bat`** — ou execute pelo Prompt de Comando:

```bat
start_ui.bat
```

O script verifica o ambiente virtual, instala o Streamlit se necessário e abre a interface no navegador automaticamente em `http://127.0.0.1:8501`.

**3. (Opcional) Ative Claude e ChatGPT via Puter:**

Abra outro Prompt de Comando na pasta do projeto e execute:

```bat
start_puter.bat
```

A interface detecta automaticamente o Puter Bridge e habilita os provedores Claude e ChatGPT.

**4. Para encerrar:**

Feche a janela do Prompt de Comando onde o `start_ui.bat` está rodando, ou pressione `Ctrl+C`.

---


## Como Funciona

A ferramenta executa **todas as análises disponíveis** em uma única chamada, usando cada provedor configurado:

| Provedor | Custo | Requer configuração |
|----------|-------|---------------------|
| **Groq** (Llama 3.3) | Gratuito | `GROQ_API_KEY` no `.env` |
| **Google Gemini** | Gratuito | `GOOGLE_API_KEY` no `.env` |
| **Claude** via Puter | Gratuito | Puter Bridge rodando |
| **ChatGPT** via Puter | Gratuito | Puter Bridge rodando |
| **Standard** (sem IA) | Gratuito | Nenhuma |

Cada provedor disponível executa as 3 análises independentemente. Os resultados são comparados no relatório final, o que permite avaliar a consistência entre diferentes modelos.

---

### Como usar a interface

A interface é dividida em duas áreas:

#### Barra lateral (esquerda)

| Seção | O que fazer |
|-------|-------------|
| **Arquivo de Logs** | Faça upload de um arquivo `.json` ou marque "Usar dataset padrão" |
| **Provedores de IA** | Marque os provedores desejados. Provedores sem configuração aparecem desabilitados com a instrução para ativá-los |
| **Puter Bridge** | Indica 🟢 Online ou 🔴 Offline. Se offline, expanda "Como ativar Claude/ChatGPT?" para ver o comando |
| **Nome base dos relatórios** | Define o prefixo dos arquivos gerados em `reports/` |
| **Executar Análise** | Clica para iniciar. Fica desabilitado se nenhum provedor estiver selecionado |

#### Área principal (direita)

Antes de executar, exibe um preview dos primeiros 10 logs do arquivo selecionado.

Após a execução:

1. **Visão Geral do Dataset** — métricas globais: total de logs, taxa (logs/min), duração e padrões duplicados.
2. **Abas por provedor** — uma aba para cada provedor executado, contendo:
   - Health Score, severidade, número de issues e modelo utilizado
   - Ações prioritárias recomendadas
   - Gráficos de distribuição por nível e por serviço
   - Detalhes das 3 análises (níveis de log, logs desnecessários, sampling)
   - Botão para baixar o relatório JSON daquele provedor
3. **Aba Comparativo** — tabela lado a lado com Health Score, severidade e issues de todos os provedores, mais botão para baixar o relatório consolidado.

---

### Formato do arquivo de logs

A ferramenta espera logs em formato JSON com a seguinte estrutura:

```json
{
  "timestamp": "2026-04-21T10:30:00.000Z",
  "level": "ERROR",
  "service": "payment-service",
  "instance": "pod-123",
  "request_id": "req-abc",
  "message": "Payment processing failed",
  "http": {
    "method": "POST",
    "path": "/api/payments",
    "status_code": 500
  },
  "error": {
    "type": "DatabaseException",
    "message": "Connection timeout"
  },
  "tags": ["payment", "error", "timeout"]
}
```

**Campos principais:**
- `timestamp` - Data/hora do log (ISO 8601)
- `level` - Nível: DEBUG, INFO, WARN, ERROR
- `service` - Nome do serviço
- `message` - Mensagem do log
- `http` (opcional) - Dados HTTP
- `error` (opcional) - Dados de erro
- `tags` (opcional) - Tags do log

### Relatórios gerados

Após a análise, os relatórios são salvos automaticamente em `reports/`:

```
reports/
├── {nome}_groq.json
├── {nome}_gemini.json
├── {nome}_claude_ai.json
├── {nome}_chatgpt.json
├── {nome}_sem_ia.json
└── {nome}_comparativo.json
```

Onde `{nome}` é o valor definido no campo "Nome base dos relatórios" (padrão: `synthetic_logs`).

---

## Configuração

### Arquivo .env

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

### Configuração para Groq (GRATUITO)

```bash
# .env
GROQ_API_KEY=sua_chave_groq_aqui
GROQ_MODEL_NAME=llama-3.3-70b-versatile
```

**Como obter a API key:**
1. Acesse https://console.groq.com/
2. Crie uma conta gratuita
3. Gere uma API key em API Keys

### Configuração para Google Gemini (GRATUITO)

```bash
# .env
GOOGLE_API_KEY=sua_chave_google_aqui
GEMINI_MODEL_NAME=gemini-flash-latest
```

**Como obter a API key:**
1. Acesse https://aistudio.google.com/app/apikey
2. Crie uma conta Google
3. Gere uma API key

### Configuração para Claude e ChatGPT (via Puter — GRATUITO)

O Puter Bridge permite usar Claude e ChatGPT sem custo. Inicie-o em um terminal separado antes de abrir a interface:

**Linux/Mac:**
```bash
./start_puter.sh
```

**Windows:**
```bat
start_puter.bat
```

A interface detecta o Puter Bridge automaticamente e habilita os provedores Claude e ChatGPT na barra lateral.

---

## Interpretação de Resultados

### Arquivos Gerados

Após a análise, os relatórios são salvos na pasta `reports/`:

```
reports/
├── synthetic_logs_groq.json       # Resultado do Groq
├── synthetic_logs_gemini.json     # Resultado do Gemini
├── synthetic_logs_claude_ai.json  # Resultado do Claude
├── synthetic_logs_chatgpt.json    # Resultado do ChatGPT
├── synthetic_logs_sem_ia.json     # Resultado Standard (sem IA)
└── synthetic_logs_comparativo.json # Comparativo consolidado
```

> **Atenção:** os arquivos são sobrescritos a cada execução. Altere o campo "Nome base dos relatórios" na barra lateral para preservar relatórios anteriores.

### Health Score

Métrica de 0 a 100 que indica a saúde do sistema de logs:

| Score | Status | Ação |
|-------|--------|------|
| 80-100 | ✅ Excelente | Manter boas práticas |
| 60-79 | ⚠️ Bom | Melhorias recomendadas |
| 40-59 | 🟠 Regular | Ação necessária |
| 0-39 | 🔴 Crítico | Ação urgente |

### Níveis de Severidade

- **ok** - Tudo certo ✅
- **low** - Problemas menores 🟡
- **medium** - Atenção necessária 🟠
- **high** - Ação necessária 🔴
- **critical** - Urgente ⚠️

### Estrutura do Relatório Individual

```json
{
  "metadata": {
    "analysis_timestamp": "...",
    "analysis_mode": "groq",
    "llm_provider": "groq",
    "model": "llama-3.3-70b-versatile"
  },
  "summary": {
    "total_logs": 1000,
    "level_distribution": {},
    "log_rate": {}
  },
  "analyses": {
    "log_levels": {},
    "unnecessary_logs": {},
    "sampling_recommendations": {}
  },
  "overall_assessment": {
    "health_score": 75,
    "overall_severity": "medium",
    "total_issues": 5,
    "priority_actions": []
  }
}
```

### Ações Prioritárias

O relatório lista ações ordenadas por prioridade:

```json
"priority_actions": [
  {
    "priority": 1,
    "action": "Ajustar níveis de log",
    "reason": "Configuração inadequada detectada"
  },
  {
    "priority": 2,
    "action": "Remover logs desnecessários",
    "reason": "Potencial de redução de 35%"
  }
]
```

**Comece sempre pela ação de prioridade 1!**

---

## Exemplos Práticos

### Exemplo 1: Primeira Análise

1. Inicie a interface com `./start_ui.sh` (Linux/Mac) ou `start_ui.bat` (Windows)
2. Na barra lateral, marque "Usar dataset padrão"
3. Selecione o provedor **Standard (sem IA)** — não requer configuração
4. Clique em **Executar Análise**

**Resultado típico na aba Standard:**
```
Health Score: 65/100
Severidade: MEDIUM
Issues: 8
Potencial de redução: 28%
```

---

### Exemplo 2: Comparar Provedores

1. Configure ao menos uma chave de API no arquivo `.env` (Groq ou Gemini)
2. (Opcional) Inicie o Puter Bridge para habilitar Claude e ChatGPT
3. Na barra lateral, marque todos os provedores disponíveis
4. Clique em **Executar Análise**
5. Acesse a **Aba Comparativo** para ver Health Score e issues lado a lado entre todos os provedores

---

### Exemplo 3: Workflow Completo de Melhoria

**Passo 1: Análise antes da intervenção**
1. Faça upload do seu arquivo de logs na barra lateral
2. Defina o campo "Nome base dos relatórios" como `before`
3. Execute a análise — o relatório `reports/before_sem_ia.json` será gerado

**Passo 2: Implementar recomendações**
- Consulte as ações prioritárias exibidas na aba do provedor escolhido
- Implemente as melhorias no seu sistema de logging

**Passo 3: Validar melhorias**
1. Faça upload dos logs atualizados
2. Defina o nome base como `after`
3. Execute novamente e compare o Health Score com o relatório anterior

---

## Troubleshooting

### Erro: "Módulo não instalado"

```bash
pip install -r requirements.txt
```

### Provedor de IA aparece desabilitado na interface

O provedor exige uma API key que ainda não foi configurada. Abra o arquivo `.env` na raiz do projeto e adicione a chave correspondente:

```bash
# Criar .env a partir do exemplo (se ainda não existir)
cp .env.example .env

# Editar e adicionar sua chave
nano .env        # Linux/Mac
notepad .env     # Windows
```

Reinicie a interface após salvar o arquivo.

### Puter Bridge não conecta

```bash
# Verifique se o bridge está rodando
curl http://localhost:3000/health

# Se não estiver, inicie-o
./start_puter.sh

# Verifique os logs do bridge
cat puter-bridge.log
```

### Formato de log inválido

Certifique-se que seu log tem os campos mínimos:

```json
{
  "timestamp": "2026-04-21T10:00:00.000Z",
  "level": "INFO",
  "service": "my-service",
  "message": "Log message"
}
```

---

## Dicas e Boas Práticas

### 1. Preserve Relatórios Importantes

Antes de executar uma nova análise sobre os mesmos logs, altere o campo **"Nome base dos relatórios"** na barra lateral (ex: `producao_20260812`) para não sobrescrever resultados anteriores.

### 2. Compare Provedores para Maior Confiança

Quando diferentes provedores concordam em um issue, a probabilidade de ser um problema real é maior. Divergências indicam casos limítrofes que merecem análise manual.

### 3. Use o Modo Standard como Baseline

O modo Standard é determinístico — os mesmos logs sempre produzem o mesmo resultado. Use-o para comparações antes/depois de mudanças no sistema de logging.

### 4. Dataset de Teste

Na primeira execução, marque **"Usar dataset padrão"** na barra lateral para validar a instalação com os logs sintéticos incluídos.

---

## Recursos Adicionais

- **Parar Puter Bridge:** `./stop_puter.sh` (Linux/Mac) ou feche o Prompt de Comando do `start_puter.bat` (Windows)
- **Documentação técnica:** `docs/ARQUITETURA.md`
- **Início rápido:** `docs/INICIO_RAPIDO.md`

---

## Suporte

- Issues: Abra uma issue no repositório
- Contribuições: Pull requests são bem-vindos

---

**Versão:** 4.0
**Última atualização:** Julho 2026
