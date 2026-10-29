"""نواة الأمن: سياق المستخدم، فلترة السرية، وسجل التدقيق.

القاعدة: كل بيانات تصل للواجهة أو للمودل تمر عبر visible_transactions().
لا نعتمد على البرومبت لإخفاء السري — الصفوف المحجوبة لا تصل للمودل أصلاً.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from config import CONFIDENTIALITY_LEVELS

# الأدوار: مدير إدارة (manager) يرى بيانات إدارته فقط ويعمل عليها؛ مراجع (reviewer) يقرأ فقط دون أي تعديل
ROLE_CLEARANCE = {"guest": 0, "reviewer": 1, "employee": 1, "manager": 1, "admin": 2}
ROLE_LABEL = {"guest": "زائر", "reviewer": "مراجع (قراءة فقط)", "employee": "موظف",
              "manager": "مدير إدارة", "admin": "مدير النظام"}
WRITE_ROLES = {"employee", "manager", "admin"}  # من يحق له التعديل (المراجع والزائر لا)


@dataclass(frozen=True)
class AuthContext:
    logged_in: bool = False
    username: str | None = None
    role: str = "guest"
    department: str = ""  # إدارة مدير الإدارة (تقيّد ما يراه)

    @property
    def can_write(self) -> bool:  # هل لدور المستخدم حق التعديل؟ (المراجع والزائر لا)
        return self.logged_in and self.role in WRITE_ROLES

    @property
    def role_label(self) -> str:  # اسم الدور بالعربية للعرض
        return ROLE_LABEL.get(self.role, self.role)

    @property
    def clearance(self) -> int:  # رقم صلاحية السرية للدور (0 زائر .. 2 مدير)
        return ROLE_CLEARANCE.get(self.role, 0)

    @property
    def visible_levels(self) -> list[str]:  # مستويات السرية التي يراها المستخدم
        return [n for n, v in CONFIDENTIALITY_LEVELS.items() if v <= self.clearance]


GUEST = AuthContext()


def visible_transactions(df: pd.DataFrame, ctx: AuthContext) -> pd.DataFrame:  # يُرجع فقط الصفوف المسموحة لصلاحية المستخدم
    """يُرجع فقط الصفوف المسموحة لصلاحية المستخدم. القيمة غير المعروفة = أعلى سرية."""
    top = max(CONFIDENTIALITY_LEVELS.values())
    levels = df["السرية"].map(CONFIDENTIALITY_LEVELS).fillna(top)
    out = df[levels <= ctx.clearance]
    if ctx.role == "manager" and ctx.department and "القسم المكلف" in out.columns:
        out = out[out["القسم المكلف"].astype(str) == ctx.department]  # مدير الإدارة: إدارته فقط
    return out


# ---- سجل التدقيق (Audit Trail) ----
_logger = logging.getLogger("audit")
if not _logger.handlers:
    _handler = logging.FileHandler("audit.log", encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def audit(event: str, ctx: AuthContext, **details) -> None:  # يسجّل حدثاً في سجل التدقيق (audit.log)
    # repr() يمنع حقن أسطر مزيفة في السجل
    extra = " ".join(f"{k}={v!r}" for k, v in details.items())
    _logger.info("%s | user=%s role=%s %s", event, ctx.username or "-", ctx.role, extra)