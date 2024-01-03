import os
import shutil

# Путь к папке с изображениями
image_folder = 'train'

# Создаем подпапки для каждого изображения
for filename in os.listdir(image_folder):
    if filename.endswith('.jpg'):
        # Получаем имя изображения без расширения
        image_name = os.path.splitext(filename)[0]
        
        # Создаем папку на основе имени изображения
        folder_path = os.path.join(image_folder, image_name)
        os.makedirs(folder_path, exist_ok=True)
        
        # Перемещаем файл в соответствующую папку
        source_path = os.path.join(image_folder, filename)
        destination_path = os.path.join(folder_path, filename)
        shutil.move(source_path, destination_path)
