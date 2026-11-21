import asyncio
import html as html_lib
import json
import logging
import os
import re
import time
import urllib.parse
try:
    from curl_cffi.requests import AsyncSession
except ImportError:
    AsyncSession = None

try:
    from aiogram import Bot, Dispatcher, F
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
except ImportError:
    Bot = Dispatcher = F = None
    InlineKeyboardMarkup = InlineKeyboardButton = CallbackQuery = None

BOT_TOKEN = "8593240850:AAGqei6Qv-DQnx5IZurU9VEriw84zKwrXYg"
CHAT_ID = 374188835

BASE_DIR = os.getenv("AVITO_DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")
PRICE_CACHE_FILE = os.path.join(BASE_DIR, "price_cache.json")
ITEMS_STORE_FILE = os.path.join(BASE_DIR, "items_store.json")
DEALS_FILE = os.path.join(BASE_DIR, "deals.json")
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
BLACKLIST_FILE = os.path.join(BASE_DIR, "blacklist.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
PROXIES_FILE = os.path.join(BASE_DIR, "proxies.txt")
CITIES_CACHE_FILE = os.path.join(BASE_DIR, "cities_cache.json")

bot = Bot(token=BOT_TOKEN) if Bot else None
dp = Dispatcher() if Dispatcher else None
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WORKER] %(message)s")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/html, application/xhtml+xml, */*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.avito.ru/"
}

# Расширенная база 120+ ключевых городов и регионов РФ для мгновенного резолва
KNOWN_CITIES = {
    "москва": 637640,
    "санкт-петербург": 653240,
    "питер": 653240,
    "спб": 653240,
    "новосибирск": 641780,
    "екатеринбург": 651470,
    "казань": 646390,
    "нижний новгород": 641570,
    "челябинск": 656240,
    "самара": 648170,
    "омск": 642450,
    "ростов-на-дону": 647030,
    "уфа": 622830,
    "красноярск": 633350,
    "воронеж": 625810,
    "пермь": 643350,
    "волгоград": 625070,
    "краснодар": 632660,
    "саратов": 649470,
    "тюмень": 655450,
    "тольятти": 649030,
    "барнаул": 621540,
    "ижевск": 654940,
    "ульяновск": 655180,
    "иркутск": 630130,
    "хабаровск": 657150,
    "ярославль": 658600,
    "владивосток": 644560,
    "махачкала": 624100,
    "томск": 657310,
    "оренбург": 642340,
    "кемерово": 631270,
    "новокузнецк": 631620,
    "рязань": 647460,
    "набережные челны": 646460,
    "астрахань": 620950,
    "пенза": 643190,
    "киров": 631720,
    "липецк": 636390,
    "чебоксары": 658090,
    "калининград": 630730,
    "тула": 654520,
    "курск": 635830,
    "ставрополь": 651810,
    "сочи": 634450,
    "тверь": 653940,
    "магнитогорск": 656360,
    "иваново": 628920,
    "брянск": 622350,
    "белгород": 621930,
    "сургут": 655820,
    "владимир": 624520,
    "чита": 627190,
    "архангельск": 620430,
    "калуга": 630890,
    "смоленск": 650530,
    "волжский": 625140,
    "курган": 635460,
    "череповец": 625470,
    "орёл": 642140,
    "орел": 642140,
    "саранск": 638840,
    "вологда": 625380,
    "якутск": 648070,
    "владикавказ": 650990,
    "подольск": 639380,
    "мурманск": 638970,
    "тамбов": 653770,
    "стерлитамак": 623100,
    "петрозаводск": 630980,
    "кострома": 632340,
    "нижневартовск": 655750,
    "новороссийск": 633100,
    "йошкар-ола": 637170,
    "таганрог": 647240,
    "комсомольск-на-амуре": 657190,
    "сыктывкар": 633910,
    "нальчик": 629630,
    "шахты": 647270,
    "дзержинск": 641620,
    "братск": 630170,
    "орск": 642370,
    "ангарск": 630160,
    "благовещенск": 620130,
    "энгельс": 649510,
    "старый оскол": 622080,
    "великий новгород": 640720,
    "псков": 644070,
    "бийск": 621570,
    "прокопьевск": 631650,
    "южно-сахалинск": 648530,
    "балаково": 649480,
    "армавир": 632730,
    "рыбинск": 658630,
    "северодвинск": 620540,
    "абакан": 656710,
    "петропавловск-камчатский": 631070,
    "норильск": 633450,
    "уссурийск": 644670,
    "волгодонск": 647080,
    "сызрань": 648280,
    "каменск-уральский": 651520,
    "новочеркасск": 647160,
    "златоуст": 656300,
    "альметьевск": 646320,
    "миасс": 656410,
    "салават": 623060,
    "пятигорск": 651910,
    "копейск": 656330,
    "находка": 644630,
    "рубцовск": 621640,
    "майкоп": 620020,
    "ковров": 624560,
    "березники": 643400,
    "кисловодск": 651870,
    "нефтекамск": 622990,
    "нефтеюганск": 655730,
    "новочебоксарск": 658110,
    "дербент": 624130,
    "батайск": 647060,
    "кызыл": 654850,
    "черкесск": 631160,
    "первоуральск": 651560,
    "назрань": 629940,
    "каспийск": 624160,
    "новомосковск": 654570,
    "ессентуки": 651840,
    "муром": 624600
}

