"""
=============================================================================
🌽 Corn Multi-Factory Comparison & Profit Optimization System
(ระบบเปรียบเทียบกำไรและจัดการสูตรโรงงานข้าวโพด)
พัฒนาด้วย Python & Flet Framework (Mobile-First Web App)
ออกแบบพิเศษสำหรับคุณแม่ - ตัวหนังสือใหญ่ อ่านง่าย สบายตา สีคอนทราสต์สูง
คำนวณเปรียบเทียบทุกโรงงานพร้อมกันแบบเรียลไทม์เพื่อหา "โรงงานที่ทำกำไรสูงสุด"
พร้อมระบบเพิ่ม/แก้ไข/ลบสูตรโรงงานได้เองอย่างอิสระ บันทึกถาวรด้วย Storage
=============================================================================
"""

import sys

# บังคับใช้ UTF-8 เพื่อป้องกัน UnicodeEncodeError จาก Emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import flet as ft
import asyncio
import json
import os
import shutil
import socket
from datetime import datetime
from typing import List, Dict, Any, Optional


# =============================================================================
# 1. ตารางมาตรฐานหักความชื้นหลัก (MASTER MOISTURE SHRINKAGE TABLE)
# =============================================================================

MASTER_MOISTURE_TABLE: Dict[int, Dict[str, float]] = {
    35: {"dry_pct": 69.5, "broken_pct": 4.5, "dust_pct": 0.5, "good_pct": 64.5},
    34: {"dry_pct": 71.0, "broken_pct": 4.5, "dust_pct": 0.5, "good_pct": 66.0},
    33: {"dry_pct": 72.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 68.5},
    32: {"dry_pct": 73.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 69.5},
    31: {"dry_pct": 74.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 70.5},
    30: {"dry_pct": 75.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 71.5},
    29: {"dry_pct": 76.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 72.5},
    28: {"dry_pct": 77.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 73.5},
    27: {"dry_pct": 78.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 74.5},
    26: {"dry_pct": 79.5, "broken_pct": 3.5, "dust_pct": 0.5, "good_pct": 75.5},
    25: {"dry_pct": 80.5, "broken_pct": 2.5, "dust_pct": 0.5, "good_pct": 77.5},
    24: {"dry_pct": 81.5, "broken_pct": 2.5, "dust_pct": 0.5, "good_pct": 78.5},
    23: {"dry_pct": 82.5, "broken_pct": 2.5, "dust_pct": 0.5, "good_pct": 79.5},
    22: {"dry_pct": 83.5, "broken_pct": 2.5, "dust_pct": 0.5, "good_pct": 80.5},
    21: {"dry_pct": 84.5, "broken_pct": 2.5, "dust_pct": 0.5, "good_pct": 81.5},
    20: {"dry_pct": 85.5, "broken_pct": 2.5, "dust_pct": 0.5, "good_pct": 82.5},
}

DEFAULT_FACTORIES: List[Dict[str, Any]] = [
    {
        "id": "cp",
        "name": "CP (ซีพี)",
        "moisture_bias": 0.0,        # ไบแอส 0.0 (ตรงตามตารางหลัก)
        "req_sifting": True,         # ร่อนคัดแยก
        "transport_rate": 0.15,      # ค่าขนส่ง 0.15 ฿/กก.
        "default_price": 11.20,
        "color": "#C2410C",
        "bg_color": "#FFEDD5",
        "emoji": "🏢",
        "is_default": True,
    },
    {
        "id": "kaona",
        "name": "ก้าวหน้าอาหารสัตว์",
        "moisture_bias": 0.0,        # ไบแอส 0.0 (ตรงตามตารางหลัก)
        "req_sifting": True,         # ร่อนคัดแยก
        "transport_rate": 0.15,      # ค่าขนส่ง 0.15 ฿/กก.
        "default_price": 11.20,
        "color": "#059669",
        "bg_color": "#D1FAE5",
        "emoji": "🌽",
        "is_default": True,
    },
    {
        "id": "betagro",
        "name": "Betagro (เบทาโกร)",
        "moisture_bias": -0.5,       # ไบแอส -0.5 (เหลือน้ำหนักเพิ่ม 0.5%)
        "req_sifting": False,        # ไม่ร่อน (เม็ดเต็ม 100%)
        "transport_rate": 0.35,      # ค่าขนส่ง 0.35 ฿/กก.
        "default_price": 11.00,
        "color": "#0369A1",
        "bg_color": "#E0F2FE",
        "emoji": "🏭",
        "is_default": True,
    },
    {
        "id": "sunfeed",
        "name": "Sunfeed (ซันฟีด)",
        "moisture_bias": 0.0,        # ไบแอส 0.0
        "req_sifting": False,        # ไม่ร่อน
        "transport_rate": 0.40,      # ค่าขนส่ง 0.40 ฿/กก.
        "default_price": 11.10,
        "color": "#D97706",
        "bg_color": "#FEF3C7",
        "emoji": "🌾",
        "is_default": True,
    },
]


# =============================================================================
# 2. ระบบจัดการการบันทึกข้อมูลโรงงานและการตั้งค่าผู้ใช้ (STORAGE & PREFERENCES)
# =============================================================================
#
# ข้อมูลถูกเก็บ 2 ชั้น เพื่อไม่ให้สูตรโรงงานที่แก้ไว้หายเวลา deploy ขึ้นคลาวด์ใหม่
#
#   ชั้นที่ 1 : ไฟล์ JSON ใน DATA_DIR
#              - รันที่บ้าน  -> เก็บข้างไฟล์ app.py ตามปกติ
#              - รันบนคลาวด์ -> ผูก Persistent Disk ไว้ที่ /var/data แล้วระบบจะย้ายไปเก็บที่นั่นเอง
#
#   ชั้นที่ 2 : Client Storage ของเบราว์เซอร์ (เก็บที่เครื่องคุณแม่ ไม่ได้อยู่บนเซิร์ฟเวอร์)
#              - รอดจากการ deploy ใหม่เสมอ แม้ใช้ Render แบบ Free ที่ล้างดิสก์ทุกครั้ง
#
# ลำดับการอ่านตอนเปิดแอป : ชั้นที่ 2 -> ชั้นที่ 1 -> ค่าเริ่มต้นในโค้ด
# ทุกครั้งที่กดบันทึก จะเขียนลงทั้งสองชั้นพร้อมกัน
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ตำแหน่งที่คลาวด์ mount Persistent Disk ไว้ (จะมีอยู่จริงก็ต่อเมื่อผูกดิสก์แล้วเท่านั้น)
CLOUD_DISK_PATHS = ("/var/data", "/data")

# ชื่อไฟล์ข้อมูลทั้งหมดที่ต้องตามไปอยู่ใน DATA_DIR
PREFS_FILENAME = "user_preferences.json"
FACTORIES_FILENAME = "factories_config.json"


def _resolve_data_dir() -> str:
    """
    หาโฟลเดอร์สำหรับเก็บไฟล์ข้อมูล โดยเลือกที่ที่ "รอดจากการ deploy" ก่อนเสมอ

    ลำดับการเลือก:
      1. ตัวแปรสภาพแวดล้อม CORN_DATA_DIR (ตั้งเองได้ ถ้าอยากกำหนดตำแหน่งเอง)
      2. /var/data หรือ /data ถ้ามีอยู่จริงและเขียนได้ (คือผูก Persistent Disk ไว้)
      3. โฟลเดอร์เดียวกับ app.py (โหมดรันที่บ้าน)
    """
    for path in (os.environ.get("CORN_DATA_DIR"), *CLOUD_DISK_PATHS):
        if path and os.path.isdir(path) and os.access(path, os.W_OK):
            return path
    return BASE_DIR


DATA_DIR = _resolve_data_dir()


def _data_path(filename: str) -> str:
    """
    คืนพาธเต็มของไฟล์ข้อมูลใน DATA_DIR

    ถ้าเพิ่งผูกดิสก์ใหม่ (ดิสก์ยังว่าง) จะคัดลอกไฟล์ตั้งต้นที่มากับโค้ดไปให้ครั้งแรก
    เพื่อให้สูตรโรงงานที่เคยตั้งไว้ไม่หายตอนย้ายที่เก็บ
    """
    target = os.path.join(DATA_DIR, filename)
    if DATA_DIR != BASE_DIR and not os.path.exists(target):
        seed = os.path.join(BASE_DIR, filename)
        if os.path.exists(seed):
            try:
                shutil.copyfile(seed, target)
                print(f"[Storage] คัดลอกไฟล์ตั้งต้น {filename} ไปยัง {DATA_DIR}")
            except Exception as err:
                print(f"[Storage] คัดลอกไฟล์ตั้งต้น {filename} ไม่สำเร็จ: {err}")
    return target


def _write_json_atomic(path: str, payload: Any) -> bool:
    """
    เขียนไฟล์ JSON แบบ atomic คือเขียนลงไฟล์ชั่วคราวให้เสร็จก่อน แล้วค่อยสลับชื่อทับของเดิม
    ถ้าไฟดับหรือปิดเครื่องกลางคัน ไฟล์ข้อมูลเดิมจะยังอยู่ครบ ไม่พังกลางทาง
    """
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        return True
    except Exception as err:
        print(f"[Storage] บันทึก {os.path.basename(path)} ไม่สำเร็จ: {err}")
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return False


