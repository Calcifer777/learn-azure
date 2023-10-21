import asyncio
import logging
import random
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(name: str):
  i = random.randint(1, 2)
  logger.warning(f"Sleeping for {i}s...")
  time.sleep(i)
  return "Hello, " + name