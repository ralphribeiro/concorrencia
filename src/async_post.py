import asyncio
from datetime import datetime as dt
from itertools import cycle
import hashlib
from random import randint
from time import perf_counter_ns
from uuid import uuid4

from aiohttp import ClientSession


def timer(func):
    def inner(*args):
        inicio = perf_counter_ns()
        r = func(*args)
        fim = perf_counter_ns()
        print(f'{func.__name__}(): {(fim-inicio)/10**6}ms')
        return r
    return inner


async def post_(session: ClientSession, url: str, payload: dict) -> bytes:
    async with session.post(
        url, headers={'Content-Type': 'application/json'}, json=payload
    ) as response:
        return await response.content.read()


def chunked_client(num_chunks):
    semaphore = asyncio.Semaphore(num_chunks)

    async def pool(url: str, payload: dict):
        nonlocal semaphore
        async with semaphore:
            async with ClientSession() as session:
                content = await post_(session, url, payload)
                return content
    return pool


async def spin(msg):
    for char in cycle('|/-\\'):
        status = char + ' ' + msg
        print(status, flush=True, end='\r')
        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            break
    print(' ' * len(status), end='\r')


def generate_cpf():
    cpf = [randint(0, 9) for x in range(9)]
    for _ in range(2):
        val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
        cpf.append(11 - val if val > 1 else 0)
    return '%s%s%s.%s%s%s.%s%s%s-%s%s' % tuple(cpf)


def get_random_payload():
    event_id = hashlib.sha256(str(dt.now()).encode()).hexdigest()
    user_id = hashlib.sha256(str(dt.now())[::-1].encode()).hexdigest()
    return {
        'transaction_date': dt.now().isoformat(),
        'client_id': 4,
        'event_code': '7',
        'status': 1,
        'returned_score': randint(0, 100),
        'session_id': uuid4().hex,
        'transaction_id': uuid4().hex,
        'transaction_type': '7',
        'user_id': user_id,
        'user_key_1': 'email',
        'user_key_2': None,
        'user_key_3': None,
        'user_key_4': None,
        'tags': '-',
        'score_reason': '-',
        'channel': 2,
        'cpf': generate_cpf(),
        'event_id': event_id,
    }


async def processing(url, num_chunk, qtd):
    spinner = asyncio.create_task(spin('carregando...'))
    http_chunked = chunked_client(num_chunk)
    tasks = [asyncio.create_task(
        http_chunked(url, get_random_payload())) for p in range(qtd)]
    ret = await asyncio.gather(*tasks)
    spinner.cancel()
    return ret


@timer
def main():
    url = 'url linda'
    num_chunk = 10
    qtd = 100
    return asyncio.run(processing(url, num_chunk, qtd))


if __name__ == '__main__':
    ret = main()
    # print(ret)
