"""
用户 Profile 加载模块

提供统一接口从不同数据源（本地 YAML / Supabase DB）加载用户。
对外暴露 get_first_profile() 和 get_next_profile()，调用方无需关心数据源细节。
"""

import logging
import os
from typing import List, Optional, Tuple

from superc.profile import Profile

logger = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Local YAML loader
# ---------------------------------------------------------------------------

def _load_from_yaml() -> List[Profile]:
    """从 data/local_user.yaml 加载本地用户配置"""
    import yaml

    # 项目根目录下的 data/local_user.yaml
    yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "local_user.yaml")
    if not os.path.exists(yaml_path):
        logger.error(f"本地用户配置文件不存在: {yaml_path}")
        return []

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "users" not in data or not data["users"]:
        logger.error("local_user.yaml 中没有用户数据")
        return []

    profiles = []
    for user in data["users"]:
        profile = Profile(
            vorname=user.get("vorname", ""),
            nachname=user.get("nachname", ""),
            email=user.get("email", ""),
            phone=user.get("phone", ""),
            geburtsdatum_day=user.get("geburtsdatum_day", 1),
            geburtsdatum_month=user.get("geburtsdatum_month", 1),
            geburtsdatum_year=user.get("geburtsdatum_year", 1990),
            preferred_locations=user.get("preferred_locations", "superc"),
        )
        profiles.append(profile)

    logger.info(f"从本地文件加载了 {len(profiles)} 个用户")
    return profiles


# ---------------------------------------------------------------------------
# DB loader
# ---------------------------------------------------------------------------

def _load_first_from_db():
    """从数据库获取第一个等待中的用户，返回 (db_record, Profile) 或 (None, None)"""
    from db.utils import get_first_waiting_profile

    try:
        db_profile = get_first_waiting_profile()
        if db_profile:
            profile = Profile.from_db_record(db_profile)
            return db_profile, profile
        return None, None
    except Exception as e:
        logger.error(f"获取数据库profile失败: {e}")
        return None, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_first_profile(local_mode: bool = False) -> Tuple[Optional[object], Optional[Profile]]:
    """
    获取第一个待处理的用户 profile。

    Returns:
        (db_record, Profile) — 本地模式下 db_record 为 None
        (None, None) — 无用户可处理
    """
    if local_mode:
        profiles = _load_from_yaml()
        if profiles:
            profile = profiles[0]
            logger.info(f"[本地模式] 当前处理用户: {profile.full_name}")
            profile.print_info()
            return None, profile
        else:
            logger.info("本地用户配置为空")
            return None, None

    db_profile, profile = _load_first_from_db()
    if profile:
        logger.info(f"当前处理用户: {profile.full_name} (ID: {db_profile.id})")
        profile.print_info()
    else:
        logger.info("等待队列为空，暂无用户进行检查")
    return db_profile, profile


def get_next_profile(local_mode: bool = False) -> Tuple[Optional[object], Optional[Profile]]:
    """
    获取下一个等待中的用户 profile。
    本地模式下只有一个用户，处理完即结束。
    """
    if local_mode:
        logger.info("[本地模式] 没有更多用户")
        return None, None

    db_profile, profile = _load_first_from_db()
    if profile:
        logger.info(f"找到下一个用户: {profile.full_name} (ID: {db_profile.id})")
        profile.print_info()
    else:
        logger.info("没有更多等待的用户")
    return db_profile, profile
