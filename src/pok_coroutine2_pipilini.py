import asyncio
from functools import partial, wraps
import logging
import itertools
from os import mkdir
from os.path import dirname, exists
from os.path import join as p_join
from shutil import rmtree
from time import perf_counter_ns
from urllib.parse import urljoin


from aiofiles import open as aopen
from aiohttp import ClientSession
from requests import get


logging.basicConfig(level=logging.INFO)

base_url = 'https://pokeapi.co/api/v2/'
n_poks = 30
poks = get(urljoin(base_url, f'pokemon/?limit={n_poks}')).json()['results']

folder_name = 'sprites'
_path = p_join(dirname(__file__), folder_name)

if exists(_path):
    rmtree(_path)
mkdir(_path)


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


async def pipilini(*funcs):
    wraps(*funcs)

    async def inner(data):
        result = data
        for f in funcs:
            result = await f(result)
        return result
    return inner


async def get_pokemons(url_sprite: str, name: str):
    download_path = p_join(_path, name)

    async with ClientSession() as session:
        pipi = await pipilini(
            partial(get_sprite_url, session),
            partial(download_bin, session),
            partial(save_file, download_path)
        )

        ret = await pipi(url_sprite)
        logging.info(f'feito! {name}, {ret} bytes')


async def spin(msg):
    for char in itertools.cycle('|/-\\'):
        status = char + ' ' + msg
        print(status, flush=True, end='\r')
        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            break
    print(' ' * len(status), end='\r')  # type: ignore


async def processing():
    spinner = asyncio.create_task(spin('carregando...'))
    await asyncio.gather(
        *[asyncio.create_task(get_pokemons(p['url'], p['name'])) for p in poks]
    )
    spinner.cancel()


def main():
    inicio = perf_counter_ns()
    asyncio.run(processing())
    fim = perf_counter_ns()
    print(f'Tempo gasto: {(fim-inicio)/10**6}ms')


if __name__ == '__main__':
    main()
