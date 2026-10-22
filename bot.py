import asyncio
import logging
import os
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramNetworkError

import config
import database
from handlers import user, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Веб-сервер для Render (Health Check)
async def handle_ping(request):
    return web.json_response({
        "status": "online",
        "bot": "Miragix VPN",
        "message": "I am alive and running!"
    })

async def start_web_server():
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    app.router.add_get("/ping", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {port} (для Render)")

# Автоматический фоновый самопингер (защита от спячки Render без сторонних сервисов)
async def keep_alive_task():
    app_url = os.getenv("RENDER_EXTERNAL_URL") or "https://miragix-vpn-bot.onrender.com"
    health_url = f"{app_url.rstrip('/')}/health"
    await asyncio.sleep(30)  # Подождать 30 секунд после старта
    logging.info(f"Запущена встроенная защита от спячки. Пинг на: {health_url}")
    
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(health_url, timeout=10) as resp:
                    logging.info(f"Защита от спячки: успешный пинг ({resp.status})")
        except Exception as e:
            logging.warning(f"Ошибка самопинга: {e}")
        await asyncio.sleep(600)  # Каждые 10 минут

async def run_bot_polling(bot: Bot, dp: Dispatcher):
    while True:
        try:
            try:
                await bot.delete_webhook(drop_pending_updates=True)
            except Exception as e:
                logging.warning(f"Не удалось удалить вебхук: {e}")

            logging.info("Miragix VPN Бот подключился к Telegram и ожидает сообщений...")
            await dp.start_polling(bot, handle_signals=False)
        except TelegramNetworkError as e:
            logging.warning(f"Сетевой сбой при связи с Telegram: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}. Перезапуск через 5 секунд...")
            await asyncio.sleep(5)

async def main():
    if not config.BOT_TOKEN:
        logging.error("Критическая ошибка: BOT_TOKEN не указан в файле .env!")
        return

    # Инициализация базы данных
    await database.init_db()

    # Запуск легковесного веб-сервера для Render
    await start_web_server()

    # Запуск авто-пингера против спячки в фоне
    asyncio.create_task(keep_alive_task())

    # Создание бота и диспетчера
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(admin.router)
    dp.include_router(user.router)

    await run_bot_polling(bot, dp)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
