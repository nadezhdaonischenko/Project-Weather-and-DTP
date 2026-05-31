# %% [markdown]
# ⚙️ Архитектура данных и автоматизация (Data Pipeline)
# 
# В данном проекте реализована гибридная схема движения данных, объединяющая ручную предобработку и полную автоматизацию через **GitHub Actions**.
# 
### 1. 📥 Первичная загрузка (Manual Ingestion)
# *   **Сбор данных:** Первичная выгрузка сырых данных ГИБДД осуществляется через текущий ноутбук (`data_loading_api.ipynb`).
# *   **Буферизация:** Данные скачиваются локально в папку `gibdd_local_archive/` для проверки корректности.
# *   **Синхронизация:** Через **GitHub Desktop** файлы фиксируются (commit) и отправляются в репозиторий.
# *   **Оптимизация хранилища:** После завершения `push` локальные файлы на компьютере можно **удалять**. Репозиторий GitHub выступает в роли постоянного облачного буфера и архива данных.
# 
# ---
# 
### 2. 🤖 Автоматизация через GitHub Actions
# 
# Процесс поддержания актуальности данных полностью автономен:
# 
# *   **`GIBDD Sync` (Раз в месяц):** 
#     Автоматически считывает новые JSON-файлы из "буфера" в репозитории и загружает их в **Supabase** для обновления дашборда.
# *   **`Daily Weather Update` (Ежедневно в 09:00 МСК):** 
#     Скрипт собирает актуальные метеоданные через API и записывает их в базу данных, обеспечивая свежую аналитику каждое утро.
# *   **`Update City Reference` (Раз в полгода):** 
#     Актуализирует геоданные и справочники городов (используя API Dadata и Geopy) без ручного вмешательства.
# 
# ---
# 
### 💡 Преимущества такой схемы:
# 1.  **Чистота системы:** Локальный диск не захламляется гигабайтами сырых данных.
# 2.  **Надежность:** GitHub хранит историю версий архива — всегда можно восстановить данные за прошлые периоды.
# 3.  **Автономность:** Интерактивный дашборд обновляется самостоятельно, используя облачные скрипты и базу данных Supabase.

# %%
yaml

# Название процесса: Обновление справочника городов
name: Update City Reference

# Триггеры запуска
on:
  schedule:
    # Запуск 1 января и 1 июля в 00:00 UTC (3:00 ночи по МСК)
    # Позволяет обновлять данные по городам дважды в год
    - cron: '0 0 1 1,7 *' 
  
  # Кнопка "Run workflow" для ручного запуска в любое время
  workflow_dispatch:      

jobs:
  # Основная задача обновления
  update:
    # Используем виртуальную машину на базе Ubuntu (Linux)
    runs-on: ubuntu-latest
    
    steps:
      # Шаг 1: Копируем (клонируем) файлы твоего репозитория на сервер GitHub
      - uses: actions/checkout@v4

      # Шаг 2: Устанавливаем Python версии 3.9
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      # Шаг 3: Установка списка библиотек для работы с данными
      # pandas (таблицы), lxml (XML/HTML), requests (API), supabase (БД), 
      # dadata (чистка адресов), geopy (координаты)
      - name: Install dependencies
        run: pip install pandas lxml requests supabase dadata geopy

      # Шаг 4: Запуск самого скрипта обновления городов
      - name: Run Update
        # Передаем "Секреты" из настроек GitHub в переменные окружения
        # Секреты DADATA нужны для работы с сервисом стандартизации адресов
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          DADATA_TOKEN: ${{ secrets.DADATA_TOKEN }}
          DADATA_SECRET: ${{ secrets.DADATA_SECRET }}
        # Команда запуска файла скрипта
        run: python update_cities.py 

# %%
import os, re, time, requests
import pandas as pd
from io import StringIO
from geopy.geocoders import Nominatim
from dadata import Dadata
from supabase import create_client

# Настройки из GitHub Secrets
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DADATA_TOKEN = os.getenv("DADATA_TOKEN")
DADATA_SECRET = os.getenv("DADATA_SECRET")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
dadata = Dadata(DADATA_TOKEN, DADATA_SECRET)
geolocator = Nominatim(user_agent="city_updater_bot", timeout=10)

