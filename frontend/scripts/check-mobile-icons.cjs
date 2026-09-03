const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const { variants, rasterSources } = require('./mobile-icon-config.cjs')

const projectRoot = path.resolve(__dirname, '..')
const srcRoot = path.join(projectRoot, 'src')
const sourceIconRoot = path.join(srcRoot, 'static', 'ui-icons')
const runtimeIconRoot = path.join(srcRoot, 'static', 'ui-icons', 'png')
const manifestPath = path.join(runtimeIconRoot, 'manifest.json')
const ignoredDirectories = new Set(['node_modules', 'dist', 'unpackage', 'static'])
const sourceExtensions = new Set(['.vue', '.js', '.ts', '.json', '.css', '.scss', '.sass', '.less'])
const unstableGlyphIconPattern = /[\u2301\u2315\u231b\u23f1\u2605\u2661\u2665\u2726]|\p{Extended_Pictographic}/u
const errors = []

function walk(directory) {
  const files = []
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue
    const fullPath = path.join(directory, entry.name)
    if (entry.isDirectory()) files.push(...walk(fullPath))
    else if (sourceExtensions.has(path.extname(entry.name))) files.push(fullPath)
  }
  return files
}

function walkAllFiles(directory) {
  const files = []
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name)
    if (entry.isDirectory()) files.push(...walkAllFiles(fullPath))
    else files.push(fullPath)
  }
  return files
}

function relative(file) {
  return path.relative(projectRoot, file).replaceAll('\\', '/')
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function sortedKeys(value) {
  return Object.keys(value || {}).sort()
}

function sameJson(left, right) {
  return JSON.stringify(left) === JSON.stringify(right)
}

function normalizeRasterSourceEntry(entry) {
  if (typeof entry === 'string') {
    return { source: entry, themeable: false }
  }
  return {
    source: String(entry?.source || '').trim(),
    themeable: entry?.themeable === true
  }
}

function requireNonEmptyFile(file, message) {
  if (!fs.existsSync(file) || !fs.statSync(file).isFile() || fs.statSync(file).size === 0) {
    errors.push(message)
  }
}

function usesUnsupportedCssFilter(content) {
  return content.split(/\r?\n/).some((line) => {
    const match = line.match(/(?:^|[;{]\s*)(?:-webkit-)?filter\s*:\s*([^;}]+)/i)
    if (!match) return false
    return !/^none(?:\s*!important)?\s*$/i.test(match[1].trim())
  })
}

for (const file of walk(srcRoot)) {
  const filePath = relative(file)
  if (filePath.startsWith('src/pages-sub-admin/') || /src\/components\/Admin/.test(filePath)) continue
  const content = fs.readFileSync(file, 'utf8')

  if (/(?:\/static\/|@\/static\/|\.\.?\/)[^'"`\s)]+\.svg(?:\?[^'"`\s)]*)?/i.test(content)) {
    errors.push(`${filePath}: mobile runtime still references an SVG icon`)
  }
  if (/(?:-webkit-)?mask(?:-image)?\s*:/i.test(content)) {
    errors.push(`${filePath}: mobile runtime still uses CSS mask rendering`)
  }
  if (usesUnsupportedCssFilter(content)) {
    errors.push(`${filePath}: mobile runtime still uses CSS filter rendering`)
  }
  if (unstableGlyphIconPattern.test(content)) {
    errors.push(`${filePath}: mobile runtime still contains an emoji or unstable glyph icon`)
  }
}

const vectorSources = fs.readdirSync(sourceIconRoot)
  .filter((name) => name.toLowerCase().endsWith('.svg'))
  .sort()
const normalizedRasterSources = rasterSources
  .map(normalizeRasterSourceEntry)
  .filter(({ source }) => Boolean(source))
const expectedPngFiles = new Set()
let manifest = null

try {
  manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'))
} catch (error) {
  errors.push('src/static/ui-icons/png/manifest.json: generated icon manifest is missing or invalid')
}

if (manifest) {
  if (manifest.schemaVersion !== 1) {
    errors.push('src/static/ui-icons/png/manifest.json: unsupported manifest version')
  }
  if (!sameJson(manifest.variants, variants)) {
    errors.push('src/static/ui-icons/png/manifest.json: icon color variants are stale')
  }
  if (!sameJson(sortedKeys(manifest.vectorSources), vectorSources)) {
    errors.push('src/static/ui-icons/png/manifest.json: vector source list is stale')
  }
}

for (const sourceName of vectorSources) {
  const sourcePath = path.join(sourceIconRoot, sourceName)
  const outputName = sourceName.replace(/\.svg$/i, '.png')
  if (manifest && manifest.vectorSources?.[sourceName] !== sha256(fs.readFileSync(sourcePath))) {
    errors.push(`src/static/ui-icons/${sourceName}: source changed after PNG generation`)
  }

  for (const variant of ['original', ...Object.keys(variants)]) {
    const relativePng = `${variant}/${outputName}`
    expectedPngFiles.add(relativePng)
    requireNonEmptyFile(
      path.join(runtimeIconRoot, variant, outputName),
      `src/static/ui-icons/png/${relativePng}: generated icon is missing or empty`
    )
  }

  const blueVariantPath = path.join(runtimeIconRoot, 'blue', outputName)
  const neutralVariantPath = path.join(runtimeIconRoot, 'neutral', outputName)
  if (
    sourceName.startsWith('tab-') &&
    fs.existsSync(blueVariantPath)
    && fs.existsSync(neutralVariantPath)
    && sha256(fs.readFileSync(blueVariantPath)) === sha256(fs.readFileSync(neutralVariantPath))
  ) {
    errors.push(
      `src/static/ui-icons/${sourceName}: blue and neutral PNG variants are identical`
    )
  }
}

for (const { source: sourceName, themeable } of normalizedRasterSources) {
  const sourcePath = path.join(sourceIconRoot, sourceName)
  const outputName = sourceName.replace(/\.[^.]+$/i, '.png')
  if (!fs.existsSync(sourcePath)) {
    errors.push(`src/static/ui-icons/${sourceName}: configured raster source is missing`)
    continue
  }
  if (manifest && manifest.rasterSources?.[sourceName] !== sha256(fs.readFileSync(sourcePath))) {
    errors.push(`src/static/ui-icons/${sourceName}: source changed after PNG generation`)
  }
  const requiredVariants = themeable ? ['original', ...Object.keys(variants)] : ['original']
  for (const variant of requiredVariants) {
    const relativePng = `${variant}/${outputName}`
    expectedPngFiles.add(relativePng)
    requireNonEmptyFile(
      path.join(runtimeIconRoot, variant, outputName),
      `src/static/ui-icons/png/${relativePng}: generated icon is missing or empty`
    )
  }
}

if (
  manifest &&
  !sameJson(
    sortedKeys(manifest.rasterSources),
    normalizedRasterSources.map(({ source }) => source).sort()
  )
) {
  errors.push('src/static/ui-icons/png/manifest.json: raster source list is stale')
}

if (fs.existsSync(runtimeIconRoot)) {
  for (const file of walkAllFiles(runtimeIconRoot)) {
    if (path.extname(file).toLowerCase() !== '.png') continue
    const relativePng = path.relative(runtimeIconRoot, file).replaceAll('\\', '/')
    if (!expectedPngFiles.has(relativePng)) {
      errors.push(`src/static/ui-icons/png/${relativePng}: orphaned generated icon`)
    }
  }
}

if (errors.length) {
  console.error(errors.join('\n'))
  process.exit(1)
}

console.log('Mobile icon audit passed: user-facing runtime uses generated PNG assets.')
