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

export function fetchMajorCatalogRegions(params = {}) {
  const query = buildQuery(params)
  return getPublic(`/major-catalog/regions${query ? `?${query}` : ''}`)
}

export function fetchMajorCatalogSchools(params = {}) {
  const query = buildQuery(params)
  return getPublic(`/major-catalog/schools${query ? `?${query}` : ''}`)
}

export function searchMajorCatalog(params = {}) {
  const query = buildQuery(params)
  return getPublic(`/major-catalog/search${query ? `?${query}` : ''}`)
}

export function fetchMajorCatalogSchoolPrograms(schoolId, params = {}) {
  const query = buildQuery(params)
  return getPublic(
    `/major-catalog/schools/${encodeURIComponent(schoolId)}/programs${query ? `?${query}` : ''}`
  )
}
