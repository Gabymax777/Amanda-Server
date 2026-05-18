import os
import discord
from discord import app_commands
from discord.ext import commands, tasks  # 💡 Añadido tasks para la automatización diaria
from flask import Flask
import threading
import io
from datetime import datetime, time
import zoneinfo  # 💡 Para manejar la hora de España de forma estricta sin importar el hosting

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
# ⚙️ CONFIGURACIÓN GLOBAL Y MEMORIA TEMPORAL
# =========================================================================
ID_CANAL_SUGERENCIAS = 1505170785772503160 
ID_CANAL_INFORMES_STAFF = 1505914253918343259  
ID_DESARROLLADOR_DM = 929718842928812032

# Zona horaria oficial de España para que las tareas se ejecuten exactas
ZONA_ESPANA = zoneinfo.ZoneInfo("Europe/Madrid")

# Lista en memoria para guardar las IDs de los mensajes que te enviamos al DM hoy
mensajes_enviados_hoy = []


# =========================================================================
# 🔧 FUNCIÓN NÚCLEO: GENERACIÓN DEL REPORTE TÉCNICO
# =========================================================================
async def generar_reporte_tecnico():
    """Procesa el historial de sugerencias y devuelve el embed junto con el archivo MD"""
    canal = bot.get_channel(ID_CANAL_SUGERENCIAS)
    if not canal:
        return None, None

    conteo_peticiones = {}
    detalles_peticiones = {
        "Calculadora (GX / Pro)": [],
        "Bloc de Notas Avanzado": [],
        "Soporte / Mejoras Aurora IA": [],
        "Editores de Video / Multimedia": [],
        "Herramientas de Diseño Gráfico": [],
        "Otras Peticiones Únicas": []
    }
    total_leidos = 0

    async for mensaje in canal.history(limit=100):
        if mensaje.embeds:
            for embed in mensaje.embeds:
                propuesta = embed.description.strip() if embed.description else ""
                
                if propuesta:
                    total_leidos += 1
                    propuesta_lower = propuesta.lower()
                    
                    usuario_nombre = embed.author.name if embed.author else "Usuario Desconocido"
                    usuario_id = "Desconocida"
                    if embed.footer and embed.footer.text:
                        usuario_id = embed.footer.text.replace("Enviado por ID: ", "").strip()

                    datos_sugerencia = {
                        "usuario": usuario_nombre,
                        "id": usuario_id,
                        "texto": propuesta
                    }

                    if "calculadora" in propuesta_lower:
                        clave = "Calculadora (GX / Pro)"
                    elif "notas" in propuesta_lower or "bloc" in propuesta_lower:
                        clave = "Bloc de Notas Avanzado"
                    elif "aurora" in propuesta_lower or "ia" in propuesta_lower:
                        clave = "Soporte / Mejoras Aurora IA"
                    elif "video" in propuesta_lower or "editor" in propuesta_lower:
                        clave = "Editores de Video / Multimedia"
                    elif "foto" in propuesta_lower or "photoshop" in propuesta_lower:
                        clave = "Herramientas de Diseño Gráfico"
                    else:
                        clave = "Otras Peticiones Únicas"

                    conteo_peticiones[clave] = conteo_peticiones.get(clave, 0) + 1
                    detalles_peticiones[clave].append(datos_sugerencia)

    if total_leidos == 0:
        return None, None

    # Markdown (.md)
    md_contenido = f"# REPORTING TÉCNICO DE SUGERENCIAS\n"
    md_contenido += f"**Total de registros analizados:** {total_leidos}\n"
    md_contenido += f"**Generado por:** Amanda Technical Manager\n"
    md_contenido += f"--------------------------------------------------\n\n"

    for categoria, sugerencias in detalles_peticiones.items():
        if sugerencias:
            md_contenido += f"## 📁 {categoria} ({len(sugerencias)} peticiones)\n"
            md_contenido += f"==================================================\n"
            for sug in sugerencias:
                md_contenido += f"👤 **Usuario:** {sug['usuario']} (ID: {sug['id']})\n"
                md_contenido += f"💬 **Propuesta:**\n```text\n{sug['texto']}\n```\n"
                md_contenido += f"--------------------------------------------------\n"
            md_contenido += f"\n"

    archivo_binario = io.BytesIO(md_contenido.encode('utf-8'))
    discord_file = discord.File(fp=archivo_binario, filename="reporte_desarrollo.md")

    # Embed resumido
    reporte_texto = ""
    for peticion, cantidad in sorted(conteo_peticiones.items(), key=lambda item: item, reverse=True):
        reporte_texto += f"• **{peticion}**: Solicitado por `{cantidad}` usuario(s).\n"

    embed_reporte = discord.Embed(
        title="📊 Informe Consolidado de Sugerencias",
        description=f"He analizado los últimos `{total_leidos}` registros del canal de Clay. Aquí tienes el resumen general:\n\n{reporte_texto}\n📂 *Descarga el archivo adjunto para ver las sugerencias completas de cada usuario.*",
        color=discord.Color.from_rgb(46, 204, 113) 
    )
    embed_reporte.set_footer(text="Amanda Technical Manager • Análisis en tiempo real")

    return embed_reporte, discord_file


