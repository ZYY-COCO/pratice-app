from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.dependencies import get_current_user_id
from app.schemas.major_catalog import (
    MajorCatalogFavoriteListResponse,
    MajorCatalogFavoriteMutationResponse,
    MajorCatalogFavoriteStatusRequest,
    MajorCatalogFavoriteStatusResponse,
    MajorCatalogFavoriteTargetType,
)
from app.services.major_catalog import (
    MajorCatalogUnavailableError,
    get_school_programs,
    list_regions,
    list_schools,
    search_catalog,
)
from app.services.major_catalog_favorites import (
    MajorCatalogFavoritesMigrationRequiredError,
    MajorCatalogFavoritesUnavailableError,
    delete_major_catalog_favorite as delete_major_catalog_favorite_record,
    get_major_catalog_favorite_statuses as get_major_catalog_favorite_status_records,
    list_major_catalog_favorites as list_major_catalog_favorite_records,
    save_major_catalog_favorite as save_major_catalog_favorite_record,
)


router = APIRouter(prefix="/major-catalog", tags=["专业目录"])


def _catalog_unavailable(error: MajorCatalogUnavailableError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="专业目录数据正在准备中，请稍后重试",
    )


def _favorites_unavailable(error: MajorCatalogFavoritesUnavailableError) -> HTTPException:
    detail = (
        "院校专业收藏尚未完成数据库升级"
        if isinstance(error, MajorCatalogFavoritesMigrationRequiredError)
        else "院校专业收藏服务暂时不可用，请稍后重试"
    )
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


@router.get("/favorites", response_model=MajorCatalogFavoriteListResponse)
def list_major_catalog_favorites(
    target_type: MajorCatalogFavoriteTargetType | None = Query(default=None, alias="type"),
    catalog_year: str | None = Query(default=None, alias="year", pattern=r"^20\d{2}$"),
    limit: int = Query(default=30, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str = Depends(get_current_user_id),
) -> MajorCatalogFavoriteListResponse:
    try:
        result = list_major_catalog_favorite_records(
            user_id=user_id,
            limit=limit,
            cursor=cursor,
            target_type=target_type,
            catalog_year=catalog_year,
        )
        return MajorCatalogFavoriteListResponse(**result)
    except MajorCatalogFavoritesUnavailableError as error:
        raise _favorites_unavailable(error) from error
    except MajorCatalogUnavailableError as error:
        raise _catalog_unavailable(error) from error


@router.post("/favorites/status", response_model=MajorCatalogFavoriteStatusResponse)
def get_major_catalog_favorite_statuses(
    payload: MajorCatalogFavoriteStatusRequest,
    user_id: str = Depends(get_current_user_id),
) -> MajorCatalogFavoriteStatusResponse:
    try:
        result = get_major_catalog_favorite_status_records(
            user_id=user_id,
            references=[item.model_dump() for item in payload.items],
        )
        return MajorCatalogFavoriteStatusResponse(**result)
    except MajorCatalogFavoritesUnavailableError as error:
        raise _favorites_unavailable(error) from error
    except MajorCatalogUnavailableError as error:
        raise _catalog_unavailable(error) from error


@router.put(
    "/favorites/{catalog_year}/{target_type}/{target_id}",
    response_model=MajorCatalogFavoriteMutationResponse,
)
def save_major_catalog_favorite(
    catalog_year: str = Path(pattern=r"^20\d{2}$"),
    target_type: MajorCatalogFavoriteTargetType = Path(),
    target_id: str = Path(min_length=1, max_length=128),
    user_id: str = Depends(get_current_user_id),
) -> MajorCatalogFavoriteMutationResponse:
    try:
        result = save_major_catalog_favorite_record(
            user_id=user_id,
            catalog_year=catalog_year,
            target_type=target_type,
            target_id=target_id,
        )
        return MajorCatalogFavoriteMutationResponse(**result)
    except KeyError as error:
        label = "院校" if target_type == "school" else "专业"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到该年份的{label}",
        ) from error
    except MajorCatalogFavoritesUnavailableError as error:
        raise _favorites_unavailable(error) from error
    except MajorCatalogUnavailableError as error:
        raise _catalog_unavailable(error) from error


@router.delete(
    "/favorites/{catalog_year}/{target_type}/{target_id}",
    response_model=MajorCatalogFavoriteMutationResponse,
)
def delete_major_catalog_favorite(
    catalog_year: str = Path(pattern=r"^20\d{2}$"),
    target_type: MajorCatalogFavoriteTargetType = Path(),
    target_id: str = Path(min_length=1, max_length=128),
    user_id: str = Depends(get_current_user_id),
) -> MajorCatalogFavoriteMutationResponse:
    try:
        result = delete_major_catalog_favorite_record(
            user_id=user_id,
            catalog_year=catalog_year,
            target_type=target_type,
            target_id=target_id,
        )
        return MajorCatalogFavoriteMutationResponse(**result)
    except MajorCatalogFavoritesUnavailableError as error:
        raise _favorites_unavailable(error) from error


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
