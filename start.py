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
        self.stats = {}

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
            return False

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
                    return False
                self.chats = chats
                break
            elif 1 <= n <= len(chats):
                self.chats.append(chats[n - 1])
            else:
                print("Неверный номер")
                return False

        return True

    async def scan_messages(self):
        print("\nСканирование сообщений...")
        total = 0

        for chat in self.chats:
            count = 0
            async for _ in app.search_messages(chat.id, from_user="me", limit=0):
                count += 1
            self.stats[chat.id] = count
            total += count

            name = chat.first_name or chat.username
            print(f"- {name}: {count}")

        print(f"\nВСЕГО сообщений к удалению: {total}")
        return total

    async def delete_messages(self):
        for chat in self.chats:
            name = chat.first_name or chat.username
            print(f"\nУдаление в чате: {name}")

            ids = []
            async for msg in app.search_messages(chat.id, from_user="me", limit=0):
                ids.append(msg.id)

            for chunk in self.chunks(ids, self.delete_chunk_size):
                try:
                    await app.delete_messages(chat.id, chunk)
                except FloodWait as e:
                    sleep(e.value)

            print("Готово")

    async def run(self):
        total = await self.scan_messages()

        if total == 0:
            print("Удалять нечего")
            return

        print("\n⚠️ ВНИМАНИЕ ⚠️")
        print("Это действие НЕОБРАТИМО.")
        print("Сообщения будут удалены НАВСЕГДА.\n")

        confirm = input('Чтобы продолжить, напиши "DELETE": ')
        if confirm != "DELETE":
            print("Отменено пользователем")
            return

        await self.delete_messages()


async def main():
    async with app:
        cleaner = Cleaner()
        ok = await cleaner.select_private_chats()
        if ok:
            await cleaner.run()


app.run(main())
