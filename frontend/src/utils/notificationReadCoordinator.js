// Keep notification reads and unread snapshots consistent across page instances.
// A page can start its snapshot request before the user taps a notification;
// the revision check below makes that snapshot retry after the read is persisted.
const pendingReadRequests = new Map()
let readMutationRevision = 0

export function trackNotificationRead(key, operation) {
  const normalizedKey = String(key || '').trim()
  if (normalizedKey && pendingReadRequests.has(normalizedKey)) {
    return pendingReadRequests.get(normalizedKey)
  }

  readMutationRevision += 1
  const promise = Promise.resolve()
    .then(operation)
    .finally(() => {
      if (normalizedKey && pendingReadRequests.get(normalizedKey) === promise) {
        pendingReadRequests.delete(normalizedKey)
      }
    })

  if (normalizedKey) pendingReadRequests.set(normalizedKey, promise)
  return promise
}

async function waitForPendingNotificationReads() {
  // A second read can enter while the first batch is settling, so keep waiting
  // until the queue is empty instead of taking only one snapshot.
  while (pendingReadRequests.size) {
    await Promise.allSettled([...pendingReadRequests.values()])
  }
}

export async function readAfterNotificationMutations(operation) {
  let result
  // Cover the race where a GET started just before a user tapped “查看”. A
  // finite retry limit prevents a busy notification stream from blocking UI.
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const revisionAtStart = readMutationRevision
    await waitForPendingNotificationReads()
    result = await operation()
    if (revisionAtStart === readMutationRevision && pendingReadRequests.size === 0) {
      return result
    }
  }
  return result
}
