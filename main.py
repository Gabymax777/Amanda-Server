import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
import threading

# --- SERVIDOR WEB FALSO PARA RENDER (AMANDA) ---
app = Flask('')

@app.route('/')
def home():
    return "Amanda está activa y gestionando informes técnicos 24/7"

def run():
    # Render asignará un puerto automático para Amanda
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=puerto)

threading.Thread(target=run, daemon=True).start()
# ------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True  # CRÍTICO: Para poder leer el historial del canal de sugerencias

bot = commands.Bot(command_prefix=".", intents=intents)
TOKEN_AMANDA = os.environ.get("TOKEN_AMANDA")

# 📌 PEGA AQUÍ LA ID DEL CANAL DONDE CLAY ENVÍA LAS SUGERENCIAS ACTUAlMENTE
ID_CANAL_SUGERENCIAS = 1505170785772503160 

# --- COMANDO DE BARRA /RESUMEN_SUGERENCIAS ---
@bot.tree.command(name="resumen_sugerencias", description="Genera un reporte técnico consolidado de las sugerencias")
async def resumen_sugerencias(interaction: discord.Interaction):
    # Solo tú (o tus líderes si quieres) deberíais usar esto, lo hacemos efímero para ti
    await interaction.response.defer(ephemeral=True)

    canal = bot.get_channel(ID_CANAL_SUGERENCIAS)
    if not canal:
        await interaction.followup.send("❌ Error: No encuentro el canal de sugerencias configurado.", ephemeral=True)
        return

    # Creamos un diccionario para contar cuántas veces se repite cada petición
    conteo_peticiones = {}
    total_leidos = 0

    # Amanda lee los últimos 100 mensajes del canal para analizarlos
    async for mensaje in canal.history(limit=100):
        # Filtramos: Solo leemos mensajes que tengan un diseño Embed (el diseño naranja de Clay)
        if mensaje.embeds:
            for embed in mensaje.embeds:
                # El texto de la propuesta que el usuario escribió con Clay está en la descripción del Embed
                propuesta = embed.description.lower().strip() if embed.description else ""
                
                if propuesta:
                    total_leidos += 1
                    # Clasificación inteligente básica: Agrupamos palabras clave comunes
                    if "calculadora" in propuesta:
                        clave = "Calculadora (GX / Pro)"
                    elif "notas" in propuesta or "bloc" in propuesta:
                        clave = "Bloc de Notas Avanzado"
                    elif "aurora" in propuesta or "ia" in propuesta:
                        clave = "Soporte / Mejoras Aurora IA"
                    elif "video" in propuesta or "editor" in propuesta:
                        clave = "Editores de Video / Multimedia"
                    elif "foto" in propuesta or "photoshop" in propuesta:
                        clave = "Herramientas de Diseño Gráfico"
                    else:
                        # Si es una sugerencia única, guardamos la frase corta
                        clave = propuesta[:40] + "..." if len(propuesta) > 40 else propuesta

                    conteo_peticiones[clave] = conteo_peticiones.get(clave, 0) + 1

    if total_leidos == 0:
        await interaction.followup.send("📋 No he encontrado ninguna sugerencia en el historial para procesar.", ephemeral=True)
        return

    # Construimos el reporte elegante para mostrártelo
    reporte_texto = ""
    # Ordenamos de mayor a menor cantidad de peticiones
    for peticion, cantidad in sorted(conteo_peticiones.items(), key=lambda item: item[1], reverse=True):
        reporte_texto += f"• **{peticion}**: Solicitado por `{cantidad}` usuario(s).\n"

    embed_reporte = discord.Embed(
        title="📊 Informe Consolidado de Sugerencias",
        description=f"He analizado los últimos `{total_leidos}` registros del canal de Clay. Aquí tienes el resumen de lo que más pide tu comunidad:\n\n{reporte_texto}",
        color=discord.Color.from_rgb(46, 204, 113) # Verde técnico
    )
    embed_reporte.set_footer(text="Amanda Technical Manager • Análisis en tiempo real")

    # Te manda el mensaje oculto solo a ti en tu pantalla
    await interaction.followup.send(embed=embed_reporte, ephemeral=True)


@bot.event
async def on_ready():
    id_mi_servidor = 1479175423764987914 
    try:
        bot.tree.copy_global_to(guild=discord.Object(id=id_mi_servidor))
        await bot.tree.sync(guild=discord.Object(id=id_mi_servidor))
        print(f"🚀 ¡Éxito! Amanda conectada y comando /resumen_sugerencias sincronizado en {id_mi_servidor}.")
    except Exception as e:
        print(f"Hubo un error al sincronizar a Amanda: {e}")

if TOKEN_AMANDA:
    bot.run(TOKEN_AMANDA)
