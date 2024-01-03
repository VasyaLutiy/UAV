import os
import csv
import json
import math
import argparse

import urllib.parse
import urllib.request

import time
import random
from tqdm import tqdm

def calculate_distance(lat1, lon1, lat2, lon2):
    # Радиус Земли в метрах
    earth_radius = 6371000

    # Конвертируем координаты из градусов в радианы
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Вычисляем разницу между долготами и широтами
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Вычисляем расстояние между точками по формуле Гаверсинуса
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c

    return distance

def interpolate_coordinates(lon1, lat1, lon2, lat2, step_size):
    # Вычисляем расстояние между двумя точками
    total_distance = calculate_distance(lat1, lon1, lat2, lon2)

    # Вычисляем количество шагов
    num_steps = int(total_distance / step_size)

    # Проверяем, если количество шагов равно нулю, возвращаем пустой список
    if num_steps == 0:
        return []

    # Вычисляем дельту для широты и долготы
    lat_delta = (lat2 - lat1) / num_steps
    lon_delta = (lon2 - lon1) / num_steps

    # Создаем список для хранения координат точек
    coordinates = []

    # Вычисляем координаты для каждого шага
    for step in range(num_steps):
        # Вычисляем текущую широту и долготу
        lat = lat1 + (step * lat_delta)
        lon = lon1 + (step * lon_delta)
        # Добавляем текущие координаты в список
        coordinates.append((lat, lon))
    return coordinates
# Задаем координаты двух точек

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--num',
                    help='Marker number')

parser.add_argument('--last', required=False)
parser.add_argument('--step', required=False)

args = parser.parse_args()
print(args.num, args.last)

folder_name = f'map_{args.num}'
if os.path.isdir(folder_name):
   print("Already exists")
#   exit(0)
#os.mkdir(folder_name)

Coordfile0_path = f'../train/map_{args.num}.txt'
with open(Coordfile0_path, 'r') as file:
    coordinates = file.read().strip().split(';')
file.close()

lon0 = round(float(coordinates[0].strip()), 6)
lat0 = round(float(coordinates[1].strip()), 6)

#######
lon0 = round(float(lon0 + 0.0008), 6)
#######
lat1 = round(float(lat0 + 0.0002), 6)

if args.last:
   CoordfileE_path = f'../train/map_{args.last}.txt'
   with open(CoordfileE_path, 'r') as file:
        coordinates = file.read().strip().split(';')
   file.close()
   
   lon1 = round(float(coordinates[0].strip()), 6)
   lat1 = round(float(coordinates[1].strip()), 6)
   print("Waypoint End: ", int(calculate_distance(lat0, lon0, lat1, lon1)), "meters...")

print('lon0:', lon0)
print('lat0:', lat0)
print('lon1:', lon1)
print('lat1:', lat1)

# Вычисляем координаты точек на прямой с шагом 1 метр
step_size = int(args.step)  # в метрах
print("Step size :", step_size, " meters")
coordinates = interpolate_coordinates(lat0, lon0, lat1, lon1, step_size)

# Создаем список словарей с координатами
data = [{'lon': round(float(coord[0]), 6), 'lat': round(float(coord[1]), 6)} for coord in coordinates]

# Сохраняем данные в файл JSON
with open('coordinates001.json', 'w') as file:
    json.dump(data, file)
file.close()
#print(len(data))

def simulation(list_coordinates):
    num = 0
    for coord in tqdm(coordinates):
        lat, lng = coord["lat"], coord["lon"]
        img_file = f'../simulation/map_{num}.jpg'
        txt_file = f'../simulation/map_{num}.txt'
        print(img_file)
        num = num + 1
        img_mark = str(lng) + ";" + str(lat)
# Входные параметры GET запроса
        params = {
            'scale': '4',
            'center': f'{lng},{lat}',
            'zoom': '17',
            'size': '1280x1280',
            'maptype': 'satellite',
            'format': 'jpg',
            'key': 'AIzaSyAFXbCT7IyNFK1OcbiPQ4hJpk7E7ooVtyk'
        }
# Формирование URL с параметрами
        url = 'https://maps.googleapis.com/maps/api/staticmap?' + urllib.parse.urlencode(params)
# Скачивание изображения
        urllib.request.urlretrieve(url, img_file)

        df=open(txt_file,'w')
        df.write(img_mark)
        df.close()

        
def generate_random_number(range_min, range_max):
    return random.uniform(range_min, range_max)

with open('coordinates001.json', 'r') as f:
    coordinates = json.load(f)
f.close()
i = 1
if args.last:
    simulation(coordinates)
    exit(0)

for coord in tqdm(coordinates):
    if i // 10 == 0:
        num = '00' + str(i)
    elif i // 10 > 0 and i < 100:
        num = '0' + str(i)
    elif i // 100 >= 0:
        num = str(i)
    lat, lng = coord["lat"], coord["lon"]
    img_file = f'map_{args.num}/map_{num}.jpg'
    txt_file = f'map_{args.num}/map_{num}.txt'
    
    img_mark = str(lng) + ";" + str(lat)
    params = {
       'scale': '4',
       'center': f'{lng},{lat}',
       'zoom': '17',
       'size': '1280x1280',
       'maptype': 'satellite',
       'format': 'jpg',
       'key': 'AIzaSyAFXbCT7IyNFK1OcbiPQ4hJpk7E7ooVtyk'
    }
# Формирование URL с параметрами
    url = 'https://maps.googleapis.com/maps/api/staticmap?' + urllib.parse.urlencode(params)
    urllib.request.urlretrieve(url, img_file)
    
    df=open(txt_file,'w')
    df.write(img_mark)
    df.close()
    i = i + 1
print("Last coords ", lng, lat)

