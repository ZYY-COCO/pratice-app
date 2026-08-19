import { request } from './http'

function buildQuery(params = {}) {
  return Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&')
}

function getPublic(path) {
  return request({
    url: path,
    method: 'GET',
    authRedirect: false,
    header: { Authorization: '' }
  })
}

export function fetchSchoolAnnouncementRegions(params = {}) {
  const query = buildQuery(params)
  return getPublic(`/school-announcements/regions${query ? `?${query}` : ''}`)
}

export function fetchSchoolAnnouncementSchools(params = {}) {
  const query = buildQuery(params)
  return getPublic(`/school-announcements/schools${query ? `?${query}` : ''}`)
}

export function searchSchoolAnnouncements(params = {}) {
  const query = buildQuery(params)
  return getPublic(`/school-announcements/search${query ? `?${query}` : ''}`)
}

export function fetchSchoolAnnouncements(schoolId, params = {}) {
  const query = buildQuery(params)
  return getPublic(
    `/school-announcements/schools/${encodeURIComponent(schoolId)}${query ? `?${query}` : ''}`
  )
}

export function fetchSchoolAnnouncementDetail(announcementId) {
  return getPublic(`/school-announcements/${encodeURIComponent(announcementId)}`)
}
