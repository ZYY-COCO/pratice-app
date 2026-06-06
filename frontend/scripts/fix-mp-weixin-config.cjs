const fs = require('fs')
const path = require('path')

const projectRoot = path.resolve(__dirname, '..')
const mpRoot = path.join(projectRoot, 'dist', 'build', 'mp-weixin')
const files = [
  path.join(mpRoot, 'project.config.json'),
  path.join(mpRoot, 'project.private.config.json')
]

for (const file of files) {
  if (!fs.existsSync(file)) continue

  const config = JSON.parse(fs.readFileSync(file, 'utf8'))
  config.setting = config.setting || {}
  config.setting.ignoreDevUnusedFiles = false
  fs.writeFileSync(file, `${JSON.stringify(config, null, 2)}\n`, 'utf8')
  console.log(`[mp-weixin] disabled ignoreDevUnusedFiles in ${path.relative(projectRoot, file)}`)
}
