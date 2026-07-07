# %% [markdown]
# ## Исследовательский анализ данных о связи погоды и ДТП

# %% [markdown]
# ### Цели и задачи проекта
# 
# <font color='#777778'></font>
# 
# **Цель:**
#    Провести исследовательский анализ данных о связах погоды и дорожно-транспортных происшествий на данных трех городов Омск, Новосибирск и Тюмень в периоды 2015-2025 годов.
# 
# **Задачи:**
# 1. Загрузить данные и познакомиться с их содержимым.
# 2. Провести предобработку данных.
# 3. Провести исследовательский анализ данных:
#     - изучить данные более детально;
#     - изучить взаимосвязь данных.
# 4. Сформулировать выводы по проведённому анализу.

# %% [markdown]
# ### Описание данных
# 
# <font color='#777778'></font>
# Данные состоят из **3** датасетов:
# 
# #### Описание датасета `cities_coords`
# - `id` — уникальный id таблицы;
# - `created_at` — дата заполнения;
# - `name` — наименование города;
# - `region` — наименование региона;
# - `population` — населенность, чел.;
# - `latitude` — широта;
# - `longitude` — долгота; 
# - `okato_region` — код ОКАТО региона;
# - `okato_city` — код ОКАТО города.
# 
# #### Описание датасета `weather_history_3_cities`
# - `id` — уникальный id таблицы;
# - `created_at` — дата заполнения;
# - `city` — наименование города;
# - `timestamp` — дата и время замера погоды;
# - `temp` — температура;
# - `humidity` — влажность;
# - `precipitation` — общее количество осадков;
# - `weather_code` — код погодных условий;
# - `weather_description` — описание погоды;
# - `wind_speed` — скорость ветра;
# - `pressure` — давление;
# - `snow_depth` — высота снежного покрова, м;
# - `rain` — дождь;
# - `snowfall` — количество свежевыпавшего снега, м;
# - `apparent_temp` — ощущаемая температура;
# 
# #### Описание датасета `gibdd_accidents_history_3_cities`
# - `id` — уникальный id таблицы;
# - `created_at` — дата заполнения;
# - `kart_id` — уникальный номер карточки ДТП;
# - `dtp_date` — дата ДТП;
# - `dtp_time` — время ДТП, время местное;
# - `district` — район города;
# - `dtp_type` — тип ДТП;
# - `pog_total` — общее количество погибших;
# - `ran_total` — общее количество раненных;
# - `vehicles_count` — общее количество ТС участников;
# - `participants_count` — общее число участников ДТП (водители, пешеходы);
# - `city_name` — наименование города, связь с таблицей `cities_coords`;
# - `address_street` — улица, где произошло ДТП;
# - `address_house` — номер дома;
# - `road_category` — категория дороги;
# - `weather` — погода;
# - `road_condition` — состояние дорожного полотна;
# - `light_condition` — освещение;
# - `latitude` — широта, места ДТП;
# - `longitude` — долгота, места ДТП;
# - `road_faults` — недостатки дороги;
# - `v_id` — номер ТС в ДТП;
# - `v_type` — тип ТС;
# - `v_marka` — марка ТС;
# - `v_color` — цвет ТС;
# - `v_year` — год выпуска ТС;
# - `v_ownership` — тип владения ТС;
# - `p_role` — роль учатника в ДТП;
# - `p_gender` — пол учатника ДТП;
# - `p_experience` — стаж воздения учатника ДТП;
# - `p_severity` — состояние учатника на момент ДТП;
# - `p_alcohol` — уровень алкоголя в крови участника;
# - `p_safety_belt` — ремень безопасности (пристегнут ли учатник ДТП да/нет);
# - `p_violations` — нарушение ПДД;
# - `p_additional_violations` — дополнительные нарушения, зафиксированные на месте ДТП;
# - `city_id` — id города, связь с таблицей `cities_coords`.

# %% [markdown]
# ### Содержимое проекта
# 
# <font color='#777778'></font>
# 1. Загрузка данных и знакомство с ними.
# 2. Предобработка данных.
# 3. Исследовательский анализ данных.
# 4. Итоговый вывод и рекомендации.
# 5. Загрузка итоговых таблиц в базу
# 
# ---

# %% [markdown]
# ## 1. Загрузка данных и знакомство с ними
# 
# ### 1.1 Загрузим библиотеки и датасеты. 
# Будем использовать pandas и библиотеки визуализации данных matplotlib и seaborn, а также phik для построения матрицы корреляции.

# %%
# Импортируем библиотеку pasndas и create_client из библиотеки supebase для получения данных
import pandas as pd
from supabase import create_client

# Дополнительные библиотеки
import time
import re
import phik
from phik import resources, report

# Загружаем библиотеки для визуализации данных
import matplotlib.pyplot as plt
import seaborn as sns

import math
import numpy as np

# %%
# Настройки подключения
SUPABASE_URL = "https://amr***.supabase.co"
SUPABASE_KEY = "***"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# %%
def fetch_all_rows_robust(table_name, order_col, current_df=None):
    all_data = current_df.to_dict('records') if current_df is not None else []
    offset = len(all_data)
    limit = 1000
    
    print(f"Загрузка {table_name} (сортировка по {order_col}) с отметки {offset}...")
    
    while True:
        try:
            # Добавляем .order(order_col) для стабильности страниц
            res = supabase.table(table_name).select("*").order(order_col).range(offset, offset + limit - 1).execute()
            
            if not res.data:
                break
                
            all_data.extend(res.data)
            offset += len(res.data) # инкремент по факту полученных данных
            
            if offset % 5000 == 0:
                print(f"Загружено {offset} строк...")
                
        except Exception as e:
            print(f"Ошибка на отметке {offset}: {e}. Пробую снова...")
            time.sleep(5)
            continue
            
    print(f"Готово! {table_name}: {len(all_data)} строк.")
    return pd.DataFrame(all_data)

# Вызываем с указанием правильных ID-колонок для каждой таблицы
df_cities = fetch_all_rows_robust("cities_coords", "id") # или как называется ID в этой таблице
df_weather = fetch_all_rows_robust("weather_history_3_cities", "id") 
df_dtp = fetch_all_rows_robust("gibdd_accidents_history_3_cities", "kart_id")

# %% [markdown]
# ### 1.2 Познакомимся с данными и изучим общую информацию о них.

# %% [markdown]
# ### 1.2.1 Познакомимся с данными датасета `cities_coords` 
# Выведем первые строки методом `head()`, а информацию о датафрейме методом `info()`:

# %%
# Выводим первые строки датафрейма на экран
df_cities.head()

# %%
# Выводим информацию о датафрейме
df_cities.info()

# %% [markdown]
# Датасет `cities_coords` содержит 9 столбцов и 172 строки, в которых представлена информация о городах и их регионе, населенности, координатам и кодам ОКАТО.
# - Названия столбцов лаконичны и отображают информацию соответствующую данным. Но дополним наименование столбца `name` уточняющих словом *city* для единообразия в данных, таким образом переименнуем в `city_name`.
# - Cтолбец `created_at` можно удалить, так информация содержащаяся в нем не представляет ценности для анализа.
# - Cтолбец `id`. Тип данных `int64` соответствует содержанию, но может быть понижен до `int8`.
# - Типы данных остальных столбцов соответствуют данным в них.
# - Ряд населенных пунктов не был идентифицирован сервисом геокодирования из-за различий в используемых классификаторах административно-территориального деления. Данные также будут исключены из текущего цикла обработки.

# %% [markdown]
# ### 1.2.2 Познакомимся с данными датасета `weather_history_3_cities` 
# Выведем первые строки методом `head()`, а информацию о датафрейме методом `info()`:

# %%
# Выводим первые строки датафрейма на экран
df_weather.head()

# %%
df_weather.info()

# %% [markdown]
# Датасет `weather_history_3_cities` содержит 15 столбцов и 289 296 строк, в которых представлена информация о погоде в 3-х городах.
# - Названия столбцов лаконичны и отображают информацию соответствующую данным. Но дополним наименование столбца `city` уточняющих словом *name* для единообразия в данных, таким образом переименнуем в `city_name`.
# - Cтолбец `created_at` можно удалить, так информация содержащаяся в нем не представляет ценности для анализа.
# - Даннные столбца `timestamp` преобразуем в datetime64.
# - Остальные типы данных столбцов соответствуют данным в них, пропусков нет.

# %% [markdown]
# ### 1.2.3 Познакомимся с данными датасета `gibdd_accidents_history_3_cities` 
# Выведем первые строки методом `head()`, а информацию о датафрейме методом `info()`:

# %%
# Выводим первые строки датафрейма на экран
df_dtp.head()

# %%
df_dtp.info()

# %% [markdown]
# Датасет `gibdd_accidents_history_3_cities` содержит 37 столбцов и 112 581 строк, в которых представлена информация о дтп в 3-х городах.
# - Названия столбцов лаконичны и отображают информацию соответствующую данным. 
# - Cтолбец `created_at` можно удалить, так информация содержащаяся в нем не представляет ценности для анализа.
# - Даннные столбца `dtp_date` и `dtp_time` объединим и преобразуем в datetime64.
# - Остальные типы данных столбцов соответствуют данным в них.
# - Пропуски только в столбца `p_experience` и `v_year`, вследствии того что не все участники ДТП являются водителями, также возможен человеческий фактор. Удаление данных не предусматривается.

# %% [markdown]
# ---
# 
# ### Промежуточный вывод:

# %% [markdown]
# - Первичное знакомство с данными, показало их соотвествие описанию. Данные выглядят корректно. 

# %% [markdown]
# ### 1.2.4 Фильтр данных датасета `cities_coords` 
# - Оставим строки в таблице только искомы городов: Омск, Новосибирск, Тюмень

# %%
# Создаем список нужных городов
target_cities = ['Омск', 'Новосибирск', 'Тюмень']

# Фильтруем датафрейм
df_cities_filter = df_cities[df_cities['name'].isin(target_cities)]

# %% [markdown]
# ## 2. Предобработка данных

# %% [markdown]
# - Переименуем столбцы 

# %%
# Приведем столбцы с названиями городов к единому наименованию
df_cities_filter = df_cities_filter.rename(columns={'name': 'city_name'})
df_weather = df_weather.rename(columns={'city': 'city_name'})

# %% [markdown]
# - Преобразуем все текстовые данные во всех таблица к нижмему регистру Для единообразия

# %%
# Приводим к нижнему регистру содержимое всех текстовых ячеек используя map
df_cities_filter = df_cities_filter.map(lambda x: x.lower() if isinstance(x, str) else x)
df_weather = df_weather.map(lambda x: x.lower() if isinstance(x, str) else x)
df_dtp = df_dtp.map(lambda x: x.lower() if isinstance(x, str) else x)

# %% [markdown]
# - Удалим столбец `created_at` во всех таблицах

# %%
# Удалим лишние столбцы
df_cities_filter = df_cities_filter.drop(columns=['created_at'])
df_weather = df_weather.drop(columns=['created_at'])
df_dtp = df_dtp.drop(columns=['created_at'])

# %% [markdown]
# #### 2.1 Изучим корректность типов данных и при необходимости проведем их преобразование

# %% [markdown]
# - Проведем понижение целочисленных типов данных, для оптимизации

# %%
def optimize_types(df):
    # Копируем датафрейм, чтобы не повредить оригинал
    df = df.copy()
    
    for col in df.columns:
        # Проверяем, является ли столбец числовым
        if pd.api.types.is_numeric_dtype(df[col]):
            # Проверяем, есть ли в столбце дробная часть
            # Если это целые числа
            if pd.api.types.is_integer_dtype(df[col]):
                df[col] = pd.to_numeric(df[col], downcast='integer')
            # Если это числа с плавающей точкой
            else:
                df[col] = pd.to_numeric(df[col], downcast='float')
                
    return df

# Применяем оптимизацию к таблицам
df_cities_filter = optimize_types(df_cities_filter)
df_dtp = optimize_types(df_dtp)
df_weather = optimize_types(df_weather)

# %%
# Преобразуем в datetime64 столбец timestamp в df_weather
df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp'])

# %%
# Создаем единый столбец даты и времени из столбцов dtp_date и dtp_time и преобразуем в datetime64 
# Так как это строки (object), мы их сконкатенируем.
df_dtp['full_datetime'] = pd.to_datetime(
    df_dtp['dtp_date'].astype(str) + ' ' + df_dtp['dtp_time'].astype(str)
)
# ОКРУГЛЯЕМ ДО ЧАСА (для будущего объединения с погодой)
df_dtp['full_datetime'] = df_dtp['full_datetime'].dt.round('h')

# Удалим лишние столбецы даты и времени
df_dtp = df_dtp.drop(columns=['dtp_date', 'dtp_time'])

# %%
# Перепроверим и выведем типы данных с помощью атрибута .dtypes
df_cities_filter.dtypes

# %%
df_weather.dtypes

# %%
df_dtp.dtypes

# %% [markdown]
# - **Все типы данных соответствуют данным столбцов**

# %% [markdown]
# #### 2.2 Изучим пропущенные значения в данных

# %% [markdown]
# 1. **`df_cities_filter`**

# %%
# Применяем метод isna()
df_cities_filter.isna().sum().sort_values(ascending=False).reset_index().style.background_gradient(cmap='coolwarm', axis=0)

# %% [markdown]
# - Пропусков нет.

# %% [markdown]
# 2. **`df_weather`**

# %%
# Применяем метод isna()
df_weather.isna().sum().sort_values(ascending=False).reset_index().style.background_gradient(cmap='coolwarm', axis=0)

# %% [markdown]
# - Пропусков нет.

# %% [markdown]
# 3. **`df_dtp`**

# %%
# Применяем метод isna()
df_dtp.isna().sum().sort_values(ascending=False).reset_index().style.background_gradient(cmap='coolwarm', axis=0)

# %%
# Подсчитываем долю строк с пропусками
(df_dtp.isna().sum()/df_dtp.shape[0]).sort_values(ascending=False).reset_index().style.background_gradient(cmap='coolwarm', axis=0)

# %% [markdown]
# - 26% пропусков в столбце `p_experience` и 7% пропусков в столбце `v_year`. Скорее всего данная информация не заполняется в случае, если участник ДТП не является водителей или нет информации. Тип пропусков MAR. Принято решение заменить пропуски на "no data".

# %%
# Заменим пропуски в столбце `p_experience` методом .fillna()
df_dtp['p_experience'] = df_dtp['p_experience'].fillna('no data')

# %%
# Заменим пропуски в столбце `p_experience` методом .fillna()
df_dtp['v_year'] = df_dtp['v_year'].fillna('no data')

# %% [markdown]
# #### 2.3 Проверим данные на дубликаты

# %% [markdown]
# 1. **`df_cities_filter`**

# %%
# Выведем количество уникальных значений во всех столбцах
df_cities_filter.nunique()

# %% [markdown]
# - Одна строка по каждому городу, данные все отличны.

# %%
df_cities_filter.head()

# %% [markdown]
# 2. **`df_weather`**

# %%
# Выведем количество уникальных значений во всех столбцах
df_weather.nunique()

