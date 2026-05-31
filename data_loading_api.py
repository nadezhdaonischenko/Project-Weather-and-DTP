# %%
import pandas as pd
import requests
import re
import time
from io import StringIO
from geopy.geocoders import Nominatim
from supabase import create_client
import os
import json
from dadata import Dadata
from supabase import create_client, Client
from datetime import datetime

# %%
# --- 1. НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ---

SUPABASE_URL = "https://amr***"
SUPABASE_KEY = "eyJ***"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# %%
# --- 2. ПАРСИНГ СПИСКА ГОРОДОВ ---
url = 'https://ru.wikipedia.org/wiki/Список_городов_России'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

# %%
def main():
    try:
        response = requests.get(url, headers=headers)
        all_tables = pd.read_html(StringIO(response.text))
        df = next(t for t in all_tables if len(t) > 1000)
        print(f"Загружен полный список: {len(df)} городов.")
    except Exception as e:
        print(f"Ошибка парсинга Википедии: {e}")
        return
    
    # --- 3. ЧИСТКА И ФИЛЬТРАЦИЯ ---
    # Убираем сноски из названий колонок
    df.columns = [re.sub(r'\[.*?\]', '', str(col)).strip() for col in df.columns]

    # Чистим колонку Население и переводим в числа
    pop_col = [c for c in df.columns if 'Население' in c][0]
    df[pop_col] = df[pop_col].astype(str).str.replace(r'\D', '', regex=True).replace('', '0').astype(int)

    # Оставляем только города > 100 000 человек, только большие (можно расширить при необходимости)
    df_filtered = df[df[pop_col] >= 100000].copy()
    print(f"После фильтрации осталось {len(df_filtered)} городов.")

    # --- 4. ПОЛУЧЕНИЕ КООРДИНАТ ---
    # Словарь для исправления названий регионов под требования Nominatim
    REGION_FIXES = {
        "Ханты-Мансийский автономный округ — Югра": "ХМАО",
        "Ханты-Мансийский автономный округ": "ХМАО",
        "Ямало-Ненецкий автономный округ": "ЯНАО",
        "Югра": "ХМАО"
    }

    geolocator = Nominatim(user_agent="city_mapper_v4_unique", timeout=10)
    final_batch = []

    print("Начинаю поиск координат (с исправлением регионов)...")

    for index, row in df_filtered.iterrows():
        city = re.sub(r'\[.*?\]', '', str(row['Город'])).strip()
        raw_region = re.sub(r'\[.*?\]', '', str(row['Регион'])).strip()
    
        # Применяем исправление, если регион есть в словаре
        region = REGION_FIXES.get(raw_region, raw_region)
    
        # Формируем поисковый запрос
        # Иногда для ХМАО/ЯНАО лучше работает схема: "Город, Россия" 
        query = f"{city}, {region}, Россия"
    
        success = False
        for attempt in range(3):
            try:
                location = geolocator.geocode(query)
            
                # Если не нашло с регионом, пробуем только город и страну
                if not location:
                    location = geolocator.geocode(f"{city}, Россия")
                
                if location:
                    final_batch.append({
                        "name": city,
                        "region": raw_region, # сохраняем оригинальное название для базы
                        "population": int(row[pop_col]),
                        "latitude": location.latitude,
                        "longitude": location.longitude
                    })
                    print(f"OK: {city} ({region})")
                    success = True
                    break
                else:
                    print(f"Не найдено: {query}")
                    break
                
            except Exception as e:
                print(f"Попытка {attempt+1} для {city} ошибка: {e}")
                time.sleep(2)
            
        time.sleep(1.5)

    # --- 5. ОТПРАВКА В SUPABASE ---
    # Если города есть, загружаем их мелкими порциями
    if len(final_batch) > 0:
        chunk_size = 10  # Берем по 10 городов за раз
        for i in range(0, len(final_batch), chunk_size):
            chunk = final_batch[i:i + chunk_size]
            try:
                # Отправляем порцию в Supabase, используем .upsert() во избежания дублей
                supabase.table("cities_coords").upsert(chunk, on_conflict='name').execute()
                print(f"Успешно: загружены города с {i} по {i + len(chunk)}")
                # Даем серверу передохнуть полсекунды
                time.sleep(0.5)
            except Exception as e:
                print(f"Ошибка на шаге {i}: {e}")
                print("Пробую подождать 5 секунд и отправить снова...")
                time.sleep(5)
                supabase.table("cities_coords").insert(chunk).execute()
    
        print("\n--- ВСЁ ГОТОВО! Таблица в Supabase заполнена! ---")
    else:
        print("Ошибка: Список final_batch пуст. Придется перезапустить поиск координат.")

if __name__ == "__main__":
    main()

# %%
# ДОБАВЛЕНИЕ КОДОВ ОКАТО

# НАСТРОЙКИ
DADATA_URL = "5aa***"
DADATA_KEY = "9cc***"

