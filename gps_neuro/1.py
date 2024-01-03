import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.layers import Dense, Flatten, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

num_classes = 44
loaded_model = keras.models.load_model(f'{num_classes}_class_InceptionV3_x_final_model.h5')
#loaded_model.summary()
model = loaded_model

def NMEA_0183_gps(json_data):
# Загрузка данных из JSON
    data = json.loads(json_data)
    #print(data)
# Функция для преобразования долготы/широты в формат NMEA
    def decimal_degrees_to_nmea(degrees):
        degrees_int = int(degrees)
        minutes_decimal = (degrees - degrees_int) * 60
        minutes_int = int(minutes_decimal)
        seconds_decimal = (minutes_decimal - minutes_int) * 60
        return "{:02d}{:02d}.{:04d}".format(degrees_int, minutes_int, int(seconds_decimal * 10000))
# Извлечение данных из JSON
    latitude = data['latitude']
    longitude = data['longitude']
    altitude = data['altitude']
    speed = data['speed']
    timestamp = data['timestamp']
# Преобразование координат в формат NMEA
    latitude_nmea = decimal_degrees_to_nmea(latitude)
    longitude_nmea = decimal_degrees_to_nmea(longitude)
# Формирование строк NMEA
    gga_sentence = "$GPGGA,{},{},{},N,{},E,1,08,0.9,{} M,46.9,M,,,".format(timestamp, latitude_nmea, longitude_nmea, altitude, speed)
    vtg_sentence = "$GPVTG,{}T,0.0,{}N,0.0,{}K,A".format(timestamp, speed, speed)

# Вывод строк NMEA
    return(gga_sentence,vtg_sentence)

from tensorflow.keras.preprocessing import image
import random
import json
import datetime

img_width = 224
img_height = 224

num_classes = 44

with open(f'{num_classes}_class_Names_.json', 'r') as openfile:
    # Reading from json file
    keys_list = json.load(openfile)
#keys_list
def preprocess_images(img):
    img = img.astype('float32')
    img /= 255.01
    return img
for i in range(0,14):      
    ii = f'simulation/map_{i}.jpg'
# Загрузка изображения и преобразование его к размеру, соответствующему обучающим данным
    img = image.load_img(ii, target_size=(img_width, img_height))
    img = image.img_to_array(img)
    img = preprocess_images(img)
    img = np.expand_dims(img, axis=0)

# Применение модели к изображению
    predictions = model.predict(img, verbose=0)
    # Получение класса с наибольшей вероятностью
    predicted_class = np.argmax(predictions[0])
    class_name = keys_list[predicted_class]
    with open(f'train2/{class_name}/map_006.txt', 'r') as file:
        line = file.readline().strip()  # Считываем первую строку из файла и удаляем пробельные символы
    output = line
    
    # Разделение строки на значения lon и lat
    lon, lat = line.split(';')
    lon = float(lon)
    lat = float(lat)
    print(ii, f"pred gps : {keys_list[predicted_class]} : {output}")
    # Получение текущего времени
    current_timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
# Формирование словаря данных
    data = {
        "latitude": lat,
        "longitude": lon,
        "altitude": 100.0,
        "speed": 60.5,
        "timestamp": current_timestamp
    }
# Преобразование словаря в JSON-строку
    json_data = json.dumps(data)
    (gga_sentence,vtg_sentence) = NMEA_0183_gps(json_data)

    #print(gga_sentence)
    #print(vtg_sentence)
    ## добавить GPRMC
    ## $GNRMC,204520.00,A,5109.0262239,N,11401.8407338,W,0.004,102.3,130522,0.0,E,D*3B