# %% [markdown]
# - количество строк по каждому городу составляет:
#   - данные за 2015-2025 год - 11 лет (3 года высокосные)
#   - 365 * 24 * 8 + 366 * 24 * 3 = 96 432 - т.е. каждый город из трех имеет столько строк
#   - 96 432 *3 = 289 296, следовательно id полный и уникальный столбец.

# %%
# Рассмотрим уникальные значения столбца `city_name`
df_weather['city_name'].unique()

# %% [markdown]
# - три города: Омск, Новосибирск, Тюмень

# %%
# Рассмотрим уникальные значения столбца `temp`
print(sorted(df_weather['temp'].unique()))

# %% [markdown]
# - аномальных значений в столбце температуры `temp` не наблюдается
# - температура находиться в диапазоне от -43.2 до 37.5 градусов.

# %%
# Рассмотрим уникальные значения столбца `humidity`
print(sorted(df_weather['humidity'].unique()))

# %% [markdown]
# - аномальных значений в столбце влажности `humidity` не наблюдается
# - влажность находится в диапазоне от 10 до 100 %.

# %%
# Рассмотрим уникальные значения столбца `precipitation`
print(sorted(df_weather['precipitation'].unique()))

# %% [markdown]
# - аномальных значений в столбце данных об общем количестве осадков `precipitation` не наблюдается
# - общее количество осадков находится в диапазоне от 0.0 (осадков нет) до 16.8 мм (ливень) или до 2.66 см (сильный снегопад/метель).

# %%
# Рассмотрим уникальные значения столбцов `weather_code` и `weather_description`
print(sorted(df_weather['weather_code'].unique()))
print(df_weather['weather_description'].unique())

# %% [markdown]
# - всего 13 вариантов кодов и их описания

# %%
# Рассмотрим уникальные значения столбца `wind_speed`
print(sorted(df_weather['wind_speed'].unique()))

# %% [markdown]
# - аномальных значений в столбце данных об общем количестве осадков `wind_speed` не наблюдается
# - скорость ветра находится в диапазоне от 0.0 (штиль) до 53.0 м/с (сильный шторм (ураган))

# %%
# Рассмотрим уникальные значения столбца `pressure`
print(sorted(df_weather['pressure'].unique()))

# %% [markdown]
# - аномальных значений в столбце давления `pressure` не наблюдается
# - давление находится в диапазоне от 954.8 (низкое давление (циклон)) до 1054.6 гПа (высокое давление (антициклон))

# %%
# Рассмотрим уникальные значения столбца `snow_depth`
print(sorted(df_weather['snow_depth'].unique()))

# %% [markdown]
# - аномальных значений в столбце высоты снежного покрова `snow_depth` не наблюдается
# - высота снежного покрова находится в диапазоне от 0.0 (чистый асфальт) до 0.92 м (глубокий снег)

# %%
# Рассмотрим уникальные значения столбца `rain`
print(sorted(df_weather['rain'].unique()))

# %% [markdown]
# - аномальных значений в столбце данных о дождях `rain` не наблюдается
# - количество дождя находится в диапазоне от 0.0 (осадков нет) до 16.8 мм (ливень).

# %%
# Рассмотрим уникальные значения столбца `snowfall`
print(sorted(df_weather['snowfall'].unique()))

# %% [markdown]
# - аномальных значений в столбце данных о снеге `snowfall` не наблюдается
# - количество снего находится в диапазоне от 0.0 (осадков нет) до 2.66 см (сильный снегопад/метель).

# %%
# Рассмотрим уникальные значения столбца `apparent_temp`
print(sorted(df_weather['apparent_temp'].unique()))

# %% [markdown]
# - аномальных значений в столбце температура «по ощущениям» `apparent_temp` не наблюдается
# - температура «по ощущениям» находиться в диапазоне от -48.4 до 38.8 градусов.

# %% [markdown]
# 3. **`df_dtp`** 

# %%
# Выведем количество уникальных значений во всех столбцах
# Выбираем только те колонки, где нет списков
df_dtp.select_dtypes(exclude=['object']).nunique()

# %% [markdown]
# - количество карточек ДТП от ГИБДД составялет 55 227 шт. Одна карточка может иметь более одной строки данных
# - большая часть данных находится в списках, в связи с этим далее произведем преобразование данных

# %%
# Находим столбцы со списками и превращаем их в строки
for col in df_dtp.columns:
    if df_dtp[col].apply(lambda x: isinstance(x, list)).any():
        df_dtp[col] = df_dtp[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)

# Теперь .nunique() сработает без ошибок
print(df_dtp.nunique())

# %%
# Рассмотрим уникальные значения столбца `full_datetime`
df_dtp['full_datetime'].unique()

# %%
# Рассмотрим уникальные значения столбца `dtp_time`
df_dtp['district'].unique()

# %% [markdown]
# - для единообразия преобразуем данные оставив только само название района

# %%
# Убираем "район", "ао", "г.тюмени" и любые вариации пробелов
pattern = r'район|ао|г\.тюмени|г\. тюмени'

df_dtp['district'] = (df_dtp['district']
                      .str.replace(pattern, '', regex=True) # Удаляем слова
                      .str.strip() # Убираем лишние пробелы по краям
                     )

# Проверяем результат
print(df_dtp['district'].unique())

# %% [markdown]
# - из 19 осталось 11 наименований районов городов

# %%
# Рассмотрим уникальные значения столбца `dtp_type`
df_dtp['dtp_type'].value_counts()

# %% [markdown]
# - в данных представлено 18 разнообразных типов ДТП. Сделам дополнительный столбец, консолидировав данные.

# %%
dtp_mapping = {
    # Группа: Столкновения (взаимодействие ТС)
    'столкновение': 'Столкновение',
    'наезд на стоящее тс': 'Столкновение',
    'наезд на внезапно возникшее препятствие': 'Столкновение',
    'наезд на гужевой транспорт': 'Столкновение',

    # Группа: Наезды на уязвимых участников (люди/вело)
    'наезд на пешехода': 'Наезд на человека',
    'наезд на велосипедиста': 'Наезд на человека',
    'падение пассажира': 'Наезд на человека',
    'наезд на лицо, не являющееся участником дорожного движения, осуществляющее несение службы': 'Наезд на человека',
    'наезд на лицо, не являющееся участником дорожного движения, осуществляющее какую-либо другую деятельность': 'Наезд на человека',
    'наезд на лицо, не являющееся участником дорожного движения, осуществляющее производство работ': 'Наезд на человека',

    # Группа: Инфраструктура и среда
    'наезд на препятствие': 'Наезд на препятствие',
    'съезд с дороги': 'Съезд/Опрокидывание',
    'опрокидывание': 'Съезд/Опрокидывание',
    'наезд на животное': 'Прочие/Животные',

    # Группа: Технические и прочие инциденты
    'отбрасывание предмета': 'Технический фактор/Груз',
    'падение груза': 'Технический фактор/Груз',
    'возгорание вследствие технической неисправности движущегося или остановившегося тс, участвующего в дорожном движении.': 'Технический фактор/Груз',
    'иной вид дтп': 'Иной вид'
}

df_dtp['dtp_type_group'] = df_dtp['dtp_type'].map(dtp_mapping)

# %%
# Проверяем, появились ли пустые значения после маппинга
print(df_dtp[df_dtp['dtp_type_group'].isna()]['dtp_type'].unique())

# %%
# Рассмотрим уникальные значения столбца `pog_total`
df_dtp['pog_total'].unique()

# %% [markdown]
# - количество погибших в данных от 0 до 4 человек

# %%
# Рассмотрим уникальные значения столбца `ran_total`
print(sorted(df_dtp['ran_total'].unique()))

# %% [markdown]
# - количество постродавших в данных от 0 до 25 человек

# %%
# Рассмотрим уникальные значения столбца `vehicles_count`
print(sorted(df_dtp['vehicles_count'].unique()))

# %% [markdown]
# - количество ТС при ДТП в данных от 1 до 13

# %%
# Рассмотрим уникальные значения столбца `participants_count`
print(sorted(df_dtp['participants_count'].unique()))

# %% [markdown]
# - общее количество участников ДТП в данных от 1 до 31

# %%
# Рассмотрим уникальные значения столбца `city_name`
print(sorted(df_dtp['city_name'].unique()))

# %% [markdown]
# - такое разнообразие наименрований города и его пригородов вносит неразбериху, консолидируем данные, а именно приведем наименования только к трем городам используя id города

# %%
# Смотрим, какие ID привязаны к названиям, содержащим 'омск', 'тюмень' и т.д.
print(df_dtp.groupby(['city_id', 'city_name']).size().reset_index(name='count'))

# %%
# Создаем словарь
id_to_city = {
    89: 'новосибирск',
    98: 'омск',
    142: 'тюмень'
}

# Преобразовываем
df_dtp['city_name'] = df_dtp['city_id'].map(id_to_city)

# Проверяем
print(df_dtp['city_name'].unique())


# %%
# Рассмотрим уникальные значения столбца `address_street`
df_dtp['address_street'].unique()

# %%
# Рассмотрим уникальные значения столбца `address_house`
df_dtp['address_house'].unique()

# %% [markdown]
# - рассмотрев подробнее столбцы `address_street` и `address_house`, принято решение их удалить, так как для дальнейшего анализа, они не несут смыловой нагрузки (для определения места ДТП данные широты и долготы более чем достаточно), а их разноообразиии, в том числе в написании, только занимает место памяти.

# %%
# Удаляем ненужные столбцы
df_dtp = df_dtp.drop(columns=['address_street', 'address_house'])

# %%
# Рассмотрим уникальные значения столбца `road_category`
df_dtp['road_category'].unique()

# %% [markdown]
# - преобразуем данные для удобного использования

# %%
# Создаем словарь для упрощения названий
road_mapping = {
    'федеральная (дорога федерального значения)': 'федеральная',
    'региональная или межмуниципальная (дорога регионального или межмуниципального значения)': 'региональная',
    'местного значения (дорога местного значения, включая относящиеся к собственности поселений, муниципальных районов, городских округов)': 'местная',
    'местного значения (дороги местного значения, включая относящиеся к собственности поселений, муниципальных районов, городских округов)': 'местная',
    'не указано': 'не указано',
    'другие места': 'другое'
}

df_dtp['road_category'] = df_dtp['road_category'].map(road_mapping)

# Проверяем
print(df_dtp['road_category'].unique())

# %%
# Рассмотрим уникальные значения столбца `weather`
df_dtp['weather'].unique()

# %% [markdown]
# - Переименнуем для дальнейшего использования и во избежания путаницы с погодой от OpenMeteo

# %%
df_dtp.rename(columns={'weather': 'weather_from_gibdd'}, inplace=True)

# %% [markdown]
# - в данных 6 вариантов описания погоды

# %%
# Рассмотрим уникальные значения столбца `road_condition`
df_dtp['road_condition'].unique()

# %% [markdown]
# - в данных представлено 11 вариантов состояния дорожного полотна, преобразуем в группы в новом столбце для сохранение деталей в карте 

# %%
condition = {
    'сухое': 'сухое',
    'мокрое': 'мокрое/вода',
    'залитое (покрытое) водой': 'мокрое/вода',
    'загрязненное': 'грязное/пыльное',
    'пыльное': 'грязное/пыльное',
    'со снежным накатом': 'зима (лед/снег)',
    'заснеженное': 'зима (лед/снег)',
    'гололедица': 'зима (лед/снег)',
    'обработанное противогололедными материалами': 'обработано (химия)',
    'не установлено': 'не указано',
    'свежеуложенная поверхностная обработка': 'ремонт'
}

df_dtp['road_condition_group'] = df_dtp['road_condition'].map(condition)

# %%
# Рассмотрим уникальные значения столбца `light_condition`
df_dtp['light_condition'].unique()

# %% [markdown]
# - в данных представлено 6 вариантов освещения и каждый несет свою смысловую нагрузку, оставим без изменений

# %%
# Рассмотрим уникальные значения столбца `latitude`
df_dtp['latitude'].unique()

# %%
# Рассмотрим уникальные значения столбца `longitude`
df_dtp['longitude'].unique()

# %% [markdown]
# - Данные широты и долготы ДТП оставляем без изменений

# %%
# Рассмотрим уникальные значения столбца `road_faults`
df_dtp['road_faults'].value_counts().head(10)

# %% [markdown]
# - Консолидируем данные, добавим бинарные колонки по основным вариантам недостатков дорог

# %%
import numpy as np

# Словарь: Ключ - название колонки, Значение - регулярное выражение для поиска
patterns = {
    'road_marking': 'разметк',
    'road_signs': 'знак',
    'street_lighting': 'освещен|свет',
    'pavement_defects': 'покрыти|ямы|выбоин|колея|неровн|обочин',
    'winter_conditions': 'зимн|снег|гололед|скольз',
    'traffic_light': 'светофор',
    'drainage_system': 'ливнев|водоотвод',
    'road_narrowing': 'сужен',
    'bus_stop_elements': 'остановочн|автобусн|пешеход|тротуар',
    'road_works_zone_tsod': 'местах проведения|работТСОД'
}

# 1. Создаем бинарные колонки (Flags)
for col_en, pattern in patterns.items():
    df_dtp[col_en] = df_dtp['road_faults'].str.contains(pattern, case=False, na=False).astype(int)

# 2. Функция для создания единой текстовой колонки с перечислением всех проблем
def summarize_faults(row):
    # Собираем все названия категорий, где стоит 1
    found = [col for col, pattern in patterns.items() if row[col] == 1]
    
    if not found:
        low_text = str(row['road_faults']).lower()
        if any(x in low_text for x in ['не установлены', 'не выявлены', 'отсутствуют']):
            return 'no_faults'
        return 'other_faults'
    
    # Склеиваем найденные недостатки через точку с запятой
    return '; '.join(found)

# Создаем итоговую колонку
df_dtp['faults_consolidated'] = df_dtp.apply(summarize_faults, axis=1)

# Выводим результат
print("Статистика по консолидированным группам:")
print(df_dtp['faults_consolidated'].value_counts().head(10))

# %%
# Проверяем, появились ли пустые значения после маппинга
print(df_dtp[df_dtp['faults_consolidated'].isna()]['road_faults'].unique())

# %%
# Рассмотрим уникальные значения столбца `v_id`
print(sorted(df_dtp['v_id'].unique()))

# %% [markdown]
# - в ДТП принимало участие от 1 до 7 ТС

# %%
# Рассмотрим уникальные значения столбца `v_type`
df_dtp['v_type'].unique()

# %% [markdown]
# - Консолидируем данные, добавим столбец с категорией ТС

