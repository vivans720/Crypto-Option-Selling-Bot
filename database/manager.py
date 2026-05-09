from sqlalchemy import create_all, create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Trade, BotState
from config.settings import settings
import logging
import json
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_url: str = settings.DB_PATH):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def save_trade(self, trade_data: dict):
        with self.get_session() as session:
            trade = Trade(**trade_data)
            session.merge(trade)
            session.commit()

    def get_open_trades(self) -> List[Trade]:
        with self.get_session() as session:
            return session.query(Trade).filter(Trade.status == "OPEN").all()

    def close_trade(self, trade_id: str, exit_data: dict):
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                for key, value in exit_data.items():
                    setattr(trade, key, value)
                trade.status = "CLOSED"
                trade.exit_time = datetime.utcnow()
                session.commit()
            else:
                logger.error(f"Trade {trade_id} not found to close.")

    def set_state(self, key: str, value: any):
        with self.get_session() as session:
            val_str = json.dumps(value) if not isinstance(value, str) else value
            state = BotState(key=key, value=val_str)
            session.merge(state)
            session.commit()

    def get_state(self, key: str, default=None):
        with self.get_session() as session:
            state = session.query(BotState).filter(BotState.key == key).first()
            if not state:
                return default
            try:
                return json.loads(state.value)
            except:
                return state.value

    def get_total_pnl(self) -> float:
        with self.get_session() as session:
            from sqlalchemy import func
            return session.query(func.sum(Trade.pnl)).scalar() or 0.0
