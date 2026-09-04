export function createAdaptiveNextRequestBroker() {
  let generation = 0
  let activeRequest = null

  function run(key, task) {
    const normalizedKey = String(key || '')
    if (!normalizedKey) {
      return Promise.reject(new Error('adaptive next request key is required'))
    }
    if (typeof task !== 'function') {
      return Promise.reject(new TypeError('adaptive next request task is required'))
    }

    if (activeRequest?.generation === generation) {
      if (activeRequest.key === normalizedKey) {
        return activeRequest.promise
      }
      const conflict = new Error('another adaptive next request is still running')
      conflict.code = 'ADAPTIVE_NEXT_REQUEST_IN_FLIGHT'
      return Promise.reject(conflict)
    }

    const request = {
      generation,
      key: normalizedKey,
      promise: null
    }
    const isCurrent = () => (
      request.generation === generation &&
      activeRequest === request
    )
    request.promise = Promise.resolve()
      .then(() => task({ isCurrent }))
      .finally(() => {
        if (activeRequest === request) {
          activeRequest = null
        }
      })
    activeRequest = request
    return request.promise
  }

  function invalidate() {
    generation += 1
    activeRequest = null
  }

  function hasInFlight(key) {
    if (!activeRequest || activeRequest.generation !== generation) return false
    return key === undefined || activeRequest.key === String(key || '')
  }

  return {
    run,
    invalidate,
    hasInFlight
  }
}
