import aiorun
import environs
import aiogram
import asyncio

from aiogram import F

env = environs.Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
RAW_CHAT_ID = env.int("CHAT_ID")
MAX_DICKS = env.int("MAX_DICKS", 10)

CHAT_ID = -(int(1e12) + RAW_CHAT_ID)


print("listening to chat", RAW_CHAT_ID)
print(f"limiting to {MAX_DICKS} max dicks")


class LowerBoundQueue[T]:
    def __init__(self, bound: int) -> None:
        self._add = asyncio.Queue[T](maxsize=bound)
        self._remove = asyncio.Queue[T]()

    def add(self, item: T) -> None:
        if self._add.full():
            self._remove.put_nowait(self._add.get_nowait())

        self._add.put_nowait(item)

    async def take(self) -> T:
        return await self._remove.get()


queue = LowerBoundQueue[int](bound=MAX_DICKS)

dp = aiogram.Dispatcher()

DICK_REMOVER_BOT = 6465471545


@dp.message(F.via_bot.id == DICK_REMOVER_BOT)
async def handle_message(message: aiogram.types.Message) -> None:
    queue.add(message.message_id)
    print("put", get_chat_link(message.message_id), "into bounded queue")


def get_chat_link(post_id: int) -> str:
    return f"https://t.me/c/{RAW_CHAT_ID}/{post_id}"


async def remover(bot: aiogram.Bot) -> None:
    while True:
        item = await queue.take()
        print("taken", get_chat_link(item), "from queue")
        await bot.delete_message(CHAT_ID, item)

        print("deleted", get_chat_link(item))


async def run_bot(bot: aiogram.Bot) -> None:
    try:
        await dp.start_polling(bot, handle_signals=False)
    except (asyncio.CancelledError, Exception):
        print("Bot polling was cancelled, shutting down gracefully.")


async def main() -> None:
    bot = aiogram.Bot(token=BOT_TOKEN)

    _remover = asyncio.create_task(remover(bot))
    await asyncio.gather(_remover, run_bot(bot))


aiorun.run(main(), stop_on_unhandled_errors=True)
