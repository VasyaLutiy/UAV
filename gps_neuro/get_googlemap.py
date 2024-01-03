import urllib.request
import time
import random

def generate_random_number(range_min, range_max):
    return random.uniform(range_min, range_max)

long = 50.401135
lat = 30.230288

sim = [-0.001, 0.001, -0.0005, 0.0005]

for i in range(0, 40):
    if i // 10 == 0:
        num = '00' + str(i)
    elif i // 10 > 0:
        num = '0' + str(i)
    print(num)
#    long = long + generate_random_number(-0.001, 0.001)
#    long = long + 0.001
#    lat = lat + sim[int(generate_random_number(0, 3))]
    lat = lat + 0.0001
    img_file = f'map6/map_{num}.jpg'
    txt_file = f'map/map_{num}.txt'
    img_mark = str(long) + ";" + str(lat)
    df=open(txt_file,'w')
    url = f'https://maps.googleapis.com/maps/api/staticmap?scale=4&center={long},{lat}&zoom=16&size=1920x1080&maptype=satellite&format=jpg&key=AIzaSyAFXbCT7IyNFK1OcbiPQ4h>
    urllib.request.urlretrieve(url, img_file)
    df.write(img_mark)
    df.close()
print("Last coords ", long, lat)
