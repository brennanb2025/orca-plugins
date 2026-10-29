// Catalog CI: validates orca-catalog.json with Orca's own validator, re-fetches every listed
// release to confirm its commit and contentHash, and checks images. Adapted from the official
// catalog's script, minus orca-marketplace.json: every plugin here lives in a subdirectory, which
// Orca builds before catalog format 2 cannot install.
// Usage: ORCA_DIR=/path/to/orca node scripts/check-catalog.mjs
import { execFileSync } from 'node:child_process'
import { isDeepStrictEqual } from 'node:util'
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import process from 'node:process'

const CATALOG_ROOT = path.resolve(import.meta.dirname, '..')
const CATALOG = path.join(CATALOG_ROOT, 'orca-catalog.json')
const ASSETS = path.join(CATALOG_ROOT, 'assets')

const orcaDir = process.env.ORCA_DIR
if (!orcaDir) {
  console.error('set ORCA_DIR to an Orca checkout with dependencies installed')
  process.exit(2)
}
const validator = path.join(orcaDir, 'config', 'scripts', 'validate-plugin-files.mjs')
const errors = []
const readJson = (file) => JSON.parse(readFileSync(file, 'utf8'))

function validate(target) {
  try {
    return {
      ok: true,
      out: execFileSync(process.execPath, [validator, target], {
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe']
      })
    }
  } catch (error) {
    return { ok: false, out: `${error.stdout ?? ''}${error.stderr ?? ''}` }
  }
}

// 1. Schema, limits and image files, exactly as Orca reads them.
const catalogResult = validate(CATALOG)
process.stdout.write(catalogResult.out)
if (!catalogResult.ok) {
  errors.push('orca-catalog.json failed validation (see above)')
}
const catalog = readJson(CATALOG)

// 2. Every release must be the exact bytes its author published.
for (const entry of catalog.plugins ?? []) {
  for (const [index, release] of (entry.releases ?? []).entries()) {
    const at = `${entry.id} releases[${index}] (${release.version})`
    const dir = mkdtempSync(path.join(tmpdir(), 'orca-catalog-release-'))
    const before = errors.length
    try {
      const git = (...args) =>
        execFileSync('git', args, {
          cwd: dir,
          encoding: 'utf8',
          stdio: ['ignore', 'pipe', 'pipe']
        }).trim()
      git('init', '-q')
      git('fetch', '-q', '--depth=1', entry.source.url, release.commit)
      git('checkout', '-q', '--detach', 'FETCH_HEAD')
      if (git('rev-parse', 'HEAD') !== release.commit) {
        errors.push(`${at}: commit ${release.commit} could not be fetched exactly`)
        continue
      }
      const pluginDir = path.join(dir, ...(entry.source.path ?? '').split('/'))
      const manifest = readJson(path.join(pluginDir, 'orca-plugin.json'))
      if (`${manifest.publisher}.${manifest.id}` !== entry.id) {
        errors.push(`${at}: manifest is ${manifest.publisher}.${manifest.id}, not ${entry.id}`)
      }
      const result = validate(pluginDir)
      const marker = result.out.indexOf('Catalog release entry for HEAD')
      if (!result.ok || marker === -1) {
        errors.push(`${at}: plugin does not validate:\n${result.out.trim()}`)
        continue
      }
      const printed = JSON.parse(
        result.out.slice(result.out.indexOf('{', marker), result.out.lastIndexOf('}') + 1)
      )
      for (const [key, value] of Object.entries(printed)) {
        if (!isDeepStrictEqual(release[key], value)) {
          errors.push(
            `${at}: ${key} is ${JSON.stringify(release[key])} in the catalog but ${JSON.stringify(value)} at that commit`
          )
        }
      }
      for (const key of ['capabilities', 'fileTypes']) {
        if (key in release && !(key in printed)) {
          errors.push(`${at}: ${key} is listed but the release has none`)
        }
      }
      if (errors.length === before) {
        console.log(`${at}: matches the published commit`)
      }
    } catch (error) {
      errors.push(
        `${at}: could not fetch ${entry.source.url} at ${release.commit}: ${(error.stderr ?? error.message).toString().trim()}`
      )
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  }
}

// 3. Every file under assets/ belongs to a listed release, so nothing unreviewed is hosted here.
const referenced = new Set(
  (catalog.plugins ?? []).flatMap((entry) =>
    (entry.releases ?? []).flatMap((release) => {
      const images = release.images ?? {}
      return [images.icon, images.cover, ...(images.screenshots ?? [])]
        .filter(Boolean)
        .map((image) => path.posix.normalize(image.path))
    })
  )
)
const walk = (dir) =>
  readdirSync(dir).flatMap((name) => {
    const file = path.join(dir, name)
    return statSync(file).isDirectory()
      ? walk(file)
      : [path.relative(CATALOG_ROOT, file).split(path.sep).join('/')]
  })
for (const file of walk(ASSETS)) {
  if (file !== 'assets/.gitkeep' && !referenced.has(file)) {
    errors.push(`${file}: not referenced by any release in orca-catalog.json`)
  }
}

for (const error of errors) {
  console.error(`error: ${error}`)
}
console.log(errors.length === 0 ? 'catalog: ok' : `catalog: ${errors.length} error(s)`)
process.exit(errors.length === 0 ? 0 : 1)
