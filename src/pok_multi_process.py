from os import mkdir
from os.path import dirname, exists, join as p_join
from requests import get
from shutil import rmtree, copyfileobj
import multiprocessing
from time import perf_counter_ns


def timer(func):
    def inner(*args):
        inicio = perf_counter_ns()
        r = func(*args)
        fim = perf_counter_ns()
        print(f'{func.__name__}(): {(fim-inicio)/10**6}ms')
        return r
    return inner


url_base = 'https://pokeapi.co/api/v2/pokemon'
folder_name = 'sprites'
_path = p_join(dirname(__file__), folder_name)

if exists(_path):
    rmtree(_path)

mkdir(_path)


def get_pokemon(n):
    response = get(f'{url_base}/{n}')
    return response.json()


def get_sprite_link(raw):
    name = raw['name']
    sprite = raw['sprites']['front_default']
    return {name: sprite}


def download_sprite(pok: dict):
    name, url = list(pok.items())[0]
    name += f'.{url.rsplit(".")[-1]}'
    path = p_join(_path, name)

    with get(url, stream=True) as r:
        with open(path, 'wb') as f:
            copyfileobj(r.raw, f)


def get_sprites(qtt_ini, qtt_fin):
    raws = (get_pokemon(n) for n in range(qtt_ini, qtt_fin + 1))
    poks = (get_sprite_link(p) for p in raws)
    for p in poks:
        download_sprite(p)

@timer
def main():
    process = []
    num_sprites = 20
    num_process = 10
    args = [(v+1, v+num_process) for v in range(0, num_sprites, num_process)]
    for a in args:
        p = multiprocessing.Process(target=get_sprites, args=a)
        p.start()
        process.append(p)

    for p in process:
        p.join()


main()
