from dataclasses import dataclass
from zoneinfo import ZoneInfo

from .paths import DATA_DIR, SITE_DIR


@dataclass(frozen=True)
class Settings:
    timezone: ZoneInfo = ZoneInfo("Asia/Shanghai")
    site_output_dir: str = str(SITE_DIR)
    data_output_dir: str = str(DATA_DIR)
    max_topic_cards: int = 5


DEFAULT_SETTINGS = Settings()