# %%
def consolidate_vehicle_types(text):
    # Обработка пропусков (NaN, None, пустые строки)
    if pd.isna(text) or str(text).strip() == '':
        return 'pedestrian_or_no_data'
    
    t = str(text).lower().strip()
    
    # 1. Общественный транспорт (Public Transport)
    if any(x in t for x in ['автобус', 'троллейбус', 'трамвай', 'длиной от', 'одноэтажн', 'двухэтажн', 'сочлененн']):
        return 'общественный'
    
    # 2. Грузовой транспорт (Trucks & Heavy Logistics)
    if any(x in t for x in ['грузов', 'тягач', 'самосвал', 'рефрижератор', 'фургон', 'бортов', 
                            'цистерн', 'лесовоз', 'цементовоз', 'бетоносмеситель', 'шасси']):
        return 'грузовой'
    
    # 3. Легковые автомобили (Passenger Cars)
    if any(x in t for x in ['класс', 'минивэн', 'универсал', 'легковые']):
        return 'легковые'
    
    # 4. Мототехника и СИМ (Motorcycles, Bikes & Micromobility)
    if any(x in t for x in ['мотоцикл', 'мопед', 'мотороллер', 'велосипед', 'квадрицикл', 
                            'трицикл', 'квадроцикл', 'средство передвижения малой мощности', 'мототранспорт']):
        return 'мототехника'
    
    # 5. Спецтехника и Дорожные работы (Construction & Maintenance)
    if any(x in t for x in ['трактор', 'грейдер', 'экскаватор', 'кран', 'погрузчик', 'эвакуатор', 
                            'коммунального', 'содержания дорог', 'снегоуборочн', 'самоходные', 'спецтехника', 'строит']):
        return 'спецтехника'
    
    # 6. Экстренные и Государственные службы (Emergency & State Services)
    if any(x in t for x in ['скорой', 'медицинский', 'мвд', 'полиции', 'аварийно-спасательн', 
                            'пожарные', 'военного', 'под стражей', 'инкассации', 'денежной выручки']):
        return 'экстренные_и_государственные'
    
    # 7. Сельхоз и Внедорожная техника (Agriculture & Off-road)
    if any(x in t for x in ['мотоблок', 'снегоход']):
        return 'внедорожная'
    
    # 8. Рельсовый транспорт (Rail)
    if 'ж/д' in t or 'подвижной состав' in t:
        return 'рельсовый'
    
    # Все остальное, что не попало в фильтры или помечено как "иное"
    return 'иное'

# Применяем трансформацию
df_dtp['vehicle_category'] = df_dtp['v_type'].apply(consolidate_vehicle_types)

# Быстрая проверка
print(df_dtp['vehicle_category'].value_counts())

# %%
# Проверяем, появились ли пустые значения после маппинга
print(df_dtp[df_dtp['vehicle_category'].isna()]['v_type'].unique())

# %%
# Рассмотрим уникальные значения столбца `v_marka`
df_dtp['v_marka'].unique()

# %% [markdown]
# - Оставим марку ТС без изменений

# %%
# Рассмотрим уникальные значения столбца `v_model`
df_dtp['v_model'].unique()

# %% [markdown]
# - Оставим модель ТС без изменений

# %%
# Рассмотрим уникальные значения столбца `v_color`
print(sorted(df_dtp['v_color'].unique()))

# %% [markdown]
# - Консолидтируем данные, объединим отсутствующие данные

# %%
def consolidate_color_simple(text):
    # Объединяем пустоты и спец. маркеры
    if pd.isna(text) or str(text).strip() in ['', 'не заполнено']:
        return 'данные отсутствуют'
    
    t = str(text).lower().strip()
    
    # Причесываем "иные цвета"
    if 'иные' in t:
        return 'другие цвета'
        
    return t

df_dtp['v_color_clean'] = df_dtp['v_color'].apply(consolidate_color_simple)
df_dtp.drop(columns=['v_color'], inplace=True)

# Проверка уникальных значений
print(df_dtp['v_color_clean'].unique())

# %%
# Рассмотрим уникальные значения столбца `v_year`
df_dtp['v_year'].unique()

# %% [markdown]
# - Уберем из года ".0", уберем аномальное значение

# %%
def clean_vehicle_year(value):
    # Если это уже 'no data' или пусто
    if pd.isna(value) or value == 'no data' or value == '':
        return 'no data'
    
    try:
        # Преобразуем во float, затем в int (чтобы убрать .0)
        year = int(float(value))

        # Убираем аномалии: 1.0, слишком старые (например, до 1930) 
        # или будущие года (в базе есть 2025, что возможно, но 1.0 точно ошибка)
        if year < 1930 or year > 2025:
            return 'no data'
            
        return year
    except (ValueError, TypeError):
        return 'no data'

# Применяем очистку
df_dtp['v_year_clean'] = df_dtp['v_year'].apply(clean_vehicle_year)
df_dtp.drop(columns=['v_year'], inplace=True)

print(sorted(df_dtp['v_year_clean'].unique(), key=lambda x: (str(type(x)), x)))

def categorize_vehicle_age(year):
    if year == 'no data':
        return 'Нет данных'
    
    current_year = 2025
    age = current_year - year
    
    if age <= 3:
        return 'Новые (до 3 лет)' # Гарантийные авто, современные системы безопасности
    elif age <= 7:
        return 'Современные (4-7 лет)' # Актуальные системы безопасности
    elif age <= 15:
        return 'Подержанные (8-15 лет)' # Средний парк, возможен износ систем
    elif age <= 25:
        return 'Старые (16-25 лет)' # Устаревшие технологии
    else:
        return 'Раритетные (25+ лет)' # Высокий риск технических неисправностей

# Создаем новый столбец с периодами
df_dtp['vehicle_age_group'] = df_dtp['v_year_clean'].apply(categorize_vehicle_age)

# Проверка распределения
print(df_dtp['vehicle_age_group'].value_counts())

# %%
# Рассмотрим уникальные значения столбца `v_ownership`
df_dtp['v_ownership'].unique()

# %% [markdown]
# - Разгрузим столбец на 2 подстолбца: происхождение капитала и форма собственности

# %%
def process_ownership(text):
    if pd.isna(text) or str(text).strip() in ['', 'иное', 'не заполнено']:
        return 'данные отсутствуют', 'данные отсутствуют'
    
    t = str(text).lower().strip()
    
    # --- 1. Определяем происхождение капитала (Origin) ---
    if 'совместная российская и иностранная' in t:
        origin = 'смешанная'
    elif any(word in t for word in ['иностранная', 'иностранных', 'международных']):
        origin = 'иностранная'
    else:
        origin = 'российская'
    
    # --- 2. Определяем конкретную форму (Detail) ---
    if 'частная' in t: 
        detail = 'частная'
    elif 'муниципальная' in t: 
        detail = 'муниципальная'
    elif 'федеральная' in t: 
        detail = 'федеральная'
    elif 'субъектов' in t: 
        detail = 'региональная'
    elif 'коллективная' in t: 
        detail = 'коллективная'
    elif 'смешанная российская' in t: 
        detail = 'смешанная гос-частная'
    elif any(word in t for word in ['совместная', 'иностранных', 'международных']):
        detail = 'иностранная/совместная'
    else:
        detail = 'прочее'
        
    return origin, detail

# Применяем функцию (создаем сразу две колонки)
df_dtp[['v_ownership_origin', 'v_ownership_detail']] = df_dtp['v_ownership'].apply(
    lambda x: pd.Series(process_ownership(x))
)

# Проверка результата
print(df_dtp[['v_ownership_origin', 'v_ownership_detail']].value_counts())

# %%
# Рассмотрим уникальные значения столбца `p_role`
df_dtp['p_role'].unique()

# %% [markdown]
# - Объединим данные по велосипедистам. Итого 4 варианта участника ДТП.

# %%
def clean_person_role(text):
    if pd.isna(text) or str(text).strip() == '':
        return 'данные отсутствуют'
    
    t = str(text).lower().strip()
    
    # Объединяем велосипедистов
    if 'велосипедист' in t:
        return 'велосипедист'
        
    return t

# Применяем очистку
df_dtp['p_role'] = df_dtp['p_role'].apply(clean_person_role)

# Проверяем результат
print(df_dtp['p_role'].value_counts())

# %%
# Рассмотрим уникальные значения столбца `p_gender`
df_dtp['p_gender'].unique()

# %% [markdown]
# - Объединим данные без указания пола. Итого 3 варианта пола участника ДТП.

# %%
def clean_gender(text):
    # Объединяем пустые строки, NaN и "не определен"
    if pd.isna(text) or str(text).strip() in ['', 'не определен']:
        return 'данные отсутствуют'
    
    return str(text).lower().strip()

# Применяем очистку
df_dtp['p_gender'] = df_dtp['p_gender'].apply(clean_gender)

# Проверяем результат
print(df_dtp['p_gender'].value_counts())

# %%
# Рассмотрим уникальные значения столбца `p_experience`
df_dtp['p_experience'].unique()

# %% [markdown]
# - Уберем из стажа ".0", уберем аномальное значение.

# %%
# 1. Функция очистки
def clean_p_experience(value):
    if pd.isna(value) or value == 'no data' or value == '':
        return np.nan 
    try:
        experience = int(float(value))
        if experience > 80:
            return np.nan
        return experience
    except (ValueError, TypeError):
        return np.nan

# Применяем очистку
df_dtp['p_experience_clean'] = df_dtp['p_experience'].apply(clean_p_experience)

# 2. Создаем группы стажа
# Границы: 0, 1 год, 3 года, 5 лет, 10 лет, 20 лет, 80 лет
bins = [-1, 0, 3, 5, 10, 20, 80]
labels = ['До года', '1-3 года', '3-5 лет', '5-10 лет', '10-20 лет', 'Свыше 20 лет']

df_dtp['experience_group'] = pd.cut(
    df_dtp['p_experience_clean'], 
    bins=bins, 
    labels=labels
).astype(object).fillna('no data') # Возвращаем 'no data' для пропусков

print(df_dtp['experience_group'].value_counts(dropna=False))

# %%
# Рассмотрим уникальные значения столбца `p_severity`
df_dtp['p_severity'].unique()

# %% [markdown]
# - Консолидируем в 3 группы. Уточняющий столбец не удаляем.

# %%
def consolidate_severity(text):
    if pd.isna(text) or str(text).strip() == '':
        return 'нет данных'
    
    t = str(text).lower().strip()
    
    # 1. Погибшие (все упоминания смерти)
    if 'скончался' in t:
        return 'погибший'
    
    # 2. Раненые (лечение стационарное, амбулаторное или медпомощь)
    if any(word in t for word in ['ранен', 'лечени', 'травм', 'поврежден']):
        return 'раненый'
    
    # 3. Не пострадавшие
    if 'не пострадал' in t:
        return 'не пострадал'
        
    return 'нет данных'

# Применяем консолидацию
df_dtp['p_severity_clean'] = df_dtp['p_severity'].apply(consolidate_severity)

# Проверяем результат
print(df_dtp['p_severity_clean'].value_counts())


# %%
# Проверяем, появились ли пустые значения после маппинга
print(df_dtp[df_dtp['p_severity_clean'].isna()]['p_severity'].unique())

# %%
# Рассмотрим уникальные значения столбца `p_alcohol`
print(sorted(df_dtp['p_alcohol'].unique()))

# %% [markdown]
# - Консолидируем в 3 группы. Уточняющий столбец не удаляем.

# %%
def clean_alcohol_status(value):
    # Приводим к строке, удаляем пробелы и дополняем нулем до двух знаков (07, 01)
    val = str(value).strip().zfill(2)
    
    # 00 — Состояние опьянения не установлено (трезв)
    if val == '00':
        return 'трезв'
    
    # Коды 01-80 обычно обозначают установленное опьянение (алкоголь, наркотики)
    # Коды 88, 99 или пустые строки — это отказы или отсутствие данных
    if val in ['', 'nan', '99', '88']:
        return 'нет данных / отказ'
    
    # Все остальные числовые коды (01, 04, 24 и т.д.) трактуем как нетрезвое состояние
    return 'нетрезв'

# Применяем очистку
df_dtp['p_alcohol_clean'] = df_dtp['p_alcohol'].apply(clean_alcohol_status)

# Смотрим результат
print(df_dtp['p_alcohol_clean'].value_counts())

# %%
# Рассмотрим уникальные значения столбца `p_safety_belt`
df_dtp['p_safety_belt'].unique()

# %% [markdown]
# - 2 варианта. Переводем в бинарную систему.

# %%
df_dtp['p_safety_belt'] = df_dtp['p_safety_belt'].map({'да': 1, 'нет': 0})

# %%
# Рассмотрим уникальные значения столбца `p_violations`
df_dtp['p_violations'].value_counts().head(10)

# %%
# Рассмотрим уникальные значения столбца `p_additional_violations`
df_dtp['p_additional_violations'].value_counts().head(10)

# %%
# 1. Единый словарь маппинга
violation_map = {
    # --- СТАТУС И СОСТОЯНИЕ ---
    'v_driver_status': 'права|лишен|категории|опьянен|алкогол|наркот|освидетельство|веществ|моложе|16 лет|14 лет',
    'v_driver_docs': 'осаго|незарегистри|документ|нпа',
    'v_driver_safety': 'ремн|шлем|детских|удерживающ',
    'v_driver_escape': 'оставление места|выпрыгивание|выход или выпрыгивание|оставление движущегося', 
    
    # --- ТЕХНИКА И СКОРОСТЬ ---
    'v_driver_speed': 'скорост|превышение',
    'v_driver_tech': 'техническими неисправностями|технеисправности|светопропускание|неисправного тс|тормозной системой|неисправностей или условий|эксплуатация тс с техническими|технически неисправного|ослепление',
    
    # --- МАНЕВРЫ И ПРАВИЛА ДВИЖЕНИЯ ---
    'v_driver_overtaking': 'встречн|обгон|трамвайные пути|односторонним|выезда на встречную',
    'v_driver_maneuver': 'разворот|задним ходом|перестроение|перестроения|круговом|начале движения|расположения тс|подача сигналов|объездо|обеспечения безопасности при начале',
    'v_driver_priority': 'очередности|светофор|сигналов|преимущества в движении тс|знаков|разметки|регулиров|подчинение|остановок трамвая|проезда перекрестков|регулирования',
    'v_driver_distance': 'дистанции|бокового интервала|выбор дистанции',
    
    # --- СПЕЦИФИКА И ГРУЗЫ ---
    'v_driver_heavy_cargo': 'тяжеловесного|крупногабаритного|нагрузки на ось|массы тс|габаритов тс|погрузки|крепления грузов|выгрузки|опасных грузов',
    'v_driver_dangerous': 'опасное вождение|жилых зонах|общественным транспортом|помех для водителя',

    # --- ПРОЧЕЕ ---
    'v_driver_other': 'перевозки люди|перевозки людей|грузов|буксировка|буксировки|остановки|стоянки|ж/д переездов|внешними световыми|режима труда|мобильной|другие нарушения|иные нарушения|другими нарушениями|освещения|светом фар',
    
    # --- НАРУШЕНИЯ ПЕШЕХОДОВ / СИМ / ВЕЛО ---
    'v_pedestrian_rules': 'пешеходу|неустановленном месте|вдоль проезжей части|без цели её перехода|преимущества пешеходу|пешеходного перехода|выход из-за стоящего|тротуара|вне пешеходного|зоне его видимости|подземного|надземного',
    'v_micromobility_rules': 'велосипедист|сим|мопед|скейтборд|роликовых|не спешившись|светоотражающими|гужевой',
    
    # --- СПЕЦСЛУЖБЫ ---
    'v_police_emergency': 'маячком|цветографические|сопротивление|исполнении|задержании|правоохранительных|цветографические схемы|звуковым сигналом',
    
    # --- НЕТ НАРУШЕНИЙ ---
    'v_no_violations': 'не установлены|не выявлены|отсутствуют|нет нарушений|не установлено'
}

