import { writeFileSync } from 'fs'
import { resolve } from 'path'

export interface EnvConfig {
  companyName: string
  sector: string
  website: string
  port: string
  dataDir: string
  providers: Record<string, string>  // envKey → plaintext value
}

const ALL_PROVIDER_KEYS = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GOOGLE_API_KEY', 'MISTRAL_API_KEY']

export function writeEnv(config: EnvConfig, targetDir = process.cwd()): void {
  const today = new Date().toISOString().slice(0, 10)
  const dataDir = config.dataDir || './data'
  const port = config.port || '8000'

  const lines: string[] = [
    `# 3rdParty Agent — Yapılandırma`,
    `# ${today} tarihinde CLI sihirbazı tarafından oluşturuldu.`,
    `# Bu dosyayı paylaşmayın veya git commit etmeyin!`,
    '',
    `# Şirket`,
    `COMPANY_NAME="${config.companyName}"`,
    config.sector  ? `COMPANY_SECTOR="${config.sector}"`  : `# COMPANY_SECTOR=`,
    config.website ? `COMPANY_WEBSITE="${config.website}"` : `# COMPANY_WEBSITE=`,
    '',
    `# Sunucu`,
    `PORT=${port}`,
    `DATA_DIR=${dataDir}`,
    `DATABASE_URL=sqlite:///${dataDir}/app.db`,
    '',
    `# AI Sağlayıcı Anahtarları`,
    `# Platform başlatıldığında bu anahtarlar şifrelenerek veritabanına aktarılır.`,
  ]

  for (const envKey of ALL_PROVIDER_KEYS) {
    if (config.providers[envKey]) {
      lines.push(`${envKey}=${config.providers[envKey]}`)
    } else {
      lines.push(`# ${envKey}=`)
    }
  }

  lines.push('')

  writeFileSync(resolve(targetDir, '.env'), lines.join('\n'), 'utf-8')
}
