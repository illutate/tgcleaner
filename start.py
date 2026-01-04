import os
from time import sleep
from pyrogram import Client
from pyrogram.errors import FloodWait

API_ID = int(os.getenv("API_ID") or input("Enter Telegram API_ID: "))
API_HASH = os.getenv("API_HASH") or input("Enter Telegram API_HASH: ")

app = Client("cleaner", api_id=API_ID, api_hash=API_HASH)


class Cleaner:
    def __init__(self, delete_chunk_size=100):
        self.chats = []
        self.delete_chunk_size = delete_chunk_size

    @staticmethod
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    async def get_private_chats(self):
        chats = []
        async for dialog in app.get_dialogs():
            if dialog.chat.type.name == "PRIVATE":
                chats.append(dialog.chat)
        return chats

    async def select_private_chats(self):
        chats = await self.get_private_chats()

        if not chats:
            print("Личных чатов не найдено")
            return

        print("\nУдалить все твои сообщения в личных чатах:\n")

        for i, chat in enumerate(chats):
            name = chat.first_name or chat.username or "Unknown"
            print(f"  {i + 1}. {name}")

        print(f"\n  {len(chats) + 1}. (!) ВСЕ ЛИЧНЫЕ ЧАТЫ (!)\n")

        nums = input("Выбери номера (через запятую): ").split(",")

        for n in map(lambda x: int(x.strip()), nums):
            if n == len(chats) + 1:
                confirm = input('Напиши "I UNDERSTAND": ')
                if confirm.upper() != "I UNDERSTAND":
                    print("Отмена")
                    return
                self.chats = chats
                break
            elif 1 <= n <= len(chats):
                self.chats.append(chats[n - 1])
            else:
                print("Неверный номер")
                return

        print("\nВыбраны чаты:")
        for c in self.chats:
            print("-", c.first_name or c.username)

    async def run(self):
        for chat in self.chats:
            print(f"\nОбработка чата: {chat.first_name or chat.username}")
            message_ids = []

            async for msg in app.search_messages(
                chat_id=chat.id,
                from_user="me",
                limit=0
            ):
                message_ids.append(msg.id)

            print(f"Найдено сообщений: {len(message_ids)}")

            for chunk in self.chunks(message_ids, self.delete_chunk_size):
                try:
                    await app.delete_messages(chat.id, chunk)
                except FloodWait as e:
                    sleep(e.value)

            print("Готово")


async def main():
    async with app:
        cleaner = Cleaner()
        await cleaner.select_private_chats()
        await cleaner.run()


app.run(main())
