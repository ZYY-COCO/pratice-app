import { request } from './http'

function getPublic(url) {
  return request({
    url,
    method: 'GET',
    authRedirect: false,
    header: { Authorization: '' }
  })
}

export function fetchHomeContent() {
  return getPublic('/home-content')
}

export function fetchPublishedScorelines() {
  return getPublic('/admission-data/scorelines')
}
