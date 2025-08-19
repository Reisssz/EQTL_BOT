import logging
import pandas as pd
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime
import os
from threading import Lock
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SessionManager:
    """Gerenciador de sessões simplificado"""
    
    def __init__(self):
        self.sessions: Dict[int, Dict[str, Any]] = {}
        self.user_states: Dict[int, str] = {}  # user_id: estado (MA, PA, PI, AL)
        self.lock = Lock()
    
    def set_user_state(self, user_id: int, estado: str):
        """Define o estado do usuário"""
        with self.lock:
            self.user_states[user_id] = estado.upper()
    
    def get_user_state(self, user_id: int) -> Optional[str]:
        """Retorna o estado do usuário"""
        with self.lock:
            return self.user_states.get(user_id)
    
    def create_session(self, user_id: int, user_name: str, estado: str):
        """Cria uma nova sessão"""
        with self.lock:
            self.sessions[user_id] = {
                "user_id": user_id,
                "name": user_name,
                "estado": estado.upper(),
                "login_time": datetime.now(),
                "last_activity": datetime.now()
            }
            self.user_states[user_id] = estado.upper()
    
    def is_authenticated(self, user_id: int) -> bool:
        """Verifica se usuário está autenticado"""
        with self.lock:
            return user_id in self.sessions
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retorna informações do usuário"""
        with self.lock:
            return self.sessions.get(user_id)
    
    def logout_user(self, user_id: int):
        """Remove a sessão do usuário"""
        with self.lock:
            if user_id in self.sessions:
                del self.sessions[user_id]
            if user_id in self.user_states:
                del self.user_states[user_id]

class CSVDatabase:
    """Banco de dados CSV simplificado"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.data = None
        self.reload_data()
    
    def reload_data(self):
        """Carrega os dados do CSV"""
        try:
            self.data = pd.read_csv(
                self.csv_file,
                dtype=str,
                low_memory=False
            ).fillna('')
            logger.info(f"Dados carregados: {len(self.data)} registros")
        except Exception as e:
            logger.error(f"Erro ao carregar CSV: {e}")
            self.data = pd.DataFrame()
    
    def buscar_instalacao(self, estado: str, numero: str) -> Optional[Dict[str, Any]]:
        """Busca instalação por estado e número"""
        if self.data.empty:
            return None
        
        numero_limpo = ''.join(filter(str.isdigit, numero))
        
        # Busca por instalação OU número do medidor
        mask = (
            (self.data['ESTADO'] == estado.upper()) & 
            (
                (self.data['INSTALACAO'] == numero_limpo) |
                (self.data['NUMERO_MEDIDOR'] == numero_limpo) |
                (self.data['MEDIDOR_ANTERIOR'] == numero_limpo)
            )
        )
        
        resultados = self.data[mask]
        if not resultados.empty:
            return resultados.iloc[0].to_dict()
        return None
    
    def buscar_troca_titularidade(self, estado: str, instalacao: str) -> List[Dict[str, Any]]:
        """Busca histórico de troca de titularidade"""
        if self.data.empty:
            return []
        
        mask = (
            (self.data['ESTADO'] == estado.upper()) & 
            (self.data['INSTALACAO'] == instalacao) &
            (self.data['TIPO_EVENTO'] == 'TROCA_TITULARIDADE')
        )
        
        return self.data[mask].to_dict('records')

