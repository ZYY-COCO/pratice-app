from fastapi import APIRouter, HTTPException, Query, status

from app.services.major_catalog import (
    MajorCatalogUnavailableError,
    get_school_programs,
    list_regions,
    list_schools,
    search_catalog,
)


router = APIRouter(prefix="/major-catalog", tags=["专业目录"])


def _catalog_unavailable(error: MajorCatalogUnavailableError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="专业目录数据正在准备中，请稍后重试",
    )


@router.get("/regions")
def get_regions(
    exam_code: str | None = Query(default=None, max_length=4),
    catalog_year: str | None = Query(default=None, pattern=r"^\d{4}$"),
) -> dict:
    try:
        return list_regions(exam_code=exam_code, catalog_year=catalog_year)
    except MajorCatalogUnavailableError as error:
        raise _catalog_unavailable(error) from error


@router.get("/schools")
def get_schools(
    region: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=60),
    exam_code: str | None = Query(default=None, max_length=4),
    catalog_year: str | None = Query(default=None, pattern=r"^\d{4}$"),
) -> dict:
    try:
        return list_schools(region=region, keyword=keyword, exam_code=exam_code, catalog_year=catalog_year)
    except MajorCatalogUnavailableError as error:
        raise _catalog_unavailable(error) from error
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该地区") from error


@router.get("/search")
def search_catalog_records(
    keyword: str = Query(..., min_length=1, max_length=60),
    region: str | None = Query(default=None, max_length=20),
    exam_code: str | None = Query(default=None, max_length=4),
    catalog_year: str | None = Query(default=None, pattern=r"^\d{4}$"),
) -> dict:
    try:
        return search_catalog(
            keyword=keyword,
            region=region,
            exam_code=exam_code,
            catalog_year=catalog_year,
        )
    except MajorCatalogUnavailableError as error:
        raise _catalog_unavailable(error) from error
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该地区") from error


@router.get("/schools/{school_id}/programs")
def get_school_catalog_programs(
    school_id: str,
    keyword: str | None = Query(default=None, max_length=60),
    exam_code: str | None = Query(default=None, max_length=4),
    catalog_year: str | None = Query(default=None, pattern=r"^\d{4}$"),
) -> dict:
    try:
        return get_school_programs(
            school_id=school_id,
            keyword=keyword,
            exam_code=exam_code,
            catalog_year=catalog_year,
        )
    except MajorCatalogUnavailableError as error:
        raise _catalog_unavailable(error) from error
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该招生单位") from error
