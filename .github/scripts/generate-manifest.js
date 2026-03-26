const fs = require('fs')
const path = require('path')
const matter = require('gray-matter')

const divisions = [
  'engineering', 'design', 'marketing', 'sales', 'product',
  'project-management', 'testing', 'support', 'spatial-computing',
  'specialized', 'game-development', 'academic'
]

const divisionMeta = {
  'engineering':        { color: '#7C3AED', name: 'Engineering' },
  'design':             { color: '#EC4899', name: 'Design' },
  'marketing':          { color: '#F97316', name: 'Marketing' },
  'sales':              { color: '#10B981', name: 'Sales' },
  'product':            { color: '#3B82F6', name: 'Product' },
  'project-management': { color: '#8B5CF6', name: 'Project Management' },
  'testing':            { color: '#EF4444', name: 'Testing' },
  'support':            { color: '#14B8A6', name: 'Support' },
  'spatial-computing':  { color: '#06B6D4', name: 'Spatial Computing' },
  'specialized':        { color: '#F59E0B', name: 'Specialized' },
  'game-development':   { color: '#84CC16', name: 'Game Development' },
  'academic':           { color: '#A78BFA', name: 'Academic' },
}

const manifest = {
  version: '1.0.0',
  lastUpdated: new Date().toISOString().split('T')[0],
  totalAgents: 0,
  source: 'https://github.com/salmandev/agency-agents',
  credit: 'Originally created by @msitarzewski · Fork maintained by @salmandev',
  divisions: []
}

let totalAgents = 0

for (const division of divisions) {
  const divPath = path.join(process.cwd(), division)
  if (!fs.existsSync(divPath)) {
    console.log(`SKIP (folder not found): ${division}`)
    continue
  }

  const files = fs.readdirSync(divPath)
    .filter(f => f.endsWith('.md'))
    .sort()

  const agents = []

  for (const file of files) {
    const filePath = path.join(divPath, file)
    let raw

    try {
      raw = fs.readFileSync(filePath, 'utf8')
    } catch (e) {
      console.log(`ERROR reading ${file}: ${e.message}`)
      continue
    }

    let parsed
    try {
      parsed = matter(raw)
    } catch (e) {
      console.log(`ERROR parsing frontmatter in ${file}: ${e.message}`)
      console.log(`  → Fix the frontmatter in ${division}/${file} and re-run`)
      continue
    }

    const fm = parsed.data

    // Extract name — from frontmatter or from H1 heading
    let name = fm.name
    if (!name) {
      const h1 = raw.match(/^#\s+(.+)/m)
      name = h1 ? h1[1].replace(/^[\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}\s]+/u, '').trim() : file
    }

    // Build slug from filename
    const slug = file
      .replace('.md', '')
      .replace(new RegExp(`^${division}-`), '')

    agents.push({
      id: file.replace('.md', ''),
      slug,
      name,
      emoji:        fm.emoji        || '🤖',
      color:        fm.color        || divisionMeta[division].color,
      division,
      description:  fm.description  || fm.vibe || '',
      tags:         fm.tags         || [],
      tools:        fm.tools        || ['claude-code', 'cursor', 'copilot', 'windsurf', 'aider', 'qwen'],
      featured:     fm.featured     || false,
      difficulty:   fm.difficulty   || 'intermediate',
      custom:       fm.custom       || false,
      file:         `${division}/${file}`,
      rawUrl:       `https://raw.githubusercontent.com/salmandev/agency-agents/main/${division}/${file}`,
    })
  }

  manifest.divisions.push({
    id:         division,
    name:       divisionMeta[division].name,
    color:      divisionMeta[division].color,
    agentCount: agents.length,
    agents
  })

  totalAgents += agents.length
  console.log(`✅ ${divisionMeta[division].name}: ${agents.length} agents`)
}

manifest.totalAgents = totalAgents

fs.writeFileSync(
  path.join(process.cwd(), 'manifest.json'),
  JSON.stringify(manifest, null, 2)
)

console.log(`\n✅ manifest.json generated`)
console.log(`   ${totalAgents} agents across ${manifest.divisions.length} divisions`)
console.log(`   Saved to: ${path.join(process.cwd(), 'manifest.json')}`)