#!/usr/bin/env python3
import keyboard
import pyperclip
import requests
import io
import random
import urllib.parse
import json
import time
import os
import platform
from bs4 import BeautifulSoup
from PIL import Image

# Определяем операционную систему для работы с буфером обмена
system = platform.system()
if system == "Windows":
    import win32clipboard
    from io import BytesIO
elif system == "Darwin":
    import subprocess
else:
    import subprocess

def set_clipboard_image(image):
    """
    Копирует изображение в буфер обмена, поддерживая Windows, macOS и Linux.
    """
    if system == "Windows":
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # пропускаем заголовок BMP
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
    elif system == "Darwin":
        temp_file = "temp_image.png"
        image.save(temp_file)
        subprocess.run(['osascript', '-e',
                        'set the clipboard to (read (POSIX file "' + os.path.abspath(temp_file) + '") as TIFF picture)'],
                       check=True)
        os.remove(temp_file)
    else:  # Linux
        temp_file = "temp_image.png"
        image.save(temp_file)
        subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', temp_file], check=True)
        os.remove(temp_file)

def get_random_user_agent():
    """
    Возвращает случайный user-agent.
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'
    ]
    return random.choice(user_agents)

def search_pixabay_api(query):
    """
    Поиск изображений через Pixabay API.
    Требует наличия API-ключа.
    """
    API_KEY = ""  # Замените на ваш ключ Pixabay
    encoded_query = urllib.parse.quote(query)
    url = f"https://pixabay.com/api/?key={API_KEY}&q={encoded_query}&image_type=photo&min_width=512&min_height=512"
    try:
        print("Поиск через Pixabay API...")
        response = requests.get(url, timeout=10)
        data = response.json()
        hits = data.get("hits", [])
        image_urls = [hit["largeImageURL"] for hit in hits if "largeImageURL" in hit]
        print(f"Pixabay API: найдено {len(image_urls)} изображений")
        return image_urls
    except Exception as e:
        print(f"Ошибка в Pixabay API: {e}")
        return []

def search_unsplash_api(query):
    """
    Поиск изображений через Unsplash API.
    Требует наличия API-ключа.
    """
    ACCESS_KEY = ""  # Замените на ваш ключ Unsplash
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.unsplash.com/search/photos?query={encoded_query}&per_page=10&orientation=landscape"
    headers = {"Authorization": f"Client-ID {ACCESS_KEY}"}
    try:
        print("Поиск через Unsplash API...")
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        results = data.get("results", [])
        image_urls = [result["urls"]["full"] for result in results if "urls" in result and "full" in result["urls"]]
        print(f"Unsplash API: найдено {len(image_urls)} изображений")
        return image_urls
    except Exception as e:
        print(f"Ошибка в Unsplash API: {e}")
        return []

def search_bing_images(query):
    """
    Поиск изображений через Bing Images.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.bing.com/images/search?q={encoded_query}&qft=+filterui:imagesize-large"
    headers = {"User-Agent": get_random_user_agent()}
    try:
        print("Поиск через Bing Images...")
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        image_urls = []
        for a in soup.find_all("a", href=True):
            if "/images/search?" in a["href"] and "mediaurl=" in a["href"]:
                media_url = a["href"].split("mediaurl=")[1].split("&")[0]
                decoded_url = urllib.parse.unquote(media_url)
                if decoded_url.startswith("http") and not decoded_url.endswith((".svg", ".gif")):
                    image_urls.append(decoded_url)
        print(f"Bing Images: найдено {len(image_urls)} изображений")
        return image_urls
    except Exception as e:
        print(f"Ошибка в Bing Images: {e}")
        return []

def search_image(query):
    """
    Ищет изображение, используя несколько провайдеров.
    Порядок: Pixabay API, Unsplash API, Bing Images (резервный вариант).
    """
    providers = [search_pixabay_api, search_unsplash_api, search_bing_images]
    random.shuffle(providers)
    all_urls = []
    for provider in providers:
        urls = provider(query)
        if urls:
            all_urls.extend(urls)
            if len(all_urls) >= 5:
                break
    if all_urls:
        random.shuffle(all_urls)
        selected_url = random.choice(all_urls)
        print(f"Выбрано изображение из {len(all_urls)} найденных")
        return selected_url
    else:
        print("Изображение не найдено у всех провайдеров.")
        return None

def download_image(url):
    """
    Загружает изображение по указанному URL и проверяет его размер.
    Если изображение меньше 512x512, увеличивает его до минимальных размеров.
    """
    try:
        headers = {"User-Agent": get_random_user_agent()}
        response = requests.get(url, headers=headers, timeout=10)
        image = Image.open(io.BytesIO(response.content))
        width, height = image.size
        print(f"Размер загруженного изображения: {width}x{height} пикселей")
        if width < 512 or height < 512:
            ratio = max(512 / width, 512 / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            print(f"Увеличиваем изображение до {new_width}x{new_height}")
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image
    except Exception as e:
        print(f"Ошибка при загрузке изображения: {e}")
        return None

def on_hotkey():
    """
    Обработчик горячей клавиши.
    Берёт запрос из буфера обмена, ищет изображение и копирует его в буфер обмена.
    """
    try:
        query = pyperclip.paste().strip()
        if not query:
            print("Буфер обмена пуст. Нечего искать.")
            return
        print(f"Ищем изображение по запросу: {query}")
        search_modifiers = [" high resolution", " large size", " high quality", " HD", " 4K", ""]
        modifier = random.choice(search_modifiers)
        enhanced_query = query + modifier
        print(f"Используем запрос: {enhanced_query}")
        image_url = search_image(enhanced_query)
        if image_url:
            print(f"Найдено изображение: {image_url}")
            image = download_image(image_url)
            if image:
                width, height = image.size
                print(f"Итоговый размер изображения: {width}x{height}")
                set_clipboard_image(image)
                print("Изображение скопировано в буфер обмена!")
            else:
                print("Не удалось загрузить изображение.")
        else:
            print("Изображение не найдено.")
    except Exception as e:
        print(f"Ошибка в обработчике горячих клавиш: {e}")

def main():
    print("Программа поиска изображений запущена!")
    print("Скопируйте запрос в буфер обмена и нажмите Ctrl+Delete для поиска.")
    keyboard.add_hotkey("ctrl+delete", on_hotkey)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Программа завершена пользователем.")

if __name__ == "__main__":
    main()
