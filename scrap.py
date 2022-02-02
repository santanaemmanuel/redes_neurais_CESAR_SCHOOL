from asyncore import loop
import json
import aiohttp
import aiofiles
import asyncio
import os
import shutil
from bs4 import BeautifulSoup, SoupStrainer

def flatten(nested_list):
    '''Funcao criada para achatar as listas de URL's fitlradas'''
    return [k for i in nested_list for j in i for k in j]

def soup_filter(content, param_list):
    '''Funcao criada para filtrar conteudos relevantes de uma URL atraves
    de um conjunto de parametros'''
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
    '''Funcao criada para evitar cards promocionais que nao seguem a estrutura
    de um card convencional de magic'''
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
    '''funcao criada para realizar uma consulta em uma URL'''
    try:
        async with session.get(url=url) as response:
            return await response.read()
    except Exception as e:
        print(f'Unable to get url {url} due to {e}.')


async def get_urls(urls):
    '''funcao criada para realizar multiplas consultas simultaneas a URLs'''
    async with aiohttp.ClientSession() as session:
        htmls = await asyncio.gather(*[asyncio.create_task(fetch(url, session)) for url in urls])
        return htmls

def get_filtered_urls(urls, filter_params):
    '''funcao criada para englobar tanto a consulta a uma URL como filtrar
    o conteudo retornado'''
    loop = asyncio.get_event_loop()
    all_contents = loop.run_until_complete(get_urls(urls))
    filtered_urls = [
        [soup_filter(content=url, param_list=params) for url in all_contents if not check_legality(content=url)]
        for params
        in filter_params
    ]
    return filtered_urls

async def fatch_files(url, session, folder, file_name):
    '''funcao criada para realizar o download de elementos em sites
    de forma assincrona'''
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
    '''funcao criada para realizar o download de multiplos elementos
    de forma simultanea e assincrona'''
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[asyncio.create_task(fatch_files(url, session, folder, str(e) + ext)) for e, url in enumerate(urls)])

'''Abaixo segue a lista de parametros passados
ao filtrar o conteudo obtido nas URLs.'''
#Filtrar Sets
set_params = {
    'tag':'a',
    'attr':'href',
    'prefix': r'https://scryfall.com/sets',
    'str_content': '',
}
#Filtrar cartas
cards_params = {
    'tag':'a',
    'attr':'href',
    'prefix': r'https://scryfall.com/card',
    'str_content': '',
}
#Filtrar as imagens
img_params = {
    'tag':'img',
    'attr':'src',
    'prefix': r'https://c1.scryfall.com/file/scryfall-cards/',
    'str_content': '',
}
#Filtrar o json contendo metadados da carta
json_params = {
    'tag':'a',
    'attr':'href',
    'prefix': r'https://api.scryfall.com/cards/',
    'str_content': 'format=json',
}

#url principal
url = r'https://scryfall.com/sets'
#buscar por todos os sets de magic
all_sets_urls = get_filtered_urls([url], [set_params])
all_sets_urls = flatten(all_sets_urls)
#bucar por todas as cartas do set
all_cards_urls = get_filtered_urls(all_sets_urls, [cards_params])
all_cards_urls = flatten(all_cards_urls)
print(all_cards_urls)
#Limita a quantidade de cartas que serao buscadas
all_cards_urls = all_cards_urls[:1000]

#Buscar por todas as urls das imgs e jsons de info das cartas
all_img_json_urls = get_filtered_urls(
    urls=all_cards_urls,
    filter_params=[img_params, json_params]
)


#Filtrar cartas validas e com apenas uma imagem
all_img_json_urls = [
    (imgs[0], jsons[0]) 
    for imgs, jsons  
    in zip(*all_img_json_urls) 
    if len(jsons) == len(imgs) == 1
]
#Transpoe a lista
all_img_json_urls = [i for i in zip(*all_img_json_urls)]
#separa a lista em 2 variaveis
all_img_urls, all_json_urls = all_img_json_urls

#salvar todas as imagens e Jsons
metadata_folder = r'dataset\raw\metadata'
imgs_folder = r'dataset\raw\imgs'
os.makedirs(metadata_folder, exist_ok=True)
os.makedirs(imgs_folder, exist_ok=True)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(get_files(all_img_urls, imgs_folder, '.jpg'))
loop.run_until_complete(get_files(all_json_urls, metadata_folder, '.json'))

'''Esta ultima etapa ira filtrar uma quantidade menor de cartas a ser
utilizada no treinamento e avaliacao do modelo. Nesse caso foram 
separados 600 cartas de cada cor'''
color_count = {
    'W':0,
    'U':0,
    'B':0,
    'R':0,
    'G':0
}
#cria a pasta de cada cor
class_list = ['W','U','R','G','B']
img_folder = r'dataset\raw\imgs'
metadata_folder = r'dataset\raw\metadata'
destination_folder = r'dataset\mtg_cards'
for class_name in class_list:
    class_path = os.path.join(destination_folder, class_name)
    os.makedirs(class_path, exist_ok=True)

#Separa 600 cards de cada cor para as pastas
cards_amount = 600
files = os.listdir(metadata_folder)
for f in files:
    card_id= f.split('.')[0]
    card_json_file = os.path.join(metadata_folder, f)     
    with open(card_json_file, mode='r', encoding='utf-8') as card_info:
        card_json_info = json.loads(card_info.read())
        colors = card_json_info['colors']
    if len(colors) == 1:
        color = colors[0]
        if color_count[color] < cards_amount:
            img_scr = os.path.join(img_folder, card_id+'.jpg')
            img_dst = os.path.join(destination_folder, color)
            img_dst = os.path.join(img_dst, card_id+'.jpg')
            shutil.copyfile(img_scr, img_dst)
            color_count[color] += 1