ACCESSORY_STOP_WORDS = [
    "чехол", "стекло", "коробка", "запчаст", "ремонт", "кабель", "блок",
    "зарядк", "аккумулятор", "дисплей", "пленка", "ремешок", "корпус", "плата",
    "watch", "часы", "airpods", "наушник", "переходник", "адаптер", "шнур"
]

MODEL_MIN_THRESHOLDS = {
    "11": 10500,
    "11 pro": 15000,
    "11 pro max": 19000,
    "12": 17000,
    "12 mini": 14000,
    "12 pro": 26000,
    "12 pro max": 36000,
    "13": 28000,
    "13 mini": 23000,
    "13 pro": 38000,
    "13 pro max": 45000,
    "14": 38000,
    "14 plus": 41000,
    "14 pro": 52000,
    "14 pro max": 59000,
    "15": 48000,
    "15 pro": 65000,
    "15 pro max": 75000,
    "16": 62000,
    "16 pro": 85000,
    "16 pro max": 99000
}

current_proxy_index = 0

def load_proxies():
    if not os.path.exists(PROXIES_FILE):
        return []
    try:
        with open(PROXIES_FILE, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    except Exception:
        return []

def get_next_proxy():
    global current_proxy_index
    proxies = load_proxies()
    if not proxies:
        return None
    proxy = proxies[current_proxy_index % len(proxies)]
    current_proxy_index = (current_proxy_index + 1) % len(proxies)
    return proxy

def get_dynamic_min_price(model_name: str, fallback_min: int = 3000) -> int:
    name = (model_name or "").lower().strip()
    for m_key in sorted(MODEL_MIN_THRESHOLDS.keys(), key=len, reverse=True):
        if m_key in name:
            return MODEL_MIN_THRESHOLDS[m_key]
    return fallback_min

def load_tasks():
    if not os.path.exists(TASKS_FILE): return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f: json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception: pass

def load_json(fpath, default=None):
    if default is None: default = {}
    if not os.path.exists(fpath): return default
    try:
        with open(fpath, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def save_json(fpath, data):
    try:
        with open(fpath, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

def calculate_trimmed_mean(prices, trim_percent: float = 0.20):
    if not prices: return 0
    valid_p = sorted([p for p in prices if p > 0])
    n = len(valid_p)
    if n < 3: return int(sum(valid_p) / n)
    k = max(1, int(n * trim_percent))
    core = valid_p[k:-k] if (n - 2 * k) > 0 else valid_p
    return int(sum(core) / len(core))

def calculate_smart_market_prices(items: list, min_threshold: int = 3000) -> dict:
    """
    Интеллектуальный расчет рыночной цены на основе открытых объявлений:
    1. Исключает битые и дефектные устройства (экран, iCloud, без Face ID, под ремонт).
    2. Исключает подозрительно дешевые (запчасти, чехлы, фейки) ниже min_threshold.
    3. Группирует открытые объявления по объемам памяти (128 ГБ, 256 ГБ, 512 ГБ).
    4. Для каждого объема памяти и для общего рынка рассчитывает 20% trimmed mean.
    """
    if not items:
        return {"avg_price": 0, "by_memory": {}, "sample_size": 0}

    # Отбираем исправные лоты без критических дефектов
    clean_items = []
    for it in items:
        p = it.get("price", 0)
        if p < min_threshold:
            continue
        defects = it.get("defects", [])
        if any("🚫" in d or "💥" in d or "⚠️" in d or "🔧" in d for d in defects):
            continue
        clean_items.append(it)

    # Если после фильтрации дефектов выборка слишком мала, берем хотя бы без блокировок и разбитых экранов
    if len(clean_items) < 3:
        clean_items = [
            it for it in items
            if it.get("price", 0) >= min_threshold and not any("🚫" in d or "💥" in d for d in it.get("defects", []))
        ]

    if not clean_items:
        clean_items = [it for it in items if it.get("price", 0) >= min_threshold]

    if not clean_items:
        return {"avg_price": 0, "by_memory": {}, "sample_size": 0}

    # Группировка по памяти
    memory_groups = {}
    for it in clean_items:
        mem = it.get("memory") or "Основная"
        memory_groups.setdefault(mem, []).append(it["price"])

    by_memory = {}
    for mem, prices in memory_groups.items():
        if len(prices) >= 2:
            by_memory[mem] = calculate_trimmed_mean(prices, 0.20)
        elif prices:
            by_memory[mem] = prices[0]

    all_prices = [it["price"] for it in clean_items]
    overall_avg = calculate_trimmed_mean(all_prices, 0.20)

    # Базовая цена (если есть группа 128 ГБ - ориентируемся на неё, иначе общий срез)
    base_avg = by_memory.get("128 ГБ") or overall_avg

    return {
        "avg_price": base_avg or overall_avg,
        "by_memory": by_memory,
        "sample_size": len(clean_items)
    }

def extract_memory_from_text(text):
    if not text: return None
    m = re.search(r"\b(64|128|256|512|1024)\s*(?:gb|гб|тб|tb)?\b", text.lower())
    if m:
        val = m.group(1)
        return "1 ТБ" if val == "1024" else f"{val} ГБ"
    return None

def analyze_condition_and_defects(title: str, text: str = "") -> dict:
    full_text = f"{title} {text}".lower()
    defects = []
    conditions = []
    
    # 1. Face ID / Touch ID
    if any(k in full_text for k in ["без face id", "не работает face", "face id off", "фейс не работает", "без фейс", "face id не", "не работает touch", "без touch id"]):
        defects.append("⚠️ Не работает Face ID")
    elif "face id работает" in full_text or "face id ok" in full_text:
        conditions.append("✅ Face ID работает")
        
    # 2. True Tone
    if any(k in full_text for k in ["без true tone", "нет true tone", "трутон не работает", "без трутон", "true tone off"]):
        defects.append("⚠️ Без True Tone")
    elif "true tone" in full_text and "работает" in full_text:
        conditions.append("✅ True Tone")
        
    # 3. Screen / Body condition
    if any(k in full_text for k in ["разбит", "трещина", "треснут", "скол на экране", "битый экран", "паутинка", "полосы на экране", "пятно на матрице", "полоса"]):
        defects.append("💥 Разбит / Трещины")
    elif any(k in full_text for k in ["идеал", "в идеале", "как новый", "состояние нового", "без сколов", "без царапин"]):
        conditions.append("✨ Идеальное состояние")
        
    # 4. Screen Replacement
    if any(k in full_text for k in ["менялся дисплей", "заменен экран", "экран меняли", "копия дисплея", "ошибка экрана"]):
        defects.append("🔧 Менян экран")
        
    # 5. Lock / iCloud / MDM / R-Sim
    if any(k in full_text for k in ["icloud", "айклауд", "пароль на экране", "mdm", "обход", "заблокирован", "r-sim", "р-сим", "демо", "demo"]):
        defects.append("🚫 Блокировка / iCloud / R-Sim")
        
    # 6. Battery Health
    m_bat = re.search(r"\b(?:акб|батаре[яеи]|емкость|состояние|battery|health)[:\s]*(\d{2,3})\s*%", full_text)
    if m_bat:
        pct = int(m_bat.group(1))
        if 50 <= pct <= 100:
            if pct >= 85:
                conditions.append(f"🔋 АКБ {pct}%")
            elif pct >= 75:
                conditions.append(f"🟡 АКБ {pct}%")
            else:
                defects.append(f"🪫 АКБ {pct}% (сервис)")
                
    # 7. Bundle / Box / Warranty
    if any(k in full_text for k in ["полный комплект", "родная коробка", "с коробкой", "коробка чек"]):
        conditions.append("📦 Полный комплект")
    if any(k in full_text for k in ["есть чек", "с чеком", "чек из магазина"]):
        conditions.append("🧾 Есть чек")
    if any(k in full_text for k in ["на гарантии", "гарантия apple", "гарантия до"]):
        conditions.append("🛡 На гарантии")
        
    is_critical = any("🚫" in d or "💥" in d for d in defects)
    return {
        "defects": defects,
        "conditions": conditions,
        "is_critical": is_critical
    }

def extract_image_url(raw_item: dict) -> str:
    images = raw_item.get("images") or []
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict):
            for res_key in ["1280x960", "864x648", "640x480", "432x324"]:
                if res_key in first and first[res_key]:
                    return first[res_key]
            for v in first.values():
                if isinstance(v, str) and v.startswith("http"):
                    return v
        elif isinstance(first, str) and first.startswith("http"):
            return first
    img = raw_item.get("image")
    if isinstance(img, dict):
        for res_key in ["1280x960", "640x480", "432x324"]:
            if res_key in img and img[res_key]:
                return img[res_key]
        for v in img.values():
            if isinstance(v, str) and v.startswith("http"):
                return v
    elif isinstance(img, str) and img.startswith("http"):
        return img
    return ""

def get_iphone_series(text: str):
    t = text.lower()
    m = re.search(r"\b(?:iphone|айфон)\s*(?:apple)?\s*(se(?:\s*\d{4})?|xr|xs|x|1[1-7]|[6-8])\b", t)
    if m:
        val = m.group(1).replace(" ", "")
        if val.startswith("se"): return "se"
        return val
    m2 = re.search(r"\b(se|xr|xs|x|1[1-7]|[6-8])\s*(?:pro\s*max|promax|pro|plus|mini|макс|про)\b", t)
    if m2:
        return m2.group(1)
    return None

def get_iphone_modifier(text: str) -> str:
    t = text.lower().replace("-", " ").replace("_", " ")
    if "pro max" in t or "про макс" in t or "promax" in t:
        return "pro_max"
    if "max" in t or "макс" in t:
        return "max"
    if "pro" in t or "про" in t:
        return "pro"
    if "plus" in t or "плюс" in t:
        return "plus"
    if "mini" in t or "мини" in t:
        return "mini"
    return "base"

def is_matching_model(target_model: str, title: str, url_path: str = "") -> bool:
    if not target_model or not title:
        return False
        
    t = title.lower()
    u = (url_path or "").lower().replace("_", " ")
    combined = f"{t} {u}"
    
    # 1. Reject accessories and parts
    if any(sw in combined for sw in ACCESSORY_STOP_WORDS):
        return False
        
    m = target_model.lower().strip()
    
    # 2. iPhone specific strict matching
    if "iphone" in m or "айфон" in m:
        if "iphone" not in combined and "айфон" not in combined:
            return False
            
        target_series = get_iphone_series(m)
        title_series = get_iphone_series(t)
        
        if target_series and title_series and target_series != title_series:
            return False
        if target_series and not title_series:
            return False
            
        target_mod = get_iphone_modifier(m)
        title_mod = get_iphone_modifier(t)
        if target_mod != title_mod:
            return False
            
        if url_path:
            url_series = get_iphone_series(u)
            if target_series and url_series and target_series != url_series:
                return False
            url_mod = get_iphone_modifier(u)
            if target_mod != url_mod:
                return False
            
        # Check memory if explicitly requested in target
        target_mem = extract_memory_from_text(m)
        title_mem = extract_memory_from_text(t) or extract_memory_from_text(u)
        if target_mem and title_mem and target_mem != title_mem:
            return False
            
        return True
        
    # Non-iPhone matching (Samsung, Xiaomi, etc.)
    words = [w for w in re.split(r"\s+", m) if len(w) > 1]
    return all(w in combined for w in words)

async def resolve_city_location_id(city_name: str, session: AsyncSession, proxy: str = None) -> int:
    """
    Разрешает ID локации Авито с постоянным дисковым кэшированием (поддержка любого города РФ).
    Возвращает 0, если поиск по всей России.
    """
    cleaned = (city_name or "").strip().lower()
    
    # Определение режима "Вся Россия"
    if cleaned in ["вся россия", "россия", "рф", "все города", "all", "любой", ""]:
        return 0

    # 1. Быстрый поиск в KNOWN_CITIES
    for k, v in KNOWN_CITIES.items():
        if k == cleaned or cleaned == k:
            return v
    for k, v in KNOWN_CITIES.items():
        if k in cleaned or cleaned in k:
            return v

    # 2. Постоянный дисковый кэш
    cache = load_json(CITIES_CACHE_FILE, {})
    if cleaned in cache:
        return cache[cleaned]

    # 3. Динамический запрос к Авито API slocations
    try:
        url = f"https://www.avito.ru/web/1/slocations?q={urllib.parse.quote(city_name)}"
        req_kw = {"headers": HEADERS, "impersonate": "safari15_5", "timeout": 8}
        if proxy: req_kw["proxy"] = proxy
        r = await session.get(url, **req_kw)
        if r.status_code == 200:
            data = r.json()
            locations = data.get("result", {}).get("locations", [])
            for loc in locations:
                names = loc.get("names", {})
                for n in names.values():
                    if cleaned in n.lower():
                        loc_id = loc.get("id")
                        cache[cleaned] = loc_id
                        save_json(CITIES_CACHE_FILE, cache)
                        logging.info(f"Город '{city_name}' определен через API Авито (ID: {loc_id}) и сохранен в кэш.")
                        return loc_id
            if locations:
                loc_id = locations[-1].get("id")
                cache[cleaned] = loc_id
                save_json(CITIES_CACHE_FILE, cache)
                return loc_id
    except Exception as e:
        logging.warning(f"Location resolve error for '{city_name}': {e}")
        
    return 637640  # Дефолт к Москве только при фатальной недоступности

async def fetch_avito_items(model_query: str, city_name: str, min_p: int, max_p: int, session: AsyncSession = None):
    """
    Сканирование Авито с сортировкой по дате (&s=104) для мгновенного нахождения свежих лотов.
    """
    items = []
    seen_ids = set()
    b_list = load_json(BLACKLIST_FILE, [])
    blacklisted_ids = {str(b.get("id")) for b in b_list}
    blacklisted_names = {b.get("name", "").lower() for b in b_list if b.get("name")}
    
    cfg = load_json(SETTINGS_FILE, {})
    filter_critical_defects = cfg.get("filter_defects", True)

    proxy = get_next_proxy()
    if proxy:
        logging.info(f"Используется прокси: {proxy}")
        
    own_session = session is None
    s = session if session is not None else AsyncSession()

    try:
        loc_id = await resolve_city_location_id(city_name, s, proxy)
        
        # Формирование URL: при loc_id == 0 ищется по всей России без привязки к городу
        loc_param = f"locationId={loc_id}&" if loc_id > 0 else ""
        q_encoded = urllib.parse.quote(model_query)
        
        # ВАЖНО: &s=104 гарантирует сортировку "По дате (сначала свежие)",
        # благодаря чему новое объявление находится мгновенно в ту же секунду!
        url = f"https://www.avito.ru/web/1/main/items?{loc_param}categoryId=84&q={q_encoded}&s=104"
        
        req_kw = {"headers": HEADERS, "impersonate": "safari15_5", "timeout": 10}
        if proxy: req_kw["proxy"] = proxy
        
        r = await s.get(url, **req_kw)
        if r.status_code == 429:
            logging.warning(f"Avito 429 на '{model_query}' ({city_name}). Ротация прокси...")
            proxy = get_next_proxy()
            await asyncio.sleep(1.5)
        elif r.status_code == 200:
            data = r.json()
            raw_items = data.get("items", [])
            for raw in raw_items:
                iid = str(raw.get("id", ""))
                if not iid or iid == "0" or iid in seen_ids or iid in blacklisted_ids:
                    continue
                
                seller_info = raw.get("seller") or {}
                seller_name = (seller_info.get("name") or "").lower()
                if seller_name and any(bn in seller_name for bn in blacklisted_names):
                    continue

                title = raw.get("title", "").strip()
                if not title: continue
                
                raw_url = raw.get("urlPath") or ""
                clean_path = raw_url.split("?")[0] if raw_url else ""

                # Строгая проверка соответствия модели
                if not is_matching_model(model_query, title, clean_path):
                    continue
                
                # Анализ дефектов и состояния
                inspect_res = analyze_condition_and_defects(title, clean_path)
                if filter_critical_defects and inspect_res["is_critical"]:
                    continue

                # Извлечение цены
                price_dict = raw.get("priceDetailed", {})
                p_str = price_dict.get("string", "")
                raw_nums = re.findall(r"\d+", p_str.replace("\xa0", "").replace(" ", ""))
                if not raw_nums: continue
                price_val = int(raw_nums[0])
                
                if not (min_p <= price_val <= max_p):
                    continue
                
                seen_ids.add(iid)
                if clean_path:
                    full_url = f"https://www.avito.ru{clean_path}" if clean_path.startswith("/") else f"https://www.avito.ru/{clean_path}"
                else:
                    full_url = f"https://www.avito.ru/{iid}"
                    
                memory = extract_memory_from_text(title) or extract_memory_from_text(clean_path)
                img_url = extract_image_url(raw)
                
                # Извлечение реального города лота (если поиск велся по всей России)
                item_city = city_name
                if loc_id == 0:
                    geo = raw.get("geo", {})
                    item_city = geo.get("geoReferences", [{}])[0].get("content") or geo.get("formattedAddress") or "Россия"
                    item_city = item_city.split(",")[0].strip()

                items.append({
                    "id": iid,
                    "title": title,
                    "price": price_val,
                    "url": full_url,
                    "image": img_url,
                    "memory": memory,
                    "city": item_city,
                    "defects": inspect_res["defects"],
                    "conditions": inspect_res["conditions"],
                    "seller": seller_info.get("name", "Частное лицо")
                })
    except Exception as e:
        logging.warning(f"Error fetching Avito items for '{model_query}' ({city_name}): {e}")
    finally:
        if own_session:
            await s.close()
            
    return items

async def send_deal_notification(it: dict, task_name: str, price_num: int, prev_price: int, avg_p: int, thread_id: int = None, is_drop: bool = False):
    iid = it["id"]
    cfg = load_json(SETTINGS_FILE, {})
    send_photo_enabled = cfg.get("send_photos", True)
    
    diff = avg_p - price_num if avg_p > 0 else 0
    diff_pct = int((diff / avg_p) * 100) if avg_p > 0 else 0

    if is_drop:
        drop_pct = int(((prev_price - price_num) / prev_price) * 100) if prev_price > 0 else 0
        badge = f"📉 <b>СНИЖЕНИЕ ЦЕНЫ НА {drop_pct}%!</b>"
        price_line = f"💵 <b>Цена: <s>{prev_price:,} ₽</s> ➔ {price_num:,} ₽</b>".replace(",", " ")
    elif diff > 0 and diff_pct >= 5:
        badge = f"🔥 <b>ВЫГОДА +{diff:,} ₽ (-{diff_pct}%)</b>".replace(",", " ")
        price_line = f"💵 <b>Цена: {price_num:,} ₽</b>".replace(",", " ")
    else:
        badge = "⚡️ <b>НОВОЕ ПРЕДЛОЖЕНИЕ</b>"
        price_line = f"💵 <b>Цена: {price_num:,} ₽</b>".replace(",", " ")

    msg = f"{badge}\n\n"
    msg += f"📱 <b>{html_lib.escape(it['title'])}</b>\n"
    msg += f"{price_line}\n"
    
    mem_tag = f" ({it['memory']})" if it.get("memory") else ""
    if avg_p > 0 and diff > 0:
        msg += f"📊 Рыночная{mem_tag}: ~{avg_p:,} ₽ | Профит: <b>+{diff:,} ₽</b>\n".replace(",", " ")
    elif avg_p > 0:
        msg += f"📊 Рыночная{mem_tag}: ~{avg_p:,} ₽\n".replace(",", " ")
        
    if it.get("city"):
        msg += f"📍 Город: {html_lib.escape(it['city'])}\n"
    if it.get("seller"):
        msg += f"👤 Продавец: {html_lib.escape(it['seller'])}\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="↗️ На Авито", url=it["url"]),
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_{iid}"),
            InlineKeyboardButton(text="🧮 Маржа", callback_data=f"calc_{iid}")
        ]
    ])

    img_url = it.get("image")
    sent = False
    
    if send_photo_enabled and img_url and img_url.startswith("http"):
        try:
            send_kw = {
                "chat_id": CHAT_ID,
                "photo": img_url,
                "caption": msg,
                "parse_mode": "HTML",
                "reply_markup": kb
            }
            if thread_id: send_kw["message_thread_id"] = thread_id
            await bot.send_photo(**send_kw)
            sent = True
        except Exception as e:
            logging.warning(f"send_photo failed, falling back to send_message: {e}")
            sent = False
            
    if not sent:
        try:
            send_kw = {
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "reply_markup": kb
            }
            if thread_id: send_kw["message_thread_id"] = thread_id
            await bot.send_message(**send_kw)
        except Exception as e:
            logging.warning(f"Telegram notification error: {e}")