def _read_json(path: str) -> Optional[Any]:
    """อ่านไฟล์ JSON คืน None ถ้าไม่มีไฟล์หรือไฟล์เสีย"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as err:
        print(f"[Storage] อ่าน {os.path.basename(path)} ไม่สำเร็จ: {err}")
        return None


# -----------------------------------------------------------------------------
# ชั้นที่ 2 : Client Storage ของเบราว์เซอร์
# -----------------------------------------------------------------------------
# ทุกฟังก์ชันในส่วนนี้เป็น async เพราะต้องวิ่งไปคุยกับเบราว์เซอร์ปลายทางจริง ๆ
# และทุกฟังก์ชัน "ห้ามโยน error ออกมา" เด็ดขาด เพราะถ้าชั้นนี้ใช้ไม่ได้
# แอปต้องยังทำงานต่อได้ตามปกติด้วยไฟล์ในชั้นที่ 1 เหมือนเดิม
# -----------------------------------------------------------------------------

CLIENT_KEY_FACTORIES = "corn.factories.v3"
CLIENT_KEY_PREFS = "corn.prefs.v1"

# จำนวนครั้งและระยะเวลาที่ยอมรอให้เบราว์เซอร์ผูก service เข้ามา (รวมราว 1.8 วินาที)
_CLIENT_READY_ATTEMPTS = 12
_CLIENT_READY_DELAY = 0.15

# เก็บ service ของแต่ละหน้าเว็บไว้ เพราะ Flet ถือ service ด้วย weak reference
# ถ้าไม่ถือตัวแปรไว้เอง มันจะถูกถอดออกจากหน้าเว็บทิ้งกลางทาง
# ค่า None หมายถึงหน้านี้ลองแล้วไม่สำเร็จ จะได้ไม่ต้องรอซ้ำอีกรอบ
_client_services: Dict[int, Any] = {}

# ปกติชั้นที่ 2 (เครื่องผู้ใช้) จะชนะไฟล์เสมอ
# ถ้าแก้ไฟล์ factories_config.json ด้วยมือแล้วอยากให้ค่าในไฟล์ชนะ
# ให้ตั้ง CORN_DISABLE_CLIENT_STORE=1 ก่อนเปิดโปรแกรม เพื่อปิดชั้นที่ 2 ชั่วคราว
CLIENT_STORE_DISABLED = os.environ.get(
    "CORN_DISABLE_CLIENT_STORE", "0"
).strip().lower() in ("1", "true", "yes")


async def _client_service(page: "ft.Page") -> Optional[Any]:
    """
    คืน SharedPreferences service ของหน้าเว็บนี้ (สร้างและรอให้พร้อมแค่ครั้งแรกครั้งเดียว)

    Flet ผูก service เข้าหน้าเว็บแบบไม่พร้อมกัน จึงต้องวนรอจนกว่า .page จะใช้งานได้
    ถ้ารอจนครบแล้วยังไม่พร้อม ถือว่าหน้านี้ใช้ Client Storage ไม่ได้ และจำไว้เลย
    """
    if CLIENT_STORE_DISABLED:
        return None

    key = id(page)
    if key in _client_services:
        return _client_services[key]

    service = None
    try:
        service = ft.SharedPreferences()
    except Exception as err:
        print(f"[ClientStore] สร้าง service ไม่สำเร็จ: {err}")
        _client_services[key] = None
        return None

    for _ in range(_CLIENT_READY_ATTEMPTS):
        try:
            if service.page is not None:
                _client_services[key] = service
                _register_client_cleanup(page, key)
                return service
        except Exception:
            pass
        try:
            page.update()
        except Exception:
            pass
        await asyncio.sleep(_CLIENT_READY_DELAY)

    print("[ClientStore] เบราว์เซอร์ไม่รองรับ Client Storage ใช้ไฟล์อย่างเดียว")
    _client_services[key] = None
    _register_client_cleanup(page, key)
    return None


def _register_client_cleanup(page: "ft.Page", key: int) -> None:
    """เคลียร์ service ทิ้งเมื่อผู้ใช้ปิดหน้าเว็บ จะได้ไม่ค้างสะสมในหน่วยความจำ"""
    if getattr(page, "on_disconnect", None) is not None:
        return

    def _cleanup(e):
        _client_services.pop(key, None)

    try:
        page.on_disconnect = _cleanup
    except Exception:
        pass


async def _client_read(page: "ft.Page", key: str) -> Optional[Any]:
    """อ่านค่า JSON จาก Client Storage คืน None ถ้าไม่มีหรืออ่านไม่ได้"""
    service = await _client_service(page)
    if service is None:
        return None
    try:
        raw = await service.get(key)
    except Exception as err:
        print(f"[ClientStore] อ่าน {key} ไม่สำเร็จ: {err}")
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception as err:
        print(f"[ClientStore] ข้อมูล {key} เสียหาย: {err}")
        return None


async def _client_write(page: "ft.Page", key: str, payload: Any) -> None:
    """เขียนค่าลง Client Storage แบบ fire-and-forget (ไม่รอผล ไม่ขวางหน้าจอ)"""
    service = await _client_service(page)
    if service is None:
        return
    try:
        await service.set(key, json.dumps(payload, ensure_ascii=False))
    except Exception as err:
        print(f"[ClientStore] บันทึก {key} ไม่สำเร็จ: {err}")


def _mirror_to_client(page: Optional["ft.Page"], key: str, payload: Any) -> None:
    """
    สั่งให้ไปเขียน Client Storage เบื้องหลัง เรียกจากโค้ดธรรมดา (ไม่ใช่ async) ได้เลย
    ถ้าสั่งไม่ได้ก็ปล่อยผ่าน เพราะไฟล์ในชั้นที่ 1 ถูกบันทึกไปแล้ว
    """
    if page is None:
        return
    try:
        page.run_task(_client_write, page, key, payload)
    except Exception as err:
        print(f"[ClientStore] สั่งบันทึก {key} เบื้องหลังไม่สำเร็จ: {err}")


class UserPreferences:
    """บันทึกและโหลดราคารับซื้อและความชื้นล่าสุดที่เคยกรอกไว้"""
    PREFS_FILE = _data_path(PREFS_FILENAME)
    DEFAULTS: Dict[str, Any] = {"buy_price": 8.50, "moisture": 28.0}
    _cache: Dict[str, Any] = {}

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if cls._cache:
            return cls._cache
        data = _read_json(cls.PREFS_FILE)
        if isinstance(data, dict) and data:
            cls._cache = data
        else:
            cls._cache = dict(cls.DEFAULTS)
        return cls._cache

    @classmethod
    def save(cls, buy_price: float, moisture: float, page: Optional["ft.Page"] = None):
        cls._cache = {"buy_price": buy_price, "moisture": moisture}
        _write_json_atomic(cls.PREFS_FILE, cls._cache)
        _mirror_to_client(page, CLIENT_KEY_PREFS, cls._cache)

    @classmethod
    def adopt(cls, data: Dict[str, Any]):
        """รับค่าที่ดึงมาจาก Client Storage มาใช้ พร้อมเขียนกลับลงไฟล์ให้ตรงกัน"""
        cls._cache = dict(data)
        _write_json_atomic(cls.PREFS_FILE, cls._cache)


class FactoryStorage:
    """
    คลาสจัดการการบันทึกและโหลดรายชื่อ/สูตรของโรงงาน

    บันทึกลงไฟล์ factories_config.json (ใน DATA_DIR) และ Client Storage ของเบราว์เซอร์
    ส่วน page.session เก็บไว้เป็นแคชระหว่างใช้งาน เพื่อไม่ต้องอ่านไฟล์ซ้ำทุกครั้ง
    """
    STORAGE_KEY = "corn_factories_v3"
    BACKUP_FILE = _data_path(FACTORIES_FILENAME)
    _memory_cache: List[Dict[str, Any]] = []

    @classmethod
    def load_factories(cls, page: Optional[ft.Page] = None) -> List[Dict[str, Any]]:
        """โหลดรายการโรงงานทั้งหมด"""
        if page is not None:
            try:
                session_data = page.session.get(cls.STORAGE_KEY)
                if session_data and isinstance(session_data, list) and len(session_data) > 0:
                    cls._memory_cache = session_data
                    return session_data
            except Exception:
                pass

        data = _read_json(cls.BACKUP_FILE)
        if isinstance(data, list) and len(data) > 0:
            cls._memory_cache = data
            if page is not None:
                try:
                    page.session.set(cls.STORAGE_KEY, data)
                except Exception:
                    pass
            return data

        cls._memory_cache = list(DEFAULT_FACTORIES)
        cls.save_factories(page, cls._memory_cache)
        return cls._memory_cache

    @classmethod
    def save_factories(cls, page: Optional[ft.Page], factories: List[Dict[str, Any]]):
        """บันทึกรายการโรงงานลงทั้งหน่วยความจำ ไฟล์ดิสก์ และเครื่องคุณแม่ทันที"""
        cls._memory_cache = list(factories)
        if page is not None:
            try:
                page.session.set(cls.STORAGE_KEY, factories)
            except Exception:
                pass

        _write_json_atomic(cls.BACKUP_FILE, factories)
        _mirror_to_client(page, CLIENT_KEY_FACTORIES, factories)

    @classmethod
    def adopt(cls, page: Optional[ft.Page], factories: List[Dict[str, Any]]):
        """รับสูตรที่ดึงมาจาก Client Storage มาใช้ พร้อมเขียนกลับลงไฟล์ให้ตรงกัน"""
        cls._memory_cache = list(factories)
        if page is not None:
            try:
                page.session.set(cls.STORAGE_KEY, factories)
            except Exception:
                pass
        _write_json_atomic(cls.BACKUP_FILE, factories)

    @classmethod
    def add_factory(cls, page: Optional[ft.Page], factory_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        factories = cls.load_factories(page)
        factories.append(factory_data)
        cls.save_factories(page, factories)
        return factories

    @classmethod
    def update_factory(cls, page: Optional[ft.Page], factory_id: str, updated_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        factories = cls.load_factories(page)
        for i, f in enumerate(factories):
            if f.get("id") == factory_id:
                factories[i] = {**f, **updated_data}
                break
        cls.save_factories(page, factories)
        return factories

    @classmethod
    def delete_factory(cls, page: Optional[ft.Page], factory_id: str) -> List[Dict[str, Any]]:
        factories = cls.load_factories(page)
        factories = [f for f in factories if f.get("id") != factory_id]
        cls.save_factories(page, factories)
        return factories

    @classmethod
    def reset_to_defaults(cls, page: Optional[ft.Page]) -> List[Dict[str, Any]]:
        cls.save_factories(page, list(DEFAULT_FACTORIES))
        return list(DEFAULT_FACTORIES)


async def hydrate_from_client(page: "ft.Page") -> None:
    """
    ดึงข้อมูลที่เก็บอยู่ในเครื่องคุณแม่มาใช้ก่อนสร้างหน้าจอ

    ต้องเรียกเป็นอย่างแรกใน main() เพราะหน้าจอถูกสร้างจากค่าที่โหลดไว้แล้ว
    ถ้าเครื่องยังไม่เคยมีข้อมูล จะส่งค่าจากไฟล์ขึ้นไปเก็บไว้ให้แทน (ครั้งแรกครั้งเดียว)
    """
    # --- สูตรโรงงาน ---
    try:
        stored = await _client_read(page, CLIENT_KEY_FACTORIES)
        if isinstance(stored, list) and len(stored) > 0:
            FactoryStorage.adopt(page, stored)
            print(f"[ClientStore] ใช้สูตรโรงงานจากเครื่องผู้ใช้ {len(stored)} โรงงาน")
        else:
            _mirror_to_client(page, CLIENT_KEY_FACTORIES, FactoryStorage.load_factories(page))
    except Exception as err:
        print(f"[ClientStore] ดึงสูตรโรงงานไม่สำเร็จ ใช้ไฟล์แทน: {err}")

    # --- ราคารับซื้อ / ความชื้นล่าสุด ---
    try:
        stored_prefs = await _client_read(page, CLIENT_KEY_PREFS)
        if isinstance(stored_prefs, dict) and stored_prefs:
            UserPreferences.adopt(stored_prefs)
        else:
            _mirror_to_client(page, CLIENT_KEY_PREFS, UserPreferences.load())
    except Exception as err:
        print(f"[ClientStore] ดึงค่าที่ตั้งไว้ไม่สำเร็จ ใช้ไฟล์แทน: {err}")


# =============================================================================
# 3. เครื่องยนต์คำนวณกำไรเปรียบเทียบ (CALCULATION & COMPARISON ENGINE)
# =============================================================================

class CornCalculator:
    TRUCK_WEIGHT = 30000.0   # 30 ตัน = 30,000 กก.
    DRYING_COST_RATE = 0.45  # ค่าอบแห้ง = 0.45 บาท/กก.แห้ง

    @classmethod
    def lookup_moisture_table(cls, moisture: float) -> Dict[str, float]:
        """ค้นหาและประมาณค่าแบบเส้นตรง (Linear Interpolation) จากตารางมาตรฐาน"""
        m = max(20.0, min(35.0, moisture))
        low_m = int(m)
        high_m = low_m + 1 if low_m < 35 else 35
        
        if low_m == high_m or abs(m - low_m) < 1e-6:
            return MASTER_MOISTURE_TABLE[low_m]
            
        t_low = MASTER_MOISTURE_TABLE[low_m]
        t_high = MASTER_MOISTURE_TABLE[high_m]
        
        fraction = (m - low_m) / (high_m - low_m)
        dry_pct = t_low["dry_pct"] + fraction * (t_high["dry_pct"] - t_low["dry_pct"])
        broken_pct = t_low["broken_pct"] + fraction * (t_high["broken_pct"] - t_low["broken_pct"])
        dust_pct = t_low["dust_pct"] + fraction * (t_high["dust_pct"] - t_low["dust_pct"])
        good_pct = dry_pct - broken_pct - dust_pct
        
        return {
            "dry_pct": dry_pct,
            "broken_pct": broken_pct,
            "dust_pct": dust_pct,
            "good_pct": good_pct,
        }

    @classmethod
    def calculate_single_factory(cls, factory: Dict[str, Any], buy_price: float, initial_moisture: float, sell_price: float) -> Dict[str, Any]:
        initial_weight = cls.TRUCK_WEIGHT
        raw_material_cost = initial_weight * buy_price
        
        moisture_bias = float(factory.get("moisture_bias", 0.0))
        req_sifting = bool(factory.get("req_sifting", False))
        transport_rate = float(factory.get("transport_rate", 0.0))
        
        # 1. คำนวณความชื้นจริงที่โรงงานใช้ค้นหาตาราง (Initial Moisture + Bias)
        effective_moisture = initial_moisture + moisture_bias
        table_row = cls.lookup_moisture_table(effective_moisture)
        
        # 2. คำนวณน้ำหนักแห้งรวม
        final_dry_weight = initial_weight * (table_row["dry_pct"] / 100.0)
        
        # 3. ต้นทุน (ค่าซื้อข้าวโพด + ค่าอบ 0.45 ฿ + ค่าขนส่ง)
        drying_cost = final_dry_weight * cls.DRYING_COST_RATE
        transport_cost = final_dry_weight * transport_rate
        total_cost = raw_material_cost + drying_cost + transport_cost
        
        # 4. รายรับ (กรณีมีการร่อนคัดแยก หรือไม่มี)
        if req_sifting:
            # คำนวณน้ำหนักเม็ดแตกและฝุ่นจากน้ำหนักแห้งสุทธิหลังอบ (final_dry_weight)
            broken_weight = final_dry_weight * (table_row["broken_pct"] / 100.0)
            dust_weight = final_dry_weight * (table_row["dust_pct"] / 100.0)
            good_weight = final_dry_weight - broken_weight - dust_weight
            
            # ราคาขาย: เม็ดแตกถูกกว่า 2 ฿, ฝุ่นถูกกว่า 7.5 ฿
            broken_price = max(0.0, sell_price - 2.0)
            dust_price = max(0.0, sell_price - 7.5)
            
            good_rev = good_weight * sell_price
            broken_rev = broken_weight * broken_price
            dust_rev = dust_weight * dust_price
            total_revenue = good_rev + broken_rev + dust_rev
        else:
            good_weight = final_dry_weight
            broken_weight = 0.0
            dust_weight = 0.0
            broken_price = 0.0
            dust_price = 0.0
            good_rev = total_revenue = final_dry_weight * sell_price
            broken_rev = 0.0
            dust_rev = 0.0
            
        net_profit = total_revenue - total_cost
        profit_per_kg_wet = net_profit / initial_weight
        profit_per_kg_dry = net_profit / final_dry_weight if final_dry_weight > 0 else 0.0
        
        return {
            "factory_id": factory.get("id"),
            "factory_name": factory.get("name"),
            "factory_emoji": factory.get("emoji", "🏭"),
            "factory_color": factory.get("color", "#0F172A"),
            "factory_bg_color": factory.get("bg_color", "#F1F5F9"),
            "moisture_bias": moisture_bias,
            "effective_moisture": effective_moisture,
            "req_sifting": req_sifting,
            "transport_rate": transport_rate,
            "buy_price": buy_price,
            "initial_moisture": initial_moisture,
            "sell_price": sell_price,
            "initial_weight": initial_weight,
            "final_weight": final_dry_weight,
            "table_dry_pct": table_row["dry_pct"],
            "broken_pct": table_row["broken_pct"],
            "dust_pct": table_row["dust_pct"],
            "good_pct": (100.0 - table_row["broken_pct"] - table_row["dust_pct"]) if req_sifting else 100.0,
            "raw_material_cost": raw_material_cost,
            "drying_cost": drying_cost,
            "transport_cost": transport_cost,
            "total_cost": total_cost,
            "total_revenue": total_revenue,
            "net_profit": net_profit,
            "profit_per_kg_wet": profit_per_kg_wet,
            "profit_per_kg_dry": profit_per_kg_dry,
            "good_weight": good_weight,
            "broken_weight": broken_weight,
            "dust_weight": dust_weight,
            "good_rev": good_rev,
            "broken_rev": broken_rev,
            "dust_rev": dust_rev,
            "broken_price": broken_price,
            "dust_price": dust_price,
        }

    @classmethod
    def compare_all_factories(cls, factories: List[Dict[str, Any]], buy_price: float, initial_moisture: float, price_dict: Dict[str, float]) -> List[Dict[str, Any]]:
        results = []
        for f in factories:
            fid = f.get("id", "")
            s_price = price_dict.get(fid, float(f.get("default_price", 11.00)))
            calc = cls.calculate_single_factory(f, buy_price, initial_moisture, s_price)
            results.append(calc)
            
        # เรียงลำดับจากกำไรมากที่สุดไปน้อยที่สุด (Leaderboard)
        results.sort(key=lambda x: x["net_profit"], reverse=True)
        return results


# =============================================================================
# 4. ธีมและค่าสีสำหรับผู้สูงอายุ (HIGH CONTRAST & ACCESSIBLE THEME)
# =============================================================================

class AppColors:
    BG = "#F8FAFC"                  # Slate 50 พื้นหลังสว่างสะอาดตา
    CARD_BG = "#FFFFFF"             # ขาวคมชัด
    HEADER_BG = "#0F172A"           # สีกรมท่าเข้ม พรีเมียม อ่านง่าย
    
    TEXT_MAIN = "#0F172A"           # Slate 900 ตัวหนังสือหลัก คอนทราสต์สูง
    TEXT_MUTED = "#475569"          # Slate 600 สีเทาเข้ม
    TEXT_WHITE = "#FFFFFF"
    
    WINNER_GREEN = "#15803D"        # เขียวสดใส คอนทราสต์สูง
    WINNER_BG = "#DCFCE7"           # พื้นหลังเขียวอ่อน
    WINNER_BORDER = "#22C55E"
    
    LOSS_RED = "#B91C1C"            # แดงเข้ม ชัดเจน
    LOSS_BG = "#FEE2E2"             # พื้นหลังแดงอ่อน
    
    BTN_PRIMARY = "#16A34A"         # ปุ่มหลัก สีเขียวสดใส
    BTN_SECONDARY = "#0284C7"       # ปุ่มรอง สีฟ้าสดใส
    BTN_AMBER = "#D97706"           # ปุ่มสีทองอำพัน
    BORDER_LIGHT = "#CBD5E1"


# =============================================================================
# 5. ฟังก์ชันหลักของ FLET WEB APP (MAIN APPLICATION CONTROLLER)
# =============================================================================

async def main(page: ft.Page):
    page.title = "🌽 เปรียบเทียบกำไรโรงงานข้าวโพด (สำหรับคุณแม่)"
    page.bgcolor = AppColors.BG
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # ดึงสูตรโรงงานและค่าที่ตั้งไว้จากเครื่องผู้ใช้ก่อนสร้างหน้าจอทั้งหมด
    # ต้องอยู่บรรทัดแรกสุด เพราะหน้าจอด้านล่างถูกสร้างจากค่าที่โหลดไว้แล้ว
    await hydrate_from_client(page)

    CORRECT_PIN = "1234"
    entered_pin = []
    
    # ตัวแปรควบคุมหน้าจอหลัก
    main_view = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
    )

    # -------------------------------------------------------------------------
    # PIN Gate Screen Components
    # -------------------------------------------------------------------------
    pin_dots = [
        ft.Container(
            width=26,
            height=26,
            border_radius=13,
            border=ft.Border.all(3, AppColors.HEADER_BG),
            bgcolor=AppColors.CARD_BG,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )
        for _ in range(4)
    ]
    
    pin_error_text = ft.Text(
        value="",
        size=18,
        weight=ft.FontWeight.BOLD,
        color=AppColors.LOSS_RED,
        text_align=ft.TextAlign.CENTER,
    )
    
    def update_pin_dots():
        for i in range(4):
            if i < len(entered_pin):
                pin_dots[i].bgcolor = AppColors.WINNER_GREEN
                pin_dots[i].border = ft.Border.all(3, AppColors.WINNER_GREEN)
            else:
                pin_dots[i].bgcolor = AppColors.CARD_BG
                pin_dots[i].border = ft.Border.all(3, AppColors.HEADER_BG)
        page.update()

    current_screen_name = ["pin"]

    def handle_pin_digit(digit: str):
        if len(entered_pin) < 4:
            entered_pin.append(digit)
            update_pin_dots()
            pin_error_text.value = ""
            
            if len(entered_pin) == 4:
                pin_str = "".join(entered_pin)
                if pin_str == CORRECT_PIN:
                    entered_pin.clear()
                    update_pin_dots()
                    show_main_calculator_screen()
                else:
                    pin_error_text.value = "❌ รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง"
                    entered_pin.clear()
                    update_pin_dots()
        page.update()

    def handle_pin_backspace(e):
        if entered_pin:
            entered_pin.pop()
            update_pin_dots()
            pin_error_text.value = ""
        page.update()

    def handle_pin_clear(e):
        entered_pin.clear()
        update_pin_dots()
        pin_error_text.value = ""
        page.update()

    # รองรับการกดตัวเลขจากคีย์บอร์ด (Physical Keyboard & Numpad)
    def on_keyboard_event(e: ft.KeyboardEvent):
        if current_screen_name[0] != "pin":
            return
        
        k = str(e.key or "").strip()
        if k in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            handle_pin_digit(k)
        elif k.startswith("Numpad ") and k.replace("Numpad ", "").isdigit():
            handle_pin_digit(k.replace("Numpad ", ""))
        elif k.startswith("Numpad") and k.replace("Numpad", "").isdigit():
            handle_pin_digit(k.replace("Numpad", ""))
        elif k.startswith("Digit") and k.replace("Digit", "").isdigit():
            handle_pin_digit(k.replace("Digit", ""))
        elif k in ["Backspace", "Delete"]:
            handle_pin_backspace(None)
        elif k in ["Escape", "c", "C"]:
            handle_pin_clear(None)

    page.on_keyboard_event = on_keyboard_event

    # =========================================================================
    # VIEW 0: หน้าจอใส่รหัสผ่าน (PIN GATE SCREEN)
    # =========================================================================
    def build_pin_screen():
        def make_numpad_btn(text: str, on_click, bg="#FFFFFF", text_color=AppColors.TEXT_MAIN, icon=None):
            content_controls = []
            if icon:
                content_controls.append(ft.Icon(icon, size=28, color=text_color))
            if text:
                content_controls.append(ft.Text(text, size=26, weight=ft.FontWeight.BOLD, color=text_color))
                
            return ft.Container(
                content=ft.Button(
                    content=ft.Row(content_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                    on_click=on_click,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=20),
                        elevation=3,
                    ),
                    bgcolor=bg,
                    height=72,
                ),
                expand=1,
            )

        pin_card = ft.Container(
            width=460,
            padding=ft.Padding.symmetric(horizontal=24, vertical=28),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    ft.Container(
                        width=90,
                        height=90,
                        border_radius=45,
                        bgcolor="#FEF3C7",
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("🌽", size=52),
                    ),
                    ft.Text(
                        "แอพเปรียบเทียบกำไรโรงงานข้าวโพด",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT_MAIN,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "คำนวณหาโรงงานที่คุ้มที่สุดสำหรับคุณแม่ ❤️",
                        size=17,
                        weight=ft.FontWeight.W_500,
                        color=AppColors.TEXT_MUTED,
                    ),
                    ft.Divider(height=10, color=AppColors.BORDER_LIGHT),
                    
                    ft.Text(
                        "🔒 กดตัวเลขบนแป้นพิมพ์ หรือแตะปุ่ม 4 หลัก",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT_MAIN,
                    ),
                    
                    ft.Container(
                        padding=ft.Padding.symmetric(vertical=10),
                        content=ft.Row(
                            controls=pin_dots,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=18,
                        )
                    ),
                    pin_error_text,
                    
                    ft.Column(
                        spacing=12,
                        controls=[
                            ft.Row([
                                make_numpad_btn("1", lambda e: handle_pin_digit("1")),
                                make_numpad_btn("2", lambda e: handle_pin_digit("2")),
                                make_numpad_btn("3", lambda e: handle_pin_digit("3")),
                            ], spacing=12),
                            ft.Row([
                                make_numpad_btn("4", lambda e: handle_pin_digit("4")),
                                make_numpad_btn("5", lambda e: handle_pin_digit("5")),
                                make_numpad_btn("6", lambda e: handle_pin_digit("6")),
                            ], spacing=12),
                            ft.Row([
                                make_numpad_btn("7", lambda e: handle_pin_digit("7")),
                                make_numpad_btn("8", lambda e: handle_pin_digit("8")),
                                make_numpad_btn("9", lambda e: handle_pin_digit("9")),
                            ], spacing=12),
                            ft.Row([
                                make_numpad_btn("ลบ", handle_pin_backspace, bg="#FEE2E2", text_color=AppColors.LOSS_RED, icon=ft.Icons.BACKSPACE_OUTLINED),
                                make_numpad_btn("0", lambda e: handle_pin_digit("0")),
                                make_numpad_btn("ล้าง", handle_pin_clear, bg="#F1F5F9", text_color=AppColors.TEXT_MUTED, icon=ft.Icons.REFRESH),
                            ], spacing=12),
                        ]
                    ),
                    
                    ft.Container(
                        padding=ft.Padding.only(top=10),
                        content=ft.Text(
                            "💡 กดตัวเลข 1 2 3 4 บนคีย์บอร์ด หรือแตะปุ่มบนหน้าจอได้เลยค่ะ",
                            size=15,
                            color=AppColors.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                        )
                    )
                ]
            )
        )
        
        return ft.Container(
            alignment=ft.Alignment(0, 0),
            padding=16,
            content=ft.Card(
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=28),
                bgcolor=AppColors.CARD_BG,
                content=pin_card,
            )
        )

    # =========================================================================
    # VIEW 1: หน้าจอหลักคำนวณและเปรียบเทียบกำไร (MAIN COMPARATOR SCREEN)
    # =========================================================================
    
    # ตัวแปรเก็บค่าช่องกรอกข้อมูลส่วนกลาง
    # โหลดค่าล่าสุดที่เคยบันทึกไว้
    prefs = UserPreferences.load()
    txt_buy_price = ft.TextField(
        label="ราคารับซื้อที่ความชื้น 30%",
        hint_text="เช่น 6.75",
        value=f"{prefs.get('buy_price', 6.75):.2f}",
        suffix=ft.Text("บาท / กก.", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
        keyboard_type=ft.KeyboardType.TEXT,
        text_size=24,
        label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        border_color=AppColors.BORDER_LIGHT,
        focused_border_color=AppColors.WINNER_GREEN,
        focused_border_width=3,
        border_radius=14,
        content_padding=16,
        filled=True,
        fill_color=AppColors.CARD_BG,
    )

    # Dictionary เก็บช่องกรอกราคาขายของแต่ละโรงงาน {factory_id: TextField}
    factory_price_fields: Dict[str, ft.TextField] = {}

    # ฟังก์ชันสร้างปุ่มปรับแต่งด่วน (+ / - / จุด / ลบ)
    def make_quick_bar(text_field, is_moist=False):
        def change_val(delta):
            try:
                v = float(text_field.value.strip().replace(",", "") or "0")
                new_v = max(0.0, v + delta)
                if is_moist:
                    new_v = max(15.0, min(38.0, new_v))
                    text_field.value = f"{new_v:.1f}"
                else:
                    text_field.value = f"{new_v:.2f}"
                page.update()
            except ValueError:
                pass

        def insert_dot(e):
            val = text_field.value.strip()
            if "." not in val:
                text_field.value = val + "."
                page.update()

        def clear_val(e):
            text_field.value = ""
            page.update()

        step1 = 0.5 if is_moist else 0.50
        step2 = 0.1 if is_moist else 0.10

        btn_style_small = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )

        def quick_btn(label, on_click, bg, fg):
            # expand=True ทำให้ปุ่มยืดเต็มช่องของตัวเองเสมอ ไม่ว่าจอจะกว้างแค่ไหน
            # จึงไม่มีทางล้นขอบจอเหมือนตอนเรียงปุ่มทั้ง 6 ไว้แถวเดียว
            return ft.Button(
                label,
                on_click=on_click,
                style=btn_style_small,
                bgcolor=bg,
                color=fg,
                height=40,
                expand=True,
            )

        return ft.Column([
            ft.Row([
                quick_btn(f"-{step1:.1f}%" if is_moist else f"-{step1:.2f}", lambda e: change_val(-step1), "#F1F5F9", AppColors.LOSS_RED),
                quick_btn(f"-{step2:.1f}%" if is_moist else f"-{step2:.2f}", lambda e: change_val(-step2), "#F1F5F9", AppColors.LOSS_RED),
                quick_btn("📍 จุด .", insert_dot, "#FEF3C7", "#92400E"),
            ], spacing=6),
            ft.Row([
                quick_btn(f"+{step2:.1f}%" if is_moist else f"+{step2:.2f}", lambda e: change_val(+step2), "#DCFCE7", AppColors.WINNER_GREEN),
                quick_btn(f"+{step1:.1f}%" if is_moist else f"+{step1:.2f}", lambda e: change_val(+step1), "#DCFCE7", AppColors.WINNER_GREEN),
                quick_btn("✕ ลบ", clear_val, "#FEE2E2", AppColors.LOSS_RED),
            ], spacing=6),
        ], spacing=6)

    # ป๊อปอัปดูรายละเอียดการคำนวณของแต่ละโรงงาน
    def show_detail_dialog(res: Dict[str, Any]):
        is_profit = res["net_profit"] >= 0
        has_sifting = res["req_sifting"]

        def make_drow(label: str, val: str, bold=False, color=AppColors.TEXT_MAIN):
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(label, size=15, color=AppColors.TEXT_MUTED if not bold else color, weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL),
                    ft.Text(val, size=15, color=color, weight=ft.FontWeight.BOLD if bold else ft.FontWeight.W_500),
                ]
            )

        sifting_controls = []
        if has_sifting:
            good_p = res.get("good_pct", 96.0)
            broken_p = res.get("broken_pct", 3.5)
            dust_p = res.get("dust_pct", 0.5)
            sifting_controls = [
                ft.Text("🔍 การร่อนคัดแยก (คิดจากน้ำหนักแห้งหลังอบ):", size=15, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                make_drow(f"  - เม็ดแห้งดีสุทธิ ({good_p:.1f}%):", f"{res['good_weight']:,.1f} กก. ({res['good_rev']:,.2f} ฿)"),
                make_drow(f"  - เม็ดแตก ({broken_p:.1f}% @ {res['broken_price']:.2f}฿):", f"{res['broken_weight']:,.1f} กก. ({res['broken_rev']:,.2f} ฿)"),
                make_drow(f"  - ฝุ่น/รำ ({dust_p:.1f}% @ {res['dust_price']:.2f}฿):", f"{res['dust_weight']:,.1f} กก. ({res['dust_rev']:,.2f} ฿)"),
                ft.Divider(height=10, color=AppColors.BORDER_LIGHT),
            ]

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Text(f"{res['factory_emoji']} รายละเอียด: {res['factory_name']}", size=20, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Container(
                width=460,
                content=ft.ListView(
                    controls=[
                        ft.Container(
                            padding=14,
                            border_radius=14,
                            bgcolor=AppColors.WINNER_BG if is_profit else AppColors.LOSS_BG,
                            border=ft.Border.all(2, AppColors.WINNER_GREEN if is_profit else AppColors.LOSS_RED),
                            content=ft.Column([
                                ft.Text("กำไรสุทธิจากการส่งโรงงานนี้ (30 ตัน)", size=14, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                                ft.Text(
                                    f"{res['net_profit']:+,.2f} บาท",
                                    size=26,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.WINNER_GREEN if is_profit else AppColors.LOSS_RED,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(f"เฉลี่ย: {res['profit_per_kg_wet']:+.2f} ฿/กก.ชื้น | {res['profit_per_kg_dry']:+.2f} ฿/กก.แห้ง", size=13, color=AppColors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
                        ),
                        ft.Container(height=10),
                        
                        make_drow("ราคารับซื้อข้าวโพดสด (ความชื้น 30%):", f"{res['buy_price']:.2f} บาท/กก."),
                        make_drow("ราคาขายหน้าป้าย:", f"{res['sell_price']:.2f} บาท/กก."),
                        make_drow(f"น้ำหนักแห้งสุทธิหลังอบ ({res['table_dry_pct']:.1f}%):", f"{res['final_weight']:,.2f} กก.", bold=True, color="#0F172A"),
                        ft.Divider(height=10, color=AppColors.BORDER_LIGHT),
                        
                        *sifting_controls,
                        
                        make_drow("💰 รายรับรวมทั้งหมด:", f"{res['total_revenue']:,.2f} บาท", bold=True, color="#065F46"),
                        make_drow("  - ค่าซื้อข้าวโพดสด (30 ตัน):", f"{res['raw_material_cost']:,.2f} บาท"),
                        make_drow("  - ค่าอบแห้ง (0.45 ฿):", f"{res['drying_cost']:,.2f} บาท"),
                        make_drow(f"  - ค่าขนส่ง ({res['transport_rate']:.2f} ฿):", f"{res['transport_cost']:,.2f} บาท"),
                        make_drow("💸 ต้นทุนรวมทั้งหมด:", f"{res['total_cost']:,.2f} บาท", bold=True, color=AppColors.LOSS_RED),
                    ]
                )
            ),
            actions=[
                ft.TextButton("ปิดหน้าต่าง", on_click=lambda e: page.pop_dialog())
            ]
        )
        page.show_dialog(dlg)

    def open_master_table_dialog(e):
        table_rows = []
        for m in range(35, 19, -1):
            r = MASTER_MOISTURE_TABLE[m]
            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"{m}%", size=15, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)),
                        ft.DataCell(ft.Text(f"{r['dry_pct']:.1f}%", size=15, weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(f"{r['broken_pct']:.1f}%", size=15, color="#D97706")),
                        ft.DataCell(ft.Text(f"{r['dust_pct']:.1f}%", size=15, color="#DC2626")),
                        ft.DataCell(ft.Text(f"{r['good_pct']:.1f}%", size=15, weight=ft.FontWeight.BOLD, color="#16A34A")),
                    ]
                )
            )

        table_dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.TABLE_CHART_OUTLINED, color=AppColors.WINNER_GREEN, size=26),
                ft.Text("ตารางมาตรฐานหักความชื้น", size=20, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    scroll=ft.ScrollMode.ADAPTIVE,
                    spacing=10,
                    controls=[
                        ft.Text("ตารางหลักอ้างอิงการสูญเสียน้ำหนักและการร่อนคัดแยก:", size=13, color=AppColors.TEXT_MUTED),
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("ความชื้น", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("นน.แห้ง", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("แตก", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("ฝุ่น", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("เม็ดดี", weight=ft.FontWeight.BOLD)),
                            ],
                            rows=table_rows,
                            column_spacing=12,
                            data_row_min_height=36,
                            data_row_max_height=40,
                        ),
                    ]
                )
            ),
            actions=[
                ft.TextButton("ปิดหน้าต่าง", on_click=lambda e: page.pop_dialog())
            ]
        )
        page.show_dialog(table_dlg)

    def build_main_calculator_screen():
        factories = FactoryStorage.load_factories(page)

        # การ์ดแสดงราคาขายหน้าป้ายของแต่ละโรงงาน
        factory_price_cards = []
        for f in factories:
            fid = f.get("id", "")
            current_val = factory_price_fields.get(fid, None)
            val_str = current_val.value if current_val else f"{float(f.get('default_price', 11.0)):.2f}"
            
            tf = ft.TextField(
                label=f"ราคาป้ายวันนี้ ({f.get('name')})",
                hint_text="เช่น 11.20",
                value=val_str,
                suffix=ft.Text("บาท / กก.", size=18, weight=ft.FontWeight.BOLD, color=f.get("color", AppColors.TEXT_MUTED)),
                keyboard_type=ft.KeyboardType.TEXT,
                text_size=24,
                label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, color=f.get("color", AppColors.TEXT_MAIN)),
                border_color=AppColors.BORDER_LIGHT,
                focused_border_color=f.get("color", AppColors.WINNER_GREEN),
                focused_border_width=3,
                border_radius=14,
                content_padding=16,
                filled=True,
                fill_color=AppColors.CARD_BG,
            )
            factory_price_fields[fid] = tf

            # ป้ายข้อมูลสูตรโรงงาน
            sifting_badge = "ร่อนคัดแยก" if f.get("req_sifting") else "ไม่ร่อน (100%)"
            bias_str = f"{f.get('moisture_bias', 0.0):+.1f}%"
            formula_desc = f"ไบแอส {bias_str} | {sifting_badge} | ส่ง {f.get('transport_rate', 0):.2f} ฿"

            card = ft.Card(
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=18),
                bgcolor=AppColors.CARD_BG,
                content=ft.Container(
                    padding=16,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row([
                                        ft.Text(f.get("emoji", "🏭"), size=24),
                                        ft.Text(f.get("name", ""), size=18, weight=ft.FontWeight.BOLD, color=f.get("color", AppColors.TEXT_MAIN)),
                                    ], spacing=6),
                                    ft.Container(
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                        border_radius=8,
                                        bgcolor=f.get("bg_color", "#F1F5F9"),
                                        content=ft.Text(sifting_badge, size=12, color=f.get("color", AppColors.TEXT_MAIN), weight=ft.FontWeight.BOLD),
                                    )
                                ]
                            ),
                            ft.Text(formula_desc, size=13, color=AppColors.TEXT_MUTED),
                            ft.Container(height=2),
                            tf,
                            make_quick_bar(tf, is_moist=False),
                        ]
                    )
                )
            )
            factory_price_cards.append(card)

        # ฟังก์ชันคำนวณและนำทางไปหน้าผลลัพธ์
        def on_calculate_clicked(e):
            try:
                b_price = float(txt_buy_price.value.strip().replace(",", "") or "0")
                moist = 30.0  # ล็อกที่ความชื้นมาตรฐาน 30%
                
                if b_price <= 0:
                    page.snack_bar = ft.SnackBar(ft.Text("⚠️ กรุณากรอกราคารับซื้อข้าวโพดชื้นให้ถูกต้องค่ะ", size=16), bgcolor=AppColors.LOSS_RED, open=True)
                    page.update()
                    return

                # ดึงราคาขายของแต่ละโรงงาน
                current_factories = FactoryStorage.load_factories(page)
                price_dict = {}
                for f in current_factories:
                    fid = f.get("id", "")
                    tf = factory_price_fields.get(fid)
                    price_val = float(tf.value.strip().replace(",", "") or f.get("default_price", 11.0)) if tf else float(f.get("default_price", 11.0))
                    price_dict[fid] = price_val

                # บันทึกค่าราคารับซื้อและความชื้นล่าสุด
                UserPreferences.save(b_price, moist, page)
                
                # บันทึกราคาขายล่าสุดของแต่ละโรงงานลง storage ถาวร
                for f in current_factories:
                    fid = f.get("id", "")
                    if fid in price_dict:
                        f["default_price"] = price_dict[fid]
                FactoryStorage.save_factories(page, current_factories)

                # คำนวณเปรียบเทียบ
                ranking = CornCalculator.compare_all_factories(current_factories, b_price, moist, price_dict)
                
                if not ranking:
                    return

                # นำทางไปหน้าแสดงผลลัพธ์ทันที!
                show_results_screen(ranking, b_price)

            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("⚠️ กรุณากรอกเฉพาะตัวเลขเท่านั้นค่ะแม่", size=16), bgcolor=AppColors.LOSS_RED, open=True)
                page.update()

        # รวมหน้าจอ Main Input
        main_content = ft.Container(
            width=520,
            padding=ft.Padding.symmetric(horizontal=16, vertical=20),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    # 1. แถบ Header
                    ft.Card(
                        elevation=3,
                        shape=ft.RoundedRectangleBorder(radius=20),
                        bgcolor=AppColors.HEADER_BG,
                        content=ft.Container(
                            padding=16,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row([
                                        ft.Text("🌽", size=32),
                                        ft.Column([
                                            ft.Text("เปรียบเทียบกำไรโรงงาน", size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                                            ft.Text("หาโรงงานที่คุ้มค่าที่สุดวันนี้", size=13, color="#94A3B8"),
                                        ], spacing=2),
                                    ], spacing=10),
                                    ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.TABLE_CHART_OUTLINED,
                                            icon_color=AppColors.TEXT_WHITE,
                                            tooltip="ดูตารางมาตรฐานหักความชื้น",
                                            on_click=open_master_table_dialog,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.SETTINGS_ROUNDED,
                                            icon_color=AppColors.TEXT_WHITE,
                                            tooltip="จัดการ/เพิ่มสูตรโรงงาน",
                                            on_click=lambda e: show_factory_manager_screen(),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.LOCK_OUTLINED,
                                            icon_color=AppColors.TEXT_WHITE,
                                            tooltip="ล็อคหน้าจอ",
                                            on_click=lambda e: show_pin_screen(),
                                        ),
                                    ], spacing=0)
                                ]
                            )
                        )
                    ),
                    
                    # 2. ส่วนราคารับซื้อข้าวโพดชื้น (คิดที่ความชื้นมาตรฐาน 30%)
                    ft.Card(
                        elevation=3,
                        shape=ft.RoundedRectangleBorder(radius=18),
                        bgcolor=AppColors.CARD_BG,
                        content=ft.Container(
                            padding=16,
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Row([
                                        ft.Text("🌾", size=24),
                                        ft.Text("ราคารับซื้อข้าวโพดชื้น (ที่ความชื้น 30%)", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                                    ], spacing=8),
                                    ft.Text("ราคาที่เราจ่ายซื้อข้าวโพดสดจากเกษตรกร (คำนวณที่ความชื้นมาตรฐาน 30%)", size=13, color=AppColors.TEXT_MUTED),
                                    ft.Container(height=2),
                                    txt_buy_price,
                                    make_quick_bar(txt_buy_price, is_moist=False),
                                    ft.Container(height=6),
                                    # ปุ่มคำนวณหาโรงงานที่คุ้มที่สุดอยู่ต่อจากช่องกรอกทันที
                                    ft.Button(
                                        content=ft.Row([
                                            ft.Icon(ft.Icons.SEARCH_ROUNDED, size=28, color=AppColors.TEXT_WHITE),
                                            ft.Text("🏆 คำนวณหาโรงงานที่คุ้มที่สุด", size=22, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                                        on_click=on_calculate_clicked,
                                        bgcolor=AppColors.BTN_PRIMARY,
                                        height=62,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=16),
                                            elevation=4,
                                        ),
                                    ),
                                ]
                            )
                        )
                    ),
                    
                    # 3. ส่วนราคาขายหน้าป้ายของแต่ละโรงงาน
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("🏷️ ราคาขายป้ายโรงงานวันนี้", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                            ft.TextButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.TUNE_ROUNDED, size=16, color=AppColors.BTN_SECONDARY),
                                    ft.Text("ตั้งค่าโรงงาน", size=14, color=AppColors.BTN_SECONDARY, weight=ft.FontWeight.BOLD),
                                ], spacing=4),
                                on_click=lambda e: show_factory_manager_screen(),
                            )
                        ]
                    ),
                    
                    *factory_price_cards,
                    
                    ft.Container(height=24)
                ]
            )
        )
        return main_content

    # =========================================================================
    # VIEW 2: หน้าจอแสดงผลลัพธ์การจัดอันดับกำไร (RESULTS SCREEN)
    # =========================================================================
    def build_results_screen(ranking: List[Dict[str, Any]], b_price: float):
        winner = ranking[0]
        runner_up = ranking[1] if len(ranking) > 1 else None
        diff_vs_2nd = (winner["net_profit"] - runner_up["net_profit"]) if runner_up else 0.0

        # สร้างการ์ดผลลัพธ์
        result_cards = []
        
        # 👑 1. WINNER HERO BANNER
        winner_card = ft.Card(
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=22, side=ft.BorderSide(3, AppColors.WINNER_BORDER)),
            bgcolor=AppColors.WINNER_BG,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Row([
                            ft.Text("🏆", size=36),
                            ft.Column([
                                ft.Row([
                                    ft.Text("โรงงานที่ทำกำไรมากที่สุด (อันดับ 1)", size=15, weight=ft.FontWeight.BOLD, color="#166534"),
                                    ft.Container(
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                        border_radius=6,
                                        bgcolor="#FEF3C7" if winner.get("req_sifting") else "#F1F5F9",
                                        content=ft.Text(
                                            "🔍 ร่อนคัดแยก" if winner.get("req_sifting") else "✨ ไม่ร่อน (100%)",
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color="#92400E" if winner.get("req_sifting") else AppColors.TEXT_MUTED,
                                        ),
                                    ),
                                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                ft.Text(f"{winner['factory_emoji']} {winner['factory_name']}", size=24, weight=ft.FontWeight.BOLD, color=winner['factory_color']),
                            ], spacing=2),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        
                        ft.Divider(height=8, color="#86EFAC"),
                        
                        ft.Text("กำไรสุทธิสูงสุดต่อคัน (30 ตัน)", size=14, color="#166534"),
                        ft.Text(
                            f"{winner['net_profit']:+,.2f} ฿",
                            size=34,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.WINNER_GREEN,
                        ),
                        ft.Text(f"เฉลี่ย: {winner['profit_per_kg_wet']:+.2f} ฿/กก.ชื้น | {winner['profit_per_kg_dry']:+.2f} ฿/กก.แห้ง", size=14, color="#166534", weight=ft.FontWeight.W_500),
                        
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=12, vertical=5),
                            border_radius=8,
                            bgcolor="#FFFFFF",
                            border=ft.Border.all(1, "#86EFAC"),
                            content=ft.Text(
                                f"🌾 น้ำหนักแห้งสุทธิหลังอบ ({winner['table_dry_pct']:.1f}%): {winner['final_weight']:,.2f} กก.",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#15803D",
                            ),
                        ),
                        
                        ft.Container(
                            visible=runner_up is not None,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                            border_radius=10,
                            bgcolor="#DCFCE7",
                            border=ft.Border.all(1, "#86EFAC"),
                            content=ft.Text(
                                f"🌟 แนะนำส่งที่นี่! ได้กำไรมากกว่าอันดับ 2 ({runner_up['factory_name'] if runner_up else ''}) อยู่ {diff_vs_2nd:+,.2f} บาท",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#15803D",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ),
                            
                        ft.Button(
                            content=ft.Row([
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=AppColors.TEXT_WHITE),
                                ft.Text("ดูวิธีคิดต้นทุนละเอียด", size=16, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                            on_click=lambda e, w=winner: show_detail_dialog(w),
                            bgcolor=AppColors.WINNER_GREEN,
                            height=44,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        ),
                    ]
                )
            )
        )
        result_cards.append(winner_card)

        # 🥈 2. OTHER FACTORY CARDS (อันดับ 2, 3, 4...)
        if len(ranking) > 1:
            result_cards.append(
                ft.Text("📊 อันดับกำไรโรงงานอื่นๆ:", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN)
            )

            for rank_idx, r in enumerate(ranking[1:], 2):
                is_pos = r["net_profit"] >= 0
                diff_vs_winner = r["net_profit"] - winner["net_profit"]
                
                rank_card = ft.Card(
                    elevation=2,
                    shape=ft.RoundedRectangleBorder(radius=18),
                    bgcolor=AppColors.CARD_BG,
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Row([
                                            ft.Container(
                                                width=32,
                                                height=32,
                                                border_radius=16,
                                                bgcolor="#E2E8F0",
                                                alignment=ft.Alignment(0, 0),
                                                content=ft.Text(f"#{rank_idx}", size=15, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                                            ),
                                            ft.Text(f"{r['factory_emoji']} {r['factory_name']}", size=18, weight=ft.FontWeight.BOLD, color=r['factory_color']),
                                            ft.Container(
                                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                border_radius=6,
                                                bgcolor="#FEF3C7" if r.get("req_sifting") else "#F1F5F9",
                                                content=ft.Text(
                                                    "ร่อน" if r.get("req_sifting") else "ไม่ร่อน",
                                                    size=11,
                                                    weight=ft.FontWeight.BOLD,
                                                    color="#92400E" if r.get("req_sifting") else AppColors.TEXT_MUTED,
                                                ),
                                            ),
                                        ], spacing=6),
                                        ft.Text(
                                            f"{r['net_profit']:+,.2f} ฿",
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=AppColors.WINNER_GREEN if is_pos else AppColors.LOSS_RED,
                                        ),
                                    ]
                                ),
                                
                                ft.Text(
                                    f"ป้าย {r['sell_price']:.2f} ฿ | นน.แห้ง {r['final_weight']:,.0f} กก. ({r['table_dry_pct']:.1f}%) | ส่ง {r['transport_rate']:.2f} ฿",
                                    size=13,
                                    color=AppColors.TEXT_MUTED,
                                ),
                                
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                            border_radius=8,
                                            bgcolor="#FEE2E2",
                                            content=ft.Text(
                                                f"น้อยกว่าอันดับ 1 อยู่ {diff_vs_winner:,.2f} ฿",
                                                size=12,
                                                color=AppColors.LOSS_RED,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ),
                                        ft.TextButton(
                                            content=ft.Row([
                                                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=AppColors.BTN_SECONDARY),
                                                ft.Text("ดูรายละเอียด", size=13, color=AppColors.BTN_SECONDARY, weight=ft.FontWeight.BOLD),
                                            ], spacing=4),
                                            on_click=lambda e, res=r: show_detail_dialog(res),
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )
                result_cards.append(rank_card)

        results_layout = ft.Container(
            width=520,
            padding=ft.Padding.symmetric(horizontal=16, vertical=20),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    # Header พร้อมปุ่มย้อนกลับ
                    ft.Card(
                        elevation=3,
                        shape=ft.RoundedRectangleBorder(radius=20),
                        bgcolor=AppColors.HEADER_BG,
                        content=ft.Container(
                            padding=16,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                                            icon_color=AppColors.TEXT_WHITE,
                                            tooltip="กลับหน้ากรอกราคา",
                                            on_click=lambda e: show_main_calculator_screen(),
                                        ),
                                        ft.Column([
                                            ft.Text("🏆 สรุปผลกำไรโรงงาน", size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                                            ft.Text(f"ซื้อ {b_price:.2f} ฿ (ชื้น 30%) | {len(ranking)} โรงงาน", size=13, color="#94A3B8"),
                                        ], spacing=2),
                                    ], spacing=6),
                                    ft.IconButton(
                                        icon=ft.Icons.TABLE_CHART_OUTLINED,
                                        icon_color=AppColors.TEXT_WHITE,
                                        tooltip="ดูตารางมาตรฐานหักความชื้น",
                                        on_click=open_master_table_dialog,
                                    ),
                                ]
                            )
                        )
                    ),
                    
                    # รายการการ์ดผลลัพธ์
                    *result_cards,
                    
                    # ปุ่มย้อนกลับด้านล่าง
                    ft.Button(
                        content=ft.Row([
                            ft.Icon(ft.Icons.EDIT_ROUNDED, size=22, color=AppColors.BTN_SECONDARY),
                            ft.Text("⬅️ กลับไปแก้ไขราคา / คำนวณใหม่", size=18, weight=ft.FontWeight.BOLD, color=AppColors.BTN_SECONDARY),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                        on_click=lambda e: show_main_calculator_screen(),
                        bgcolor=AppColors.CARD_BG,
                        height=54,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=16),
                            side=ft.BorderSide(2, AppColors.BORDER_LIGHT),
                            elevation=2,
                        ),
                    ),
                    
                    ft.Container(height=24)
                ]
            )
        )
        return results_layout

    # =========================================================================
    # VIEW 3: หน้าจอจัดการและเพิ่มโรงงาน (FACTORY MANAGER SCREEN)
    # =========================================================================
    def build_factory_manager_screen():
        factories = FactoryStorage.load_factories(page)

        # กล่องเพิ่ม / แก้ไขโรงงาน
        def open_factory_edit_dialog(factory: Optional[Dict[str, Any]] = None):
            is_new = factory is None
            
            tf_name = ft.TextField(
                label="ชื่อโรงงาน",
                hint_text="เช่น CP, Betagro, นครสวรรค์พืชผล",
                value="" if is_new else factory.get("name", ""),
                text_size=18,
                filled=True,
            )
            tf_emoji = ft.TextField(
                label="ไอคอน Emoji",
                hint_text="เช่น 🏢, 🏭, 🌾, 🌽",
                value="🏭" if is_new else factory.get("emoji", "🏭"),
                text_size=18,
                width=120,
                filled=True,
            )
            tf_target = ft.TextField(
                label="ความชื้นเป้าหมาย (%)",
                hint_text="เช่น 14.5",
                value="14.5" if is_new else str(factory.get("target_moisture", 14.5)),
                text_size=18,
                keyboard_type=ft.KeyboardType.NUMBER,
                filled=True,
            )
            tf_bias = ft.TextField(
                label="ค่าเบี่ยงเบนความชื้น (Bias %)",
                hint_text="เช่น +1.5 หรือ -1.3 หรือ 0.0",
                value="0.0" if is_new else str(factory.get("moisture_bias", 0.0)),
                text_size=18,
                keyboard_type=ft.KeyboardType.NUMBER,
                filled=True,
            )
            sw_sifting = ft.Switch(
                label="มีการร่อนคัดแยก (เม็ดดี 96.17%, แตก 3.33%, ฝุ่น 0.50%)",
                value=False if is_new else factory.get("req_sifting", False),
            )
            tf_transport = ft.TextField(
                label="ค่าขนส่ง (บาท/กก.แห้ง)",
                hint_text="เช่น 0.30, 0.50, 0.15",
                value="0.30" if is_new else str(factory.get("transport_rate", 0.30)),
                text_size=18,
                keyboard_type=ft.KeyboardType.NUMBER,
                filled=True,
            )
            tf_default_price = ft.TextField(
                label="ราคาขายเริ่มต้น (บาท/กก.)",
                hint_text="เช่น 11.20",
                value="11.00" if is_new else str(factory.get("default_price", 11.00)),
                text_size=18,
                keyboard_type=ft.KeyboardType.NUMBER,
                filled=True,
            )

            def save_factory_data(e):
                name_str = tf_name.value.strip()
                if not name_str:
                    return
                
                try:
                    target_v = float(tf_target.value.strip() or "14.5")
                    bias_v = float(tf_bias.value.strip() or "0.0")
                    trans_v = float(tf_transport.value.strip() or "0.0")
                    def_pr = float(tf_default_price.value.strip() or "11.0")
                    
                    if is_new:
                        new_id = f"fac_{int(datetime.now().timestamp())}"
                        new_factory = {
                            "id": new_id,
                            "name": name_str,
                            "target_moisture": target_v,
                            "moisture_bias": bias_v,
                            "req_sifting": sw_sifting.value,
                            "transport_rate": trans_v,
                            "default_price": def_pr,
                            "color": "#0369A1",
                            "bg_color": "#E0F2FE",
                            "emoji": tf_emoji.value.strip() or "🏭",
                            "is_default": False,
                        }
                        FactoryStorage.add_factory(page, new_factory)
                    else:
                        updated_f = {
                            "name": name_str,
                            "target_moisture": target_v,
                            "moisture_bias": bias_v,
                            "req_sifting": sw_sifting.value,
                            "transport_rate": trans_v,
                            "default_price": def_pr,
                            "emoji": tf_emoji.value.strip() or "🏭",
                        }
                        FactoryStorage.update_factory(page, factory.get("id"), updated_f)
                    
                    # เคลียร์ cache ช่องราคาเพื่อให้หน้าหลักสร้างใหม่ตามค่าที่อัปเดต
                    factory_price_fields.clear()
                    
                    page.pop_dialog()
                    show_factory_manager_screen()
                    page.snack_bar = ft.SnackBar(
                        ft.Text(f"✅ บันทึกข้อมูล '{name_str}' สำเร็จและจดจำค่าเรียบร้อยแล้วค่ะ", size=16),
                        bgcolor=AppColors.WINNER_GREEN,
                        open=True
                    )
                    page.update()
                    
                except ValueError:
                    pass

            edit_dlg = ft.AlertDialog(
                title=ft.Text("➕ เพิ่มโรงงานใหม่" if is_new else f"✏️ แก้ไขสูตร: {factory.get('name')}", size=20, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=460,
                    content=ft.Column(
                        scroll=ft.ScrollMode.ADAPTIVE,
                        spacing=12,
                        controls=[
                            ft.Row([tf_name, tf_emoji], spacing=8),
                            tf_target,
                            tf_bias,
                            sw_sifting,
                            tf_transport,
                            tf_default_price,
                        ]
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: page.pop_dialog()),
                    ft.ElevatedButton(
                        "บันทึกข้อมูล",
                        bgcolor=AppColors.BTN_PRIMARY,
                        color=AppColors.TEXT_WHITE,
                        on_click=save_factory_data,
                    )
                ]
            )
            page.show_dialog(edit_dlg)

        # ยืนยันการลบโรงงาน
        def confirm_delete_factory(f: Dict[str, Any]):
            del_dlg = ft.AlertDialog(
                title=ft.Text(f"⚠️ ยืนยันการลบ {f.get('name')}?", size=20, weight=ft.FontWeight.BOLD),
                content=ft.Text(f"ต้องการลบสูตรโรงงาน '{f.get('name')}' ออกจากระบบใช่หรือไม่คะแม่?", size=16),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: page.pop_dialog()),
                    ft.ElevatedButton(
                        "ลบโรงงานนี้",
                        bgcolor=AppColors.LOSS_RED,
                        color=AppColors.TEXT_WHITE,
                        on_click=lambda e: (
                            FactoryStorage.delete_factory(page, f.get("id")),
                            factory_price_fields.clear(),
                            page.pop_dialog(),
                            show_factory_manager_screen()
                        )
                    )
                ]
            )
            page.show_dialog(del_dlg)

        # ยืนยันการรีเซ็ตกลับเป็นค่าเริ่มต้น
        def confirm_reset_defaults():
            reset_dlg = ft.AlertDialog(
                title=ft.Text("🔄 รีเซ็ตเป็นค่าเริ่มต้น?", size=20, weight=ft.FontWeight.BOLD),
                content=ft.Text("ต้องการรีเซ็ตรายชื่อโรงงานกลับเป็นชุดเริ่มต้น (CP, Betagro, Sunfeed, ก้าวหน้า) ใช่หรือไม่คะ?", size=16),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: page.pop_dialog()),
                    ft.ElevatedButton(
                        "ยืนยันรีเซ็ต",
                        bgcolor=AppColors.LOSS_RED,
                        color=AppColors.TEXT_WHITE,
                        on_click=lambda e: (
                            FactoryStorage.reset_to_defaults(page),
                            factory_price_fields.clear(),
                            page.pop_dialog(),
                            show_factory_manager_screen()
                        )
                    )
                ]
            )
            page.show_dialog(reset_dlg)

        # การ์ดแสดงรายการโรงงานที่มีอยู่
        fac_items = []
        for f in factories:
            sifting_str = "ร่อนคัดแยก" if f.get("req_sifting") else "ไม่ร่อน (100%)"
            bias_str = f"{f.get('moisture_bias', 0.0):+.1f}%"
            
            c = ft.Card(
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=16),
                bgcolor=AppColors.CARD_BG,
                content=ft.Container(
                    padding=14,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row([
                                ft.Text(f.get("emoji", "🏭"), size=28),
                                ft.Column([
                                    ft.Text(f.get("name", ""), size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                                    ft.Text(f"ไบแอส {bias_str} | {sifting_str} | ค่าส่ง {f.get('transport_rate', 0):.2f} ฿", size=13, color=AppColors.TEXT_MUTED),
                                ], spacing=2),
                            ], spacing=10),
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    icon_color=AppColors.BTN_SECONDARY,
                                    tooltip="แก้ไข",
                                    on_click=lambda e, fac=f: open_factory_edit_dialog(fac),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=AppColors.LOSS_RED,
                                    tooltip="ลบ",
                                    on_click=lambda e, fac=f: confirm_delete_factory(fac),
                                ),
                            ], spacing=0)
                        ]
                    )
                )
            )
            fac_items.append(c)

        manager_content = ft.Container(
            width=520,
            padding=ft.Padding.symmetric(horizontal=16, vertical=20),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    # Header
                    ft.Card(
                        elevation=3,
                        shape=ft.RoundedRectangleBorder(radius=20),
                        bgcolor=AppColors.HEADER_BG,
                        content=ft.Container(
                            padding=16,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                                            icon_color=AppColors.TEXT_WHITE,
                                            tooltip="กลับหน้าหลัก",
                                            on_click=lambda e: show_main_calculator_screen(),
                                        ),
                                        ft.Column([
                                            ft.Text("จัดการสูตรโรงงาน", size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                                            ft.Text("เพิ่ม/แก้ไขสูตรเป้าความชื้นและค่าขนส่ง", size=13, color="#94A3B8"),
                                        ], spacing=2),
                                    ], spacing=6),
                                    ft.Text("⚙️", size=28),
                                ]
                            )
                        )
                    ),
                    
                    # ปุ่มเพิ่มโรงงานใหม่ขนาดใหญ่
                    ft.Button(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, size=24, color=AppColors.TEXT_WHITE),
                            ft.Text("+ เพิ่มโรงงานใหม่", size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                        on_click=lambda e: open_factory_edit_dialog(None),
                        bgcolor=AppColors.BTN_PRIMARY,
                        height=56,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16), elevation=3),
                    ),
                    
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"📋 รายชื่อโรงงานทั้งหมด ({len(factories)} โรงงาน)", size=17, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
                            ft.TextButton(
                                content=ft.Text("🔄 รีเซ็ตค่าเริ่มต้น", size=14, color=AppColors.LOSS_RED),
                                on_click=lambda e: confirm_reset_defaults(),
                            )
                        ]
                    ),
                    
                    *fac_items,
                    
                    ft.Container(height=10),
                    
                    ft.Button(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=22, color=AppColors.TEXT_WHITE),
                            ft.Text("← กลับหน้าคำนวณเปรียบเทียบ", size=18, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_WHITE),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                        on_click=lambda e: show_main_calculator_screen(),
                        bgcolor=AppColors.HEADER_BG,
                        height=54,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16)),
                    ),
                    
                    ft.Container(height=20)
                ]
            )
        )
        return manager_content

    # -------------------------------------------------------------------------
    # ฟังก์ชันสลับหน้าจอ (VIEW CONTROLLER)
    # -------------------------------------------------------------------------
    def show_pin_screen():
        current_screen_name[0] = "pin"
        entered_pin.clear()
        update_pin_dots()
        pin_error_text.value = ""
        main_view.content = build_pin_screen()
        page.update()

    def show_main_calculator_screen():
        current_screen_name[0] = "main"
        main_view.content = build_main_calculator_screen()
        page.update()

    def show_results_screen(ranking: List[Dict[str, Any]], b_price: float):
        current_screen_name[0] = "results"
        main_view.content = build_results_screen(ranking, b_price)
        page.update()

    def show_factory_manager_screen():
        current_screen_name[0] = "factory_manager"
        main_view.content = build_factory_manager_screen()
        page.update()

    # เริ่มต้นแอปที่หน้าจอ PIN
    show_pin_screen()
    page.add(main_view)


# =============================================================================
# 6. จุดเริ่มต้นการทำงาน (ENTRY POINT)
# =============================================================================

if __name__ == "__main__":
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    port = int(os.environ.get("PORT", 8550))
    is_cloud = "PORT" in os.environ or "RENDER" in os.environ

    print("=" * 65)
    print("🌽 Corn Multi-Factory Comparison & Profit Optimization System")
    print(f"💾 ที่เก็บข้อมูล: {DATA_DIR}"
          + ("  (โฟลเดอร์แอป)" if DATA_DIR == BASE_DIR else "  (ดิสก์ถาวร)"))

    if is_cloud:
        # ===== โหมด Cloud (Render / Railway / Koyeb) =====
        from contextlib import asynccontextmanager
        import uvicorn
        import flet.fastapi as flet_fastapi
        from fastapi import FastAPI

        print(f"🚀 Cloud Mode: Port {port}")
        print("=" * 65)

        @asynccontextmanager
        async def lifespan(app_instance: FastAPI):
            await flet_fastapi.app_manager.start()
            yield
            await flet_fastapi.app_manager.shutdown()

        fastapi_app = FastAPI(lifespan=lifespan)
        fastapi_app.mount("/", flet_fastapi.app(main))

        uvicorn.run(
            fastapi_app, 
            host="0.0.0.0", 
            port=port, 
            proxy_headers=True, 
            forwarded_allow_ips="*", 
            log_level="info"
        )
    else:
        # ===== โหมด Local (เปิดบนคอมพิวเตอร์) =====
        local_ip = get_local_ip()
        print(f"👉 เปิดบนคอมพิวเตอร์: http://localhost:{port}")
        print(f"📱 เปิดบนมือถือ (Wi-Fi เดียวกัน): http://{local_ip}:{port}")
        print("=" * 65)

        ft.app(
            target=main,
            view=ft.AppView.WEB_BROWSER,
            host="127.0.0.1",
            port=port,
        )
