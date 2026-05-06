# Nivel Dios Picks 🏀

Bot de Telegram que analiza partidos NBA y entrega picks de apuestas diarios en español, usando IA (Groq llama3-70b).

---

## Instalación en Termux

### 1. Instalar dependencias base

```bash
pkg update && pkg upgrade
pkg install python git
```

### 2. Clonar el repositorio

```bash
git clone https://github.com/leoxfox21to/Nivel-dios-
cd Nivel-dios-
```

### 3. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 4. Configurar las claves API

Edita el archivo `.env` con tus claves:

```bash
nano .env
```

Rellena los 3 valores:

```
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
ODDS_API_KEY=tu_clave_de_odds_api
GROQ_API_KEY=tu_clave_de_groq
```

Guarda con `Ctrl+O`, luego `Ctrl+X`.

### 5. Ejecutar el bot

```bash
python main.py
```

---

## Comandos del Bot

| Comando | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida |
| `/basket` | Lista los partidos NBA de hoy con cuota O/U |
| `/basket 1` | Analiza el partido número 1 de la lista |
| `/help` | Ayuda completa en español |

---

## Fuentes de datos

- **BallDontLie API** — Estadísticas, resultados, historial (sin clave)
- **stats.nba.com** — Respaldo y lesiones (sin clave)
- **The Odds API** — Cuotas Pinnacle Over/Under y moneyline
- **Groq AI** — Análisis con modelo `llama3-70b-8192`

---

## Estructura del proyecto

```
Nivel-dios/
├── main.py              # Arranque del bot
├── config.py            # Variables de configuración
├── apis/
│   ├── balldontlie.py   # API principal de estadísticas
│   ├── nba_stats.py     # Respaldo stats.nba.com
│   ├── odds.py          # Cuotas de Pinnacle
│   └── groq_ai.py       # Análisis con IA
├── core/
│   ├── analyzer.py      # Recopila datos por partido
│   ├── filters.py       # Filtros de calidad antes de analizar
│   └── logger.py        # Registro de picks en picks_log.txt
├── bot/
│   ├── handlers.py      # Manejadores de comandos Telegram
│   └── formatter.py     # Formatea mensajes para el usuario
├── picks_log.txt        # Log de picks generados
├── .env                 # Claves API (no subir a GitHub)
└── requirements.txt     # Dependencias Python
```

---

## Obtener las claves API

- **TELEGRAM_BOT_TOKEN** → Habla con [@BotFather](https://t.me/BotFather) en Telegram, crea un bot con `/newbot`
- **GROQ_API_KEY** → Regístrate gratis en [console.groq.com](https://console.groq.com)
- **ODDS_API_KEY** → Regístrate en [the-odds-api.com](https://the-odds-api.com) (plan gratuito disponible)

---

## Mantener el bot activo en Termux

Para que el bot siga corriendo si cierras Termux, usa `nohup`:

```bash
nohup python main.py > bot.log 2>&1 &
```

Para ver el log en tiempo real:

```bash
tail -f bot.log
```

Para detenerlo:

```bash
pkill -f "python main.py"
```