def get_cities_from_wiki():
    print("Парсинг Википедии...")
    url = 'https://ru.wikipedia.org/wiki/Список_городов_России'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    all_tables = pd.read_html(StringIO(response.text))
    df = next(t for t in all_tables if len(t) > 1000)
    
    df.columns = [re.sub(r'\[.*?\]', '', str(col)).strip() for col in df.columns]
    pop_col = [c for c in df.columns if 'Население' in c][0]
    df[pop_col] = df[pop_col].astype(str).str.replace(r'\D', '', regex=True).astype(int)
    
    return df[df[pop_col] >= 100000].copy(), pop_col

def update_cities():
    df_filtered, pop_col = get_cities_from_wiki()
    print(f"Найдено {len(df_filtered)} городов > 100к.")

    for _, row in df_filtered.iterrows():
        city = re.sub(r'\[.*?\]', '', str(row['Город'])).strip()
        region = re.sub(r'\[.*?\]', '', str(row['Регион'])).strip()
        
        # 1. Сначала проверяем, есть ли город в базе
        check = supabase.table("cities_coords").select("id, okato_city").eq("name", city).execute()
        
        if check.data and check.data[0].get('okato_city'):
            continue # Город уже есть и заполнен
            
        print(f"Обработка: {city}...")
        
        # 2. Получаем координаты (Nominatim)
        lat, lon = None, None
        try:
            loc = geolocator.geocode(f"{city}, {region}, Россия")
            if loc: lat, lon = loc.latitude, loc.longitude
        except: pass
        
        # 3. Получаем ОКАТО (DaData)
        okato_city, okato_reg = None, None
        try:
            sugg = dadata.suggest("address", city, count=1, from_bound={"value":"city"}, locations=[{"region": region}])
            if sugg:
                d = sugg[0]['data']
                okato_city = d.get('okato')
                okato_reg = d.get('region_okato') or (okato_city[:2] if okato_city else None)
        except: pass

        # 4. Upsert в базу
        city_data = {
            "name": city,
            "region": region,
            "population": int(row[pop_col]),
            "latitude": lat,
            "longitude": lon,
            "okato_city": okato_city,
            "okato_region": okato_reg
        }
        supabase.table("cities_coords").upsert(city_data, on_conflict='name').execute()
        time.sleep(1.5) # Лимит Nominatim

if __name__ == "__main__":
    update_cities()

# %%
yaml

# Название всего процесса (отображается во вкладке Actions)
name: Daily Weather Update

# Триггеры (события), которые запускают этот код
on:
  schedule:
    # Автозапуск по расписанию (Cron-выражение)
    # 0 6 * * * — это 0 минут, 6 часов утра по UTC (9:00 по МСК) ежедневно
    - cron: '0 6 * * *'  
  
  # Добавляет кнопку "Run workflow" в интерфейс GitHub, чтобы запустить вручную
  workflow_dispatch:      

jobs:
  # Описание самой задачи (работы)
  update:
    # Тип виртуальной машины (выбираем свежий Linux Ubuntu)
    runs-on: ubuntu-latest
    
    steps:
      # Шаг 1: Копируем файлы из репозитория на виртуальную машину
      - name: Checkout code
        uses: actions/checkout@v3

      # Шаг 2: Устанавливаем интерпретатор Python нужной версии
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      # Шаг 3: Устанавливаем библиотеки, нужные для работы скрипта
      # requests — для API, supabase — для связи с базой данных
      - name: Install dependencies
        run: pip install requests supabase     

      # Шаг 4: Запуск самого скрипта
      - name: Run weather script
        # Прокидываем "Секреты" GitHub в переменные окружения (env)
        # Это позволяет скрипту видеть ключи базы данных, не вписывая их открытым текстом в код
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        # Команда запуска файла
        run: python weather_script.py 

# %%
import os
import requests
import time
from datetime import datetime, timedelta
from supabase import create_client

# Настройки подключения из секретов GitHub
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

