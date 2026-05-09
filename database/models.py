from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(String, primary_key=True)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    
    entry_price_call = Column(Float, nullable=False)
    entry_price_put = Column(Float, nullable=False)
    exit_price_call = Column(Float, nullable=True)
    exit_price_put = Column(Float, nullable=True)
    
    call_strike = Column(Float, nullable=False)
    put_strike = Column(Float, nullable=False)
    call_instrument = Column(String, nullable=False)
    put_instrument = Column(String, nullable=False)
    
    qty = Column(Float, default=1.0)
    status = Column(String, default="OPEN") # OPEN, CLOSED
    exit_reason = Column(String, nullable=True)
    pnl = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<Trade(id='{self.id}', status='{self.status}', pnl={self.pnl})>"

class BotState(Base):
    __tablename__ = 'bot_state'
    
    key = Column(String, primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LogEntry(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String)
    module = Column(String)
    message = Column(Text)