# 2. Создание бинарных признаков
total_cols = []
for key, pattern in violation_map.items():
    col_name = f"{key}_total"
    mask = (df_dtp['p_violations'].str.contains(pattern, case=False, na=False) | 
            df_dtp['p_additional_violations'].str.contains(pattern, case=False, na=False))
    df_dtp[col_name] = mask.astype(int)
    total_cols.append(col_name)

# 3. Корректировка флага "Нет нарушений"
real_violation_cols = [c for c in total_cols if c != 'v_no_violations_total']
has_any_violation = df_dtp[real_violation_cols].sum(axis=1) > 0
df_dtp.loc[has_any_violation, 'v_no_violations_total'] = 0

# 4. Текстовая консолидация (Исправлено перемножение матриц)
labels = [c.replace('_total', '') for c in real_violation_cols]
# Используем значения .values, чтобы избежать ошибки выравнивания индексов
df_dtp['violation_consolidated'] = (
    df_dtp[real_violation_cols]
    .dot(pd.Series(labels).values + '; ')
    .str.rstrip('; ')
)

# Заполняем случаи без категорий и "нет нарушений"
df_dtp.loc[df_dtp['v_no_violations_total'] == 1, 'violation_consolidated'] = 'no_violations'
df_dtp.loc[df_dtp['violation_consolidated'] == '', 'violation_consolidated'] = 'other_violations'

# 5. ПРОВЕРКА РАСПРЕДЕЛЕНИЯ
source_has_text = (df_dtp['p_violations'].astype(str).str.strip().str.len() > 2) | \
                  (df_dtp['p_additional_violations'].astype(str).str.strip().str.len() > 2)

is_unmapped = (df_dtp[total_cols].sum(axis=1) == 0) & source_has_text

if is_unmapped.any():
    print(f"⚠️ Найдено {is_unmapped.sum()} нераспределенных строк.")
else:
    print("✅ Все данные успешно распределены!")

# %%
# --- ВЫВОД РЕЗУЛЬТАТОВ ---

print("-" * 50)
# 1. Считаем, сколько всего ДТП попало в каждую категорию
print("📊 СТАТИСТИКА ПО КАТЕГОРИЯМ (ТОП-10):")
stats = df_dtp[total_cols].sum().sort_values(ascending=False)
print(stats.head(10))

print("-" * 50)

# 2. Проверяем долю распределения
total_rows = len(df_dtp)
unmapped_rows = is_unmapped.sum()
mapped_percent = ((total_rows - unmapped_rows) / total_rows) * 100
print(f"📈 ОХВАТ ДАННЫХ: {mapped_percent:.2f}% (Распределено {total_rows - unmapped_rows} из {total_rows})")

print("-" * 50)
# 3. Показываем пример того, как склеились данные
print("👀 ПРИМЕР РЕЗУЛЬТАТА (Первые 5 строк):")
# Выбираем только те колонки, где есть хоть одна "1" для наглядности
sample_cols = ['p_violations', 'p_additional_violations', 'violation_consolidated']
print(df_dtp[sample_cols].head(5))

# 4. Если есть нераспределенные данные, выведем их уникальные значения
if unmapped_rows > 0:
    print("-" * 50)
    print(f"⚠️ ТЕКСТЫ, КОТОРЫЕ НЕ ПОПАЛИ В СЛОВАРЬ (Первые 10 уникальных):")
    # Собираем текст из обоих столбцов, где не сработал маппинг
    missing_data = df_dtp.loc[is_unmapped, ['p_violations', 'p_additional_violations']].drop_duplicates().head(10)
    print(missing_data)
else:
    print("-" * 50)
    print("✅ ИДЕАЛЬНО: Весь текст в базе распознан!")

# %% [markdown]
# #### 2.4 Подведем итоги

# %%
df_cities_filter.info()

# %%
df_weather.info()

# %%
df_dtp.info()

# %% [markdown]
# **Все таблицы полные, без пропусков**

# %% [markdown]
# ---
# 
# ## 3. Исследовательский  и статистический анализ
# 

# %% [markdown]
# ### 3.1 Объединим данные о погоде и ДТП в один датафрейм

# %% [markdown]
# - Так как данные времени погоды в датафрейме df_weather ресурс OpenMeteo выдает в UTC, а ГИБДД в карточках ДТП отмечает местное вреня, то необходимо преобразорвание перед объединением таблиц.

# %%
# Словарь смещений для городов под UTC
city_offsets = {
    'Тюмень': 5,
    'Омск': 6,
    'Новосибирск': 7
}

# 1. Убеждаемся, что full_datetime — это datetime без зоны (naive)
df_dtp['full_datetime'] = pd.to_datetime(df_dtp['full_datetime']).dt.tz_localize(None)

# 2. Создаем временную колонку в UTC для объединения
# Вычитаем разницу часового пояса из местного времени ДТП
def to_utc(row):
    offset = city_offsets.get(row['city_name'], 0) # 'city_name' — название колонки с городом
    return row['full_datetime'] - pd.Timedelta(hours=offset)

df_dtp['dtp_hour_utc'] = df_dtp.apply(to_utc, axis=1)

# 3. Убеждаемся, что погода тоже в UTC и без зоны (для merge)
df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp']).dt.tz_localize(None)

# 4. Выполняем объединение по времени И по городу (если в df_weather есть город)
df_final = df_dtp.merge(
    df_weather, 
    left_on=['dtp_hour_utc', 'city_name'], 
    right_on=['timestamp', 'city_name'],
    how='left'
)

# %%
# Заменяем даты попавщие 2026 года на 2025 годом, для удобства будущих расчетов (попали случайно). 
# При появление полного месяца данных ГИБДД за январь 2026, этот код удалить.

# 1. Находим маску (все строки, где год 2026)
mask_2026 = df_final['dtp_hour_utc'].dt.year == 2026  

# 2. Выводим количество найденных аномалий (для проверки)
print(f"Найдено строк за 2026 год: {mask_2026.sum()}")

# 3. Массово исправляем их на нужную дату
df_final.loc[mask_2026, 'dtp_hour_utc'] = pd.Timestamp('2025-12-31 23:00:00')

# 4. Проверяем результат
print(f"Осталось строк за 2026 год: {(df_final['dtp_hour_utc'].dt.year == 2026).sum()}")

# %%
df_final.info()

# %%
# Посчитаем уникальное количество ДТП в итоговом датасете
len(df_final['kart_id'].unique())

# %% [markdown]
# - Таким образом за период с 2015 по 2025 года включительно, в таких областях как Омская, Новосибирская и Тюменская произошло 55 227 ДТП.

# %% [markdown]
# ### 3.2 Корреляция данных погоды и ДТП

# %% [markdown]
# #### 3.2.1 Корреляция данных погоды и тяжести ДТП

# %%
# 1. Подготовка списков колонок
weather_cols = ['temp', 'humidity', 'precipitation', 'wind_speed', 'pressure', 'snow_depth', 'rain', 'snowfall', 'apparent_temp']
target_cols = ['pog_total', 'ran_total', 'vehicles_count', 'participants_count']

# 2. Агрегируем данные до уровня уникального ДТП (kart_id)
# Используем ** для объединения словарей в один аргумент для .agg()
df_unique_corr = df_final.groupby('kart_id').agg({
    **{col: 'first' for col in weather_cols},   # Распаковка погодных параметров
    **{col: 'first' for col in target_cols}    # Распаковка параметров тяжести
}).reset_index()

# 3. Визуализация матрицы корреляций ПИрсона на очищенных данных
plt.figure(figsize=(12, 10))
sns.heatmap(df_unique_corr[weather_cols + target_cols].corr(), 
            annot=True, 
            cmap='RdYlGn', 
            fmt=".2f", 
            center=0)