target_cities = ["Омск", "Новосибирск", "Тюмень"]

weather_meanings = {
    0: "☀️ Ясно", 1: "🌤 Ясно", 2: "⛅️ Облачно", 3: "☁️ Пасмурно",
    45: "🌫 Туман", 48: "❄️ Иней", 51: "🌦 Морось", 61: "🌧 Дождь",
    63: "☔️ Дождь", 71: "🌨 Снег", 73: "❄️ Снег", 75: "🏔 Снегопад", 
    80: "⛈ Ливень", 85: "🌨 Снегопад", 95: "⚡️ Гроза"
}

def update_monthly_history():
    # Авто-определение дат: берем данные за последние 35 дней
    # (чтобы точно закрыть прошлый месяц и начало текущего без пропусков)
    end_dt = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    start_dt = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
    
    print(f"🔄 Запуск обновления истории за период: {start_dt} — {end_dt}")

    # Получаем координаты из базы
    res = supabase.table("cities_coords").select("name, latitude, longitude").in_("name", target_cities).execute()
    cities_from_db = res.data
    
    if not cities_from_db:
        print("Города не найдены в cities_coords!")
        return

    params = [
        "temperature_2m", "relative_humidity_2m", "precipitation", "weather_code", 
        "wind_speed_10m", "surface_pressure", 
        "snow_depth", "rain", "snowfall", 
        "apparent_temperature"
    ]

    for city in cities_from_db:
        name, lat, lon = city['name'], city['latitude'], city['longitude']
        print(f"\nОбработка: {name}")
        
        for start_dt, end_dt in intervals:
                # Жестко форматируем координаты (убираем возможные пробелы и запятые)
                clean_lat = str(lat).replace(',', '.')
                clean_lon = str(lon).replace(',', '.')
                
                print(f" {start_dt} — {end_dt}", end=" ", flush=True)
        
                api_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={clean_lat}&longitude={clean_lon}&start_date={start_dt}&end_date={end_dt}&hourly={','.join(params)}&timezone=auto"
        
                try:
                    response = requests.get(api_url, timeout=120)
                    r = response.json()
                    
                    # Если API ругается
                    if "error" in r:
                        print(f"Ошибка API: {r.get('reason')}")
                        print(f"Ссылка для проверки: {api_url}")
                        continue

                    h = r.get('hourly', {})
                    if not h or 'time' not in h:
                        print(f"Пропуск. Ответ сервера: {r}")
                        continue
   
                    total = len(h['time'])
                    batch = []
                    
                    for i in range(total):
                        w_code = h['weather_code'][i]
                        # Подставляем иконку и текст
                        description = weather_meanings.get(w_code, f"Код {w_code}")
                        
                        batch.append({
                            "city": name, 
                            "timestamp": h['time'][i], 
                            "temp": h['temperature_2m'][i],
                            "humidity": h['relative_humidity_2m'][i], 
                            "precipitation": h['precipitation'][i],
                            "weather_code": w_code,
                            "weather_description": weather_meanings.get(w_code, f"Код {w_code}"),
                            "wind_speed": h['wind_speed_10m'][i], 
                            "pressure": h['surface_pressure'][i], 
                            "snow_depth": h['snow_depth'][i], 
                            "rain": h['rain'][i], 
                            "snowfall": h['snowfall'][i],
                            "apparent_temp": h['apparent_temperature'][i]
                        })

                    if batch:
                        supabase.table("weather_history_3_cities").upsert(batch, on_conflict='city,timestamp').execute()
                        print(f"({len(batch)} ч.)")
                    
                    time.sleep(1.5)
                    
                except Exception as e:
                    print(f"Ошибка: {e}. Жду 10 сек...")
                    time.sleep(10)

if __name__ == "__main__":
    update_monthly_history()

# %%
yaml

# Название процесса: Синхронизация данных ГИБДД
name: GIBDD Sync

# Триггеры запуска
on:
  schedule:
    # Запуск 1-го числа каждого месяца в 00:00 UTC (3:00 ночи по МСК)
    - cron: '0 0 1 * *' 
  
  # Кнопка для ручного запуска процесса в любой момент
  workflow_dispatch:      

