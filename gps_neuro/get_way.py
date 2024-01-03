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
from math import cos, sin, radians

def file_number(i):
    if i // 10 == 0:
        num = '00' + str(i)
    elif i // 10 > 0 and i < 100:
        num = '0' + str(i)
    elif i // 100 >= 0:
        num = str(i)
    return(num)

def calculate_distance(lat1, lon1, lat2, lon2):
    # Радиус Земли в метрах
    earth_radius = 6371000

    # Конвертируем координаты из градусов в радианы
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

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
    lat_delta = (float(lat2) - float(lat1)) / num_steps
    lon_delta = (float(lon2) - float(lon1)) / num_steps

    # Создаем список для хранения координат точек
    coordinates = []

    # Вычисляем координаты для каждого шага
    for step in range(num_steps):
        # Вычисляем текущую широту и долготу
        lat = float(lat1) + (step * lat_delta)
        lon = float(lon1) + (step * lon_delta)
        # Добавляем текущие координаты в список
        coordinates.append((lat, lon))
    return coordinates
# Задаем координаты двух точек

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--num', required=False, help='Marker number')
parser.add_argument('--last', required=False)
parser.add_argument('--step', required=False)
parser.add_argument('--init', required=False)
parser.add_argument('--alldata', required=False)


args = parser.parse_args()

if args.alldata:
    def generate_circle_points(lon0, lat0, radius, num_points):
        points = []
        angle_increment = 360 / num_points

        for i in range(num_points):
            angle = radians(angle_increment * i)

        # Вычисление координат точки на окружности
            lon = lon0 + (radius * cos(angle))
            lat = lat0 + (radius * sin(angle))
            
            # Добавление координат в список точек
            points.append({'lon': lon, 'lat': lat})

        return points
    folder_name = f'map_{args.num}'
    if os.path.isdir(folder_name):
        print("Already exists")
#   exit(0)
    #os.mkdir(folder_name)
    txt_file = f'train3/map_{args.num}/map_{args.num}.txt'
    with open(txt_file, 'r') as file:
        coordinates = file.read().strip().split(';')
    file.close()

# Координаты центральной точки
    #lon0 = 50.402564
    #lat0 = 30.323875
    lon0 = round(float(coordinates[0].strip()), 6)
    lat0 = round(float(coordinates[1].strip()), 6)
    print("Coords from file ", lon0, lat0)
# Радиус окружности (в угловых секундах)
    radius = 0.005

# Количество точек на окружности
    num_points = 36

# Генерация точек на окружности
    circle_points = generate_circle_points(lon0, lat0, radius, num_points)

# Преобразование списка точек в формат JSON
    json_data = json.dumps(circle_points)

# Вывод JSON-строки
    with open('coordinates001.json', 'w') as file:
        file.write(json_data)
    file.close()
    exit(0)
    
if args.init:
    coordinates = args.init.split('-')
    (lon0,lat0) = coordinates[0].split(',')
    (lon1,lat1) = coordinates[1].split(',')
    #print(lon0,lon1)
    #exit(0)
    print("Waypoint End: ", calculate_distance(lat0, lon0, lat1, lon1), "meters...")

    print('lon0:', lon0)
    print('lat0:', lat0)
    print('lon1:', lon1)
    print('lat1:', lat1)

    # Вычисляем координаты точек на прямой с шагом 1 метр
    step_size = int(args.step)  # в метрах
    print("Step size :", step_size, " meters")
    coordinates = interpolate_coordinates(lat0, lon0, lat1, lon1, step_size)

    # Создаем список словарей с координатами
    data = [{lon: round(float(coord[0]), 6), lat: round(float(coord[1]), 6)} for coord in coordinates]

    # Сохраняем данные в файл JSON
    with open('coordinates001.json', 'w') as file:
        json.dump(json.loads(data), file)
        #file.write(data)
    file.close()
    print("Total waypoints ", len(data))
    exit(0)

if args.last:
#   CoordfileE_path = f'../train/map_{args.last}.txt'
   with open(CoordfileE_path, 'r') as file:
        coordinates = file.read().strip().split(';')
   file.close()
   
   lon1 = round(float(coordinates[0].strip()), 6)
   lat1 = round(float(coordinates[1].strip()), 6)
   print("Waypoint End: ", int(calculate_distance(lat0, lon0, lat1, lon1)), "meters...")

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

if args.last:
    simulation(coordinates)
    exit(0)

# Открыть файл JSON и прочитать его содержимое
with open('coordinates001.json', 'r') as file:
    json_data = json.loads(file.read())

i = 1
# Вывести координаты в нужном формате
for coord in tqdm(json_data):
    lon = coord['lon']
    lat = coord['lat']
    #print(f'{{"lon": {lon}, "lat": {lat}}}')
    num = file_number(i)
    lat, lng = coord["lat"], coord["lon"]
    img_file = f'train3/map_{args.num}/map_{num}.jpg'
    txt_file = f'train3/map_{args.num}/map_{num}.txt'
    
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
