const fs = require('fs')
const path = require('path')
const matter = require('gray-matter')

// npm install gray-matter first

const divisionMeta = {
  'engineering':        { color: '#7C3AED', emoji_fallback: '💻' },
  'design':             { color: '#EC4899', emoji_fallback: '🎨' },
  'marketing':          { color: '#F97316', emoji_fallback: '📢' },
  'sales':              { color: '#10B981', emoji_fallback: '💼' },
  'product':            { color: '#3B82F6', emoji_fallback: '📊' },
  'project-management': { color: '#8B5CF6', emoji_fallback: '🎬' },
  'testing':            { color: '#EF4444', emoji_fallback: '🧪' },
  'support':            { color: '#14B8A6', emoji_fallback: '🛟' },
  'spatial-computing':  { color: '#06B6D4', emoji_fallback: '🥽' },
  'specialized':        { color: '#F59E0B', emoji_fallback: '🎯' },
  'game-development':   { color: '#84CC16', emoji_fallback: '🎮' },
  'academic':           { color: '#A78BFA', emoji_fallback: '📚' },
}

// Tag suggestions by division
const divisionTags = {
  'engineering':        ['code', 'technical'],
  'design':             ['design', 'visual', 'ux'],
  'marketing':          ['marketing', 'growth', 'content'],
  'sales':              ['sales', 'revenue', 'pipeline'],
  'product':            ['product', 'strategy', 'roadmap'],
  'project-management': ['project', 'coordination', 'planning'],
  'testing':            ['testing', 'qa', 'quality'],
  'support':            ['support', 'operations', 'analytics'],
  'spatial-computing':  ['spatial', 'ar', 'vr', 'xr'],
  'specialized':        ['specialized', 'niche'],
  'game-development':   ['games', 'unity', 'unreal'],
  'academic':           ['academic', 'research', 'writing'],
}

const divisions = Object.keys(divisionMeta)

for (const division of divisions) {
  const divPath = path.join(process.cwd(), division)
  if (!fs.existsSync(divPath)) continue

  const files = fs.readdirSync(divPath).filter(f => f.endsWith('.md'))

  for (const file of files) {
    const filePath = path.join(divPath, file)
    const raw = fs.readFileSync(filePath, 'utf8')
    const parsed = matter(raw)

    // Skip if frontmatter already exists
    if (parsed.data && Object.keys(parsed.data).length > 0) {
      console.log(`SKIP (already has frontmatter): ${file}`)
      continue
    }

    // Extract name from first H1 heading
    const h1Match = raw.match(/^#\s+(.+)/m)
    const rawName = h1Match ? h1Match[1] : file.replace('.md', '')
    // Remove leading emoji from name
    const name = rawName.replace(/^[\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}\s]+/u, '').trim()
    
    // Extract emoji from heading or filename
    const emojiMatch = rawName.match(/^([\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}])/u)
    const emoji = emojiMatch 
      ? emojiMatch[1] 
      : divisionMeta[division].emoji_fallback

    // Build slug from filename
    // engineering-frontend-developer.md → frontend-developer
    const slug = file.replace('.md', '').replace(`${division}-`, '')

    // Build frontmatter object
    const frontmatter = {
      name,
      slug,
      division,
      emoji,
      color: divisionMeta[division].color,
      tags: [...divisionTags[division]],
      tools: ['claude-code', 'cursor', 'copilot', 'windsurf', 'aider', 'qwen'],
      featured: false,
      difficulty: 'intermediate', // default, you can manually update
    }

    // Prepend frontmatter to file
    const newContent = matter.stringify(raw, frontmatter)
    fs.writeFileSync(filePath, newContent)
    console.log(`ADDED frontmatter: ${division}/${file}`)
  }
}

console.log('\nDone. Review the files and manually adjust difficulty/featured/tags.')