const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function validateUUID(id: string) {
  if (!uuidRegex.test(id)) {
    throw new Error('Invalid conversation ID')
  }
  return id
}

export function formatDate(raw: string) {
  /** Formats a raw ISO date string as dd.MM.yyyy, hh:mm:ss */
  const date = new Date(raw)
  const formatter = new Intl.DateTimeFormat('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
  return formatter.format(date)
}