plt.title("Матрица корреляции: Метеопараметры vs Тяжесть инцидентов (уникальные ДТП)", fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# **Основные выводы:**
# 1. Взаимосвязь погоды и тяжести последствий
# 
# Слабая корреляция с тяжестью: Коэффициенты корреляции метеопараметров с количеством погибших (pog_total) и раненых (ran_total) близки к нулю (от -0.03 до 0.04). Это статистически подтверждает, что сама по себе погода не является прямым виновником тяжелых последствий — она лишь создает условия, а тяжесть ДТП больше зависит от поведения водителей и защитных систем автомобиля.
# Температура и количество участников: Наблюдается слабая отрицательная связь между температурой (temp) и числом участников/транспортных средств (от -0.01 до -0.06). Это может указывать на то, что при аномально низких температурах интенсивность движения снижается, что ведет к уменьшению массовых ДТП.
# 
# 2. Сильные метеорологические зависимости
# 
# Температура и снег: Выявлена сильная отрицательная корреляция между температурой и высотой снежного покрова (snow_depth: -0.72). Это закономерно: чем ниже температура, тем стабильнее и глубже снежный покров.
# Осадки и их тип: Коэффициент между общими осадками (precipitation) и дождем (rain) составляет 0.95, что говорит о доминировании дождевых осадков в исследуемой выборке данных. Снегопад (snowfall) имеет значительно меньшую связь с общим объемом осадков (0.31).
# 
# 3. Внутренняя структура инцидентов
#    
# Масштаб ДТП: Наблюдается сильная положительная корреляция между количеством раненых (ran_total) и числом участников (participants_count) — 0.71. Это логично: чем больше людей вовлечено в аварию, тем выше вероятность получения травм кем-либо из них.
# Связь ТС и людей: Коэффициент 0.60 между количеством машин (vehicles_count) и участников подтверждает, что большинство аварий в выборке — это столкновения двух и более транспортных средств.
# 
# **ИТОГ: Матрица доказывает, что погодные факторы сильно взаимосвязаны между собой, но их влияние на тяжесть (смертность) косвенное. Это аргумент в пользу того, что погода влияет на частоту ДТП (через видимость и сцепление), а не на их фатальность.**

# %%
# 3. Визуализация матрицы корреляций Phik
plt.figure(figsize=(12, 10))

# Вычисляем матрицу Phik для нужных колонок
phik_matrix = df_unique_corr[weather_cols + target_cols].phik_matrix()

sns.heatmap(phik_matrix, 
            annot=True, 
            cmap='RdYlGn', 
            fmt=".2f", 
            vmin=0, vmax=1, # Phik всегда от 0 до 1
            center=0.5)

plt.title("Матрица корреляции Phik: Метеопараметры vs Тяжесть (нелинейные связи)", fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# **Основные выводы по матрице Phik:**
#     
# 1. Погода и Тяжесть
# 
# К сожалению, между погодой и тяжестью ДТП связи также практически нет. Коэффициенты в районе 0.00 – 0.05 говорят о том, что метеоусловия почти не определяют количество пострадавших (ran_total) или участников (participants_count) в конкретном инциденте.
# Исключение: есть мизерный намек на связь snowfall (0.04) и temp (0.03) с тяжестью, но это на грани статистической погрешности.
# 
# 2. Группа «Тяжесть»
# 
# Видна мощная связь между ran_total и participants_count (0.96). Это логично: чем больше участников, тем выше шанс на наличие раненых.
# Связь vehicles_count с participants_count (0.41) умеренная — не в каждой машине много людей.
# 
# 3. Группа «Погода»
# 
# Здесь всё «горит» зеленым. temp и apparent_temp (0.97) почти дублируют друг друга.
# Интересна связь temp и snow_depth (0.70). Phik зафиксировал ее гораздо лучше Пирсона, так как эта связь нелинейная (снег лежит только при минусе).
# rain и precipitation (1.00) — это фактически одна и та же переменная в данных.
# 
# **ИТОГ: Гипотеза: Погода чаще влияет на количество ДТП в городе в целом, а не на тяжесть одного конкретного случая. Тяжесть больше зависит от скорости, типа столкновения или дорожной инфраструктуры.**

# %% [markdown]
# #### 3.2.2 Распределение метеорологических факторов по ДТП

# %%
# Создаем датасет с уникальными метеоусловиями на момент каждого инцидента
df_unique_weather = df_final.groupby('kart_id').agg({
      **{col: 'first' for col in weather_cols}
}).reset_index()

# Настройка стиля и сетки
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(3, 3, figsize=(22, 18))
ax = axes.flatten()

# --- Построение графиков на базе df_unique_weather ---

# 1. Температура реальная
sns.histplot(df_unique_weather['temp'], bins=40, kde=True, ax=ax[0], color='skyblue')
ax[0].axvline(0, color='red', linestyle='--', label='0°C')
ax[0].set_title('Температура воздуха (°C)')

# 2. Ощущаемая температура
sns.histplot(df_unique_weather['apparent_temp'], bins=40, kde=True, ax=ax[1], color='coral')
ax[1].axvline(0, color='red', linestyle='--')
ax[1].set_title('Ощущаемая температура (°C)')

# 3. Разница температур (эффект ветра/влажности)
temp_delta = df_unique_weather['temp'] - df_unique_weather['apparent_temp']
sns.histplot(temp_delta, bins=30, kde=True, ax=ax[2], color='teal')
ax[2].set_title('Разница (Реальная - Ощущаемая) °C')

# 4. Влажность
sns.histplot(df_unique_weather['humidity'], bins=20, kde=True, ax=ax[3], color='lightgreen')
ax[3].set_title('Влажность (%)')

# 5. Атмосферное давление
sns.histplot(df_unique_weather['pressure'], bins=40, kde=True, ax=ax[4], color='plum')
ax[4].set_title('Давление (гПа)')

# 6. Скорость ветра
sns.histplot(df_unique_weather['wind_speed'], bins=30, kde=True, ax=ax[5], color='gold')
ax[5].set_title('Скорость ветра (км/ч)')

# 7. Дождь (только когда > 0)
rain_data = df_unique_weather[df_unique_weather['rain'] > 0]['rain']
sns.histplot(rain_data, bins=30, ax=ax[6], color='royalblue')
ax[6].set_title('Интенсивность дождя (мм/ч)')

# 8. Снегопад (только когда > 0)
snowfall_data = df_unique_weather[df_unique_weather['snowfall'] > 0]['snowfall']
sns.histplot(snowfall_data, bins=30, ax=ax[7], color='grey')
ax[7].set_title('Интенсивность снегопада (см/ч)')

# 9. Глубина снега (только когда > 0)
snow_depth_data = df_unique_weather[df_unique_weather['snow_depth'] > 0]['snow_depth']
sns.histplot(snow_depth_data, bins=30, ax=ax[8], color='lavender', edgecolor='blue')
ax[8].set_title('Глубина снежного покрова (м)')

plt.suptitle('Распределение метеорологических факторов (n = уникальные ДТП)', fontsize=20, y=1.02)
plt.tight_layout()
plt.show()

# %% [markdown]
# **Разбор метеофакторов:**
# 1. Температурный режим (Термический стресс)
# *Бимодальное распределение*: На графиках температуры (реальной и ощущаемой) видны два выраженных пика: в районе 0°C и +15...17°C.
# *Зона «нулевого» риска*: Огромное количество ДТП происходит при переходе температуры через ноль. Это критическая точка, когда дорожное покрытие становится непредсказуемым из-за образования микрольда (черного льда).
# *Комфортный пик*: Высокая аварийность при +15°C объясняется общим ростом интенсивности движения и скоростей в благоприятную погоду.
# 2. Влажность и давление
# *Влажность*: Большинство ДТП происходит при высокой влажности (80–90%). Это косвенный индикатор условий плохой видимости (туман, дымка) и влажного дорожного полотна, что увеличивает тормозной путь.
# *Давление*: Распределение близко к нормальному с пиком около 1010 гПа. Резкие отклонения от нормы (циклоны) часто сопровождаются сменой погоды, что также коррелирует с всплесками аварийности.
# 3. Динамические факторы (Ветер и разница температур)
# *Скорость ветра*: Основная масса инцидентов фиксируется при ветре 10–15 км/ч. Это умеренные значения, не создающие прямых помех, что подтверждает: ветер редко является прямой причиной ДТП, но может усиливать охлаждение покрытия.
# *Разница температур*: Пик в районе 5°C (реальная температура выше ощущаемой) указывает на условия, когда при наличии ветра и влажности водитель может недооценивать риск обледенения асфальта.
# 4. Интенсивность осадков и снежный покров
# *Низкая интенсивность* — высокий риск: Графики дождя и снегопада показывают, что подавляющее число аварий происходит при минимальных осадках (первые капли дождя или легкий снег). Это «эффект неожиданности», когда сцепление уже ухудшилось, а водители еще не адаптировали стиль вождения.
# *Глубина снега*: Пик приходится на значения 0.1–0.4 м. Это свидетельствует о том, что наиболее опасны неубранные обочины и сужение проезжей части из-за снежных валов, а не экстремальные сугробы (в которые движение просто прекращается).
# 
# **ИТОГ: Данные подтверждают, что экстремальные погодные условия (ураганы, ливни) вносят меньший вклад в общую статистику, чем пограничные состояния (температура около 0°C, высокая влажность, начало осадков). Именно в эти моменты инфраструктурные дефекты становятся наиболее опасными.**

# %% [markdown]
# #### 3.2.4 Консолитация типов погоды

# %%
# Создаем словарь для объединения погоды
# убираем эмодзи и лишние пробелы из названий погоды
df_final['weather_clean'] = (
    df_final['weather_description']
    .astype(str)
    .str.replace(r'[^\w\s]', '', regex=True) # Убирает все спецсимволы и эмодзи
    .str.lower()
    .str.strip()
)

# 3. Обновленный словарь (теперь БЕЗ эмодзи в ключах)
weather_map = {
    'ясно': 'Ясно ☀️', 
    'преимущественно ясно': 'Ясно ☀️',
    'переменная облачность': 'Облачно ☁️', 
    'пасмурно': 'Облачно ☁️',
    'легкая морось': 'Морось/Небольшой снег 🌦', 
    'умеренная морось': 'Морось/Небольшой снег 🌦', 
    'плотная морось': 'Морось/Небольшой снег 🌦', 
    'небольшой дождь': 'Морось/Небольшой снег 🌦', 
    'дождь': 'Дождь/Снег 🌧/❄️', 
    'сильный дождь': 'Дождь/Снег 🌧/❄️', 
    'небольшой снег': 'Морось/Небольшой снег 🌦', 
    'снег': 'Дождь/Снег 🌧/❄️', 
    'сильный снег': 'Дождь/Снег 🌧/❄️'
}

# Применяем группировку
df_final['weather_group'] = df_final['weather_clean'].map(weather_map)

# %% [markdown]
# #### 3.2.4 Анализ средовых факторов и типологии ДТП

# %%
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Установка шрифта
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False 

# Агрегация данных по уникальным ДТП (1 kart_id = 1 запись)
# Оставляем только системные факторы среды и типа инцидента
params_to_agg = {
    'weather_group': 'first',
    'road_condition_group': 'first',
    'light_condition': 'first',
    'dtp_type_group': 'first',
    'road_category': 'first'
}

# Фильтруем существующие колонки и агрегируем
available_params = {k: v for k, v in params_to_agg.items() if k in df_final.columns}
df_env_unique = df_final.groupby('kart_id').agg(available_params).reset_index()
df_env_unique = df_env_unique.dropna(subset=['weather_group']).copy()

# 2. Список параметров для визуализации
params_env = [
    ('road_condition_group', 'Состояние дорожного покрытия', 'YlGnBu'),
    ('light_condition', 'Условия освещенности', 'coolwarm'),
    ('road_category', 'Категория дороги', 'Greens'),
    ('dtp_type_group', 'Вид дорожного происшествия', 'viridis'),
]

# Настраиваем сетку под 3 графика
fig, axes = plt.subplots(4, 1, figsize=(14, 10))

for i, (col, title, palette) in enumerate(params_env):
    if col in df_env_unique.columns:
        # Строим распределение структуры факторов внутри каждой погодной группы
        ct = pd.crosstab(df_env_unique['weather_group'], 
                         df_env_unique[col].fillna('Нет данных'), 
                         normalize='index') * 100
        
        if not ct.empty:
            ct.plot(kind='barh', stacked=True, ax=axes[i], colormap=palette, width=0.75)
            axes[i].set_title(f'Зависимость от погоды: {title}', fontsize=10, fontweight='bold')
            axes[i].set_xlabel('Доля в структуре метеогруппы (%)')
            axes[i].set_ylabel('Погода')
            axes[i].legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
            axes[i].xaxis.grid(True, linestyle='--', alpha=0.6)
    else:
        axes[i].set_title(f'Колонка {col} не найдена', color='red')

plt.suptitle('АНАЛИЗ СРЕДОВЫХ ФАКТОРОВ И ТИПОЛОГИИ ДТП', 
             fontsize=18, y=1.02, fontweight='bold')
plt.tight_layout()
plt.show()

# %% [markdown]
# **Анализ средовых факторов (состояние покрытия, освещенность, категория дороги) и типов ДТП**
# 
# 1. Состояние дорожного покрытия
# Доминирование сухого покрытия: в группах «Ясно» и «Облачно» подавляющее большинство ДТП (около 60–70%) происходит на сухом асфальте. Это подтверждает гипотезу о том, что благоприятные погодные условия могут провоцировать водителей на риск и превышение скорости.
# Влияние осадков: в группе «Дождь/Снег» ожидаемо преобладают категории «мокрое/вода» и «зима (лед/снег)». Примечательно, что значительная доля происшествий случается на «обработанном (химия)» покрытии — это указывает на то, что при интенсивных осадках реагенты не всегда обеспечивают идеальное сцепление.
# Зимний фактор: в группе «Облачно» доля «зимнего» покрытия заметно выше, чем в группе «Ясно». Это коррелирует с риском обледенения дороги в отсутствие прямого солнечного прогрева.
# 2. Условия освещенности
# Световой день: во всех погодных группах основная доля ДТП (более 60%) приходится на светлое время суток.
# Фактор сниженной видимости: в группе «Дождь/Снег» наблюдается рост доли ДТП «в темное время суток (освещение включено)» до 40%, что значительно выше, чем в ясную погоду (~25%). Это подчеркивает критическую роль качественного искусственного освещения при осадках.
# Сумерки: доля ДТП в сумерках остается стабильно низкой во всех метеогруппах, что может быть связано с меньшей продолжительностью этого периода.
# 3. Категория дороги
# Местные дороги (70–75%): на графике видно, что основной объем происшествий генерируется на местных дорогах. Доля остается высокой во всех метеогруппах, что говорит о концентрации аварийности в населенных пунктах.
# Региональные дороги (20–23%): в группе «Морось/Небольшой снег» и «Дождь/Снег» сегмент региональных дорог визуально расширяется. Это может указывать на рост опасности таких трасс при ухудшении погоды.
# Федеральные дороги (2–5%): минимальная доля ДТП во всех метеогруппах. Высокий уровень содержания и своевременная обработка реагентами эффективно нивелируют погодные риски.
# 4. Вид дорожного происшествия
# Столкновение (основной тип): лидирует во всех группах (около 50%). Стабильность показателя говорит о том, что столкновения чаще связаны с человеческим фактором (дистанция, очередность проезда), чем с погодой.
# Съезд / Опрокидывание: доля этого типа ДТП визуально возрастает в группе «Дождь/Снег», что напрямую связано с потерей сцепления с дорогой.
# Наезд на пешехода: остается стабильно значимым фактором. В условиях осадков риск возрастает из-за увеличения тормозного пути и снижения видимости.
# 
# **ИТОГ: Анализ подтверждает, что структура типов ДТП (лидерство столкновений) устойчива к изменениям погоды. Однако дорожная среда меняется кардинально. Наиболее коварной является ситуация при осадках на региональных дорогах и темное время суток с включенным освещением, когда видимость и сцепление объективно хуже, несмотря на работу коммунальных служб.**

# %% [markdown]
# #### 3.2.5 Детальный анализ участников ДТП

# %%
# Список ролей для анализа
roles = df_final['p_role'].unique()

for role in roles:
    # Фильтруем данные по конкретной роли
    df_role = df_final[df_final['p_role'] == role].copy()
    
    # Пропускаем, если данных слишком мало
    if len(df_role) < 10:
        continue
        
    # Берем топ погодных условий для этой роли
    top_weather = df_role['weather_group'].value_counts().index
    df_plot = df_role[df_role['weather_group'].isin(top_weather)].copy()

    # Параметры анализа (пол, защита, последствия)
    # Используем проверку наличия колонок, так как у пешеходов может не быть 'ремень'
    current_params = [
        ('p_gender', 'Пол', 'coolwarm'),
        ('p_severity_clean', 'Тяжесть травм', 'magma'),
        ('p_alcohol_clean', 'Влияние алкоголя', 'Blues'),
        ('experience_group', 'Стаж вождения', 'Greens') # только для водителей
    ]
    
    # Добавляем специфические колонки, если они есть
    if 'p_safety_belt' in df_role.columns:
        current_params.insert(1, ('p_safety_belt', 'Средства защиты (ремень)', 'Set2'))

    fig, axes = plt.subplots(len(current_params), 1, figsize=(14, 3 * len(current_params)))
    if len(current_params) == 1: axes = [axes]

    for i, (col, title, palette) in enumerate(current_params):
        ct = pd.crosstab(df_plot['weather_group'], df_plot[col], normalize='index') * 100
        ct.plot(kind='barh', stacked=True, ax=axes[i], colormap=palette, width=0.75)
        
        axes[i].set_title(f'{role.capitalize()}: {title} в зависимости от погоды', fontsize=14, fontweight='bold')
        axes[i].set_xlabel('Доля (%)')
        axes[i].set_ylabel('')
        axes[i].legend(bbox_to_anchor=(1.02, 1), loc='upper left')

    plt.suptitle(f'ДЕТАЛЬНЫЙ АНАЛИЗ ГРУППЫ: {role.upper()}', fontsize=14, y=1.02, fontweight='bold', color='darkblue')
    plt.tight_layout()
    plt.show()
    print("\n" + "="*50 + "\n") # Разделитель в консоли между ролями

# %% [markdown]
# **ПАССАЖИР**
# 1. Гендерный состав в зависимости от погоды
# Статистика: во всех метеогруппах сохраняется стабильное распределение: около 70% пассажиров составляют женщины (светло-серый сегмент) и около 30% — мужчины (красный сегмент).
# Вывод: данные подтверждают устойчивую социальную модель — мужчины значительно чаще выступают в роли водителей, в то время как женщины преобладают среди пассажиров вне зависимости от внешних условий.
# 2. Использование средств защиты (ремни безопасности)
# Распределение: на графике видно, что доля пристегнутых пассажиров (серый сегмент «1») составляет около 55–60%, а не пристегнутых (зеленый сегмент «0») — порядка 40–45%.
# Влияние погоды: примечательно, что в группе «Дождь/Снег» доля пристегнутых пассажиров даже немного снижается (зеленый сегмент становится шире и достигает почти 50%). Это указывает на парадокс: ухудшение дорожных условий не повышает бдительность пассажиров, а дисциплина использования ремней остается стабильно низкой.
# 3. Тяжесть травм
# Доминирующий показатель: подавляющее большинство пострадавших (более 95%) попадает в категорию «раненые» (светло-желтый цвет). Доли «погибших» (бордовый) и «не пострадавших» (черный) крайне малы.
# Метеозависимость: тяжесть последствий для пассажиров практически не коррелирует с погодой. Если авария произошла, вероятность получения травм остается одинаково высокой как в ясную погоду, так и при осадках.
# 4. Влияние алкоголя и стаж вождения
# Алкоголь: график показывает 100% результат в категории «трезв» (светло-голубой). Это может свидетельствовать о том, что опьянение пассажиров либо не фиксируется в протоколах как сопутствующий фактор, либо они действительно не употребляли алкоголь.
# Стаж: график «Стаж вождения» для пассажиров ожидаемо пуст («no data»), так как эта характеристика не применима к данной категории участников ДТП.
# 
# **ИТОГ: Анализ показывает, что группа «Пассажир» крайне инертна к погодным изменениям. Поведенческие факторы (использование ремня) и последствия ДТП для пассажиров носят системный характер и не зависят от условий видимости или состояния покрытия.**
# 
# ---
# 
# **ВОДИТЕЛЬ**
# 1. Гендерный состав в зависимости от погоды
# Статистика: Во всех погодных сценариях наблюдается стабильное распределение. Мужчины (красный сегмент) составляют подавляющее большинство — около 75% от общего числа участников с известными данными. Женщины (светло-серый сегмент) — порядка 15-18%.
# Особенность данных: В среднем в 10% случаев данные о поле водителя отсутствуют (синий сегмент).
# Вывод: Погода не влияет на гендерный состав участников ДТП. Нет тенденции к тому, что в плохую погоду женщины водят реже или чаще попадают в инциденты.
# 2. Использование средств защиты (ремень безопасности)
# Распределение: Показатели остаются практически статичными. Около 65% водителей (серый сегмент «1») используют ремни безопасности, в то время как 35% (зеленый сегмент «0») игнорируют их.
# Влияние рисков: Объективное ухудшение дорожных условий (осадки, гололед) не повышает дисциплинированность. Привычка пристегиваться — это устойчивый паттерн поведения, который не коррелирует с уровнем опасности на дороге.
# 3. Тяжесть травм в зависимости от погоды
# Статистика: Более 70% водителей попадают в категорию «не пострадал» (черный сегмент). Около 25% получают ранения (светло-желтый сегмент), и крайне малый процент погибает (фиолетовый сегмент).
# Анализ: Степень тяжести последствий идентична как в ясную погоду, так и в ливень или снегопад. Это свидетельствует о том, что водители в плохую погоду либо инстинктивно снижают скорость, либо системы безопасности автомобилей эффективно минимизируют ущерб здоровью.
# 4. Влияние алкоголя
# Показатели: Абсолютное большинство водителей — трезвые (темно-синий сегмент, более 95%). Доля нетрезвых участников (голубой сегмент) минимальна и визуально не меняется в зависимости от метеоусловий.
# Вывод: Трезвость водителя — самый стабильный показатель. Погодный фактор не является триггером, меняющим статистику «пьяных» аварий.
# 5. Стаж вождения (Ключевой динамический фактор)
# Группа риска (10–20 лет): Самый широкий сегмент во всех группах (ярко-зеленый). На них приходится около 45-50% инцидентов. Большой опыт не страхует от аварий при потере сцепления или плохой видимости.
# Опытные водители (Свыше 20 лет): В условиях «Облачно» доля водителей с максимальным стажем незначительно растет. Это может указывать на их чувствительность к снижению контрастности и освещенности.
# Начинающие водители (До 3 лет): В группе «Ясно» их доля максимальна — новички чувствуют себя увереннее. В группе «Осадки» их доля заметно сокращается, что говорит о высокой осторожности и частом отказе от поездок в сложных условиях.
# Средний стаж (3–10 лет): Эти водители стабильны в любую погоду. Они уже преодолели страхи новичков, но еще не достигли стадии «излишней самоуверенности» более опытных коллег.
# 
# **ИТОГ: Характеристики группы «Водитель» (пол, использование ремней, трезвость) практически не зависят от метеоусловий. Единственным фактором, на который влияет погода, является интенсивность движения начинающих водителей, которые минимизируют риски в осадки. При этом основной «вклад» в статистику ДТП в любую погоду вносят водители со стажем 10–20 лет, чей стиль вождения остается неизменным вопреки внешним условиям.**
# 
# ---
# 
# **ВЕЛОСИПЕДИСТ**
# 1. Пол в зависимости от погоды
# Статистика: подавляющее большинство велосипедистов во всех метеоусловиях — мужчины (темно-красный, более 80%). Доля женщин (серый) невелика и заметно снижается в периоды осадков. В группе «Дождь/Снег» присутствие женщин практически сводится к нулю.
# Вывод: мужчины чаще используют велосипед как транспортное средство независимо от погоды. Женщины-велосипедистки более чувствительны к комфорту и безопасности в сложных метеоусловиях.
# 2. Средства защиты (ремень)
# Статистика: график полностью закрашен мятным цветом с пометкой «0» (не пристегнут).
# Примечание: параметр «ремень» является технической заглушкой общего шаблона отчета, так как данный вид защиты не предусмотрен конструкцией велосипеда.
# 3. Тяжесть травм
# Доминирующий показатель: практически все поле занимает бледно-желтый цвет (категория «раненый»). Доли «не пострадавших» (черный) и «погибших» (бордовый/фиолетовый) крайне малы.
# Вывод: велосипедист — крайне уязвимый участник движения. В отличие от водителей авто, у них практически отсутствует категория «не пострадал»: любое ДТП с высокой вероятностью ведет к травмам.
# 4. Влияние алкоголя
# Статистика: наблюдается сплошной темно-синий блок («трезв»). Полоска «нетрезв» визуально неразличима.
# Вывод: в рамках данной статистики велосипедисты — самая дисциплинированная группа. Случаи опьянения за рулем велосипеда единичны и не зависят от погодных условий.
# 5. Стаж вождения
# Данные: графики по всем метеогруппам пустые, с пометкой «no data».
# Примечание: информация о стаже вождения велосипедистов не фиксируется в данной базе данных, что характерно для этой категории участников движения.
# 
# **ИТОГ: Велосипедисты — это выраженная «группа риска», где практически каждое происшествие сопряжено с травматизмом. Погода выступает «фильтром» в основном для женщин, тогда как мужчины продолжают движение в любых условиях, сохраняя при этом высокий уровень трезвости.**
# 
# ---
# 
# **ПЕШЕХОД**
# 1. Пол в зависимости от погоды
# Динамика: Это самая изменчивая категория. В облачную погоду мужчин (красный) и женщин (светло-серый) примерно поровну. В ясную погоду доля мужчин возрастает до ~70%. При осадках (дождь/снег) доля мужчин достигает почти 100%.
# Вывод: Женщины-пешеходы проявляют максимальную осторожность и стараются избегать передвижений пешком во время осадков. В плохую погоду основной риск ДТП полностью ложится на мужчин.
# 2. Средства защиты (ремень)
# Статистика: График полностью залит мятным цветом с пометкой «0».
# Примечание: Как и в случае с велосипедистами, это техническая заглушка в шаблоне отчета, так как понятие «ремень безопасности» к пешеходам неприменимо.
# 3. Тяжесть травм
# Распределение: Подавляющее число пострадавших — раненые (светло-желтый). Однако в ясную и облачную погоду виден черный блок — это категория «не пострадал» (около 5–8%).
# Особенность: Доля погибших (бордовый) визуально наиболее заметна в группе «Ясно» (около 5–7%). В условиях осадков смертельных случаев на графике практически не зафиксировано.
# Анализ: Это подтверждает, что в хорошую погоду скорости автомобилей выше, что ведет к более тяжелым последствиям. В дождь/снег водители едут медленнее, и ДТП чаще заканчиваются ранениями, а не гибелью.
# 4. Влияние алкоголя
# Статистика: Абсолютно чистый белый график с пометкой «трезв».
# Вывод: Либо пешеходы — исключительно трезвая категория, либо их состояние опьянения крайне редко фиксируется в протоколах, и их по умолчанию записывают в трезвые.
# 5. Стаж вождения
# Данные: Графики пустые, с пометкой «no data». Информация о наличии водительского удостоверения у пешеходов в данной статистике не учитывается.
# 
# **ИТОГ: Пешеход — группа, где риск гибели выше в хорошую погоду из-за высоких скоростей авто, а риск попасть в ДТП в плохую погоду практически полностью ложится на мужчин.**

# %% [markdown]
# # Аналитический отчет: Детальный анализ групп участников ДТП в зависимости от метеоусловий
# 
# ---
# 
# ## 1. Сводная таблица показателей
# *Данные агрегированы по ключевым категориям участников на основании визуального анализа инфографики.*
# 
# 
# | Группа участников | Пол (доминирующий) | Использование защиты (ремень) | Тяжесть травм (основная категория) | Влияние алкоголя | Стаж вождения (пиковый сегмент) |
# | :--- | :--- | :--- | :--- | :--- | :--- |
# | **Водитель** | **Мужчины (~75%)** | **~65% пристегнуты**, ~35% — нет. | **Низкая:** >70% не пострадали. | **Трезв (>95%)** | **10–20 лет** (~50% ДТП) |
# | **Пассажир** | **Женщины (~70%)** | **~60% пристегнуты**, ~40% — нет. | **Высокая:** >95% ранены. | **Трезв (~100%)** | — (нет данных) |
# | **Велосипедист**| **Мужчины (>80%)** | **0%** (техн. пропуск) | **Критическая:** ~98% ранены. | **Трезв (~100%)** | — (нет данных) |
# | **Пешеход** | **Мужчины (до 100% в дождь)** | **0%** (техн. пропуск) | **Опасная:** Смертность выше в ясную погоду. | **Трезв (~100%)** | — (нет данных) |
# 
# ---
# 
# ## 2. Детальный анализ по группам
# 
# ### 2.1. Водитель
# *   **Гендерный состав:** Мужчины составляют подавляющее большинство во всех сценариях. Погода не влияет на выбор того, кто садится за руль.
# *   **Средства защиты:** Дисциплина использования ремней статична (~65%) и не растет при ухудшении дорожных условий.
# *   **Стаж вождения:** Наибольший риск представляют водители со стажем **10–20 лет**. Погода выступает «фильтром» только для новичков (до 3 лет), которые резко снижают активность в осадки. Опытные водители сохраняют привычный ритм движения, что ведет к инцидентам при плохой видимости.
# 
# ### 2.2. Пассажир
# *   **Гендерный состав:** Стабильная социальная модель — ~70% пассажиров составляют женщины. 
# *   **Травматизм:** Группа крайне уязвима. Если ДТП произошло, более 95% пассажиров получают ранения независимо от погоды.
# *   **Итог:** Группа «Пассажир» максимально инертна к метеоусловиям.
# 
# ### 2.3. Велосипедист
# *   **Уязвимость:** Самая незащищенная группа. Категория «не пострадал» практически отсутствует — любое столкновение ведет к травмам.
# *   **Погодный фактор:** Осадки значительно сокращают долю женщин-велосипедисток, в то время как мужчины продолжают использовать велосипед как транспорт в любых условиях.
# *   **Дисциплина:** Самая трезвая категория участников согласно статистике.
# 
# ### 2.4. Пешеход
# *   **Парадокс погоды:** Риск гибели пешехода выше в **ясную погоду**. Это связано с более высокими скоростями автомобилей на сухом покрытии. В дождь/снег скорости ниже, что снижает летальность, но увеличивает число ранений.
# *   **Гендерный сдвиг:** В облачную погоду распределение по полу 50/50, но при осадках пешеходами в ДТП становятся почти исключительно мужчины.
# 
# ---
# 
# ## 3. Общий аналитический вывод
# Анализ подтверждает, что погодные условия кардинально меняют состояние среды (покрытие, видимость), но практически не влияют на поведенческие паттерны участников (использование ремней, трезвость). 
# 
# 1. **Главная группа риска:** Водители со стажем 10–20 лет, склонные к переоценке своих навыков в сложных метеоусловиях.
# 2. **Инфраструктурный фактор:** Высокая доля ДТП на сухом покрытии в ясную погоду указывает на системные проблемы с превышением скоростного режима и потерей концентрации.
# 3. **Безопасность:** Необходимо усиление мер защиты для «активных» участников (велосипедисты, пешеходы), так как для них метеоусловия лишь меняют тип травм, не снижая общую вероятность их получения.

# %% [markdown]
# #### 3.2.6 Детальный анализ взаимосвязи погоды и недостатков дорог

# %%
# Определяем список колонок с дефектами
fault_columns = [
    'road_marking', 'road_signs', 'street_lighting', 'pavement_defects',
    'winter_conditions', 'traffic_light', 'drainage_system', 'road_narrowing',
    'bus_stop_elements', 'road_works_zone_tsod'
]

# Схлопываем дубликаты участников, оставляя одну строку на одно ДТП
df_unique_dtp = df_final.drop_duplicates(subset=['kart_id'])

# 1. Подготовка данных 
road_weather_analysis = df_unique_dtp.groupby('weather_group')[fault_columns].sum()

# 2. Очистка названий для визуализации (делаем как во втором графике)
clean_road_columns = [c.replace('_', ' ').capitalize() for c in road_weather_analysis.columns]

# 3. Визуализация: Тепловая карта (абсолютные значения)
plt.figure(figsize=(18, 7)) # Приводим к размеру второго графика

sns.heatmap(road_weather_analysis, 
            annot=True, 
            fmt="d",          # Целые числа (библиотека seaborn)
            cmap="YlOrRd",    # Оставляем теплые тона для абсолютных значений
            xticklabels=clean_road_columns)

plt.title('Взаимосвязь погоды и выявленных недостатков дороги (кол-во ДТП)', fontsize=15)
plt.ylabel('Группа погоды', fontsize=12)
plt.xlabel('Тип недостатка дороги', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# 1. Расчет процентов: доля каждого дефекта внутри своей погодной группы
road_weather_pct = road_weather_analysis.div(road_weather_analysis.sum(axis=1), axis=0) * 100

# 2. Визуализация структурной тепловой карты дорожных условий
plt.figure(figsize=(18, 7))

# Очищаем названия колонок (типов недостатков) для осей
clean_road_columns = [c.replace('_', ' ').capitalize() for c in road_weather_pct.columns]

sns.heatmap(road_weather_pct, 
            annot=True, 
            fmt=".1f", # Один знак после запятой
            cmap="YlGnBu", # Единый стиль с предыдущей процентной картой
            xticklabels=clean_road_columns)

plt.title('Структура дорожных недостатков в зависимости от погоды (%)', fontsize=15)
plt.ylabel('Группа погоды')
plt.xlabel('Доля типа дефекта в общем объеме нарушений для данной погоды')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# %% [markdown]
# **Влияние метеоусловий на корреляцию дефектов дорожной инфраструктуры и аварийности**
# 1. Погода как фильтр видимости: Недостатки разметки (Road marking) — доминирующий фактор. В ясную погоду их доля достигает максимума (50,1%). Это подтверждает, что при хорошей видимости и сухом покрытии водители больше полагаются на визуальную навигацию, и любой ее дефект становится критическим триггером.
# 2. Погода как регулятор поведения: Эффект «Парадокса осадков» проявляется в группе «Дождь/Снег». Несмотря на сложные условия, доля дефектов разметки в общей структуре падает до 34,7%. Это связано с тем, что водители снижают скорость и повышают бдительность, компенсируя плохую видимость разметки осторожным вождением.
# 3. Погода как фактор содержания: Доля зимних дефектов (Winter conditions) в структуре нарушений ожидаемо возрастает в 3 раза при переходе от ясной погоды (11,4%) к дождю и снегу (34,3%). Это подчеркивает сложность оперативной очистки дорог в моменты активного выпадения осадков.
# 4. Оценка второстепенных факторов
# Информативность среды: Состояние дорожных знаков (Road signs) и обустройство элементов остановок (Bus stop elements) занимают стабильную долю в структуре нарушений — около 15% и 6,5% соответственно. Максимальная доля дефектов знаков (16,6%) фиксируется при мороси и небольшом снеге, что требует повышенного внимания к их очистке и светоотражающим свойствам в условиях плохой видимости.
# Технологическая устойчивость: Категории Traffic light (светофоры), Drainage system (дренаж) и Road works zone tsod показывают минимальный вклад в общую структуру (менее 1%) во всех погодных сценариях, что свидетельствует о высокой эксплуатационной надежности этих систем.
# 
# **ИТОГ: Статистика подтверждает, что более 60% всех инфраструктурных рисков в любую погоду связаны с дефектами визуального ориентирования (разметка + знаки). При этом плохая погода («Дождь/Снег») смещает акцент контроля с разметки на зимнее содержание, делая эти два фактора критически важными для безопасности в равной степени.**

# %% [markdown]
# #### 3.2.7 Детальный анализ влияния погода и нарушения ПДД

# %%
# 1. Формируем полный список анализируемых колонок
# Колонки из маппера + дополнительные, которые вы указали
additional_cols = [
    'v_pedestrian_rules_total', 
    'v_micromobility_rules_total', 
    'v_police_emergency_total', 
    'v_no_violations_total'
]
driver_violation_cols = [f"{k}_total" for k in violation_map.keys() if k.startswith('v_driver_')]
all_analysis_cols = list(set(driver_violation_cols + additional_cols))

# 2. Фильтруем только водителей
df_drivers = df_final.copy()

# 3. УСТРАНЕНИЕ ДУБЛИКАТОВ 
# Группируем по уникальному водителю в конкретном ДТП.
# Используем .max(), чтобы если нарушение было в одной из строк дублей, оно сохранилось (1).
id_columns = ['kart_id', 'v_id'] 
df_drivers_final = df_drivers.drop_duplicates(subset=id_columns)

df_drivers_unique = df_drivers_final.groupby(id_columns + ['weather_group'])[all_analysis_cols].max().reset_index()

# Проверка количества (для отладки)
print(f"Записей до очистки: {len(df_drivers)}")
print(f"Уникальных водителей: {len(df_drivers_unique)}")

# 4. Агрегация данных по погоде
violation_weather_analysis = df_drivers_unique.groupby('weather_group')[all_analysis_cols].sum()

# 5. Очистка названий столбцов для красивого графика
clean_columns = [
    c.replace('v_driver_', '').replace('v_', '').replace('_total', '').replace('_', ' ').capitalize() 
    for c in violation_weather_analysis.columns
]

# 6. Визуализация: Абсолютные значения
plt.figure(figsize=(20, 8))
sns.heatmap(violation_weather_analysis, 
            annot=True, 
            fmt="g", 
            cmap="YlOrRd", 
            xticklabels=clean_columns)

plt.title('Влияние погоды на структуру ДТП', fontsize=15)
plt.ylabel('Группа погоды')
plt.xlabel('Тип нарушения')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# 7. Визуализация: Процентная структура (доля нарушений в каждой погодной группе)
# Считаем процент от ОБЩЕГО количества водителей в этой погоде
drivers_count_per_weather = df_drivers_unique.groupby('weather_group').size()
violation_pct = violation_weather_analysis.div(drivers_count_per_weather, axis=0) * 100

plt.figure(figsize=(20, 8))
sns.heatmap(violation_pct, 
            annot=True, 
            fmt=".1f", 
            cmap="YlGnBu", 
            xticklabels=clean_columns)

plt.title('Вероятность нарушения при разной погоде (%)', fontsize=15)
plt.ylabel('Группа погоды')
plt.xlabel('Тип нарушения (% от всех водителей в данной погоде)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# %% [markdown]
# **Влияние погодных условий на структуру правонарушений участников ДТП** 
# 
# 1. Доминирующий фактор риска: Нарушение очередности проезда (Priority)
# Во всех погодных сценариях несоблюдение приоритета остается самым массовым активным правонарушением. Максимальная вероятность ошибки зафиксирована в условиях «Ясно» (15,7%) и «Облачно» (15,4%). Снижение доли этого нарушения в «Дождь/Снег» до 12,7% указывает на то, что при осадках водители проявляют вынужденную осторожность на перекрестках, в то время как хорошая видимость провоцирует излишнюю уверенность и опасную спешку.
# 2. Специфика группы «Осадки» (Дождь/Снег): Скорость и Пешеходы
# В условиях активных осадков наблюдается аномальный рост вероятности нарушений скоростного режима и правил для пешеходов:
# Скорость (Speed): Риск возрастает до 8,4% (против 5,8% в ясную погоду). Это подтверждает, что значительная часть водителей не адаптирует скорость к ухудшению сцепления с дорогой.
# Пешеходы (Pedestrian rules): Вероятность нарушений достигает максимума — 11,6% (в «Ясно» — 8,5%). Плохая видимость из-за осадков в сочетании со спешкой пешеходов делает эту категорию критической зоной риска.
# 3. Скрытие с места ДТП (Escape) и Техническое состояние (Tech)
# Скрытие (Escape): Вероятность оставления места ДТП практически неизменна и составляет около 7,4% – 7,6% вне зависимости от погоды. Это доказывает, что попытка избежать ответственности — фактор поведенческий, а не ситуативный.
# Техсостояние (Tech): В группе «Дождь/Снег» доля неисправностей выше (4,4%), чем в ясную погоду (3,4%). Осадки обостряют технические огрехи автомобиля (износ шин, плохая работа стеклоочистителей), превращая их в прямую причину аварии.
# 4. Маневрирование против Дистанции: ошибки «хорошей» погоды
# Данные подтверждают: во всех группах вероятность ошибок при маневрировании (Maneuver) выше, чем нарушений дистанции (Distance).
# В ясную погоду разрыв наиболее заметен: 8,0% (маневры) против 5,5% (дистанция).
# В «Облачно» риск составляет 7,4% против 5,4%.
# Это доказывает, что активные действия (повороты, перестроения) представляют большую угрозу, чем несоблюдение интервала, особенно в условиях хорошей видимости, когда водители склонны к более агрессивному вождению.
# 5. Парадокс пассивной безопасности (Safety)
# Доля нарушений, связанных с ремнями и креслами (Safety), минимальна: от 0,8% до 1,2%. Вопреки гипотезе, в «Облачно» (1,0%) она ниже, чем в «Ясно» (1,2%). Пренебрежение средствами защиты остается редким, но стабильным фактором, не зависящим от метеоусловий.
# 6. Контрольный показатель: Отсутствие нарушений (No violations)
# Доля участников, не совершивших правонарушений, в «Дождь/Снег» (44,1%) выше, чем в «Ясно» (42,3%). Это важный индикатор: в сложных условиях либо возрастает доля «случайных» пострадавших участников, либо общая бдительность водителей на дороге парадоксально повышается.
# 
# **ИТОГ: Группы «Ясно/Облачно» выступают зоной максимального риска для нарушений приоритета (~15,7%), провоцируя ошибки в базовой дисциплине ПДД. Группа «Осадки» смещает структуру нарушений в сторону неадекватного выбора скорости (рост до 8,4%) и рисков для пешеходов, однако фатальной ошибкой в любую погоду остается неумение водителей правильно определять приоритетность движения.**

# %% [markdown]
# #### 3.2.8 Взаимосвязь погоды и особенностей ТС

# %%
# 1. ПОДГОТОВКА ДАННЫХ (Все ТС через фильтр водителей)
# Фильтруем по роли, чтобы учесть каждое ТС, участвующее в инциденте
df_all_v = df_final[df_final['p_role'].astype(str).str.lower().str.strip() == 'водитель'].copy()

# 2. РАСЧЕТ СТАТИСТИКИ (Кросс-табуляция в %)
ct_type = pd.crosstab(df_all_v['weather_group'], df_all_v['vehicle_category'], normalize='index') * 100
ct_color = pd.crosstab(df_all_v['weather_group'], df_all_v['v_color_clean'], normalize='index') * 100
ct_age = pd.crosstab(df_all_v['weather_group'], df_all_v['vehicle_age_group'], normalize='index') * 100

# 3. ВИЗУАЛИЗАЦИЯ
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12))

# График 1: Категории ТС
ct_type.plot(kind='barh', stacked=True, colormap='viridis', width=0.5, ax=ax1)
ax1.set_title('Влияние погоды на структуру категорий всех ТС в ДТП', fontsize=14, fontweight='bold')
ax1.set_xlabel('Доля в группе (%)')
ax1.set_ylabel('')
ax1.legend(title='Категория ТС', bbox_to_anchor=(1.02, 1), loc='upper left')
ax1.grid(axis='x', linestyle='--', alpha=0.6)

# График 2: Цвета ТС (Ваша палитра без изменений)
v_colors_palette = [
    '#FFFFFF', '#2C2C2C', '#D3D3D3', '#FFFF00', '#2E7D32', '#5D4037', 
    '#D32F2F', '#E91E63', '#FF9800', '#9E9E9E', '#1976D2', '#7B1FA2', '#000000'
]
ct_color.plot(kind='barh', stacked=True, color=v_colors_palette, edgecolor='gray', width=0.5, ax=ax2)
ax2.set_title('Влияние погоды на видимость (Цвет всех ТС)', fontsize=14, fontweight='bold')
ax2.set_xlabel('Доля в группе (%)')
ax2.set_ylabel('')
ax2.legend(title='Цвет ТС', bbox_to_anchor=(1.02, 1), loc='upper left')
ax2.grid(axis='x', linestyle='--', alpha=0.6)

# График 3: Возрастные группы
ct_age.plot(kind='barh', stacked=True, colormap='magma', edgecolor='gray', width=0.5, ax=ax3)
ax3.set_title('Влияние погоды на возраст всех ТС', fontsize=14, fontweight='bold')
ax3.set_xlabel('Доля в группе (%)')
ax3.set_ylabel('')
ax3.legend(title='Возрастная группа', bbox_to_anchor=(1.02, 1), loc='upper left') # Исправлено название
ax3.grid(axis='x', linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()

# 4. Аналитический вывод
print(f"Всего проанализировано транспортных средств: {len(df_all_v)}")

# 5. Краткий аналитический вывод в консоль
print("АНАЛИЗ СТРУКТУРЫ ПАРКА В ДТП:")
for weather in ct_type.index:
    top_cat = ct_type.loc[weather].idxmax()
    top_val = ct_type.loc[weather].max()
    print(f"  - В группе [{weather}]: доминирует '{top_cat}' ({top_val:.1f}%)")
    
print("АНАЛИЗ ЦВЕТОВОЙ ПАЛИТРЫ ПАРКА В ДТП:")
for weather in ct_color.index:
    top_cat = ct_color.loc[weather].idxmax()
    top_val = ct_color.loc[weather].max()
    print(f"  - В группе [{weather}]: доминирует '{top_cat}' ({top_val:.1f}%)")

print("АНАЛИЗ ВОЗРАСТА ПАРКА В ДТП:")
for weather in ct_age.index:
    top_cat = ct_age.loc[weather].idxmax()
    top_val = ct_age.loc[weather].max()
    print(f"  - В группе [{weather}]: доминирует '{top_cat}' ({top_val:.1f}%)")

# %% [markdown]
# **Влияния погодных условий на технические характеристики транспортных средств (ТС) в моментах ДТП.**
# 
# 1. Структура категорий транспортных средств:
# Доминирование легкового транспорта: Во всех погодных группах («Ясно», «Облачно», «Осадки») легковые автомобили (голубой сегмент) составляют основной массив участников — порядка 75–80%. Стабильность этой доли подтверждает, что структура автопарка в ДТП продиктована общей интенсивностью движения, а не выбором типа транспорта под погоду.
# Общественный транспорт: Занимает стабильную долю (ярко-зеленый сегмент) — около 5–7%. Его присутствие в статистике неизменно при любой погоде, так как рейсовый транспорт работает по графику и не может быть отменен из-за метеоусловий.
# Грузовой транспорт: Стабильно входит в тройку лидеров (темно-фиолетовый сегмент), составляя примерно 5–6%. При переходе к группе «Дождь/Снег» доля грузовиков незначительно расширяется относительно легковых авто, что объясняется сохранением объемов коммерческих перевозок на фоне снижения активности частных водителей.
# Мототехника: Демонстрирует самую высокую метеозависимость. В группе «Ясно» сегмент наиболее выражен, а в условиях осадков он визуально стремится к нулю. Это подтверждает массовый отказ мотоциклистов от поездок в дождь/снег из-за критических рисков безопасности.
# 2. Видимость и цвет кузова:
# Преобладание «маскировочных» цветов: Основную долю во всех группах занимают белый, серый, черный и синий цвета (суммарно более 75%).
# Фактор риска: В условиях «Облачно» и «Дождь/Снег» серые (серый сегмент) и черные (черный сегмент) ТС создают повышенную опасность из-за низкого контраста с мокрым асфальтом и пасмурным небом. Белый цвет (белый сегмент), являясь самым массовым (~28%), также теряет свои сигнальные свойства во время снегопада.
# Безопасность ярких цветов: Доля ярких машин (красный, желтый, оранжевый) минимальна и составляет суммарно около 7–10%. Это косвенно подтверждает их более высокую пассивную безопасность: яркий автомобиль лучше заметен в потоке в любых метеоусловиях.
# 3. Возрастная структура автопарка:
# Лидеры аварийности: Самые массовые группы — «Старые (16–25 лет)» (желтый сегмент, ~35–40%) и «Подержанные (8–15 лет)» (пурпурный сегмент, ~30–35%). Суммарно на автомобили старше 8 лет приходится более 70% всех ДТП.
# Новые автомобили: Доля ТС возрастом до 3 лет (темно-синий сегмент) минимальна (около 3–5%). Это объясняется как меньшей концентрацией новых машин в потоке, так и наличием у них систем активной безопасности (ABS, ESP), которые предотвращают инциденты в сложных условиях.
# Технический риск: Высокая концентрация старых и раритетных (25+ лет) машин в группе «Осадки» указывает на дополнительный риск: отсутствие современных систем помощи водителю на возрастных авто в условиях плохого сцепления с дорогой значительно повышает вероятность аварии.
# 
# **ИТОГ: Погода практически не меняет качественный состав участников ДТП, но обостряет системные риски.
# Основной массив аварий при любой погоде генерируют подержанные и старые легковые автомобили (старше 8 лет), лишенные современных систем активной безопасности.
# В условиях плохой видимости риск усиливается из-за преобладания в потоке машин нейтральных и темных оттенков (серый, черный), которые сливаются с дорожной средой.
# Статистика подтверждает: наиболее защищенным в любую погоду остается водитель нового автомобиля яркого цвета, в то время как владельцы старых машин «маскировочных» оттенков находятся в зоне максимального риска.**

# %% [markdown]
# #### 3.2.9 ТОП-10 марок ТС попавших в ДТП с учетом погодных условий

# %%
# 1. Фильтрация
df_plot = df_final[
    (df_final['p_role'] == 'водитель') & 
    (df_final['v_marka'].str.strip().fillna('') != '')
].copy()
df_plot['v_marka'] = df_plot['v_marka'].str.upper().str.strip()

# 2. Получаем уникальные группы из столбца weather_group
weather_types = df_plot['weather_group'].dropna().unique().tolist()

# 3. Визуализация 2x2
fig, axes = plt.subplots(2, 2, figsize=(22, 16))
axes_flat = axes.flatten()
sns.set_style("whitegrid")

for i in range(4):
    ax = axes_flat[i]
    
    if i < len(weather_types):
        weather = weather_types[i]
        
        # ГРУППИРОВКА ЗДЕСЬ: фильтруем по погоде и считаем топ-10 марок
        top_data = (
            df_plot[df_plot['weather_group'] == weather]['v_marka']
            .value_counts()
            .head(10)
        )
        
        if not top_data.empty:
            sns.barplot(
                x=top_data.values, 
                y=top_data.index, 
                hue=top_data.index,
                ax=ax, 
                palette="magma",
                legend=False
            )
            
            # Оформление заголовка (название группы с эмодзи)
            ax.set_title(f"Погода: {weather}", fontsize=18, fontweight='bold')
            ax.set_ylabel('')
            ax.set_xlabel('Кол-во ДТП', fontsize=12)
            
            # Добавляем цифры в конец баров
            max_val = top_data.values.max()
            ax.set_xlim(0, max_val * 1.2) # Запас 20% под цифры
            for j, val in enumerate(top_data.values):
                ax.text(val + (max_val * 0.01), j, int(val), va='center', fontsize=13, fontweight='bold')
    else:
        # Если групп вдруг меньше 4, убираем пустую область
        fig.delaxes(ax)

plt.suptitle('Топ-10 марок ТС в ДТП по типам погодных условий', fontsize=24, y=1.02)
plt.tight_layout(pad=4.0)
plt.show()

# %% [markdown]
# **Анализ структуры аварийности по маркам ТС в зависимости от погоды**
# 
# 1. Доминирование лидеров рынка
# Статистика: Во всех четырех метеогруппах неизменными лидерами являются Toyota и ВАЗ.
# Анализ: В группе «Облачно» зафиксирован абсолютный пик: 6 742 случая у Toyota и 5 667 у ВАЗ. Это подтверждает, что аварийность напрямую коррелирует с численностью данных марок в региональном автопарке. При этом стабильно высокая доля ВАЗ во всех условиях подчеркивает фактор технической уязвимости старого модельного ряда.
# 2. Аномалии группы «Дождь/Снег»
# Смена позиций: В условиях интенсивных осадков марка ГАЗ (123 случая) поднимается на 5-е место, обходя Hyundai (117) и Honda (107). Также в топе закрепляется Mazda (64).
# Вывод: Рост относительной доли «возрастных» и коммерческих машин (ВАЗ, ГАЗ) при осадках подтверждает гипотезу о техническом риске. Отсутствие систем ABS и ESP на старых моделях лишает водителей возможности стабилизировать ТС на скользком покрытии, превращая техническое несовершенство в ключевой фактор аварийности.
# 3. «Облачно» как период максимального риска
# Статистика: Общее количество ДТП в облачную погоду (пик — более 6 700 у лидера) в 1,7 раза выше, чем в ясную, и почти в 16 раз выше, чем в периоды сильных осадков.
# Анализ: Это связано с высокой интенсивностью трафика при обманчивом ощущении безопасности. В отличие от группы «Дождь/Снег», где водители ведут себя осторожнее, пасмурная погода притупляет бдительность, не снижая при этом плотность потока.
# 4. Стабильность среднего сегмента
# Наблюдение: Марки Nissan, Hyundai, KIA и Honda во всех сценариях (кроме экстремальных осадков) уверенно занимают места с 3-го по 6-е.
# Вывод: Иномарки массового сегмента демонстрируют более предсказуемую динамику аварийности, которая снижается пропорционально ухудшению погоды, в то время как отечественные марки (ВАЗ, ГАЗ) сохраняют высокую долю инцидентов даже при минимальном трафике.
# 
# **ИТОГ: Региональная статистика ДТП отражает специфику автопарка, смещенного в сторону старых моделей. Погодный фактор (осадки/облачность) выступает катализатором аварийности: отсутствие систем активной безопасности на массовых старых авто делает их эксплуатацию в сложных условиях критически опасной.**

# %% [markdown]
# #### 3.2.10 Расчет Относительного Риска (Relative Risk) возникновения ДТП в определенную погоду

# %%
# 1. Подготовка: Убеждаемся, что dtp_hour_utc и timestamp имеют один формат (datetime64)
df_final['dtp_hour_utc'] = pd.to_datetime(df_final['dtp_hour_utc'])
df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp'])

# 2. Маппинг погоды для ИСХОДНОЙ таблицы метеоданных (Экспозиция)
# Важно: используем weather_description из таблицы погоды, а не из ДТП
df_weather['weather_clean_w'] = (
    df_weather['weather_description']
    .astype(str)
    .str.replace(r'[^\w\s]', '', regex=True)
    .str.lower()
    .str.strip()
)
df_weather['weather_group_w'] = df_weather['weather_clean_w'].map(weather_map)

# 3. Считаем экспозицию (сколько часов в сумме по городам была каждая погода)
weather_hours = df_weather['weather_group_w'].value_counts()

# 4. Считаем количество УНИКАЛЬНЫХ ДТП для каждой группы
# Используем уже созданный ранее в df_final столбец weather_group
dtp_counts = df_final.groupby('weather_group')['kart_id'].nunique()

# 5. Сборка Risk DataFrame
risk_df = pd.DataFrame({
    'dtp_count': dtp_counts,
    'total_weather_hours': weather_hours
}).fillna(0)

# Исключаем группы с нулевыми часами (чтобы не делить на 0)
risk_df = risk_df[risk_df['total_weather_hours'] > 0].copy()

# 6. Расчет Индекса Риска (ДТП на 1 час "присутствия" погоды)
risk_df['risk_index'] = risk_df['dtp_count'] / risk_df['total_weather_hours']

# 7. Расчет Относительного Риска (Baseline — "Ясно ☀️")
# Обычно за базу берут ясную погоду, чтобы понять, во сколько раз опаснее дождь
baseline_weather = 'Ясно ☀️' 

if baseline_weather in risk_df.index:
    baseline_val = risk_df.loc[baseline_weather, 'risk_index']
    risk_df['relative_risk'] = risk_df['risk_index'] / baseline_val
else:
    # Если "Ясно" нет, берем самую частую погоду
    baseline_val = risk_df['risk_index'].mean()
    risk_df['relative_risk'] = risk_df['risk_index'] / baseline_val

# Сортировка по убыванию опасности
risk_df = risk_df.sort_values('relative_risk', ascending=False)

print("ИНДЕКСЫ РИСКА (Относительно ясной погоды):")
print(risk_df[['dtp_count', 'total_weather_hours', 'relative_risk']].round(2))

# %% [markdown]
# **Основные выводы по «Индексу опасности»:**
# 
# 1. Лидеры риска: Осадки средней и высокой интенсивности (R = 1.14). Полноценный дождь и снег являются самыми опасными условиями. Вероятность попасть в ДТП в такую погоду на 14% выше, чем в ясный день. Это подтверждает, что ухудшение видимости в сочетании с мокрым или заснеженным покрытием — главный фактор аварийности.
# 2. Коварство малых осадков (R = 1.12). Морось и небольшой снег лишь незначительно уступают ливням по уровню риска. Вероятность ДТП здесь на 12% выше базового уровня. Это подтверждает гипотезу об «эффекте мыла»: тонкая водяная пленка и дорожная пыль делают дорогу предельно скользкой, при этом водители не снижают скорость так радикально, как при сильном шторме.
# 3. Парадокс облачности (R = 0.99). Облачная погода статистически оказалась даже чуть безопаснее идеального ясного неба (на 1%). Вероятно, отсутствие слепящего солнца и стабильное освещение без резких теней позволяют водителям лучше концентрироваться на дорожной обстановке.
# 4. Фактор «Ясного неба» как точка отсчета (R = 1.00). Принятое за эталон ясное небо демонстрирует средний уровень риска. Несмотря на идеальное сцепление, этот показатель может подогреваться излишней уверенностью водителей и высокими скоростями.
# 
# **ИТОГ: Хотя основной объем ДТП в абсолютных числах генерирует облачная погода (~28,5 тыс. случаев) из-за своей продолжительности, максимальная плотность риска приходится на периоды осадков. Статистически, любой выезд на дорогу во время дождя или снега повышает шансы на инцидент на 12–14% по сравнению с «идеальными» погодными условиями.**

# %% [markdown]
# ---
# 
# ## 4. Итоговый вывод и рекомендации

# %% [markdown]
# ### Итоговый вывод: «Системная ловушка адаптации»
# 
# **Главный вывод исследования**: Погода не убивает сама по себе — она лишь обнажает скрытые дефекты системы «Человек — Машина — Инфраструктура».
# 
# Ключевой конфликт заключается в том, что среда меняется динамично, а поведение участников остается статичным.
# - Математика риска (Индекс R): Самыми опасными являются не штормы, а осадки любой интенсивности. Даже небольшая морось повышает вероятность ДТП на 12% (R=1.12), а полноценный дождь — на 14% (R=1.14). Это «эффект мыла»: сцепление падает резко, а водители не снижают скорость так же радикально, как в ливень.
# - Психологический парадокс опыта: Основную массу ДТП генерируют водители со стажем 10–20 лет. В отличие от новичков, они не «фильтруются» погодой (не отказываются от поездок), а их избыточная самоуверенность ведет к росту нарушений скорости в дождь до 12,6%.
# - Технологический разрыв: Более 70% аварий совершаются на автомобилях старше 8–15 лет (лидеры — ВАЗ, старые Toyota). Отсутствие систем ABS/ESP на таком автопарке превращает любую ошибку в управлении при осадках в неконтролируемый занос.
# - Визуальная маскировка: 75% машин имеют «грязные» цвета (серый, черный, белый). В пасмурную погоду (пик по числу ДТП) они сливаются с фоном, что провоцирует фатальные ошибки приоритета проезда (20,7%) — водители просто не видят друг друга.
# - Социальная несправедливость: Водитель (мужчина) в 70% случаев остается невредим, в то время как пассажир (женщина) и пешеход становятся жертвами в 95% случаев из-за чужих ошибок и системного игнорирования ремней безопасности (~40% не пристегнуты).

# %% [markdown]
# ### Комплексные рекомендации
# 
# 1. Для Госавтоинспекции и надзорных органов:
# - Контроль «Опытных»: Сместить фокус с «новичков» на водителей со стажем 10+ лет. Усилить контроль скорости и дистанции в первый час осадков, когда риск подскакивает на 12%, а водители еще не адаптировались.
# - Рейды «Ремень и Пассажир»: Усилить проверки использования ремней именно в непогоду. Пассажиры (особенно женщины) должны быть информированы, что они — главная группа риска при столкновениях (50% всех ДТП).
# - Световой регламент: Жесткий контроль использования ближнего света (не ДХО) в облачную погоду, чтобы выделить «серый» автопарк на сером фоне дороги.
# 2. Для дорожных служб и муниципалитетов:
# - Приоритет визуальной навигации: В ясную погоду «убивает» плохая разметка (50% рисков). Необходимо обновлять её до пика летнего сезона. В облачность — обеспечить контрастность знаков.
# - Превентивное содержание: Учитывая 3-кратный рост дефектов в осадках, необходима обработка дорог при +1...+2°C, не дожидаясь гололеда (критическая точка 0°C).
# - Освещение «Серых зон»: Раннее включение фонарей в пасмурные дни для снижения ошибок при оценке приоритета на перекрестках.
# 3. Для автопроизводителей и дилеров (Социальная позиция):
# - Пропаганда систем безопасности: Продвижение систем ABS/ESP/ADAS как критически важных факторов выживания в регионах с высокой долей осадков и облачности.
# 4. Для участников движения (Пропаганда):
# - Кампания «Стаж не заменяет физику»: Разрушение мифа о том, что большой опыт вождения помогает на скользкой дороге без систем стабилизации.
# - Активный пассажир: Стимулирование пассажиров брать на себя роль контроля безопасности в салоне (ремень, скорость, фары).

# %% [markdown]
# ---
# 
# ## 5. Загрузка итоговых таблиц в базу

# %%
# Словари со списками колонок
schema = {
    'accidents': ['kart_id', 'city_name', 'dtp_type_group', 'pog_total', 'ran_total', 'vehicles_count', 'participants_count', 
                  'dtp_hour_utc', 'weather_from_gibdd'],
    'location': ['kart_id', 'district', 'city_name', 'latitude', 'longitude'],
    'road': ['kart_id', 'road_category', 'road_condition_group', 'road_marking', 'road_signs', 'street_lighting', 'pavement_defects', 
             'winter_conditions', 'traffic_light', 'drainage_system', 'road_narrowing', 'bus_stop_elements', 
             'road_works_zone_tsod', 'faults_consolidated', 'light_condition'],
    'vehicles': ['kart_id', 'v_id', 'v_marka', 'v_model', 'v_ownership_origin', 'v_ownership_detail', 'vehicle_category', 
                 'v_color_clean', 'vehicle_age_group'],
    'participants': ['kart_id', 'v_id', 'p_role', 'p_gender', 'experience_group', 'p_severity_clean', 'p_alcohol_clean', 
                     'p_safety_belt', 'violation_consolidated', 'v_driver_status_total', 
                     'v_driver_docs_total', 'v_driver_safety_total', 'v_driver_escape_total', 'v_driver_speed_total', 'v_driver_tech_total', 
                     'v_driver_overtaking_total', 'v_driver_maneuver_total', 'v_driver_priority_total', 'v_driver_distance_total', 
                     'v_driver_heavy_cargo_total', 'v_driver_dangerous_total', 'v_driver_other_total', 'v_pedestrian_rules_total', 
                     'v_micromobility_rules_total', 'v_police_emergency_total', 'v_no_violations_total', 
                    ]
}

# Создание датафреймов
dfs = {name: df_final[cols].drop_duplicates() for name, cols in schema.items()}

# 1. Добавляем таблицу городов из df_cities_filter
dfs['cities'] = df_cities_filter.drop_duplicates()

# 2. Список колонок для конвертации в Boolean
bool_cols = [
    'road_marking', 'road_signs', 'street_lighting', 'pavement_defects', 
    'winter_conditions', 'traffic_light', 'drainage_system', 'road_narrowing', 
    'bus_stop_elements', 'road_works_zone_tsod', 'p_safety_belt'
] + [col for col in dfs['participants'].columns if col.startswith('v_')]

# 3. Порядок загрузки (ВАЖНО: сначала главные таблицы)
upload_order = ['cities', 'accidents', 'location', 'road', 'vehicles', 'participants']

# --- 4. ФУНКЦИЯ ЗАГРУЗКИ ---
def run_upsert():
    for name in upload_order:
        if name not in dfs: continue
        
        df = dfs[name].copy()
        print(f"\n🚀 Upsert в таблицу: {name} ({len(df)} строк)")

        # 1. Исправленная логика BOOLEAN (НЕ трогаем v_id и kart_id)
        current_bool_cols = [c for c in df.columns if c in bool_cols and c not in ['v_id', 'kart_id']]
        for col in current_bool_cols:
            df[col] = df[col].fillna(0).astype(bool)

        # 2. Конвертация Datetime
        for col in df.select_dtypes(include=['datetime64']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        # 3. Жёсткая очистка от дублей по ключам для предотвращения ошибки ON CONFLICT
        if name == 'vehicles':
            df = df.drop_duplicates(subset=['kart_id', 'v_id'])
        elif name == 'accidents' or name == 'cities':
            df = df.drop_duplicates(subset=['kart_id' if name=='accidents' else 'id'])

        # 4. Исправленная замена NaN (решает ошибку 22P02 с Token "NaN")
        # Сначала меняем типы float-NaN, потом все остальное
        df = df.replace({np.nan: None, float('nan'): None, 'NaN': None, 'nan': None})
        records = df.to_dict(orient='records')
        
        chunk_size = 1000 # Чуть меньше для надежности
        total = len(records)
        
        for i in range(0, total, chunk_size):
            chunk = records[i : i + chunk_size]
            try:
                supabase.table(name).upsert(chunk).execute()
                print(f"   Прогресс: {min(i + chunk_size, total)} / {total}", end='\r')
            except Exception as e:
                # Выводим детальную ошибку для отладки
                print(f"\n❌ Ошибка в {name} [строки {i}:{i+chunk_size}]: {e}")
                # Если это критическая таблица - выходим
                if name in ['accidents', 'cities']: return 
                break 
        print(f"\n✅ Таблица {name} синхронизирована!")

# Запуск
run_upsert()
print("\n🏁 Все данные перенесены!")

# %%



