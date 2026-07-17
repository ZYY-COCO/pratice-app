const fs = require('fs')
const path = require('path')

const projectRoot = path.resolve(__dirname, '..')
const mpRoot = path.join(projectRoot, 'dist', 'build', 'mp-weixin')
const files = [
  path.join(mpRoot, 'project.config.json'),
  path.join(mpRoot, 'project.private.config.json')
]
const appConfigFile = path.join(mpRoot, 'app.json')
const ignoredFiles = ['static/gangyantong-home-wordmark-4k.png']
const stableDebugLibVersion = '3.13.2'

for (const file of files) {
  if (!fs.existsSync(file)) continue

  const config = JSON.parse(fs.readFileSync(file, 'utf8'))
  if (path.basename(file) === 'project.private.config.json') {
    config.libVersion = stableDebugLibVersion
  }
  config.setting = config.setting || {}
  if (path.basename(file) === 'project.private.config.json') {
    config.setting.urlCheck = false
  }
  config.setting.ignoreDevUnusedFiles = false
  config.setting.compileHotReLoad = false
  config.packOptions = config.packOptions || {}
  config.packOptions.ignore = Array.isArray(config.packOptions.ignore) ? config.packOptions.ignore : []
  ignoredFiles.forEach((value) => {
    if (!config.packOptions.ignore.some((item) => item?.type === 'file' && item?.value === value)) {
      config.packOptions.ignore.push({ type: 'file', value })
    }
  })
  fs.writeFileSync(file, `${JSON.stringify(config, null, 2)}\n`, 'utf8')
  console.log(`[mp-weixin] applied stable compile settings in ${path.relative(projectRoot, file)}`)
}

if (fs.existsSync(appConfigFile)) {
  const appConfig = JSON.parse(fs.readFileSync(appConfigFile, 'utf8'))
  appConfig.__usePrivacyCheck__ = true
  fs.writeFileSync(appConfigFile, `${JSON.stringify(appConfig, null, 2)}\n`, 'utf8')
  console.log(`[mp-weixin] enabled privacy checks in ${path.relative(projectRoot, appConfigFile)}`)
}
