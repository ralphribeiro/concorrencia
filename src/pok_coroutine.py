import asyncio
from os import mkdir
from os.path import dirname, exists, join as p_join
from shutil import rmtree
from time import perf_counter_ns
from urllib.parse import urljoin

from aiofiles import open as aopen
from aiohttp import ClientSession
from requests import get


base_url = 'https://pokeapi.co/api/v2/'
pokemons = get(urljoin(base_url, 'pokemon/?limit=100')).json()['results']

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


async def write_file(session, url, name):
    async with session.get(url) as response:
        print(f'baixando: {url.rsplit("/")[-1]}')
        async with aopen(f'{name}.png', 'wb') as f:
            content = await response.content.read()
            await f.write(content)


async def get_sprite_link(url, name):
    async with ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            result = await response.json()
            sprite_url = result['sprites']['front_default']
            await write_file(session, sprite_url, p_join(_path, name))


async def get_sprites(loop):
    tasks = []
    for p in pokemons:
        t = loop.create_task(get_sprite_link(p['url'], p['name']))
        tasks.append(t)

    for task in tasks:
        await task

@timer
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_sprites(loop))


if __name__ == '__main__':
    main()