async def process_task(task, first_run, price_cache, store, session: AsyncSession = None):
    model = task.get("model", "")
    city = task.get("city", "Вся Россия")
    thread_id = task.get("thread_id")
    task_name = f"{model} ({city})"
    
    custom_min = task.get("min_price")
    min_p = custom_min if (custom_min and custom_min > 3000) else get_dynamic_min_price(model)
    max_p = task.get("max_price", 150000)
    
    logging.info(f"Сканирование Avito: {task_name} [Мин: {min_p} ₽, Макс: {max_p} ₽]")
    items = await fetch_avito_items(model, city, min_p, max_p, session=session)
    
    if not items:
        logging.info(f"Объявлений не найдено для {task_name}")
        return
    
    logging.info(f"Найдено {len(items)} открытых объявлений для {task_name}")
    
    # ИНТЕЛЛЕКТУАЛЬНЫЙ РАСЧЕТ РЫНОЧНОЙ ЦЕНЫ НА ОСНОВЕ ОТКРЫТЫХ ОБЪЯВЛЕНИЙ
    market_data = calculate_smart_market_prices(items, min_threshold=min_p)
    computed_avg = market_data["avg_price"]
    by_memory = market_data["by_memory"]
    
    auto_market_enabled = task.get("auto_market", True)
    prev_avg = task.get("avg_price", 0)
    
    # Автоматическое обновление рыночной цены
    if auto_market_enabled or prev_avg == 0:
        if computed_avg > 0:
            task["avg_price"] = computed_avg
            task["market_by_memory"] = by_memory
            if abs(computed_avg - prev_avg) >= 500:
                logging.info(f"Рыночная цена для '{task_name}' обновлена: ~{computed_avg:,} ₽ (выборка: {market_data['sample_size']} шт.)".replace(",", " "))
    
    task_avg = task.get("avg_price", computed_avg)

    # Присваиваем каждому лоту персональную рыночную цену с учетом памяти
    for it in items:
        it["task_name"] = task_name
        it_mem = it.get("memory")
        item_market = by_memory.get(it_mem) if (it_mem and it_mem in by_memory) else task_avg
        it["avg_price"] = item_market
        
        if item_market > 0 and it["price"] < item_market:
            it["profit"] = item_market - it["price"]
        else:
            it["profit"] = 0

    store[task_name] = items
    save_json(ITEMS_STORE_FILE, store)

    # Обновление горячих сделок (Deals)
    try:
        all_deals = load_json(DEALS_FILE, [])
        if not isinstance(all_deals, list): all_deals = []
        filtered_deals = [d for d in all_deals if d.get("task_name") != task_name]
        
        for it in items:
            market_p = it.get("avg_price", task_avg)
            if market_p > 0 and it["price"] < market_p:
                diff = market_p - it["price"]
                diff_pct = int((diff / market_p) * 100)
                if diff_pct >= 5:
                    filtered_deals.append({
                        "id": it["id"],
                        "task_name": task_name,
                        "title": it["title"],
                        "city": it.get("city") or city,
                        "price": it["price"],
                        "avg_price": market_p,
                        "profit": diff,
                        "url": it["url"],
                        "image": it.get("image", ""),
                        "memory": it.get("memory", ""),
                        "seller": it.get("seller", "")
                    })
        
        filtered_deals.sort(key=lambda x: x["profit"], reverse=True)
        save_json(DEALS_FILE, filtered_deals[:60])
    except Exception as e:
        logging.warning(f"Deals update error: {e}")
    
    if first_run:
        for it in items: price_cache[it["id"]] = it["price"]
        save_json(PRICE_CACHE_FILE, price_cache)
        return
        
    # Проверка на снижение цены и появление новых объявлений
    cfg = load_json(SETTINGS_FILE, {})
    profit_threshold = cfg.get("profit_threshold", 0)  # 0 = уведомлять обо всех новых
    notify_all_new = cfg.get("notify_all_new", True)

    for it in reversed(items):
        iid = it["id"]
        price_num = it["price"]
        prev_price = price_cache.get(iid)
        item_avg_p = it.get("avg_price", task_avg)
        
        # 1. Снижение цены у существующего лота
        if prev_price and (prev_price - price_num) >= 500 and int(((prev_price - price_num) / prev_price) * 100) >= 3:
            price_cache[iid] = price_num
            save_json(PRICE_CACHE_FILE, price_cache)
            await send_deal_notification(it, task_name, price_num, prev_price, item_avg_p, thread_id, is_drop=True)
            await asyncio.sleep(0.3)
            
        # 2. Новое объявление
        elif iid not in price_cache:
            price_cache[iid] = price_num
            save_json(PRICE_CACHE_FILE, price_cache)
            diff = item_avg_p - price_num if item_avg_p > 0 else 0
            diff_pct = int((diff / item_avg_p) * 100) if item_avg_p > 0 else 0
            
            # Уведомление: отправляется мгновенно, если включен notify_all_new или цена выгодна
            if notify_all_new or item_avg_p == 0 or diff_pct >= profit_threshold:
                await send_deal_notification(it, task_name, price_num, prev_price or price_num, item_avg_p, thread_id, is_drop=False)
                await asyncio.sleep(0.3)

