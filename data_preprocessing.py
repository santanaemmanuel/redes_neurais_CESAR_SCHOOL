import os
import shutil
import re
import json


def label_encoder(card_colors):
    color_map = {
        'W':0,
        'U':1,
        'B':2,
        'R':3,
        'G':4
    }
    color_encode = [0, 0, 0, 0, 0]
    for color in card_colors:
        idx = color_map[color]
        color_encode[idx] = 1
    return color_encode

color_count = {
    'W':0,
    'U':0,
    'B':0,
    'R':0,
    'G':0
}

img_folder = r'dataset\raw_dataset\imgs'
metadata_folder = r'dataset\raw_dataset\metadata'
destination_folder = r'dataset\mtg_cards\all'

files = os.listdir(metadata_folder)
for f in files:
    card_id= f.split('.')[0]
    card_json_file = os.path.join(metadata_folder, f)     
    with open(card_json_file, mode='r', encoding='utf-8') as card_info:
        card_json_info = json.loads(card_info.read())
        colors = card_json_info['colors']
    if len(colors) == 1:
        color = colors[0]
        if color_count[color] < 600:
            img_scr = os.path.join(img_folder, card_id+'.jpg')
            img_dst = os.path.join(destination_folder, color)
            img_dst = os.path.join(img_dst, card_id+'.jpg')
            shutil.copyfile(img_scr, img_dst)
            color_count[color] += 1

