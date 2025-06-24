import asyncio
import aioconsole


async def main():
    while True:
        name_taker = asyncio.create_task(
            aioconsole.ainput("What's your name? ")
        )
        try:
            data = await asyncio.wait_for(name_taker, 3)
        except asyncio.TimeoutError:
            print("\nAre you there foo?")
            name_taker.cancel()
            break
        else:
            print(f"Hello, {data}!")

asyncio.run(main())