# Инициализация
dadata = Dadata(DADATA_URL, DADATA_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_final():
    print(" ЗАПУСК СИНХРОНИЗАЦИИ (DaData)...")
    
    res = supabase.table("cities_coords").select("id, name, region").is_("okato_city", "null").execute()
    
    for city in res.data:
        try:
            # 1. Сначала пробуем строгий поиск в указанном регионе
            suggestions = dadata.suggest(
                "address", city['name'], count=3,
                from_bound={"value": "city"}, to_bound={"value": "settlement"},
                locations=[{"region": city['region']}]
            )
            
            # 2. Если не нашли, ищем по всей РФ
            if not suggestions:
                suggestions = dadata.suggest(
                    "address", city['name'], count=3,
                    from_bound={"value": "city"}, to_bound={"value": "settlement"}
                )

            target = None
            if suggestions:
                for s in suggestions:
                    d = s['data']
                    okato = d.get('okato')
                    # Проверяем: есть ОКАТО и это не код региона (не заканчивается на 8 нулей)
                    if okato and not okato.endswith("00000000"):
                        # Доп. проверка: если искали по всей РФ, проверим, совпадает ли регион
                        if not city['region'] or city['region'].lower()[:4] in d.get('region', '').lower():
                            target = d
                            break
                
                # Если фильтр не прошел, но что-то есть — берем первое
                if not target: target = suggestions[0]['data']

                okato_city = target.get('okato')
                okato_reg = target.get('region_okato') or (okato_city[:2] if okato_city else None)

                if okato_city:
                    supabase.table("cities_coords").update({
                        "okato_city": okato_city, "okato_region": okato_reg
                    }).eq("id", city['id']).execute()
                    print(f"{city['name']}: {okato_city}")
                else:
                    print(f"{city['name']}: Нет ОКАТО в данных")
            else:
                print(f"{city['name']}: Совсем ничего не найдено")
            
            time.sleep(0.06)

        except Exception as e:
            print(f"Ошибка {city['name']}: {e}")

if __name__ == "__main__":
    sync_final()

# %%
# ПАРСИНГ ПОГОДЫ И ЗАГРУЗКА В SUPABASE

weather_meanings = {
    0: "☀️ Ясно", 1: "🌤 Преимущественно ясно", 2: "⛅️ Переменная облачность", 
    3: "☁️ Пасмурно", 45: "🌫 Туман", 48: "❄️ Иней", 51: "🌦 Легкая морось", 53: "🌦 Умеренная морось", 55: "🌧 Плотная морось",
    56: "🌨 Ледяная слабая морось", 57: "🌨 Ледяная плотная морось", 
    61: "🌧 Небольшой дождь", 63: "☔️ Дождь", 65: "🌧 Сильный дождь", 66: "🌨 Ледяной слабый дождь", 67: "🌨 Ледяной сильный дождь",
    71: "🌨 Небольшой снег", 73: "❄️ Снег", 75: "🏔 Сильный снег", 77: "❄️ Снежные зерна", 80: "⛈ Ливень", 
    81: "🌧 Умеренный ливневый дождь", 82: "⛈ Сильный ливневый дождь", 85: "🌨 Снегопад", 86: "🌨 Сильный снежный ливень", 
    95: "⚡️ Гроза", 96: "⛈ Гроза со слабым градом", 99: "⛈ Гроза с сильным градом"
}

# НАСТРОЙКИ
target_cities = ["Омск", "Новосибирск", "Тюмень"]

def fetch_history_fixed():
    print(" Получаю координаты...", flush=True)
    res = supabase.table("cities_coords").select("name, latitude, longitude").in_("name", target_cities).execute()
    cities_from_db = res.data
    
    params = [
        "temperature_2m", "relative_humidity_2m", "precipitation", "weather_code", 
        "wind_speed_10m", "surface_pressure", 
        "snow_depth", "rain", "snowfall", 
        "apparent_temperature"
    ]

    for city in cities_from_db:
        name, lat, lon = city['name'], city['latitude'], city['longitude']
        print(f"\n ГОРОД {name.upper()}", flush=True)

        for year in range(2015, 2026):
            intervals = [
                (f"{year}-01-01", f"{year}-03-31"),
                (f"{year}-04-01", f"{year}-06-30"),
                (f"{year}-07-01", f"{year}-09-30"),
                (f"{year}-10-01", f"{year}-12-31")
            ]

            for start_dt, end_dt in intervals:
                # Жестко форматируем координаты (убираем возможные пробелы и запятые)
                clean_lat = str(lat).replace(',', '.')
                clean_lon = str(lon).replace(',', '.')
                
                print(f"{start_dt} — {end_dt}", end=" ", flush=True)
                
                # Формируем ссылку
                api_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={clean_lat}&longitude={clean_lon}&start_date={start_dt}&end_date={end_dt}&hourly={','.join(params)}&timezone=auto"
                
                try:
                    response = requests.get(api_url, timeout=120)
                    r = response.json()
                    
                    # Если API ругается
                     if "error" in r:
                        print(f" Ошибка API: {r.get('reason')}")
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
    fetch_history_fixed()
    print("\n ЗАГРУЗКА 2015-2025 ЗАВЕРШЕНА!")

# %%
# ПОЛУЧЕНИЕ ПОЛНЫХ КАРТОЧЕК ДТП С ПАГИНАЦИЕЙ

def get_dtp_cards(okato_region, okato_city, year, month, start=1, end=1000):
    url = "http://stat.gibdd.ru/map/getDTPCardData"

    payload = {
        "data": {
            "date": [f"MONTHS:{month}.{year}"],
            "ParReg": okato_region,
            "order": {"type": "1", "fieldName": "dat"},
            "reg": okato_city,
            "ind": "1",
            "st": str(start),
            "en": str(end),
            "fil": {
                "isSummary": False  # Полные данные вместо сводных
            },
            "fieldNames": [
                "dat", "time", "coordinates", "infoDtp", "k_ul", "dor", "ndu",
                "k_ts", "ts_info", "pdop", "pog", "osv", "s_pch", "s_pog",
                "n_p", "n_pg", "obst", "sdor", "t_osv", "t_p", "t_s", "v_p", "v_v"
            ]
        }
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        # Двойное кодирование JSON требуется API ГИБДД
        request_data = {
            "data": json.dumps(payload["data"], separators=(',', ':'))
        }

        response = requests.post(
            url,
            json=request_data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            response_data = json.loads(response.text)
            return json.loads(response_data["data"]).get("tab", [])
        else:
            print(f"Ошибка HTTP: {response.status_code}")
            return None

    except Exception as e:
        print(f"Ошибка при запросе данных: {str(e)}")
        return None   

# %%
# ЗАГРУЗКА ДАНННЫХ ГИБДД

# Папка, куда полетят файлы
BASE_DIR = "gibdd_local_archive"

def download_to_local():
    print("НАЧАЛО ЛОКАЛЬНОГО СКАЧИВАНИЯ (2015-2025)")
    
    target_cities = ["Омск", "Новосибирск", "Тюмень"]
    
    # 1. Получаем ID и коды из таблицы
    res = supabase.table("cities_coords").select("id, name, okato_region, okato_city").in_("name", target_cities).execute()
    
    if not res.data:
        print("Города не найдены в базе!")
        return

    for city in res.data:
        city_name = city['name']
        # Используем обрезкУ кодов
        region_id = str(city['okato_region'])
        district_id = str(city['okato_city'])[:5]  # Берем первые 5 для reg
        
        print(f"\n ГОРОД: {city_name} (Reg: {region_id}, Dist: {district_id})")

        for year in range(2015, 2026):
            # Создаем путь: gibdd_local_archive/Омск/2015/
            year_path = os.path.join(BASE_DIR, city_name, str(year))
            os.makedirs(year_path, exist_ok=True)

            for month in range(1, 13):
                file_path = os.path.join(year_path, f"{month:02d}.json")

                # Если файл уже есть и он не пустой — пропускаем
                if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
                    continue

                print(f"{month:02d}.{year}", end=" -> ", flush=True)

                # Запрос с таймаутом 60 секунд
                cards = get_dtp_cards(region_id, district_id, year, month)

                if cards is not None:
                    # Сохраняем, даже если пришел пустой список [] (чтобы не перекачивать)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(cards, f, ensure_ascii=False, indent=4)
                    print(f"{len(cards)} шт.")
                else:
                    print("Ошибка/Таймаут (пропуск)")
                
                # Пауза, чтобы не злить сервер ГИБДД
                time.sleep(2)

if __name__ == "__main__":
    download_to_local()

# %%
# ЗАГРУЗКА ДАНННЫХ ГИБДД

def fix_date(d):
    if not d: return None
    try: return datetime.strptime(d, "%d.%m.%Y").strftime("%Y-%m-%d")
    except: return d
        
def safe_float(val):
    if not val or str(val).strip() in [".", "", "null", "None"]:
        return None
    try:
        return float(str(val).replace(',', '.')) # На случай, если придет запятая
    except ValueError:
        return None
        
def upload_final_with_dedup():
    print(" ЗАПУСК ПАРСИНГА ...")
    
    # Подгружаем ID городов
    city_res = supabase.table("cities_coords").select("id, name").execute()
    city_map = {c['name']: c['id'] for c in city_res.data}

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
                    try: data_list = json.load(f)
                    except: continue

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
                    # ОТ ДУБЛИКАТОВ
                    unique_rows = []
                    seen_keys = set()
                    for r in rows:
                        # Ключ должен полностью совпадать с индексом в БД (on_conflict)
                        key = (r['kart_id'], r['v_id'], r['p_role'], r['p_gender'], r['p_experience'])
                        if key not in seen_keys:
                            unique_rows.append(r)
                            seen_keys.add(key)
                    
                    # Загрузка пачками
                    batch_size = 500
                    for i in range(0, len(unique_rows), batch_size):
                        batch = unique_rows[i:i+batch_size]
                        try:
                            supabase.table("gibdd_accidents_history_3_cities").upsert(
                                batch, 
                                on_conflict="kart_id, v_id, p_role, p_gender, p_experience"
                            ).execute()
                        except Exception as e:
                            print(f"Ошибка в {city_name} {year}/{file_name}: {e}")
                
                print(f"{city_name} {year}/{file_name}: загружено {len(rows)} записей")

if __name__ == "__main__":
    upload_final_with_dedup()


