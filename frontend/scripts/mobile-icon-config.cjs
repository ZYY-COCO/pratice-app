const variants = Object.freeze({
  blue: '#3478f6',
  sakura: '#d95f93',
  mint: '#2fa36b',
  lavender: '#7668df',
  'circle-glass': '#16786f',
  neutral: '#8a94a6',
  dark: '#263650',
  white: '#ffffff',
  gold: '#f5b700',
  danger: '#e85d75',
  success: '#2fa36b',
  orange: '#d9823a',
  violet: '#7668df',
  'circle-community': '#5b8fdf',
  'circle-scores': '#6e91bf',
  'circle-materials': '#69aa9c',
  'circle-courses': '#778db5'
})

const rasterSources = Object.freeze([
  { source: 'subject-culture-scroll.webp', themeable: false },
  { source: 'subject-math-logo.png', themeable: true },
  { source: 'mock-paper-logo.png', themeable: true },
  { source: 'subject-logic-logo.png', themeable: true },
  { source: 'subject-culture-logo.png', themeable: true },
  { source: 'subject-english-logo.png', themeable: true },
  { source: 'rank-medal-1.png', themeable: false },
  { source: 'rank-medal-2.png', themeable: false },
  { source: 'rank-medal-3.png', themeable: false }
])

module.exports = { variants, rasterSources }
