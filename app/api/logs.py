"""SLS 日志查询 API"""
from fastapi import APIRouter

from app.models.schemas import LogQueryRequest, LogQueryResponse, LogVerifyConfig
from app.services.sls_query import sls_query_service

router = APIRouter(prefix="/api", tags=["logs"])


@router.post("/logs/query", response_model=LogQueryResponse)
async def query_logs(request: LogQueryRequest):
    """查询 SLS 日志。"""
    config = LogVerifyConfig(
        project=request.project,
        logstore=request.logstore,
        query=request.query,
        from_time=request.from_time,
        to_time=request.to_time,
        endpoint=request.endpoint,
        profile=request.profile,
        max_results=request.max_results,
        wait_seconds=0,
    )
    return sls_query_service.query(config)
