import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import json
import os
from aiohttp import web
import asyncio

# Configurações
ADMIN_ID = 1451570927711158313
ALLOWED_SERVERS = [1458471374812090389, 1458234841370984663]

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=['!', '/'], intents=intents)

# Arquivo para salvar categorias
CATEGORIES_FILE = 'categories.json'

# Função para carregar categorias
def load_categories():
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Função para salvar categorias
def save_categories(categories):
    with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

# Categorias globais
categories = load_categories()

# Modal para adicionar categoria
class AddCategoryModal(Modal, title='Adicionar Categoria de Scripts'):
    category_name = TextInput(
        label='Nome da Categoria',
        placeholder='Ex: Blox Fruits, Pet Simulator X, etc.',
        required=True,
        max_length=100
    )
    
    script_name_1 = TextInput(
        label='Nome do Script 1',
        placeholder='Nome do primeiro script',
        required=True,
        max_length=100
    )
    
    script_code_1 = TextInput(
        label='Código do Script 1',
        placeholder='loadstring(game:HttpGet("..."))()',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=2000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        category = self.category_name.value
        
        if category not in categories:
            categories[category] = []
        
        # Adiciona o primeiro script
        categories[category].append({
            'name': self.script_name_1.value,
            'code': self.script_code_1.value
        })
        
        save_categories(categories)
        
        # Cria view para adicionar mais scripts
        view = AddMoreScriptsView(category)
        
        embed = discord.Embed(
            title=f"✅ Categoria '{category}' Atualizada!",
            description=f"Script adicionado com sucesso!\n\n**Scripts nesta categoria:** {len(categories[category])}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# View para adicionar mais scripts
class AddMoreScriptsView(View):
    def __init__(self, category):
        super().__init__(timeout=300)
        self.category = category
    
    @discord.ui.button(label='➕ Adicionar Mais Scripts', style=discord.ButtonStyle.primary)
    async def add_more(self, interaction: discord.Interaction, button: Button):
        modal = AddMoreScriptsModal(self.category)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='✅ Finalizar', style=discord.ButtonStyle.success)
    async def finish(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="✅ Categoria Finalizada!",
            description=f"Categoria **{self.category}** com **{len(categories[self.category])}** script(s) salva com sucesso!",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

# Modal para adicionar mais scripts a uma categoria existente
class AddMoreScriptsModal(Modal, title='Adicionar Mais Scripts'):
    script_name = TextInput(
        label='Nome do Script',
        placeholder='Nome do script',
        required=True,
        max_length=100
    )
    
    script_code = TextInput(
        label='Código do Script',
        placeholder='loadstring(game:HttpGet("..."))()',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=2000
    )
    
    def __init__(self, category):
        super().__init__()
        self.category = category
    
    async def on_submit(self, interaction: discord.Interaction):
        categories[self.category].append({
            'name': self.script_name.value,
            'code': self.script_code.value
        })
        
        save_categories(categories)
        
        view = AddMoreScriptsView(self.category)
        
        embed = discord.Embed(
            title=f"✅ Script Adicionado!",
            description=f"**{self.script_name.value}** foi adicionado à categoria **{self.category}**!\n\n**Total de scripts:** {len(categories[self.category])}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# View para navegar pelos scripts
class ScriptsView(View):
    def __init__(self, categories_list, current_page=0):
        super().__init__(timeout=180)
        self.categories_list = categories_list
        self.current_page = current_page
        self.max_page = len(categories_list) - 1
        
        # Desabilita botões se necessário
        if self.current_page == 0:
            self.children[0].disabled = True
        if self.current_page >= self.max_page:
            self.children[1].disabled = True
    
    @discord.ui.button(label='⬅️ Anterior', style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            embed = self.create_embed()
            
            # Atualiza estado dos botões
            self.children[0].disabled = self.current_page == 0
            self.children[1].disabled = False
            
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='Próxima ➡️', style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page < self.max_page:
            self.current_page += 1
            embed = self.create_embed()
            
            # Atualiza estado dos botões
            self.children[0].disabled = False
            self.children[1].disabled = self.current_page >= self.max_page
            
            await interaction.response.edit_message(embed=embed, view=self)
    
    def create_embed(self):
        category_name = self.categories_list[self.current_page]
        scripts = categories[category_name]
        
        embed = discord.Embed(
            title=f"📜 Categoria: {category_name}",
            description=f"**Total de Scripts:** {len(scripts)}\n**Página {self.current_page + 1}/{len(self.categories_list)}**",
            color=discord.Color.blue()
        )
        
        for i, script in enumerate(scripts, 1):
            embed.add_field(
                name=f"{i}. {script['name']}",
                value=f"```lua\n{script['code'][:100]}{'...' if len(script['code']) > 100 else ''}```",
                inline=False
            )
        
        embed.set_footer(text="Use os botões abaixo para navegar entre as categorias")
        return embed

# Verificação de servidor
def check_server():
    async def predicate(ctx):
        if ctx.guild.id not in ALLOWED_SERVERS:
            await ctx.send("❌ Este bot não está autorizado a funcionar neste servidor!")
            return False
        return True
    return commands.check(predicate)

# Verificação de admin
def is_admin():
    async def predicate(ctx):
        if ctx.author.id != ADMIN_ID:
            await ctx.send("❌ **Erro: Você não é o Admin Branzz!**")
            return False
        return True
    return commands.check(predicate)

# Eventos do bot
@bot.event
async def on_ready():
    print(f'✅ Bot online como {bot.user}')
    print(f'📊 ID: {bot.user.id}')
    print(f'🌐 Servidores autorizados: {ALLOWED_SERVERS}')
    print(f'👑 Admin ID: {ADMIN_ID}')
    await bot.change_presence(activity=discord.Game(name="Scripts 24/7 | !scripts"))

@bot.event
async def on_guild_join(guild):
    if guild.id not in ALLOWED_SERVERS:
        print(f'⚠️ Saindo do servidor não autorizado: {guild.name} (ID: {guild.id})')
        await guild.leave()

# Comando: categoria_add (apenas Admin Branzz)
@bot.command(name='categoria_add', aliases=['add_categoria'])
@check_server()
@is_admin()
async def categoria_add(ctx):
    modal = AddCategoryModal()
    await ctx.send("Abrindo modal... (Verifique suas DMs ou interações)", delete_after=5)
    
    # Envia mensagem com botão para abrir modal
    view = View(timeout=60)
    
    async def open_modal(interaction: discord.Interaction):
        await interaction.response.send_modal(modal)
    
    button = Button(label='➕ Adicionar Categoria', style=discord.ButtonStyle.primary)
    button.callback = open_modal
    view.add_item(button)
    
    await ctx.send("**Clique no botão abaixo para adicionar uma nova categoria:**", view=view)

# Comando: scripts (qualquer pessoa)
@bot.command(name='scripts', aliases=['script'])
@check_server()
async def scripts(ctx):
    if not categories:
        embed = discord.Embed(
            title="📜 Lista de Scripts",
            description="❌ Nenhuma categoria de scripts foi adicionada ainda!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    categories_list = list(categories.keys())
    view = ScriptsView(categories_list)
    embed = view.create_embed()
    
    await ctx.send(embed=embed, view=view)

# Servidor web para manter o bot online no Render
async def web_server():
    app = web.Application()
    
    async def health(request):
        return web.Response(text='Bot está online! 🟢')
    
    app.router.add_get('/', health)
    app.router.add_get('/health', health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    await site.start()
    print('🌐 Servidor web iniciado na porta', os.getenv('PORT', 8080))

# Iniciar o bot
async def main():
    async with bot:
        # Inicia o servidor web
        bot.loop.create_task(web_server())
        
        # Pega o token
        TOKEN = os.getenv('DISCORD_TOKEN')
        
        if TOKEN is None:
            print("❌ ERRO: Token do Discord não encontrado!")
            print("Configure a variável de ambiente DISCORD_TOKEN")
            return
        
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())