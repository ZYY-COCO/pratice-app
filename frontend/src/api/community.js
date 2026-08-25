import { request, uploadFileRequest } from './http'

export function fetchCommunityPosts(params = {}) {
  return request({
    url: '/circle/community/posts',
    method: 'GET',
    data: params,
    authRedirect: false
  })
}

export function fetchLikedCommunityPosts(params = {}) {
  return request({
    url: '/circle/community/liked-posts',
    method: 'GET',
    data: params
  })
}

export function fetchMyCommunityPosts(params = {}) {
  return request({
    url: '/circle/community/my-posts',
    method: 'GET',
    data: params
  })
}

export function deleteMyCommunityPosts(postIds = []) {
  return request({
    url: '/circle/community/my-posts',
    method: 'DELETE',
    data: { post_ids: postIds }
  })
}

export function fetchMyCommunityReports(params = {}) {
  return request({
    url: '/circle/community/my-reports',
    method: 'GET',
    data: params
  })
}

export function fetchMyCommunityContentStatus(params = {}) {
  return request({
    url: '/circle/community/my-content-status',
    method: 'GET',
    data: params
  })
}

export function createCommunityModerationAppeal(targetType, targetId, payload) {
  return request({
    url: `/circle/community/moderation/${encodeURIComponent(targetType)}/${encodeURIComponent(targetId)}/appeals`,
    method: 'POST',
    data: payload
  })
}

export function fetchCommunityPost(postId) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}`,
    method: 'GET',
    authRedirect: false
  })
}

export function createCommunityPost(payload) {
  return request({
    url: '/circle/community/posts',
    method: 'POST',
    data: payload
  })
}

export function uploadCommunityImage({ filePath, file, fileName }) {
  return uploadFileRequest({
    url: '/circle/community/images',
    filePath,
    file,
    fileName,
    name: 'file',
    timeout: 120000
  })
}

export function toggleCommunityPostLike(postId) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/like`,
    method: 'POST',
    data: {}
  })
}

export function toggleCommunityCommentLike(postId, commentId) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/comments/${encodeURIComponent(commentId)}/like`,
    method: 'POST',
    data: {}
  })
}

export function fetchCommunityPostLikes(postId, params = {}) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/likes`,
    method: 'GET',
    data: params,
    authRedirect: false
  })
}

export function createCommunityComment(postId, payload) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/comments`,
    method: 'POST',
    data: payload
  })
}

export function deleteCommunityComment(postId, commentId) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/comments/${encodeURIComponent(commentId)}`,
    method: 'DELETE'
  })
}

export function createCommunityPostReport(postId, payload) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/reports`,
    method: 'POST',
    data: payload
  })
}

export function createCommunityCommentReport(postId, commentId, payload) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/comments/${encodeURIComponent(commentId)}/reports`,
    method: 'POST',
    data: payload
  })
}

export function registerCommunityPostView(postId, payload) {
  return request({
    url: `/circle/community/posts/${encodeURIComponent(postId)}/view`,
    method: 'POST',
    data: payload,
    authRedirect: false
  })
}
