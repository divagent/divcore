# app/api/routes/reports.py
import os
import secrets
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_async import get_db
from app.service.ser_div_az_search import search_dividends
from app.service.ser_div_show import DivService
from app.service.ser_az_data_lake import list_files, write_json

divRou = APIRouter()


@divRou.get("/list")
async def list_divs(db: AsyncSession = Depends(get_db),):
    return await DivService.list_divs(db)


@divRou.get("/emb")
async def list_divs_emb(db: AsyncSession = Depends(get_db),):
    return await DivService.list_divs_emb(db)


# @divRou.get("/list_lake")
# def list_files_endpoint():
#     files = list_files()
#     return {"files": files}



   


    
# @divRou.get("/pagination")
# async def list_reports(
#     db: AsyncSession = Depends(get_db),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(10, le=100),
#     query: str | None = None,
#     sort_by: str = "created_at",
#     sort_order: str = "desc",
# ):
#     return await DivService.reports_pagination(
#         db=db,
#         page=page,
#         page_size=page_size,
#         query=query,
#         sort_by=sort_by,
#         sort_order=sort_order,
#     )
    
    
# # FastAPI PATCH endpoint (required)
# @divRou.patch("/{report_id}")
# async def update_report(
#     report_id: str,
#     payload: dict,
#     db: AsyncSession = Depends(get_db),
# ):
#     return await DivService.update_partial(db, report_id, payload)




# @divRou.get("/list_filtered_reports")
# async def list_filtered_reports(
#     page: int = 1,
#     page_size: int = 10,
#     sort_by: str | None = None,
#     sort_order: str | None = "asc",
#     source: str | None = None,
#     deal_stage: str | None = None,
#     lead_owner: str | None = None,
#     first_name: str | None = None,
#     last_name: str | None = None,
#     company: str | None = None,
#     db: AsyncSession = Depends(get_db),
# ):
#     return await DivService.list_filtered_reports(
#         db,
#         page=page,
#         page_size=page_size,
#         sort_by=sort_by,
#         sort_order=sort_order,
#         source=source,
#         deal_stage=deal_stage,
#         lead_owner=lead_owner,
#         first_name=first_name,
#         last_name=last_name,
#         company=company,
#     )
