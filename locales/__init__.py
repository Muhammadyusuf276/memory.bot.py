import json
import os

# ==================== TARJIMALAR ====================

_LOCALES_DIR = os.path.dirname(__file__)
_CACHE: dict[str, dict] = {}


def _load_locale(lang: str) -> dict:
    """Til faylini yuklash va keshga olish."""
    if lang in _CACHE:
        return _CACHE[lang]
    path = os.path.join(_LOCALES_DIR, f"{lang}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _CACHE[lang] = json.load(f)
            return _CACHE[lang]
    return {}


def get_text(key: str, lang: str = "uz") -> str:
    """Tanlangan til bo'yicha tarjimani olish."""
    data = _load_locale(lang)
    if key in data:
        return data[key]
    # Fallback — o'zbek tili
    if lang != "uz":
        uz_data = _load_locale("uz")
        if key in uz_data:
            return uz_data[key]
    return key