jobs:
  # Основная задача по синхронизации данных
  sync_data:
    # Используем свежую версию виртуальной машины Ubuntu
    runs-on: ubuntu-latest
    
    # Разрешаем GitHub-боту записывать файлы в репозиторий
    permissions:
      contents: write

    steps:
    # Шаг 1: Копируем файлы репозитория на сервер GitHub
    - name: Checkout code
      uses: actions/checkout@v4

    # Шаг 2: Устанавливаем Python 3.9
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.9'

    # Шаг 3: Установка библиотек для работы с API и базой данных
    - name: Install dependencies
      run: |
        pip install requests supabase

    # Шаг 4: Скачивание свежих данных с официального сайта/API ГИБДД
    # Скрипт download.py сохраняет их во временную папку
    - name: Download new data from GIBDD
      env:
        SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
      run: python download.py

    # Шаг 5: Отправка скачанных данных в облачную базу Supabase
    - name: Upload data to Supabase
      env:
        SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
      run: python upload.py

    # Шаг 6: Сохранение скачанных JSON-файлов в историю репозитория
    # Это создает "локальный архив", который всегда под рукой на GitHub
    - name: Commit and Push new JSON files
      run: |
        # Настраиваем имя бота, который будет делать запись
        git config --global user.name 'github-actions[bot]'
        git config --global user.email 'github-actions[bot]@users.noreply.github.com'
        
        # Добавляем новую папку с JSON в очередь на сохранение
        git add gibdd_local_archive/
        
        # Делаем коммит с текущей датой. 
        # Если новых файлов нет (изменений 0), скрипт просто напишет "No changes" и пойдет дальше
        git commit -m "Auto-update GIBDD archive: $(date +'%Y-%m-%d')" || echo "No changes to commit"
        
        # Финальный "пуш" (отправка) изменений обратно в ветку на GitHub
        git push

# %%
import os, json, time
from datetime import datetime
from supabase import create_client

# --- НАСТРОЙКИ (БЕРУТСЯ ИЗ SECRETS ГИТХАБА) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BASE_DIR = "gibdd_local_archive"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Ошибка: Ключи Supabase не найдены в переменных окружения!")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_to_local():
    # Создаем папку сразу при старте скрипта
    os.makedirs(BASE_DIR, exist_ok=True) 
    print(f"ЗАПУСК СИНХРОНИЗАЦИИ...")
    # ... остальной код

def fix_date(d):
    if not d: return None
    try: return datetime.strptime(d, "%d.%m.%Y").strftime("%Y-%m-%d")
    except: return d

def safe_float(val):
    """Очистка координат от точек, запятых и мусора"""
    if not val or str(val).strip() in [".", "", "null", "None"]:
        return None
    try:
        return float(str(val).replace(',', '.'))
    except ValueError:
        return None

