# app/api/routes/wage.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File, Query
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_async import get_db
from app.pipelines.pip_div_inject import DivPipeline


injRou = APIRouter()


@injRou.post("/div_hourly", summary="update price, rate limit, background task")
async def run_hourly_pipeline(background_tasks: BackgroundTasks):
    background_tasks.add_task(DivPipeline.run_hourly)
    return {"status": "started", "message": "Hourly dividend pipeline started in background"}   


@injRou.post("/div_daily", summary="1.Delete past data. 2. Upsert new data from nasdaq.")
async def run_daily_pipeline(
    db: AsyncSession = Depends(get_db),
):
    return await DivPipeline.run_daily(db, date.today())


@injRou.post("/div_monthly_google_sheet", summary="1. Read from google sheet. 2. Sync div_type. 3. Prune non-stock type.")
async def monthly_read_from_google_sheet(
    db: AsyncSession = Depends(get_db),
):
    return await DivPipeline.run_monthly(db)


@injRou.post("/div_yearly_symbol_list", summary="1. Grab symbol list from finnhub to csv. 2. Upsert to pg.")
async def yearly_exchange_list(
    db: AsyncSession = Depends(get_db),
):
    return await DivPipeline.run_yearly(db)


