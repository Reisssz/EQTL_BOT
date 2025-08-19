# Documentação do Bot de Consulta de Energia

## Visão Geral
O Bot de Consulta de Energia é uma ferramenta desenvolvida para funcionários de companhias energéticas realizarem consultas rápidas sobre instalações e clientes. O bot oferece:

- Autenticação segura de funcionários
- Consulta detalhada de instalações por número de conta/contrato
- Gerenciamento de sessões com timeout automático
- Monitoramento em tempo real para administradores
- Recarga dinâmica de dados sem necessidade de reinício

## Comandos para Usuários Comuns

### /start
**Descrição:** Inicia a interação com o bot

**Uso:**
/start

text

**Resposta esperada:**
- Se não logado: Mensagem de boas-vindas com instrução para login
- Se logado: Saudação personalizada com menu de opções

**Pré-requisitos:** Nenhum

---

### /login
**Descrição:** Inicia o processo de autenticação

**Fluxo completo:**
1. Usuário envia `/login`
2. Bot solicita matrícula: "Digite sua matrícula:"
3. Usuário envia matrícula (apenas números)
4. Bot solicita nome completo: "Digite seu nome completo:"
5. Usuário envia nome completo

**Respostas possíveis:**
- Sucesso: Mensagem de boas-vindas com nome do usuário
- Falha: "Dados inválidos! Tente novamente: /login"

**Pré-requisitos:** Nenhum

---

### /logout
**Descrição:** Encerra a sessão do usuário

**Uso:**
/logout

text

**Resposta esperada:**
👋 Logout realizado!

text

**Pré-requisitos:** Usuário deve estar logado

---

### /meusdados
**Descrição:** Exibe os dados do funcionário logado

**Uso:**
/meusdados

text

**Resposta esperada:**
👤 Seus Dados:

• Nome: João da Silva
• Cargo: Técnico de campo
• Departamento: Operações
• Email: joao.silva@empresa.com
🕒 Login: 20/08/2023 14:30

text

**Pré-requisitos:** Usuário deve estar logado

---

### Consulta de Instalação
**Descrição:** Consulta dados de instalação por conta/contrato

**Uso:** [Número da conta/contrato]
123456789

text

**Resposta esperada (sucesso):**
🏠 123456789

• Nome Cliente: Maria Oliveira
• Endereco: Rua das Flores, 123
• Cidade: São Paulo
• CEP: 01234-567

🟢 Status: Ligado
• Tipo: Residencial
• Medidor: XYZ-1234
• Consumo Medio: 350 kWh
• Ultima Leitura: 15/08/2023

text

**Resposta esperada (falha):**
❌ Instalação não encontrada
Conta: 987654321

text

**Pré-requisitos:** Usuário deve estar logado

---

## Comandos Administrativos

### /admin_status
**Descrição:** Exibe estatísticas detalhadas do sistema

**Uso:**
/admin_status

text

**Resposta esperada:**
🤖 Status do Bot

⏱️ Uptime: 2 days, 3:45:12
👥 Sessões ativas: 15
🔢 Total consultas: 342
📊 Período atual:
• Logins: 28
• Consultas: 127
• Logins falhos: 3
• Erros: 0
🔄 Última recarga: 20/08/2023 14:00

text

**Pré-requisitos:** Acesso de administrador

---

### /admin_reload
**Descrição:** Recarrega os dados dos arquivos CSV

**Uso:**
/admin_reload

text

**Resposta esperada:**
🔄 Recarregando dados...
✅ Dados recarregados com sucesso!

text

**Pré-requisitos:** Acesso de administrador

---

### /admin_broadcast
**Descrição:** Envia mensagem para todos usuários logados

**Uso:**
/admin_broadcast Manutenção programada para amanhã

text

**Resposta esperada:**
📤 Mensagem enviada para 15 usuários ativos

text

**Pré-requisitos:** Acesso de administrador

