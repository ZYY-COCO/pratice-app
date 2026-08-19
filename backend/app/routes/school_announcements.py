from fastapi import APIRouter, HTTPException, Query, status

from app.services.school_announcements import (
    SchoolAnnouncementUnavailableError,
    get_announcement,
    get_school_announcements,
    list_regions,
    list_schools,
    search_announcements,
)


router = APIRouter(prefix="/school-announcements", tags=["院校公告"])


def _data_unavailable(error: SchoolAnnouncementUnavailableError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="院校公告数据正在准备中，请稍后重试",
    )


@router.get("/regions")
def get_regions(
    year: str | None = Query(default=None, pattern=r"^\d{4}$"),
    notice_type: str | None = Query(default=None, pattern=r"^(brochure|scoreline_retest)$"),
) -> dict:
    try:
        return list_regions(year=year, notice_type=notice_type)
    except SchoolAnnouncementUnavailableError as error:
        raise _data_unavailable(error) from error


@router.get("/schools")
def get_schools(
    region: str | None = Query(default=None, max_length=20),
    year: str | None = Query(default=None, pattern=r"^\d{4}$"),
    notice_type: str | None = Query(default=None, pattern=r"^(brochure|scoreline_retest)$"),
    keyword: str | None = Query(default=None, max_length=80),
) -> dict:
    try:
        return list_schools(region=region, year=year, notice_type=notice_type, keyword=keyword)
    except SchoolAnnouncementUnavailableError as error:
        raise _data_unavailable(error) from error


@router.get("/search")
def search_records(
    keyword: str = Query(..., min_length=1, max_length=80),
    region: str | None = Query(default=None, max_length=20),
    school_id: str | None = Query(default=None, max_length=40),
    year: str | None = Query(default=None, pattern=r"^\d{4}$"),
    notice_type: str | None = Query(default=None, pattern=r"^(brochure|scoreline_retest)$"),
) -> dict:
    try:
        return search_announcements(
            keyword=keyword,
            region=region,
            school_id=school_id,
            year=year,
            notice_type=notice_type,
        )
    except SchoolAnnouncementUnavailableError as error:
        raise _data_unavailable(error) from error


@router.get("/schools/{school_id}")
def get_school_records(
    school_id: str,
    region: str | None = Query(default=None, max_length=20),
    year: str | None = Query(default=None, pattern=r"^\d{4}$"),
    notice_type: str | None = Query(default=None, pattern=r"^(brochure|scoreline_retest)$"),
    keyword: str | None = Query(default=None, max_length=80),
) -> dict:
    try:
        return get_school_announcements(
            school_id=school_id,
            region=region,
            year=year,
            notice_type=notice_type,
            keyword=keyword,
        )
    except SchoolAnnouncementUnavailableError as error:
        raise _data_unavailable(error) from error
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该招生院校") from error


@router.get("/{announcement_id}")
def get_record(announcement_id: str) -> dict:
    try:
        return get_announcement(announcement_id)
    except SchoolAnnouncementUnavailableError as error:
        raise _data_unavailable(error) from error
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该公告") from error