def upload_final():
    print("ЗАПУСК ЗАГРУЗКИ В SUPABASE...")
    
    # Получаем актуальный справочник городов из базы
    city_res = supabase.table("cities_coords").select("id, name").execute()
    city_map = {c['name']: c['id'] for c in city_res.data}

    if not os.path.exists(BASE_DIR):
        print("Папка архива не найдена. Нечего загружать.")
        return

    for city_name in os.listdir(BASE_DIR):
        city_id = city_map.get(city_name)
        if not city_id: continue

        city_path = os.path.join(BASE_DIR, city_name)
        for year in sorted(os.listdir(city_path)):
            year_path = os.path.join(city_path, year)
            if not os.path.isdir(year_path): continue
            
            for file_name in sorted(os.listdir(year_path)):
                if not file_name.endswith(".json"): continue
                
                with open(os.path.join(year_path, file_name), 'r', encoding='utf-8') as f:
                    try: 
                        data_list = json.load(f)
                    except: 
                        continue

                if not data_list: continue
                rows = []

                for card in data_list:
                    info = card.get('infoDtp', {})
                    kart_id = card.get('KartId')
                    
                    base = {
                        "kart_id": kart_id,
                        "dtp_date": fix_date(card.get('date')),
                        "dtp_time": card.get('Time'),
                        "district": card.get('District'),
                        "dtp_type": card.get('DTP_V'),
                        "pog_total": int(card.get('POG', 0)),
                        "ran_total": int(card.get('RAN', 0)),
                        "vehicles_count": int(card.get('K_TS', 0)),
                        "participants_count": int(card.get('K_UCH', 0)),
                        "city_name": info.get('n_p'),
                        "address_street": info.get('street'),
                        "address_house": info.get('house'),
                        "road_category": info.get('dor_z'),
                        "weather": info.get('s_pog')[0] if isinstance(info.get('s_pog'), list) and info.get('s_pog') else None,
                        "road_condition": info.get('s_pch'),
                        "light_condition": info.get('osv'),
                        "latitude": safe_float(info.get('COORD_W')),
                        "longitude": safe_float(info.get('COORD_L')),
                        "road_faults": info.get('ndu'),
                        "city_id": city_id
                    }

                    # Обработка ТС и участников
                    ts_info = info.get('ts_info', [])
                    for v in ts_info:
                        v_data = {
                            "v_id": v.get('n_ts'),
                            "v_type": v.get('t_ts'),
                            "v_marka": v.get('marka_ts'),
                            "v_model": v.get('m_ts'),
                            "v_color": v.get('color'),
                            "v_year": int(v['g_v']) if str(v.get('g_v', '')).isdigit() else None,
                            "v_ownership": v.get('f_sob')
                        }
                        
                        ts_uch = v.get('ts_uch', [])
                        for p in ts_uch:
                            p_data = {
                                "p_role": p.get('K_UCH'),
                                "p_gender": p.get('POL'),
                                "p_experience": int(p['V_ST']) if str(p.get('V_ST', '')).isdigit() else None,
                                "p_severity": p.get('S_T'),
                                "p_alcohol": p.get('ALCO'),
                                "p_safety_belt": p.get('SAFETY_BELT'),
                                "p_violations": p.get('NPDD'),
                                "p_additional_violations": p.get('SOP_NPDD')
                            }
                            rows.append({**base, **v_data, **p_data})

                if rows:
                    # Очистка дубликатов внутри одной транзакции (чтобы не было ошибки 21000)
                    unique_rows = []
                    seen_keys = set()
                    for r in rows:
                        key = (r['kart_id'], r['v_id'], r['p_role'], r['p_gender'], r['p_experience'])
                        if key not in seen_keys:
                            unique_rows.append(r)
                            seen_keys.add(key)
                    
                    # Загрузка пачками по 200 строк
                    for i in range(0, len(unique_rows), 200):
                        batch = unique_rows[i:i+200]
                        try:
                            supabase.table("gibdd_accidents_history_3_cities").upsert(
                                batch, 
                                on_conflict="kart_id, v_id, p_role, p_gender, p_experience"
                            ).execute()
                        except Exception as e:
                            print(f"Ошибка пакета в {file_name}: {e}")
                
                print(f"{city_name} {year}/{file_name}: {len(rows)} строк обработано")

if __name__ == "__main__":
    upload_final()

# %%
import os
import json
import time
from datetime import datetime
from supabase import create_client, Client

# --- НАСТРОЙКИ (БЕРУТСЯ ИЗ SECRETS ГИТХАБА) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BASE_DIR = "gibdd_local_archive"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Ошибка: Переменные окружения SUPABASE_URL или SUPABASE_KEY не найдены!")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fix_date(d):
    if not d: return None
    try: return datetime.strptime(d, "%d.%m.%Y").strftime("%Y-%m-%d")
    except: return d
        
def safe_float(val):
    if not val or str(val).strip() in [".", "", "null", "None"]:
        return None
    try:
        return float(str(val).replace(',', '.'))
    except ValueError:
        return None
        
