import aiohttp
import logging
from datetime import datetime, timedelta
import config

class MarzbanService:
    def __init__(self):
        self.base_url = config.MARZBAN_URL.rstrip("/") if config.MARZBAN_URL else ""
        self.username = config.MARZBAN_USERNAME
        self.password = config.MARZBAN_PASSWORD
        self.token = None

    async def get_token(self):
        if not self.base_url:
            return None
        url = f"{self.base_url}/api/admin/token"
        data = {"username": self.username, "password": self.password}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        self.token = res.get("access_token")
                        return self.token
                    else:
                        logging.error(f"Ошибка получения токена Marzban: {resp.status}")
        except Exception as e:
            logging.error(f"Не удалось подключиться к Marzban: {e}")
        return None

    async def create_or_extend_user(self, telegram_id: int, days: int):
        username = f"user_{telegram_id}"
        
        # Если сервер еще не подключен, выдаем тестовую демонстрационную ссылку
        if not self.base_url:
            logging.info(f"Режим демо: симуляция создания пользователя {username}")
            fake_sub = f"https://demo-vpn.example/sub/{username}?token=demo12345"
            return {
                "username": username,
                "subscription_url": fake_sub,
                "expire_date": (datetime.now() + timedelta(days=days)).isoformat(),
                "is_demo": True
            }

        # Боевой режим с реальным сервером Marzban
        if not self.token:
            await self.get_token()

        headers = {"Authorization": f"Bearer {self.token}"}
        expire_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        async with aiohttp.ClientSession() as session:
            # Проверяем, существует ли пользователь
            async with session.get(f"{self.base_url}/api/user/{username}", headers=headers) as check_resp:
                if check_resp.status == 200:
                    # Пользователь существует, продлеваем
                    user_data = await check_resp.json()
                    curr_expire = user_data.get("expire") or int(datetime.now().timestamp())
                    new_expire = max(curr_expire, int(datetime.now().timestamp())) + (days * 86400)
                    
                    update_data = {
                        "expire": new_expire,
                        "status": "active"
                    }
                    async with session.put(f"{self.base_url}/api/user/{username}", json=update_data, headers=headers) as up_resp:
                        res = await up_resp.json()
                        return {
                            "username": username,
                            "subscription_url": res.get("subscription_url"),
                            "expire_date": datetime.fromtimestamp(new_expire).isoformat(),
                            "is_demo": False
                        }
                else:
                    # Создаем нового пользователя
                    create_data = {
                        "username": username,
                        "proxies": {"vless": {}},
                        "inbounds": {},
                        "expire": expire_timestamp,
                        "data_limit": 0, # Безлимит трафика
                        "status": "active"
                    }
                    async with session.post(f"{self.base_url}/api/user", json=create_data, headers=headers) as cr_resp:
                        if cr_resp.status in [200, 201]:
                            res = await cr_resp.json()
                            return {
                                "username": username,
                                "subscription_url": res.get("subscription_url"),
                                "expire_date": datetime.fromtimestamp(expire_timestamp).isoformat(),
                                "is_demo": False
                            }
                        else:
                            text = await cr_resp.text()
                            logging.error(f"Ошибка создания пользователя в Marzban: {text}")
                            return None

marzban_service = MarzbanService()
