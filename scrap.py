from itertools import chain
import json
import time
import re
import aiohttp
import aiofiles
import asyncio
import os
import shutil
import requests
import numpy as np
from bs4 import BeautifulSoup, SoupStrainer

def flatten(nested_list):
    return [k for i in nested_list for j in i for k in j]

def soup_filter(content, param_list):
    tag = param_list.get('tag')
    attr = param_list.get('attr')
    prefix = param_list.get('prefix')
    str_content = param_list.get('str_content')
    #Filtra tags
    soup = BeautifulSoup(content, 'html.parser', parse_only=SoupStrainer(tag))
    #Filtra atributo
    all_links = [link[attr] for link in soup if link.has_attr(attr)]
    #Filtra a string dos links
    filtered_links = [link for link in all_links if (str_content in link) and (link.startswith(prefix))]
    #Remove links duplicados
    filtered_links = set(filtered_links)
    return list(filtered_links)

def check_legality(content):
    tag = 'b'
    attr = 'class'
    class_name = 'card-legality-warning-pill'
    value = 'Not Legal'
    try:
        soup = BeautifulSoup(content, 'html.parser', parse_only=SoupStrainer(tag))
        return any(value in link for link in soup.findAll(tag, {attr:class_name}))
    except:
        return True
        

async def fetch(url, session):
    try:
        async with session.get(url=url) as response:
            return await response.read()
    except Exception as e:
        print(f'Unable to get url {url} due to {e}.')


async def get_urls(urls):
    async with aiohttp.ClientSession() as session:
        htmls = await asyncio.gather(*[asyncio.create_task(fetch(url, session)) for url in urls])
        return htmls

def get_filtered_urls(urls, filter_params):
    loop = asyncio.get_event_loop()
    all_contents = loop.run_until_complete(get_urls(urls))
    filtered_urls = [
        [soup_filter(content=url, param_list=params) for url in all_contents if not check_legality(content=url)]
        for params
        in filter_params
    ]
    return filtered_urls

async def fatch_files(url, session, folder, file_name):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                file_path = os.path.join(folder, file_name)
                f = await aiofiles.open(file_path, mode='wb')
                await f.write(await resp.read())
                await f.close()
    except Exception as e:
        print(f'Unable to get url {url} due to {e}.')

async def get_files(urls, folder, ext):
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[asyncio.create_task(fatch_files(url, session, folder, str(e) + ext)) for e, url in enumerate(urls)])

'''Parametros implementados na busca das cartas
Todos os parametros sao passados como dicionarios 
para filtrar os elementos de interesse dentro das
paginas web'''

set_params = {
    'tag':'a',
    'attr':'href',
    'prefix': r'https://scryfall.com/sets',
    'str_content': '',
}
cards_params = {
    'tag':'a',
    'attr':'href',
    'prefix': r'https://scryfall.com/card',
    'str_content': '',
}
img_params = {
    'tag':'img',
    'attr':'src',
    'prefix': r'https://c1.scryfall.com/file/scryfall-cards/',
    'str_content': '',
}

json_params = {
    'tag':'a',
    'attr':'href',
    'prefix': r'https://api.scryfall.com/cards/',
    'str_content': 'format=json',
}

#url principal
url = r'https://scryfall.com/sets'
#buscar por todos os sets de magic
all_sets_urls = flatten(get_filtered_urls([url], [set_params]))
#bucar por todas as cartas do set
all_cards_urls = flatten(get_filtered_urls(all_sets_urls, [cards_params]))
print(all_cards_urls)

# #Achatar todos os 3 niveis de listas aninhadas
# all_cards_urls = [k for j in all_cards_urls for i in j for k in i]
# #Limita a quantidade de cartas que serao buscadas
# all_cards_urls = all_cards_urls[:30000]

# #Buscar por todas as urls das imgs e jsons de info das cartas
# all_img_json_urls = get_filtered_urls(
#     urls=all_cards_urls,
#     filter_params=[img_params, json_params]
# )

# #Filtrar cartas validas e com apenas uma imagem
# all_img_json_urls = [
#     (imgs[0], jsons[0]) 
#     for imgs, jsons  
#     in zip(*all_img_json_urls) 
#     if len(jsons) == len(imgs) == 1
# ]
# #Achatar a lista de cartas e jsons e separa-las em 2 variaveis
# all_img_json_urls = [urls for urls in zip(*all_img_json_urls)]
# all_img_urls, all_json_urls = all_img_json_urls

# #salvar todas as imagens e Jsons
# metadata_folder = r'dataset\metadata'
# imgs_folder = r'dataset\imgs'
# asyncio.run(get_files(all_img_urls, imgs_folder, '.jpg'))
# asyncio.run(get_files(all_json_urls, metadata_folder, '.json'))





