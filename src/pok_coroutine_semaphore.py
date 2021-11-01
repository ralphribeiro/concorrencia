import asyncio
import logging
import itertools
from os import mkdir
from os.path import dirname, exists
from os.path import join as p_join
from shutil import rmtree
from time import perf_counter_ns
from urllib.parse import urljoin


from aiofiles import open as aopen
from aiohttp import ClientSession, client
from requests import get


# logging.basicConfig(level=logging.INFO)

base_url = 'https://pokeapi.co/api/v2/'
n_poks = 250
poks = get(urljoin(base_url, f'pokemon/?limit={n_poks}')).json()['results']

folder_name = 'sprites'
_path = p_join(dirname(__file__), folder_name)

if exists(_path):
    rmtree(_path)
mkdir(_path)


def timer(func):
    def inner(*args):
        inicio = perf_counter_ns()
        r = func(*args)
        fim = perf_counter_ns()
        print(f'{func.__name__}(): {(fim-inicio)/10**6}ms')
        return r
    return inner


async def get_sprite_url(session: ClientSession, url: str) -> str:
    async with session.get(url) as response:
        logging.info(f'baixando url sprite: {url}')
        response.raise_for_status()
        result = await response.json()
        return result['sprites']['front_default']


async def download_bin(session: ClientSession, url: str) -> bytes:
    async with session.get(url) as response:
        logging.info(f'baixando: {url.rsplit("/")[-1]}')
        return await response.content.read()


async def save_file(name: str, data: bytes) -> int:
    async with aopen(f'{name}.png', 'wb') as f:
        logging.info(f'salvando: {name}')
        return await f.write(data)


def chunked_client(num_chunks):
    semaphore = asyncio.Semaphore(num_chunks)

    async def pipe_sprt(url_sprite: str, name: str):
        nonlocal semaphore
        async with semaphore:
            async with ClientSession() as session:
                url = await get_sprite_url(session, url_sprite)
                content = await download_bin(session, url)
                ret = await save_file(p_join(_path, name), content)
                logging.info(f'feito! {name}, {ret} bytes')
    return pipe_sprt


async def spin(msg):
    for char in itertools.cycle('|/-\\'):
        status = char + ' ' + msg
        print(status, flush=True, end='\r')
        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            break
    print(' ' * len(status), end='\r')


async def processing(num_chunk):
    spinner = asyncio.create_task(spin('carregando...'))
    http_chunked = chunked_client(num_chunk)
    await asyncio.gather(
        *[asyncio.create_task(http_chunked(p['url'], p['name'])) for p in poks]
    )
    spinner.cancel()


@timer
def main():
    asyncio.run(processing(num_chunk=100))


if __name__ == '__main__':
    main()
