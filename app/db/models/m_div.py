from datetime import date
from decimal import Decimal
import uuid
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, ForeignKey, Index, String, Integer, Date, Numeric

from app.db.models.m_base import Base, BaseMixin

class Div(Base, BaseMixin):
    __tablename__ = "dividends"
    
    company_name: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    symbol:       Mapped[str] = mapped_column(String(50), nullable=True, index=True,unique=True)

    dividend_ex_date: Mapped[date] = mapped_column(Date,nullable=True,index=True,)
    record_date: Mapped[date] = mapped_column(Date,nullable=True,)
    payment_date: Mapped[date] = mapped_column(Date,nullable=True,)
    dividend_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4),nullable=True,)
    indicated_annual_dividend: Mapped[Decimal] = mapped_column(Numeric(10, 4),nullable=True,)
    announcement_date: Mapped[date] = mapped_column(Date,nullable=True,)
    
    # from finnhub
    latest_price: Mapped[Decimal] = mapped_column(Numeric(10, 4),nullable=True,)
    yield_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2),nullable=True,)
    market_cap: Mapped[Decimal] = mapped_column(Numeric(20, 2),nullable=True,)
    
    div_type:   Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    company_type:   Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    



class DivChunkBase(Base, BaseMixin):
    __abstract__ = True

    div_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(String, nullable=True)




class DivChunk1536(DivChunkBase):
    __tablename__ = "dividend_chunks_1536"

    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(1536),
        nullable=True,
    )
    __table_args__ = (
        Index(
            "ix_dividend_chunks_1536_div_chunk",
            "div_id",
            "chunk_index",
            unique=True,
        ),
    )


class DivChunk768(DivChunkBase):
    __tablename__ = "dividend_chunks_768"

    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(768),
        nullable=True,
    )
    __table_args__ = (
        Index(
            "ix_dividend_chunks_768_div_chunk",
            "div_id",
            "chunk_index",
            unique=True,
        ),
    )


class DivChunk3072(DivChunkBase):
    __tablename__ = "dividend_chunks_3072"

    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(3072),
        nullable=True,
    )
    __table_args__ = (
        Index(
            "ix_dividend_chunks_3072_div_chunk",
            "div_id",
            "chunk_index",
            unique=True,
        ),
    )
