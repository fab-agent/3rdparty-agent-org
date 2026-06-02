import * as p from '@clack/prompts'
import chalk from 'chalk'
import { execa } from 'execa'
import { existsSync, readFileSync } from 'fs'
import { resolve } from 'path'

function getProjectRoot(): string {
  // Walk up from cwd to find docker-compose.yml
  let dir = process.cwd()
  for (let i = 0; i < 5; i++) {
    if (existsSync(resolve(dir, 'docker-compose.yml'))) return dir
    dir = resolve(dir, '..')
  }
  return process.cwd()
}

export async function start() {
  console.log()
  p.intro(chalk.bgBlue.bold.white(' 3rdParty Agent ') + chalk.blue(' — Başlatılıyor'))

  const root = getProjectRoot()
  const envPath = resolve(root, '.env')

  if (!existsSync(envPath)) {
    p.log.error('.env dosyası bulunamadı. Önce kurulumu tamamlayın:')
    console.log(chalk.cyan('\n    3pa init\n'))
    p.outro(chalk.red('Başlatılamadı.'))
    process.exit(1)
  }

  const composePath = resolve(root, 'docker-compose.yml')
  if (!existsSync(composePath)) {
    p.log.error('docker-compose.yml bulunamadı.')
    p.log.info('Projenin kök dizininde bu komutu çalıştırın.')
    p.outro('')
    process.exit(1)
  }

  // Read port from .env for display
  const envContent = readFileSync(envPath, 'utf-8')
  const portMatch = envContent.match(/^PORT=(\d+)/m)
  const port = portMatch ? portMatch[1] : '8000'

  p.log.info(`Proje dizini: ${chalk.cyan(root)}`)
  p.log.info(`Backend port: ${chalk.cyan(port)}`)
  p.log.info('Docker ile başlatılıyor...')
  console.log()

  try {
    await execa('docker', ['compose', 'up', '--build'], {
      cwd: root,
      stdio: 'inherit',
    })
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).code !== 'ERR_PROCESS_EXIT_CODE') {
      p.log.error('Başlatma sırasında hata oluştu.')
    }
  }
}