---

## Monitoramento Automático
O sistema envia notificações automáticas para o administrador:

1. **Relatório Periódico**: A cada 10 minutos com:
   - Número de logins e consultas
   - Erros ocorridos
   - Status do sistema

2. **Eventos em Tempo Real**:
   - Logins bem-sucedidos e falhos
   - Consultas realizadas (com status de sucesso/falha)
   - Erros críticos do sistema

3. **Relatório Diário**: Consolidado com estatísticas das últimas 24h

---

## Fluxos de Erro Comuns

1. **Tentativa de login inválida**
   - Causa: Matrícula ou nome incorretos
   - Ação: Registro no log e notificação ao admin

2. **Consulta a instalação inexistente**
   - Resposta: Mensagem clara de "Instalação não encontrada"
   - Registro: Log detalhado com a conta pesquisada

3. **Comando sem permissão**
   - Resposta: Nenhuma (comandos admin são silenciosamente ignorados por não-admins)

---

## Requisitos Técnicos

### Permissões necessárias
- Leitura/escrita em diretório de logs
- Acesso aos arquivos CSV de dados
- Conexão com API do Telegram

### Formato dos arquivos CSV
1. **Funcionários (employees.csv)**:
matricula,nome,cargo,departamento,email
12345,João da Silva,Técnico de campo,Operações,joao.silva@empresa.com

text

2. **Instalações (instalacoes.csv)**:
conta_contrato,nome_cliente,endereco,cidade,cep,status,tipo,medidor,consumo_medio,ultima_leitura
123456789,Maria Oliveira,Rua das Flores 123,São Paulo,01234567,ligado,residencial,XYZ-1234,350,15/08/2023

text

### Configuração do ambiente
Variáveis de ambiente necessárias:
- `TELEGRAM_TOKEN`: Token do bot Telegram
- `ADMIN_CHAT_ID`: ID do chat do administrador
- `CSV_EMPLOYEES_PATH`: Caminho para employees.csv
- `CSV_INSTALACOES_PATH`: Caminho para instalacoes.csv

---

## Exemplos Completos

### Exemplo 1: Fluxo de Login
Usuário: /login
Bot: Digite sua matrícula:
Usuário: 12345
Bot: Digite seu nome completo:
Usuário: João da Silva
Bot: ✅ Login realizado!

Bem-vindo(a), João da Silva!
🔍 Digite uma conta/contrato para consultar

text

### Exemplo 2: Consulta Bem-sucedida
Usuário: 123456789
Bot: 🏠 123456789

• Nome Cliente: Maria Oliveira
• Endereco: Rua das Flores, 123
• Cidade: São Paulo
• CEP: 01234-567

🟢 Status: Ligado
• Tipo: Residencial
• Medidor: XYZ-1234
• Consumo Medio: 350 kWh
• Ultima Leitura: 15/08/2023

text

### Exemplo 3: Broadcast Admin
Admin: /admin_broadcast Manutenção programada para amanhã
Bot: 📤 Mensagem enviada para 15 usuários ativos

text

---

## FAQ

**Q: O bot não responde aos comandos**
A: Verifique:
1. Se o bot está online (/start deve responder)
2. Se você está logado (comandos exigem login)
3. Se digitou o comando corretamente

**Q: Como saber se meus dados estão corretos?**
A: Use /meusdados para verificar as informações que o sistema tem sobre você

**Q: Esqueci de fazer logout, o que acontece?**
A: A sessão expira automaticamente após 1 hora de inatividade

**Q: Posso consultar várias contas rapidamente?**
A: Sim, basta digitar os números das contas um após o outro

---

## Notas de Segurança
1. Todas as credenciais são validadas contra a base oficial
2. As sessões têm timeout automático
3. Ações administrativas exigem autenticação especial
4. Todos os acessos são registrados em log
5. Dados sensíveis são mascarados nos logs
New chat