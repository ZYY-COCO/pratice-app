const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const sharp = require('sharp')
const { variants, rasterSources } = require('./mobile-icon-config.cjs')

const projectRoot = path.resolve(__dirname, '..')
const sourceDir = path.join(projectRoot, 'src', 'static', 'ui-icons')
const outputDir = path.join(sourceDir, 'png')
const manifestPath = path.join(outputDir, 'manifest.json')

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function resetOutputDirectory() {
  const relativeOutput = path.relative(sourceDir, outputDir)
  if (relativeOutput !== 'png' || path.basename(outputDir) !== 'png') {
    throw new Error(`Refusing to clear unexpected icon output directory: ${outputDir}`)
  }
  fs.rmSync(outputDir, { recursive: true, force: true })
  fs.mkdirSync(outputDir, { recursive: true })
}

function normalizeOriginalSvg(markup) {
  return markup
    .replace(/fill=(['"])\s*\1/gi, 'fill="#000000"')
    .replace(/currentColor/gi, '#000000')
}

function tintSvg(markup, color) {
  let result = normalizeOriginalSvg(markup)
    .replace(/fill=(['"])(.*?)\1/gi, (match, quote, value) => {
      return /^(?:none|url\()/i.test(value) ? match : `fill="${color}"`
    })
    .replace(/stroke=(['"])(.*?)\1/gi, (match, quote, value) => {
      return /^(?:none|url\()/i.test(value) ? match : `stroke="${color}"`
    })

  result = result.replace(/<svg\b([^>]*)>/i, (match, attrs) => {
    const withoutColor = attrs.replace(/\sstyle=(['"])(.*?)\1/i, '')
    // 只设置 currentColor 的颜色，不要在根节点强制填充。开放路径（例如
    // 圆弧、时间线）一旦继承 fill 会被闭合填满，导致线性图标变成实心块。
    return `<svg${withoutColor} style="color:${color}">`
  })
  return result
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

function hexToRgb(value) {
  const normalized = String(value || '').replace('#', '')
  return {
    r: Number.parseInt(normalized.slice(0, 2), 16) || 0,
    g: Number.parseInt(normalized.slice(2, 4), 16) || 0,
    b: Number.parseInt(normalized.slice(4, 6), 16) || 0
  }
}

async function prepareRasterLogo(source) {
  const { data, info } = await sharp(source).ensureAlpha().raw().toBuffer({ resolveWithObject: true })
  const output = Buffer.from(data)

  for (let index = 0; index < output.length; index += 4) {
    const luminance = output[index] * 0.2126 + output[index + 1] * 0.7152 + output[index + 2] * 0.0722
    // 用户提供的图标为近白色画布上的深色图形。把画布转为透明，同时保留抗锯齿边缘。
    const inkOpacity = Math.max(0, Math.min(1, (245 - luminance) / 210))
    output[index + 3] = Math.round(output[index + 3] * inkOpacity)
  }

  return { data: output, info }
}

function tintPreparedRaster(prepared, color) {
  const { r, g, b } = hexToRgb(color)
  const output = Buffer.from(prepared.data)
  for (let index = 0; index < output.length; index += 4) {
    if (output[index + 3] === 0) continue
    output[index] = r
    output[index + 1] = g
    output[index + 2] = b
  }
  return { data: output, info: prepared.info }
}

async function render(source, destination, size) {
  fs.mkdirSync(path.dirname(destination), { recursive: true })
  const input = Buffer.isBuffer(source) ? source : Buffer.from(source)
  await sharp(input, { density: 384 })
    .resize(size, size, {
      fit: 'contain',
      position: 'centre',
      // 非正方形 SVG 在留白时必须使用透明像素；否则 App 端会把黑色补白显示成横线。
      background: { r: 0, g: 0, b: 0, alpha: 0 }
    })
    .png({ compressionLevel: 9, adaptiveFiltering: true })
    .toFile(destination)
}

async function renderPreparedRaster(prepared, destination, size) {
  fs.mkdirSync(path.dirname(destination), { recursive: true })
  await sharp(prepared.data, { raw: prepared.info })
    .resize(size, size, {
      fit: 'contain',
      position: 'centre',
      background: { r: 0, g: 0, b: 0, alpha: 0 }
    })
    .png({ compressionLevel: 9, adaptiveFiltering: true })
    .toFile(destination)
}

async function main() {
  resetOutputDirectory()

  const sources = fs.readdirSync(sourceDir)
    .filter((name) => name.toLowerCase().endsWith('.svg'))
    .sort()
  const vectorSourceHashes = {}
  const rasterSourceHashes = {}

  for (const sourceName of sources) {
    const sourcePath = path.join(sourceDir, sourceName)
    const outputName = sourceName.replace(/\.svg$/i, '.png')
    const raw = fs.readFileSync(sourcePath, 'utf8')
    vectorSourceHashes[sourceName] = sha256(raw)

    await render(
      normalizeOriginalSvg(raw),
      path.join(outputDir, 'original', outputName),
      256
    )

    for (const [variant, color] of Object.entries(variants)) {
      await render(tintSvg(raw, color), path.join(outputDir, variant, outputName), 160)
    }
  }

  for (const rasterEntry of rasterSources) {
    const { source: sourceName, themeable } = normalizeRasterSourceEntry(rasterEntry)
    if (!sourceName) continue
    const sourcePath = path.join(sourceDir, sourceName)
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Configured raster icon source is missing: ${sourceName}`)
    }
    const sourceBuffer = fs.readFileSync(sourcePath)
    const outputName = sourceName.replace(/\.[^.]+$/i, '.png')
    rasterSourceHashes[sourceName] = sha256(sourceBuffer)
    if (!themeable) {
      await render(
        sourceBuffer,
        path.join(outputDir, 'original', outputName),
        256
      )
      continue
    }

    const prepared = await prepareRasterLogo(sourceBuffer)
    await renderPreparedRaster(prepared, path.join(outputDir, 'original', outputName), 256)
    for (const [variant, color] of Object.entries(variants)) {
      await renderPreparedRaster(
        tintPreparedRaster(prepared, color),
        path.join(outputDir, variant, outputName),
        160
      )
    }
  }

  fs.writeFileSync(
    manifestPath,
    `${JSON.stringify({
      schemaVersion: 1,
      variants,
      vectorSources: vectorSourceHashes,
      rasterSources: rasterSourceHashes
    }, null, 2)}\n`,
    'utf8'
  )

  console.log(
    `Generated ${sources.length} vector icons in ${Object.keys(variants).length + 1} variants and ${rasterSources.length} raster fallback.`
  )
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