class EnergyBot:
    """Bot principal simplificado"""
    
    def __init__(self, database: CSVDatabase):
        self.db = database
        self.sessions = SessionManager()
        self.estados_validos = ['MA', 'PA', 'PI', 'AL']
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Primeiro acesso"""
        user_id = update.message.from_user.id
        user_name = update.message.from_user.full_name
        
        estado = self.sessions.get_user_state(user_id)
        
        if estado:
            # Usuário já escolheu estado
            self.sessions.create_session(user_id, user_name, estado)
            await update.message.reply_text(
                f"👋 Olá {user_name}!\n"
                f"📍 Estado: {estado}\n\n"
                f"🔍 Digite o número da instalação ou medidor para consultar\n"
                f"📋 Comandos: /estado | /logout"
            )
        else:
            # Primeiro acesso - perguntar estado
            await update.message.reply_text(
                "🔐 **Sistema de Consulta de Energia**\n\n"
                "📋 Para começar, escolha sua distribuidora:\n\n"
                "🇲🇦 /MA - Maranhão\n"
                "🇵🇦 /PA - Pará\n" 
                "🇵🇮 /PI - Piauí\n"
                "🇦🇱 /AL - Alagoas\n\n"
                "Selecione com: /MA, /PA, /PI ou /AL"
            )
    
    async def definir_estado(self, update: Update, context: ContextTypes.DEFAULT_TYPE, estado: str):
        """Define o estado do usuário"""
        user_id = update.message.from_user.id
        user_name = update.message.from_user.full_name
        
        if estado.upper() in self.estados_validos:
            self.sessions.set_user_state(user_id, estado.upper())
            self.sessions.create_session(user_id, user_name, estado.upper())
            
            await update.message.reply_text(
                f"✅ Estado definido: {estado.upper()}\n\n"
                f"🔍 Agora digite o número da instalação ou medidor para consultar\n"
                f"📋 Comandos: /estado | /logout"
            )
        else:
            await update.message.reply_text("❌ Estado inválido. Use /MA, /PA, /PI ou /AL")
    
    async def comando_ma(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.definir_estado(update, context, 'MA')
    
    async def comando_pa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.definir_estado(update, context, 'PA')
    
    async def comando_pi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.definir_estado(update, context, 'PI')
    
    async def comando_al(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.definir_estado(update, context, 'AL')
    
    async def comando_estado(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para alterar estado"""
        user_id = update.message.from_user.id
        
        if self.sessions.is_authenticated(user_id):
            # Mantém sessão, apenas pergunta novo estado
            await update.message.reply_text(
                "📋 Escolha nova distribuidora:\n\n"
                "🇲🇦 /MA - Maranhão\n"
                "🇵🇦 /PA - Pará\n" 
                "🇵🇮 /PI - Piauí\n"
                "🇦🇱 /AL - Alagoas"
            )
        else:
            await self.start(update, context)
    
    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /logout"""
        user_id = update.message.from_user.id
        self.sessions.logout_user(user_id)
        await update.message.reply_text("👋 Logout realizado!")
    
    async def handle_consulta(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa consultas"""
        user_id = update.message.from_user.id
        
        if not self.sessions.is_authenticated(user_id):
            await update.message.reply_text("❌ Faça login primeiro: /start")
            return
        
        user_info = self.sessions.get_user_info(user_id)
        estado = user_info['estado']
        numero = update.message.text.strip()
        
        # Busca dados
        dados = self.db.buscar_instalacao(estado, numero)
        
        if not dados:
            await update.message.reply_text(
                f"❌ Instalação/medidor não encontrado\n"
                f"Estado: {estado}\nNúmero: {numero}\n\n"
                f"📞 Verifique os dados e tente novamente"
            )
            return
        
        # Formata resposta
        resposta = self._formatar_resposta(dados, estado)
        
        # Busca trocas de titularidade
        trocas = self.db.buscar_troca_titularidade(estado, dados.get('INSTALACAO', ''))
        if trocas:
            resposta += self._formatar_trocas_titularidade(trocas)
        
        await update.message.reply_text(resposta)
    
    def _formatar_resposta(self, dados: Dict[str, Any], estado: str) -> str:
        """Formata os dados da instalação"""
        response = f"🏠 **INSTALAÇÃO ENCONTRADA** - {estado}\n\n"
        
        # Dados básicos
        campos_basicos = [
            ('INSTALACAO', '📊 Instalação'),
            ('NOME', '👤 Titular'),
            ('ENDERECO', '📍 Endereço'),
            ('BAIRRO', '🏘️ Bairro'),
            ('CIDADE', '🏙️ Cidade'),
            ('NUMERO_MEDIDOR', '🔢 Medidor Atual'),
            ('MEDIDOR_ANTERIOR', '🔄 Medidor Anterior'),
            ('CLASSE', '⚡ Classe'),
            ('TENSAO', '⚡ Tensão'),
            ('STATUS', '📋 Status')
        ]
        
        for campo, label in campos_basicos:
            if campo in dados and dados[campo] not in ['', 'nan']:
                response += f"{label}: {dados[campo]}\n"
        
        # Dados de espécies
        response += "\n💰 **ESPÉCIES:**\n"
        especies = self._extrair_especies(dados)
        for codigo, (descricao, valor) in especies.items():
            response += f"• {codigo} - {descricao}: R$ {valor}\n"
        
        return response
    
    def _extrair_especies(self, dados: Dict[str, Any]) -> Dict[str, tuple]:
        """Extrai informações de espécies do débito"""
        especies = {}
        
        # Procura por campos de espécie no formato ESPECIE_CODIGO, ESPECIE_DESCRICAO, ESPECIE_VALOR
        for campo, valor in dados.items():
            if campo.startswith('ESPECIE_') and valor not in ['', 'nan']:
                partes = campo.split('_')
                if len(partes) >= 3:
                    tipo = partes[1].lower()
                    codigo = partes[2] if len(partes) > 2 else 'Geral'
                    
                    if tipo == 'codigo':
                        if codigo not in especies:
                            especies[codigo] = ('', '')
                        descricao, valor_existente = especies[codigo]
                        especies[codigo] = (valor, valor_existente)
                    elif tipo == 'descricao':
                        if codigo not in especies:
                            especies[codigo] = ('', '')
                        descricao_existente, valor_existente = especies[codigo]
                        especies[codigo] = (descricao_existente, valor)
                    elif tipo == 'valor':
                        if codigo not in especies:
                            especies[codigo] = ('', '')
                        descricao_existente, _ = especies[codigo]
                        especies[codigo] = (descricao_existente, valor)
        
        return especies
    
    def _formatar_trocas_titularidade(self, trocas: List[Dict[str, Any]]) -> str:
        """Formata histórico de trocas de titularidade"""
        response = "\n🔄 **HISTÓRICO DE TROCAS DE TITULARIDADE:**\n"
        
        for i, troca in enumerate(trocas, 1):
            response += f"\n{i}. 📅 {troca.get('DATA_EVENTO', 'N/A')}\n"
            response += f"   👤 De: {troca.get('TITULAR_ANTERIOR', 'N/A')}\n"
            response += f"   👤 Para: {troca.get('NOVO_TITULAR', 'N/A')}\n"
            response += f"   📋 Motivo: {troca.get('MOTIVO_TROCA', 'N/A')}\n"
        
        return response

def main():
    """Função principal"""
    # Configurações
    CSV_FILE = os.getenv("CSV_FILE", "dados_energia.csv")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logger.error("Token do bot não configurado!")
        return
    
    # Inicializa banco de dados
    db = CSVDatabase(CSV_FILE)
    bot = EnergyBot(db)
    
    # Cria aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("ma", bot.comando_ma))
    application.add_handler(CommandHandler("pa", bot.comando_pa))
    application.add_handler(CommandHandler("pi", bot.comando_pi))
    application.add_handler(CommandHandler("al", bot.comando_al))
    application.add_handler(CommandHandler("estado", bot.comando_estado))
    application.add_handler(CommandHandler("logout", bot.logout))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_consulta))
    
    logger.info("Bot iniciado!")
    application.run_polling()

if __name__ == "__main__":
    main()