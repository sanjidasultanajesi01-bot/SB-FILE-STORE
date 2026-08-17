import asyncio
async def broadcast(bot,user_ids,send_func,delay=0.05):
    sent=failed=0
    for uid in user_ids:
        try: await send_func(bot,uid); sent+=1
        except Exception: failed+=1
        await asyncio.sleep(delay)
    return sent,failed
