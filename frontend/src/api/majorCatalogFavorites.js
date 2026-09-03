import { request } from './http'

function buildQuery(params = {}) {
  return Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&')
}

function buildFavoritePath({ catalogYear, targetType, targetId }) {
  return [
    '/major-catalog/favorites',
    encodeURIComponent(catalogYear),
    encodeURIComponent(targetType),
    encodeURIComponent(targetId)
  ].join('/')
}

export function listMajorCatalogFavorites(params = {}) {
  const query = buildQuery({
    type: params.type || params.targetType,
    year: params.year || params.catalogYear,
    limit: params.limit,
    cursor: params.cursor
  })

  return request({
    url: `/major-catalog/favorites${query ? `?${query}` : ''}`
  })
}

export function getMajorCatalogFavoriteStatuses(refs = []) {
  return request({
    url: '/major-catalog/favorites/status',
    method: 'POST',
    data: {
      refs: refs.map((item) => ({
        catalog_year: item.catalogYear,
        target_type: item.targetType,
        target_id: item.targetId
      }))
    }
  })
}

export function saveMajorCatalogFavorite({ catalogYear, targetType, targetId }) {
  return request({
    url: buildFavoritePath({ catalogYear, targetType, targetId }),
    method: 'PUT'
  })
}

export function deleteMajorCatalogFavorite({ catalogYear, targetType, targetId }) {
  return request({
    url: buildFavoritePath({ catalogYear, targetType, targetId }),
    method: 'DELETE'
  })
}
