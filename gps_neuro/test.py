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
from tensorflow.keras.preprocessing import image
import random

# Путь к изображению, которое вы хотите классифицировать
image_path = ['train2/map_003/map_001.jpg']
# Define the path to your training data
train_data_dir = 'train2'

# Define the image size
img_width, img_height = 224, 224

# Function to preprocess the images
def preprocess_images(img):
    img = img.astype('float32')
    img /= 255.0
    return img

# Define the data generators for training and validation
train_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_images,
    validation_split=0.2  # Split the data into 80% training and 20% validation
)

train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_width, img_height),
    batch_size=32,
    class_mode='categorical',
    shuffle=True,
    subset='training'  # Use the training subset of the data
)

validation_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_width, img_height),
    batch_size=32,
    class_mode='categorical',
    shuffle=False,
    subset='validation'  # Use the validation subset of the data
)

#random 
#values_list = list(train_generator.class_indices.values())
values_list = list(range(1, 12))
keys_list = list(train_generator.class_indices.keys())
random_keys = random.choices(keys_list, k=10)

for i in random_keys:
    random_values = random.choices(values_list, k=1)
    if random_values[0] == 0:
        num = '001'
    if random_values[0] // 10 == 0:
        num = '00' + str(random_values[0])
    elif random_values[0] // 10 > 0 and random_values[0] < 100:
        num = '0' + str(random_values[0])
    elif random_values[0] // 100 >= 0:
        num = str(random_values[0])
        
    ii = f'train2/{i}/map_{num}.jpg'
# Загрузка изображения и преобразование его к размеру, соответствующему обучающим данным
    img = image.load_img(ii, target_size=(img_width, img_height))
    img = image.img_to_array(img)
    img = preprocess_images(img)
    img = np.expand_dims(img, axis=0)

    loaded_model = keras.models.load_model('44_class_InceptionV3_x_final_model.h5')
#loaded_model.summary()
    InceptionV3_x_final_model = loaded_model
# Применение модели к изображению
    predictions = InceptionV3_x_final_model.predict(img, verbose=0)

# Получение класса с наибольшей вероятностью
    predicted_class = np.argmax(predictions[0])
    class_name = list(train_generator.class_indices.keys())[predicted_class]
    with open(f'train2/{class_name}/map_001.txt', 'r') as f:
        output = f.read()
    print(ii, f"pred gps |{class_name}:  {output}")
