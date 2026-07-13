export function confirmFavoriteRemoval() {
  return new Promise((resolve) => {
    uni.showModal({
      title: '取消收藏？',
      content: '确认取消收藏这道题吗？取消后该题将从收藏夹中移除。',
      confirmText: '取消收藏',
      cancelText: '继续保留',
      confirmColor: '#d92d20',
      success(result) {
        resolve(Boolean(result.confirm))
      },
      fail() {
        resolve(false)
      }
    })
  })
}