# =========================================================================
# ⏰ TAREAS AUTOMATIZADAS DIARIAS (Enviador automático)
# =========================================================================
# Definimos las horas estrictas con la zona horaria de España aplicada directamente
@tasks.loop(time=[
    time(10, 0, tzinfo=ZONA_ESPANA),
    time(15, 0, tzinfo=ZONA_ESPANA),
    time(20, 0, tzinfo=ZONA_ESPANA)
])
async def enviar_informe_automatico():
    try:
        usuario = await bot.fetch_user(ID_DESARROLLADOR_DM)
        if not usuario:
            print("⚠️ Error: No se pudo encontrar al desarrollador para el envío automático.")
            return

        embed, archivo = await generar_reporte_tecnico()
        if embed and archivo:
            # Mandamos el informe al DM y guardamos la referencia del mensaje enviado
            msg = await usuario.send(embed=embed, file=archivo)
            mensajes_enviados_hoy.append(msg)
            print(f"⏰ [Automatización] Informe diario enviado con éxito al DM a las {datetime.now(ZONA_ESPANA).strftime('%H:%M')}.")
        else:
            print("📋 [Automatización] No había sugerencias nuevas para reportar en este horario.")
    except discord.Forbidden:
        print("❌ Error: Tienes tus DMs cerrados en este servidor. Amanda no ha podido enviarte el informe automático.")
    except Exception as e:
        print(f"Hubo un error en el envío programado: {e}")


# =========================================================================
# 🗑️ TAREA AUTOMATIZADA: LIMPIEZA NOCTURNA
# =========================================================================
@tasks.loop(time=[time(23, 0, tzinfo=ZONA_ESPANA)])
async def limpiar_mensajes_nocturnos():
    global mensajes_enviados_hoy
    print("🗑️ [Limpieza] Iniciando borrado de los informes del DM para no saturar...")
    
    # Eliminamos secuencialmente los mensajes guardados durante el día
    for msg in mensajes_enviados_hoy:
        try:
            await msg.delete()
        except Exception:
            pass # Si ya fue borrado manualmente, ignora el fallo
            
    # Vaciamos la lista para el día siguiente
    mensajes_enviados_hoy.clear()
    print("✅ [Limpieza] Bandeja de entrada purgada e historial de memoria reiniciado.")


# =========================================================================
# 📊 COMANDO DE BARRA MANUAl: /resumen_sugerencias
# =========================================================================
@bot.tree.command(name="resumen_sugerencias", description="Genera un reporte técnico consolidado y un archivo detallado")
@app_commands.describe(enviar_a="Elige dónde quieres recibir el informe en este momento")
@app_commands.choices(enviar_a=[
    app_commands.Choice(name="📬 Recibir por Mensaje Privado (DM)", value="dm"),
    app_commands.Choice(name="📺 Enviar al Canal de Staff", value="canal")
])
async def resumen_sugerencias(interaction: discord.Interaction, enviar_a: str):
    await interaction.response.defer(ephemeral=True)

    embed, archivo = await generar_reporte_tecnico()
    if not embed:
        await interaction.followup.send("📋 No he encontrado ninguna sugerencia en el historial para procesar.", ephemeral=True)
        return

    if enviar_a == "dm":
        try:
            # Los comandos manuales también se registran en la lista si los pides al DM
            msg = await interaction.user.send(embed=embed, file=archivo)
            mensajes_enviados_hoy.append(msg)
            await interaction.followup.send("📥 ¡Listo! Te he enviado el informe y el archivo técnico a tus mensajes privados.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No pude enviarte el mensaje privado. Asegúrate de permitir mensajes directos en tus Ajustes de Privacidad.", 
                ephemeral=True
            )
    elif enviar_a == "canal":
        canal_staff = bot.get_channel(ID_CANAL_INFORMES_STAFF)
        if canal_staff:
            await canal_staff.send(embed=embed, file=archivo)
            await interaction.followup.send(f"📊 ¡Listo! He publicado el informe técnico en el canal <#{ID_CANAL_INFORMES_STAFF}>.", ephemeral=True)
        else:
            await interaction.followup.send(
                f"⚠️ Error: No encontré la ID del canal de Staff. Te adjunto el reporte aquí de forma privada:", 
                embed=embed, file=archivo,
                ephemeral=True
            )


# =========================================================================
# 🚀 ENTRADA EN VIGOR Y SINCRONIZACIÓN
# =========================================================================
@bot.event
async def on_ready():
    id_mi_servidor = 1479175423764987914 
    try:
        bot.tree.copy_global_to(guild=discord.Object(id=id_mi_servidor))
        await bot.tree.sync(guild=discord.Object(id=id_mi_servidor))
        print(f"🚀 ¡Éxito! Amanda conectada y comando /resumen_sugerencias listo.")
        
        # 💡 Iniciamos los bucles automatizados si no se están ejecutando ya
        if not enviar_informe_automatico.is_running():
            enviar_informe_automatico.start()
        if not limpiar_mensajes_nocturnos.is_running():
            limpiar_mensajes_nocturnos.start()
        print("⏰ Relojes internos de Amanda sincronizados con la hora de España.")
            
    except Exception as e:
        print(f"Hubo un error al sincronizar a Amanda: {e}")

if TOKEN_AMANDA:
    bot.run(TOKEN_AMANDA)
