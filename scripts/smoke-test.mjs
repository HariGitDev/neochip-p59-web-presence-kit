/* P59 smoke test — runs against the built output in dist/.
 * Usage: npm run build && npm run test
 * Set PROD_READY=1 to make surviving {{TBD}} tokens a hard failure (pre-launch gate). */

import { readFileSync, existsSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const dist = 'dist'
const fails = []
const warns = []

function check(name, cond, detail = '') {
  if (cond) console.log(`  PASS  ${name}`)
  else { console.log(`  FAIL  ${name} ${detail}`); fails.push(name) }
}

console.log('\nP59 smoke test\n')

check('dist/ exists', existsSync(dist))
if (!existsSync(dist)) { console.error('\nRun `npm run build` first.\n'); process.exit(1) }

const html = readFileSync(join(dist, 'index.html'), 'utf8')
const assets = readdirSync(join(dist, 'assets'))
const css = readFileSync(join(dist, 'assets', assets.find((f) => f.endsWith('.css'))), 'utf8')
const js = readFileSync(join(dist, 'assets', assets.find((f) => f.endsWith('.js'))), 'utf8')

check('index.html has a title', /<title>.+<\/title>/.test(html))
check('index.html has a meta description', /name="description"/.test(html))
check('index.html has a viewport tag', /name="viewport"/.test(html))
check('a CSS bundle was emitted', !!assets.find((f) => f.endsWith('.css')))
check('a JS bundle was emitted', !!assets.find((f) => f.endsWith('.js')))

// Design system contract
check('warm accent token present', css.includes('--accent: #B8460E'))
check('no corporate-blue accent leaked in', !/--accent:\s*#[0-9a-f]*(?:1e40af|2563eb|1d4ed8)/i.test(css))
check('focus-visible styling is present', css.includes('focus-visible'))
check('reduced-motion guard is present', css.includes('prefers-reduced-motion'))
check('overflow-x guard on body', /body\s*\{[^}]*overflow-x:\s*hidden/.test(css))

// Content guardrails — these must never appear without Hari's sign-off
const banned = [
  ['authorized distributor claim', /\bwe are an authorized distributor\b/i],
  ['ISO certification claim', /\bISO\s?9001\b/i],
  ['AS9120 claim', /\bAS9120\b/i],
  ['AS6081 claim', /\bAS6081\b/i],
  ['ERAI membership claim', /\bERAI member\b/i],
  ['in-house test lab claim', /\bin-house (test|testing) lab\b/i],
]
for (const [name, re] of banned) {
  check(`guardrail — no ${name}`, !re.test(js))
}

// TBD tokens
const tbdCount = (js.match(/\{\{TBD/g) || []).length
if (process.env.PROD_READY === '1') {
  check('no {{TBD}} tokens survive (PROD_READY)', tbdCount === 0, `found ${tbdCount}`)
} else {
  console.log(`  NOTE  ${tbdCount} {{TBD}} token(s) present — expected pre-launch.`)
  console.log('        Run with PROD_READY=1 to fail the build on these.')
  if (tbdCount === 0) warns.push('no TBD tokens — is content finalised?')
}

console.log('')
if (fails.length) {
  console.error(`FAILED — ${fails.length} check(s): ${fails.join(', ')}\n`)
  process.exit(1)
}
console.log('All checks passed.\n')
