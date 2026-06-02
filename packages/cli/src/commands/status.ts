import * as p from '@clack/prompts'
import chalk from 'chalk'
import { existsSync, readFileSync } from 'fs'
import { resolve } from 'path'

interface ProviderStatus {
  provider: string
  display_name: string
  status: string
  has_key: boolean
  models: Array<{ id: string; name: string }>
  last_tested: string | null
}

function getPort(): string {
  const envPath = resolve(process.cwd(), '.env')
  if (!existsSync(envPath)) return '8000'
  const m = readFileSync(envPath, 'utf-8').match(/^PORT=(\d+)/m)
  return m ? m[1] : '8000'
}

function statusIcon(s: string): string {
  if (s === 'active')        return chalk.green('●')
  if (s === 'invalid')       return chalk.red('●')
  if (s === 'unconfigured')  return chalk.gray('○')
  return chalk.gray('○')
}

function statusLabel(s: string): string {
  if (s === 'active')        return chalk.green('Aktif')
  if (s === 'invalid')       return chalk.red('Geçersiz key')
  return chalk.gray('Yapılandırılmamış')
}

export async function status() {
  console.log()
  p.intro(chalk.bgBlue.bold.white(' 3rdParty Agent ') + chalk.blue(' — Platform Durumu'))

  const port = getPort()
  const baseUrl = `http://localhost:${port}`
  const spin = p.spinner()

  // ─ Health check ───────────────────────────────────────────────────────────
  spin.start(`Backend kontrol ediliyor (${chalk.cyan(baseUrl)})...`)

  let healthy = false
  try {
    const resp = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(3_000) })
    healthy = resp.ok
  } catch {
    /* unreachable */
  }

  if (!healthy) {
    spin.stop(chalk.red(`✗ Backend çalışmıyor — ${baseUrl} erişilemiyor`))
    p.log.info('Başlatmak için: ' + chalk.cyan('3pa start'))
    p.outro('')
    return
  }

  spin.stop(chalk.green(`✓ Backend çalışıyor — ${chalk.cyan(baseUrl)}`))

  // ─ Provider status ────────────────────────────────────────────────────────
  try {
    const resp = await fetch(`${baseUrl}/providers/status`, { signal: AbortSignal.timeout(3_000) })
    const providers = await resp.json() as ProviderStatus[]

    console.log()
    console.log(chalk.bold('  AI Sağlayıcıları'))
    console.log(chalk.dim('  ' + '─'.repeat(46)))

    for (const prov of providers) {
      const icon  = statusIcon(prov.status)
      const label = statusLabel(prov.status)
      const models = prov.models.length > 0
        ? chalk.dim(` (${prov.models.map(m => m.name).join(', ')})`)
        : ''
      console.log(`  ${icon}  ${prov.display_name.padEnd(24)} ${label}${models}`)
    }

    const activeCount = providers.filter(p => p.status === 'active').length
    console.log()
    if (activeCount === 0) {
      p.log.warn('Aktif sağlayıcı yok. Ayarlar → Sağlayıcılar sayfasından ekleyebilirsiniz.')
    } else {
      p.log.info(`${activeCount} aktif sağlayıcı / ${providers.length} tanımlı`)
    }
  } catch {
    p.log.warn('Sağlayıcı bilgileri alınamadı.')
  }

  // ─ Config summary ─────────────────────────────────────────────────────────
  try {
    const resp = await fetch(`${baseUrl}/config`, { signal: AbortSignal.timeout(3_000) })
    const cfg = await resp.json() as Record<string, string>
    if (cfg.company_name) {
      console.log()
      console.log(chalk.bold('  Platform'))
      console.log(chalk.dim('  ' + '─'.repeat(46)))
      console.log(`  ${chalk.bold('Şirket:')}  ${cfg.company_name}`)
      if (cfg.company_sector) console.log(`  ${chalk.bold('Sektör:')}  ${cfg.company_sector}`)
    }
  } catch { /* skip */ }

  console.log()
  p.outro(chalk.dim(`Yönetim paneli: ${chalk.cyan('http://localhost:5173')}`))
}
