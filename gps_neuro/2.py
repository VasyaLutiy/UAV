import os

dir = 'train3/45class'
for root, dirs, files in os.walk(dir):
    for name in files:
        filepath = root + os.sep + name
        print(filepath)