# ==============================================================================
# Telegram Bot Callback Query Handlers
# ==============================================================================
def on_callback_query(*args, **kwargs):
    if dp and hasattr(dp, "callback_query"):
        return dp.callback_query(*args, **kwargs)
    return lambda fn: fn

@on_callback_query(F.data.startswith("fav_") if F else "fav_")
async def handle_callback_favorite(callback: CallbackQuery):
    iid = callback.data.replace("fav_", "").strip()
    favs = load_json(FAVORITES_FILE, [])
    
    if any(str(f.get("id")) == iid for f in favs):
        await callback.answer("⭐ Уже в Избранном!", show_alert=False)
        return
        
    all_deals = load_json(DEALS_FILE, [])
    item = next((d for d in all_deals if str(d.get("id")) == iid), None)
    
    if not item:
        items_store = load_json(ITEMS_STORE_FILE, {})
        for t_items in items_store.values():
            for it in t_items:
                if str(it.get("id")) == iid:
                    item = it
                    break
            if item: break

    if item:
        fav_entry = {
            "id": iid,
            "title": item.get("title", "iPhone"),
            "price": item.get("price", 0),
            "avg_price": item.get("avg_price", 0),
            "profit": item.get("profit", 0),
            "url": item.get("url", f"https://www.avito.ru/{iid}"),
            "image": item.get("image", ""),
            "city": item.get("city", ""),
            "memory": item.get("memory", ""),
            "conditions": item.get("conditions", []),
            "defects": item.get("defects", []),
            "status": "saved",
            "note": "",
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        favs.insert(0, fav_entry)
        save_json(FAVORITES_FILE, favs)
        await callback.answer("⭐ Сохранено в Избранное!", show_alert=False)
    else:
        await callback.answer("⭐ Товар добавлен в Избранное!", show_alert=False)

@on_callback_query(F.data.startswith("bl_") if F else "bl_")
async def handle_callback_blacklist(callback: CallbackQuery):
    iid = callback.data.replace("bl_", "").strip()
    b_list = load_json(BLACKLIST_FILE, [])
    
    deals = load_json(DEALS_FILE, [])
    item = next((d for d in deals if str(d.get("id")) == iid), None)
    seller_name = item.get("seller", "") if item else ""
    
    deals = [d for d in deals if str(d.get("id")) != iid]
    save_json(DEALS_FILE, deals)
    
    entry = {
        "id": iid,
        "name": seller_name,
        "title": item.get("title", "") if item else f"Лот #{iid}",
        "reason": "Заблокирован пользователем через Telegram",
        "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    b_list.insert(0, entry)
    save_json(BLACKLIST_FILE, b_list)
    await callback.answer(f"🚫 Добавлено в Чёрный список!", show_alert=True)

@on_callback_query(F.data.startswith("calc_") if F else "calc_")
async def handle_callback_calculator(callback: CallbackQuery):
    iid = callback.data.replace("calc_", "").strip()
    all_deals = load_json(DEALS_FILE, [])
    item = next((d for d in all_deals if str(d.get("id")) == iid), None)
    if item:
        p = item.get("price", 0)
        avg = item.get("avg_price", 0)
        profit = avg - p if avg > p else 0
        roi = int((profit / p) * 100) if p > 0 else 0
        await callback.answer(f"Прибыль: +{profit:,} ₽ ({roi}% ROI)".replace(",", " "), show_alert=True)
    else:
        await callback.answer("Откройте калькулятор маржи в Mini App!", show_alert=True)

async def start_telegram_polling():
    try:
        logging.info("Telegram Dispatcher polling запущен для кнопок Избранного и ЧС.")
        await dp.start_polling(bot, allowed_updates=["callback_query", "message"])
    except Exception as e:
        logging.warning(f"Telegram polling warning: {e}")

async def main(once: bool = False):
    first_run = True
    price_cache = load_json(PRICE_CACHE_FILE, {})
    store = load_json(ITEMS_STORE_FILE, {})
    logging.info(f"Фоновый радар Avito запущен {'(однократный скан)' if once else ''}!")
    
    if not once:
        asyncio.create_task(start_telegram_polling())
    
    # Семафор конкурентности для параллельного сканирования нескольких городов/задач
    sem = asyncio.Semaphore(3)

    while True:
        tasks = load_tasks()
        cfg = load_json(SETTINGS_FILE, {})
        scan_interval = cfg.get("scan_interval", 6)
        
        tasks_modified = False

        async with AsyncSession() as shared_session:
            async def run_single_task(t):
                nonlocal tasks_modified
                async with sem:
                    try:
                        old_p = t.get("avg_price")
                        await process_task(t, first_run, price_cache, store, session=shared_session)
                        if t.get("avg_price") != old_p:
                            tasks_modified = True
                    except Exception as e:
                        logging.error(f"Ошибка в задаче '{t.get('title')}': {e}")
                    await asyncio.sleep(0.8)

            # Параллельный батчевый опрос всех задач
            await asyncio.gather(*(run_single_task(t) for t in tasks))
            
        # Автосохранение обновленных рыночных цен в tasks.json
        if tasks_modified or first_run:
            save_tasks(tasks)
            
        if first_run:
            first_run = False
            lines = [f"• {t.get('model')} ({t.get('city')}): ~{t.get('avg_price', 0):,} ₽".replace(",", " ") for t in tasks]
            msg = "🟢 <b>Мониторинг Avito запущен!</b>\n\n" + "\n".join(lines)
            try: await bot.send_message(CHAT_ID, msg, parse_mode="HTML")
            except Exception: pass
            
        if once:
            logging.info("Однократное сканирование успешно завершено.")
            break
            
        # Настраиваемая быстрая пауза между полными кругами
        await asyncio.sleep(max(3.0, float(scan_interval)))

if __name__ == "__main__":
    import sys
    is_once = "--once" in sys.argv or "-o" in sys.argv
    asyncio.run(main(once=is_once))
