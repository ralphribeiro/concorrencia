import asyncio
import itertools
import logging
from collections.abc import Sequence
from os import mkdir
from os.path import dirname, exists
from os.path import join as p_join
from shutil import rmtree
from time import perf_counter_ns
from urllib.parse import urljoin

from aiofiles import open as aopen
from httpx import AsyncClient, get

logging.basicConfig(level=logging.INFO)


def prepare_folder(folder_name):
    path_ = p_join(dirname(__file__), folder_name)
    if exists(path_):
        rmtree(path_)
    mkdir(path_)
    return path_


def get_pok_urls(n_poks):
    base_url = "https://pokeapi.co/api/v2/"
    return get(urljoin(base_url, f"pokemon/?limit={n_poks}")).json()["results"]


def timer(func):
    def inner(*args):
        inicio = perf_counter_ns()
        r = func(*args)
        fim = perf_counter_ns()
        logging.info(f"{func.__name__}(): {(fim-inicio)/10**6}ms")
        return r

    return inner


async def get_sprite_url(session: AsyncClient, url: str) -> str:
    response = await session.get(url)
    logging.info(f"baixando url sprite: {url}")
    result = response.raise_for_status().json()
    return result["sprites"]["front_default"]


async def download_bin(session: AsyncClient, url: str) -> bytes:
    response = await session.get(url)
    logging.info(f'baixando: {url.rsplit("/")[-1]}')
    return response.read()


async def save_file(name: str, data: bytes) -> int:
    async with aopen(f"{name}.png", "wb") as f:
        logging.info(f"salvando: {name}")
        return await f.write(data)


def chunked_client(n_chunks: int = 1):
    semaphore = asyncio.Semaphore(n_chunks)

    async def pipe_sprt(url_sprite: str, name: str, path_: str):
        nonlocal semaphore
        async with semaphore:
            async with AsyncClient() as session:
                url = await get_sprite_url(session, url_sprite)
                content = await download_bin(session, url)
                ret = await save_file(p_join(path_, name), content)
                logging.info(f"feito! {name}, {ret} bytes")

    return pipe_sprt


async def spin(msg):
    for char in itertools.cycle("|/-\\"):
        status = char + " " + msg
        print(status, flush=True, end="\r")
        try:
            await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            break
    print(" " * len(status), end="\r")


async def processing(pok_urls: Sequence, path_: str, n_chunks: int = 10):
    spinner = asyncio.create_task(spin("carregando..."))
    chunked_requests = chunked_client(n_chunks)
    await asyncio.gather(
        *[asyncio.create_task(chunked_requests(p["url"], p["name"], path_)) for p in pok_urls]
    )
    spinner.cancel()


@timer
def main():
    n_poks = 100
    n_chunks = 50
    path_ = prepare_folder("sprites")
    pok_urls = get_pok_urls(n_poks)
    asyncio.run(processing(pok_urls, path_, n_chunks))


if __name__ == "__main__":
    main()
