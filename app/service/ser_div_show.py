# app/services/report_service.py
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.db.models.m_div import Div
from app.db.repo.repo_div_show import DivRepository


class DivService:

    @staticmethod
    async def list_divs(
        db: AsyncSession,
    ):
        return await DivRepository.list_divs(db)


    @staticmethod
    async def list_divs_emb(
        db: AsyncSession,
    ):
        return await DivRepository.list_divs_emb(db)

    # @staticmethod
    # async def reports_pagination(
    #     db: AsyncSession,
    #     page: int,
    #     page_size: int,
    #     query: str | None = None,
    #     sort_by: str = "created_at",
    #     sort_order: str = "desc",
    # ):
    #     stmt = select(Report)

    #     if query:
    #         stmt = stmt.where(Report.source.ilike(f"%{query}%"))

    #     column = getattr(Report, sort_by, Report.created_at)
    #     stmt = stmt.order_by(column.desc() if sort_order == "desc" else column.asc())

    #     total_stmt = select(func.count()).select_from(stmt.subquery())
    #     total = (await db.execute(total_stmt)).scalar()

    #     stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    #     items = (await db.execute(stmt)).scalars().all()

    #     return {
    #         "items": items,
    #         "total": total,
    #         "page": page,
    #         "page_size": page_size,
    #         "total_pages": (total + page_size - 1) // page_size,
    #     }


    # @staticmethod
    # async def list_filtered_reports(
    #     db: AsyncSession,
    #     page: int,
    #     page_size: int,
    #     sort_by: str | None,
    #     sort_order: str | None,
    #     source: str | None,
    #     deal_stage: str | None,
    #     lead_owner: str | None,
    #     first_name: str | None = None,
    #     last_name: str | None = None,
    #     company: str | None = None,
    # ):
    #     stmt = select(Report).where(Report.is_deleted.is_(False))

    #     if source:
    #         stmt = stmt.where(Report.source.ilike(f"{source}%"))

    #     if deal_stage:
    #         stmt = stmt.where(Report.deal_stage.ilike(f"{deal_stage}%"))

    #     if lead_owner:
    #         stmt = stmt.where(Report.lead_owner.ilike(f"{lead_owner}%"))

    #     if first_name:
    #         stmt = stmt.where(Report.first_name.ilike(f"{first_name}%"))

    #     if last_name:
    #         stmt = stmt.where(Report.last_name.ilike(f"{last_name}%"))

    #     if company:
    #         stmt = stmt.where(Report.company.ilike(f"{company}%"))


    #     count_stmt = select(func.count()).select_from(stmt.subquery())
    #     total_result = await db.execute(count_stmt)
    #     total_items = total_result.scalar() or 0
    #     total_pages = (total_items + page_size - 1) // page_size  # ceil division

    #     if sort_by:
    #         col = getattr(Report, sort_by, None)
    #         if col is not None:
    #             stmt = stmt.order_by(col.desc() if sort_order == "desc" else col.asc())

    #     stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    #     result = await db.execute(stmt)
    #     items = result.scalars().all()

    #     return {
    #         "items": items,
    #         "page": page,
    #         "total_pages": total_pages,
    #         "page_size": page_size,
    #         "total_items": total_items,
    #     }
