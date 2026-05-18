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
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=puerto)

threading.Thread(target=run, daemon=True).start()
# ------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True  

bot = commands.Bot(command_prefix=".", intents=intents)
TOKEN_AMANDA = os.environ.get("TOKEN_AMANDA")

# =========================================================================
# ⚙️ AJUSTES DE CONFIGURACIÓN DE AMANDA
# =========================================================================
# 📌 ID del canal de donde Amanda lee las sugerencias originales (enviadas por Clay)
ID_CANAL_SUGERENCIAS = 1505170785772503160 

# 📩 OPCIÓN 1: Activa esto (True) si quieres recibir el informe por Mensaje Privado (DM)
ENVIAR_POR_DM = True  

# 📺 OPCIÓN 2: Si pones lo de arriba en False, escribe aquí la ID del canal de Staff donde se publicará
ID_CANAL_INFORMES_STAFF = 123456789012345678  


# =========================================================================
# 📊 COMANDO DE BARRA: /resumen_sugerencias
# =========================================================================
@bot.tree.command(name="resumen_sugerencias", description="Genera un reporte técnico consolidado de las sugerencias")
async def resumen_sugerencias(interaction: discord.Interaction):
    # Defer efímero para mantener el comando vivo mientras procesa datos
    await interaction.response.defer(ephemeral=True)

    canal = bot.get_channel(ID_CANAL_SUGERENCIAS)
    if not canal:
        await interaction.followup.send("❌ Error: No encuentro el canal de sugerencias configurado.", ephemeral=True)
        return

    conteo_peticiones = {}
    total_leidos = 0

    # Amanda procesa el historial del canal
    async for mensaje in canal.history(limit=100):
        if mensaje.embeds:
            for embed in mensaje.embeds:
                propuesta = embed.description.lower().strip() if embed.description else ""
                
                if propuesta:
                    total_leidos += 1
                    # Clasificación por palabras clave
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
                        clave = propuesta[:40] + "..." if len(propuesta) > 40 else propuesta

                    conteo_peticiones[clave] = conteo_peticiones.get(clave, 0) + 1

    if total_leidos == 0:
        await interaction.followup.send("📋 No he encontrado ninguna sugerencia en el historial para procesar.", ephemeral=True)
        return

    # Construcción del listado del reporte
    reporte_texto = ""
    for peticion, cantidad in sorted(conteo_peticiones.items(), key=lambda item: item[1], reverse=True):
        reporte_texto += f"• **{peticion}**: Solicitado por `{cantidad}` usuario(s).\n"

    # Generamos el Embed de Amanda
    embed_reporte = discord.Embed(
        title="📊 Informe Consolidado de Sugerencias",
        description=f"He analizado los últimos `{total_leidos}` registros del canal de Clay. Aquí tienes el resumen de lo que más pide tu comunidad:\n\n{reporte_texto}",
        color=discord.Color.from_rgb(46, 204, 113) 
    )
    embed_reporte.set_footer(text="Amanda Technical Manager • Análisis en tiempo real")

    # 🚀 GESTIÓN DE ENVÍO SEGÚN CONFIGURACIÓN
    if ENVIAR_POR_DM:
        try:
            await interaction.user.send(embed=embed_reporte)
            await interaction.followup.send("📥 ¡Listo! Te he enviado el informe completo a tus mensajes privados.", ephemeral=True)
        except discord.Forbidden:
            # Plan de respaldo si tus DMs del servidor están apagados
            await interaction.followup.send(
                "❌ No pude enviarte el mensaje privado. Asegúrate de permitir mensajes directos de miembros del servidor en tus Ajustes de Privacidad.", 
                ephemeral=True
            )
    else:
        canal_staff = bot.get_channel(ID_CANAL_INFORMES_STAFF)
        if canal_staff:
            await canal_staff.send(embed=embed_reporte)
            await interaction.followup.send(f"📊 ¡Listo! He publicado el informe consolidado en el canal <#{ID_CANAL_INFORMES_STAFF}>.", ephemeral=True)
        else:
            # Plan de respaldo si la ID del canal del staff está mal copiada
            await interaction.followup.send(
                f"⚠️ Error: No encontré la ID del canal de Staff. Te muestro el reporte aquí provisionalmente:\n", 
                embed=embed_reporte, 
                ephemeral=True
            )


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
