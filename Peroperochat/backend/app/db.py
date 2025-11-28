import os
import json
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy import text as sql_text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def _now_local_minute() -> datetime:
    d = datetime.now()
    return d.replace(second=0, microsecond=0)

def _local_offset() -> timedelta:
    try:
        return datetime.now() - datetime.utcnow()
    except Exception:
        return timedelta(0)

class MemoryItem(Base):
    __tablename__ = "memory_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(32), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now_local_minute, nullable=False)
    meta = Column(Text, default="{}", nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

class ConversationCounter(Base):
    __tablename__ = "conversation_counter"
    id = Column(Integer, primary_key=True)
    count = Column(Integer, default=0, nullable=False)

def _db_path() -> str:
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "memory.db")

def get_engine():
    path = _db_path()
    url = f"sqlite:///{path}"
    engine = create_engine(url, echo=False, future=True)
    return engine

SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, future=True)

def _migrate_drop_weight(engine):
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql_text("PRAGMA table_info(memory_items)")).fetchall()
            cols = [r[1] for r in rows] if rows else []
            if "weight" in cols:
                conn.execute(sql_text("BEGIN"))
                conn.execute(sql_text(
                    "CREATE TABLE memory_items_new (\n"
                    "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                    "  type VARCHAR(32) NOT NULL,\n"
                    "  text TEXT NOT NULL,\n"
                    "  created_at DATETIME NOT NULL,\n"
                    "  meta TEXT NOT NULL,\n"
                    "  deleted BOOLEAN NOT NULL DEFAULT 0\n"
                    ")"
                ))
                conn.execute(sql_text(
                    "INSERT INTO memory_items_new (id, type, text, created_at, meta, deleted) "
                    "SELECT id, type, text, created_at, meta, deleted FROM memory_items"
                ))
                conn.execute(sql_text("DROP TABLE memory_items"))
                conn.execute(sql_text("ALTER TABLE memory_items_new RENAME TO memory_items"))
                conn.execute(sql_text("COMMIT"))
    except Exception:
        pass

def init_db():
    engine = get_engine()
    _migrate_drop_weight(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        if s.get(ConversationCounter, 1) is None:
            cc = ConversationCounter(id=1, count=0)
            s.add(cc)
            s.commit()
    try:
        with SessionLocal() as s:
            rows = s.query(MemoryItem).all()
            changed = 0
            offset = _local_offset()
            for r in rows:
                try:
                    if isinstance(r.created_at, datetime):
                        # meta标记避免重复迁移
                        meta_obj = {}
                        try:
                            meta_obj = json.loads(str(r.meta or "{}"))
                        except Exception:
                            meta_obj = {}
                        if not bool(meta_obj.get("tz_fixed", False)):
                            nm = (r.created_at + offset).replace(second=0, microsecond=0)
                            r.created_at = nm
                            meta_obj["tz_fixed"] = True
                            r.meta = json.dumps(meta_obj, ensure_ascii=False)
                            s.add(r)
                            changed += 1
                except Exception:
                    continue
            if changed:
                s.commit()
    except Exception:
        pass

def add_memory_item(type_: str, text: str, meta: Optional[Dict[str, Any]] = None) -> int:
    with SessionLocal() as s:
        meta_str = json.dumps(meta or {}, ensure_ascii=False)
        item = MemoryItem(type=type_, text=text, meta=meta_str)
        s.add(item)
        s.commit()
        s.refresh(item)
        return item.id

def list_memory_items(type_: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    with SessionLocal() as s:
        q = s.query(MemoryItem).filter(MemoryItem.deleted == False)
        if type_:
            q = q.filter(MemoryItem.type == type_)
        q = q.order_by(MemoryItem.created_at.desc()).limit(max(1, min(limit, 500))).offset(max(0, offset))
        rows = q.all()
        return [
            {
                "id": r.id,
                "type": r.type,
                "text": r.text,
                "created_at": r.created_at.replace(second=0, microsecond=0).isoformat(),
                "meta": r.meta,
            }
            for r in rows
        ]

def soft_delete_memory_item(id_: int) -> bool:
    with SessionLocal() as s:
        r = s.get(MemoryItem, int(id_))
        if not r:
            return False
        r.deleted = True
        s.add(r)
        s.commit()
        return True

def find_memory_item_id_by_type_text(type_: str, text: str) -> Optional[int]:
    with SessionLocal() as s:
        t = str(text or "").strip()
        r = (
            s.query(MemoryItem)
            .filter(MemoryItem.deleted == False)
            .filter(MemoryItem.type == type_)
            .filter(MemoryItem.text == t)
            .order_by(MemoryItem.id.desc())
            .first()
        )
        return (r.id if r else None)

def increment_conversation_count() -> int:
    with SessionLocal() as s:
        cc = s.get(ConversationCounter, 1)
        if not cc:
            cc = ConversationCounter(id=1, count=0)
            s.add(cc)
        cc.count = int(cc.count or 0) + 1
        s.add(cc)
        s.commit()
        return cc.count

def reset_all():
    engine = get_engine()
    with SessionLocal() as s:
        s.query(MemoryItem).delete()
        cc = s.get(ConversationCounter, 1)
        if not cc:
            cc = ConversationCounter(id=1, count=0)
            s.add(cc)
        else:
            cc.count = 0
            s.add(cc)
        s.commit()
    try:
        Base.metadata.drop_all(engine, tables=[MemoryItem.__table__])
        Base.metadata.create_all(engine, tables=[MemoryItem.__table__])
    except Exception:
        pass