def upload_final_with_dedup():
    print("ЗАПУСК ПАРСИНГА...")
    
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)
        print(f"Папка {BASE_DIR} была пуста и создана заново.")

    # Подгружаем ID городов
    try:
        city_res = supabase.table("cities_coords").select("id, name").execute()
        city_map = {c['name']: c['id'] for c in city_res.data}
    except Exception as e:
        print(f"Ошибка при получении справочника городов: {e}")
        return

    for city_name in os.listdir(BASE_DIR):
        city_id = city_map.get(city_name)
        if not city_id: continue

        city_path = os.path.join(BASE_DIR, city_name)
        for year in sorted(os.listdir(city_path)):
            year_path = os.path.join(city_path, year)
            if not os.path.isdir(year_path): continue
            
            for file_name in sorted(os.listdir(year_path)):
                if not file_name.endswith(".json"): continue
                
                with open(os.path.join(year_path, file_name), 'r', encoding='utf-8') as f:
                    try: 
                        data_list = json.load(f)
                    except: 
                        continue

                if not data_list: continue
                rows = []
                for card in data_list:
                    info = card.get('infoDtp', {})
                    kart_id = card.get('KartId')
                    
                    base = {
                        "kart_id": kart_id,
                        "dtp_date": fix_date(card.get('date')),
                        "dtp_time": card.get('Time'),
                        "district": card.get('District'),
                        "dtp_type": card.get('DTP_V'),
                        "pog_total": int(card.get('POG', 0)),
                        "ran_total": int(card.get('RAN', 0)),
                        "vehicles_count": int(card.get('K_TS', 0)),
                        "participants_count": int(card.get('K_UCH', 0)),
                        "city_name": info.get('n_p'),
                        "address_street": info.get('street'),
                        "address_house": info.get('house'),
                        "road_category": info.get('dor_z'),
                        "weather": info.get('s_pog')[0] if isinstance(info.get('s_pog'), list) and info.get('s_pog') else None,
                        "road_condition": info.get('s_pch'),
                        "light_condition": info.get('osv'),
                        "latitude": safe_float(info.get('COORD_W')),
                        "longitude": safe_float(info.get('COORD_L')),
                        "road_faults": info.get('ndu'),
                        "city_id": city_id
                    }

                    ts_info = info.get('ts_info', [])
                    for v in ts_info:
                        v_data = {
                            "v_id": v.get('n_ts'),
                            "v_type": v.get('t_ts'),
                            "v_marka": v.get('marka_ts'),
                            "v_model": v.get('m_ts'),
                            "v_color": v.get('color'),
                            "v_year": int(v['g_v']) if str(v.get('g_v', '')).isdigit() else None,
                            "v_ownership": v.get('f_sob')
                        }
                        
                        ts_uch = v.get('ts_uch', [])
                        for p in ts_uch:
                            p_data = {
                                "p_role": p.get('K_UCH'),
                                "p_gender": p.get('POL'),
                                "p_experience": int(p['V_ST']) if str(p.get('V_ST', '')).isdigit() else None,
                                "p_severity": p.get('S_T'),
                                "p_alcohol": p.get('ALCO'),
                                "p_safety_belt": p.get('SAFETY_BELT'),
                                "p_violations": p.get('NPDD'),
                                "p_additional_violations": p.get('SOP_NPDD')
                            }
                            rows.append({**base, **v_data, **p_data})

                if rows:
                    unique_rows = []
                    seen_keys = set()
                    for r in rows:
                        key = (r['kart_id'], r['v_id'], r['p_role'], r['p_gender'], r['p_experience'])
                        if key not in seen_keys:
                            unique_rows.append(r)
                            seen_keys.add(key)
                    
                    batch_size = 300
                    for i in range(0, len(unique_rows), batch_size):
                        batch = unique_rows[i:i+batch_size]
                        try:
                            supabase.table("gibdd_accidents_history_3_cities").upsert(
                                batch, 
                                on_conflict="kart_id, v_id, p_role, p_gender, p_experience"
                            ).execute()
                        except Exception as e:
                            print(f"Ошибка пакета {city_name} {year}/{file_name}: {e}")
                
                print(f"{city_name} {year}/{file_name}: {len(rows)} строк")

if __name__ == "__main__":
    upload_final_with_dedup()


