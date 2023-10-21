import asyncio
import logging
import random


async def main(name: str):
  i = random.randint(5, 10)
  logging.warning(f"Sleeping for {i}s...")
  asyncio.sleep(i)
  return "Hello, " + name