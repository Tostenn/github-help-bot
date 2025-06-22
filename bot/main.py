# from telegram import Update
# from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
# Chargement des variables d'environnement
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = '-1002870634400'

'''
definit les commandes du bot Telegram
Ce bot permet de gérer un dépôt GitHub et d'afficher des statistiques.

/start - Démarre le bot et affiche un message de bienvenue
/help - Affiche les commandes disponibles
/stats [repo] - Affiche les statistiques du dépôt GitHub
/lastcommit [repo] - Affiche le dernier commit du dépôt GitHub

connect ton compte GitHub avec un token personnel pour accéder aux dépôts privés
/github [token] - Connecte ton compte GitHub avec un token personnel
/eventLastCommit [repo] - pour etre alerté des derniers commits d'un dépôt
'''

# /start
info_start = """Gitub Help Bot
Ce bot permet de gérer un dépôt GitHub et d'afficher des statistiques.
lances la commande /help pour voir les commandes disponibles.
"""
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
# import os

# === CONFIGURATION ===
DATA_FILE = "github_users.json"
WEBHOOK_URL = "https://TON_DOMAINE/github/webhook"  # URL de ton serveur Flask

# === UTILITAIRES ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_token(user_id):
    data = load_data()
    return data.get(str(user_id), {}).get("token")

def set_user_token(user_id, token):
    data = load_data()
    data[str(user_id)] = {"token": token}
    save_data(data)

def get_headers(token=None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def get_latest_commit(owner_repo, token=None):
    headers = get_headers(token)
    url = f"https://api.github.com/repos/{owner_repo}/commits"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commit = response.json()[0]
        return f"🔧 Dernier commit sur {owner_repo} :\nAuteur : {commit['commit']['author']['name']}\nMessage : {commit['commit']['message']}\nLien : {commit['html_url']}"
    return "❌ Impossible de récupérer le commit. Vérifie le nom du dépôt."

def get_repo_stats(owner_repo, token=None):
    headers = get_headers(token)
    url = f"https://api.github.com/repos/{owner_repo}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo = response.json()
        return (f"📊 Statistiques de {owner_repo} :\n"
                f"⭐ Stars : {repo['stargazers_count']}\n"
                f"🍴 Forks : {repo['forks_count']}\n"
                f"🐛 Issues : {repo['open_issues_count']}\n"
                f"👀 Watchers : {repo['watchers_count']}")
    return "❌ Impossible de récupérer les stats. Vérifie le nom du dépôt."

def create_webhook(owner_repo, token):
    headers = get_headers(token)
    url = f"https://api.github.com/repos/{owner_repo}/hooks"
    data = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": WEBHOOK_URL,
            "content_type": "json"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        return True
    return False

# === COMMANDES TELEGRAM ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bienvenue ! Utilisez /help pour voir les commandes disponibles.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
📋 Commandes disponibles :
/start - Démarre le bot
/help - Affiche cette aide
/github [token] - Connecte ton compte GitHub
/stats [owner/repo] - Affiche les stats du dépôt
/lastcommit [owner/repo] - Affiche le dernier commit
/eventLastCommit [owner/repo] - Active les alertes sur les commits
""")

async def github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("❗ Utilisation : /github [token]")
    token = context.args[0]
    user_id = update.effective_user.id
    set_user_token(user_id, token)
    await update.message.reply_text("🔐 Ton compte GitHub est connecté avec succès !")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("❗ Utilisation : /stats [owner/repo]")
    owner_repo = context.args[0]
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    msg = get_repo_stats(owner_repo, token)
    await update.message.reply_text(msg)

async def lastcommit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("❗ Utilisation : /lastcommit [owner/repo]")
    owner_repo = context.args[0]
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    msg = get_latest_commit(owner_repo, token)
    await update.message.reply_text(msg)

async def event_last_commit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("❗ Utilisation : /eventLastCommit [owner/repo]")
    owner_repo = context.args[0]
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    if not token:
        return await update.message.reply_text("🔒 Tu dois te connecter avec /github [token] pour ajouter un webhook.")
    success = create_webhook(owner_repo, token)
    if success:
        await update.message.reply_text(f"🔔 Tu recevras maintenant des alertes pour chaque nouveau commit sur {owner_repo}.")
    else:
        await update.message.reply_text("❌ Impossible d'ajouter un webhook. Vérifie que tu es bien propriétaire ou collaborateur du dépôt.")

# === INITIALISATION DU BOT ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("github", github))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("lastcommit", lastcommit))
app.add_handler(CommandHandler("eventLastCommit", event_last_commit))

if __name__ == '__main__':
    print("🚀 Bot lancé...")
    app.run_polling()