import { readFileSync } from 'node:fs'
const md = readFileSync(new URL('../skills/audette-create-building/skill.md', import.meta.url), 'utf8')
const must = [
  'switch_customer_account', 'account context', 'audette_property_id',
  'search_documents', 'documents', 'lease', 'general web', 'provenance', 'retrieval date',
  'documents > listings', 'conflicts', 'overture__nearby_buildings', 'save_building',
  'is_primary', 'single', 'multi', 'update_asset_fields', 'verify', 'never invent'
]
const missing = must.filter(s => !md.includes(s))
if (missing.length) throw new Error('audette-create-building skill.md missing: ' + missing.join(', '))
console.log('audette-create-building skill lint OK')
