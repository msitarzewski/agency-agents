//! agency-convert: the per-agent loop of scripts/convert.sh, in one process.
//!
//! convert.sh stays the entry point and the reference implementation. When this
//! binary is built, convert.sh pipes it the agent file list and it writes the
//! same bytes the Bash converters write. scripts/test-convert-native.sh holds
//! the two to byte-identical output.
//!
//! Usage (called by convert.sh, not by hand):
//!   agency-convert convert --repo-root R --out O --tool T [--append FILE] < files
//!   agency-convert slugs   --repo-root R                                  < files
//!
//! stdin is a NUL-separated list of agent paths relative to the repo root, in
//! the order convert.sh's `find | sort -z` produced them.
//!
//! Text is handled as bytes throughout: the Bash side goes through awk, tr and
//! perl, which do not validate UTF-8 either.

use std::fs;
use std::io::{self, Read, Write};
use std::path::{Path, PathBuf};
use std::process::ExitCode;

const TOOLS: &[&str] = &[
    "antigravity",
    "gemini-cli",
    "opencode",
    "cursor",
    "aider",
    "windsurf",
    "openclaw",
    "qwen",
    "zcode",
    "kimi",
    "codex",
    "osaurus",
    "vibe",
    "dsh",
];

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(msg) => {
            eprintln!("agency-convert: {msg}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let mut args = std::env::args().skip(1);
    let mode = args.next().ok_or("missing mode (convert | slugs)")?;
    let (mut repo_root, mut out, mut tool, mut append) = (None, None, None, None);
    while let Some(flag) = args.next() {
        let value = args
            .next()
            .ok_or_else(|| format!("{flag} requires a value"))?;
        match flag.as_str() {
            "--repo-root" => repo_root = Some(PathBuf::from(value)),
            "--out" => out = Some(PathBuf::from(value)),
            "--tool" => tool = Some(value),
            // convert.sh always passes --append; empty means "not a single-file tool".
            "--append" => append = (!value.is_empty()).then(|| PathBuf::from(value)),
            _ => return Err(format!("unknown option: {flag}")),
        }
    }
    let repo_root = repo_root.ok_or("--repo-root is required")?;

    let mut listing = Vec::new();
    io::stdin()
        .read_to_end(&mut listing)
        .map_err(|e| format!("reading stdin: {e}"))?;
    let files: Vec<String> = listing
        .split(|b| *b == 0)
        .filter(|p| !p.is_empty())
        .map(|p| String::from_utf8_lossy(p).replace('\\', "/"))
        .collect();

    match mode.as_str() {
        "slugs" => print_slugs(&repo_root, &files),
        "convert" => {
            let out = out.ok_or("--out is required")?;
            let tool = tool.ok_or("--tool is required")?;
            if !TOOLS.contains(&tool.as_str()) {
                return Err(format!("unsupported tool '{tool}'"));
            }
            let count = convert_all(&repo_root, &out, &tool, append.as_deref(), &files)?;
            println!("{count}");
            Ok(())
        }
        _ => Err(format!("unknown mode '{mode}'")),
    }
}

// ---------------------------------------------------------------------------
// Agent model: lib.sh get_field / get_body / slugify
// ---------------------------------------------------------------------------

struct Agent {
    /// Path relative to the repo root, forward slashes.
    source: String,
    name: Vec<u8>,
    description: Vec<u8>,
    slug: Vec<u8>,
    body: Vec<u8>,
    raw: Vec<u8>,
}

/// Lines as awk sees them: split on LF, with no empty record after a final LF.
fn lines(text: &[u8]) -> impl Iterator<Item = &[u8]> {
    let text = text.strip_suffix(b"\n").unwrap_or(text);
    let empty = text.is_empty();
    text.split(|b| *b == b'\n').filter(move |_| !empty)
}

/// `$(...)` drops every trailing newline.
fn strip_trailing_newlines(mut v: Vec<u8>) -> Vec<u8> {
    while v.last() == Some(&b'\n') {
        v.pop();
    }
    v
}

fn trim_blank(v: &[u8]) -> &[u8] {
    let is_blank = |b: &u8| *b == b' ' || *b == b'\t';
    let start = v.iter().position(|b| !is_blank(b)).unwrap_or(v.len());
    let end = v
        .iter()
        .rposition(|b| !is_blank(b))
        .map_or(start, |i| i + 1);
    &v[start..end]
}

fn replace(v: &[u8], from: &[u8], to: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(v.len());
    let mut i = 0;
    while i < v.len() {
        if v[i..].starts_with(from) {
            out.extend_from_slice(to);
            i += from.len();
        } else {
            out.push(v[i]);
            i += 1;
        }
    }
    out
}

/// lib.sh get_field's emit(): trim padding, then strip one matching outer quote
/// pair and undo its escapes.
fn emit(val: &[u8]) -> Vec<u8> {
    let v = trim_blank(val);
    if v.len() >= 2 && v[0] == b'"' && v[v.len() - 1] == b'"' {
        let inner = replace(&v[1..v.len() - 1], b"\\\"", b"\"");
        replace(&inner, b"\\\\", b"\\")
    } else if v.len() >= 2 && v[0] == b'\'' && v[v.len() - 1] == b'\'' {
        replace(&v[1..v.len() - 1], b"''", b"'")
    } else {
        v.to_vec()
    }
}

/// lib.sh get_field: first `field: ` in the first frontmatter block, with
/// indented continuation lines folded in, joined by single spaces.
fn get_field(raw: &[u8], field: &str) -> Vec<u8> {
    let prefix = format!("{field}: ");
    let mut fences = 0;
    let mut val: Option<Vec<u8>> = None;
    for line in lines(raw) {
        if line == b"---" {
            fences += 1;
            if fences == 2 && val.is_some() {
                break;
            }
            continue;
        }
        if fences != 1 {
            continue;
        }
        match val.as_mut() {
            None => {
                if let Some(rest) = line.strip_prefix(prefix.as_bytes()) {
                    val = Some(rest.to_vec());
                }
            }
            Some(v) => {
                let rest = trim_blank_start(line);
                if rest.len() < line.len() && !rest.is_empty() {
                    v.push(b' ');
                    v.extend_from_slice(rest);
                } else {
                    break;
                }
            }
        }
    }
    val.map_or_else(Vec::new, |v| strip_trailing_newlines(emit(&v)))
}

fn trim_blank_start(v: &[u8]) -> &[u8] {
    let start = v
        .iter()
        .position(|b| *b != b' ' && *b != b'\t')
        .unwrap_or(v.len());
    &v[start..]
}

/// lib.sh get_body: everything after the second `---` line.
fn get_body(raw: &[u8]) -> Vec<u8> {
    let mut fences = 0;
    let mut body = Vec::new();
    for line in lines(raw) {
        if fences < 2 {
            if line == b"---" {
                fences += 1;
            }
            continue;
        }
        body.extend_from_slice(line);
        body.push(b'\n');
    }
    strip_trailing_newlines(body)
}

/// lib.sh slugify: ASCII lowercase, every other character becomes `-`, runs
/// collapse, one leading and one trailing `-` are dropped. A multi-byte
/// character counts once, as sed sees it in a UTF-8 locale.
fn slugify(value: &[u8]) -> Vec<u8> {
    let mut out: Vec<u8> = Vec::with_capacity(value.len());
    for ch in String::from_utf8_lossy(value).chars() {
        let c = ch.to_ascii_lowercase();
        if c.is_ascii_lowercase() || c.is_ascii_digit() {
            out.push(c as u8);
        } else if out.last() != Some(&b'-') {
            out.push(b'-');
        }
    }
    if out.first() == Some(&b'-') {
        out.remove(0);
    }
    if out.last() == Some(&b'-') {
        out.pop();
    }
    out
}

/// Reads one agent. `None` for a file convert.sh skips: no `---` first line.
fn load(repo_root: &Path, source: &str) -> Result<Option<Agent>, String> {
    let raw = fs::read(repo_root.join(source)).map_err(|e| format!("{source}: {e}"))?;
    if lines(&raw).next() != Some(b"---".as_slice()) {
        return Ok(None);
    }
    let name = get_field(&raw, "name");
    Ok(Some(Agent {
        source: source.to_string(),
        description: get_field(&raw, "description"),
        slug: slugify(&name),
        body: get_body(&raw),
        name,
        raw,
    }))
}

fn print_slugs(repo_root: &Path, files: &[String]) -> Result<(), String> {
    let mut out = io::stdout().lock();
    for source in files {
        let Some(agent) = load(repo_root, source)? else {
            continue;
        };
        if agent.slug.is_empty() {
            continue;
        }
        let mut line = agent.slug.clone();
        line.push(b'\t');
        line.extend_from_slice(source.as_bytes());
        line.push(b'\n');
        out.write_all(&line).map_err(|e| e.to_string())?;
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Output helpers
// ---------------------------------------------------------------------------

/// convert.sh yaml_quote: single-quoted YAML scalar.
fn yaml_quote(v: &[u8]) -> Vec<u8> {
    let mut out = vec![b'\''];
    out.extend_from_slice(&replace(v, b"'", b"''"));
    out.push(b'\'');
    out
}

/// convert.sh toml_escape_string: body of a TOML basic string.
fn toml_escape(v: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(v.len() + v.len() / 8);
    for &b in v {
        match b {
            b'\\' => out.extend_from_slice(b"\\\\"),
            b'"' => out.extend_from_slice(b"\\\""),
            b'\n' => out.extend_from_slice(b"\\n"),
            b'\r' => out.extend_from_slice(b"\\r"),
            b'\t' => out.extend_from_slice(b"\\t"),
            0x0C => out.extend_from_slice(b"\\f"),
            0x08 => out.extend_from_slice(b"\\b"),
            0x00..=0x1F | 0x7F => out.extend_from_slice(format!("\\u{b:04X}").as_bytes()),
            _ => out.push(b),
        }
    }
    out
}

fn join(parts: &[&[u8]]) -> Vec<u8> {
    parts.concat()
}

fn write_file(path: &Path, content: &[u8]) -> Result<(), String> {
    if let Some(dir) = path.parent() {
        fs::create_dir_all(dir).map_err(|e| format!("{}: {e}", dir.display()))?;
    }
    fs::write(path, content).map_err(|e| format!("{}: {e}", path.display()))
}

fn lossy(v: &[u8]) -> String {
    String::from_utf8_lossy(v).into_owned()
}

/// `---` frontmatter of name + description (+ extra lines), then the body.
fn frontmatter_doc(name: &[u8], agent: &Agent, extra: &[u8]) -> Vec<u8> {
    join(&[
        b"---\nname: ",
        &yaml_quote(name),
        b"\ndescription: ",
        &yaml_quote(&agent.description),
        b"\n",
        extra,
        b"---\n",
        &agent.body,
        b"\n",
    ])
}

/// `# name`, description, body: the kimi system prompt and the vibe prompt.
fn prompt_doc(agent: &Agent) -> Vec<u8> {
    join(&[
        b"# ",
        &agent.name,
        b"\n\n",
        &agent.description,
        b"\n\n",
        &agent.body,
        b"\n",
    ])
}

// ---------------------------------------------------------------------------
// Per-tool converters
// ---------------------------------------------------------------------------

fn convert_all(
    repo_root: &Path,
    out: &Path,
    tool: &str,
    append: Option<&Path>,
    files: &[String],
) -> Result<usize, String> {
    let mut accumulated = Vec::new();
    let mut count = 0;
    for source in files {
        let Some(agent) = load(repo_root, source)? else {
            continue;
        };
        if agent.name.is_empty() {
            continue;
        }
        let slug = lossy(&agent.slug);
        let dir = out.join(tool);
        match tool {
            "antigravity" | "osaurus" | "dsh" => {
                let skill = format!("agency-{slug}");
                let doc = frontmatter_doc(skill.as_bytes(), &agent, b"");
                write_file(&dir.join(&skill).join("SKILL.md"), &doc)?;
            }
            "gemini-cli" => {
                let doc = frontmatter_doc(&agent.slug, &agent, b"");
                write_file(&dir.join("agents").join(format!("{slug}.md")), &doc)?;
            }
            "opencode" => {
                let color = resolve_opencode_color(&get_field(&agent.raw, "color"));
                let extra = format!("mode: subagent\ncolor: '{color}'\n");
                let doc = frontmatter_doc(&agent.name, &agent, extra.as_bytes());
                write_file(&dir.join("agents").join(format!("{slug}.md")), &doc)?;
            }
            "cursor" => {
                let doc = join(&[
                    b"---\ndescription: ",
                    &yaml_quote(&agent.description),
                    b"\nglobs: \"\"\nalwaysApply: false\n---\n",
                    &agent.body,
                    b"\n",
                ]);
                write_file(&dir.join("rules").join(format!("{slug}.mdc")), &doc)?;
            }
            "qwen" | "zcode" => {
                let source_tools = get_field(&agent.raw, "tools");
                let tools = if tool == "qwen" {
                    qwen_tools(&source_tools)
                } else {
                    source_tools
                };
                let extra = if tools.is_empty() {
                    Vec::new()
                } else {
                    join(&[b"tools: ", &yaml_quote(&tools), b"\n"])
                };
                let doc = frontmatter_doc(&agent.slug, &agent, &extra);
                write_file(&dir.join("agents").join(format!("{slug}.md")), &doc)?;
            }
            "codex" => {
                let doc = join(&[
                    b"name = \"",
                    &toml_escape(&agent.name),
                    b"\"\ndescription = \"",
                    &toml_escape(&agent.description),
                    b"\"\ndeveloper_instructions = \"",
                    &toml_escape(&agent.body),
                    b"\"\n",
                ]);
                write_file(&dir.join("agents").join(format!("{slug}.toml")), &doc)?;
            }
            "kimi" => {
                let yaml = format!(
                    "version: 1\nagent:\n  name: {slug}\n  extend: default\n  system_prompt_path: ./system.md\n"
                );
                write_file(&dir.join(&slug).join("agent.yaml"), yaml.as_bytes())?;
                write_file(&dir.join(&slug).join("system.md"), &prompt_doc(&agent))?;
            }
            "vibe" => {
                let toml = format!("agent_type = \"agent\"\nsystem_prompt_id = \"{slug}\"\n");
                write_file(
                    &dir.join("agents").join(format!("{slug}.toml")),
                    toml.as_bytes(),
                )?;
                write_file(
                    &dir.join("prompts").join(format!("{slug}.md")),
                    &prompt_doc(&agent),
                )?;
            }
            "openclaw" => convert_openclaw(&dir.join(&slug), &agent)?,
            "aider" => {
                let division = agent.source.split('/').next().unwrap_or("");
                accumulated.extend_from_slice(&join(&[
                    b"\n---\n\n## ",
                    &agent.name,
                    b"\n\n> ",
                    &agent.description,
                    b"\n\nDivision: ",
                    division.as_bytes(),
                    b"\nFull instructions: ",
                    agent.source.as_bytes(),
                    b"\n",
                ]));
            }
            "windsurf" => {
                let rule = [b'='; 80];
                accumulated.extend_from_slice(&join(&[
                    b"\n",
                    &rule,
                    b"\n## ",
                    &agent.name,
                    b"\n",
                    &agent.description,
                    b"\n",
                    &rule,
                    b"\n\n",
                    &agent.body,
                    b"\n\n",
                ]));
            }
            _ => return Err(format!("unsupported tool '{tool}'")),
        }
        count += 1;
    }

    if matches!(tool, "aider" | "windsurf") {
        let path = append.ok_or("--append is required for aider and windsurf")?;
        let mut file = fs::OpenOptions::new()
            .append(true)
            .create(true)
            .open(path)
            .map_err(|e| format!("{}: {e}", path.display()))?;
        file.write_all(&accumulated)
            .map_err(|e| format!("{}: {e}", path.display()))?;
    }
    Ok(count)
}

/// convert.sh resolve_opencode_color: named color or hex to `#RRGGBB`.
fn resolve_opencode_color(value: &[u8]) -> String {
    let c = lossy(value)
        .trim_matches(|ch: char| ch.is_ascii_whitespace())
        .to_ascii_lowercase();
    let mapped = match c.as_str() {
        "cyan" => "#00FFFF",
        "blue" => "#3498DB",
        "green" => "#2ECC71",
        "red" => "#E74C3C",
        "purple" => "#9B59B6",
        "orange" => "#F39C12",
        "teal" => "#008080",
        "indigo" => "#6366F1",
        "pink" => "#E84393",
        "gold" | "yellow" => "#EAB308",
        "amber" => "#F59E0B",
        "neon-green" => "#10B981",
        "neon-cyan" => "#06B6D4",
        "metallic-blue" => "#3B82F6",
        "violet" => "#8B5CF6",
        "rose" => "#F43F5E",
        "lime" => "#84CC16",
        "gray" => "#6B7280",
        "fuchsia" => "#D946EF",
        "slate" => "#64748B",
        "navy" => "#000080",
        other => other,
    };
    let hex = mapped.strip_prefix('#').unwrap_or(mapped);
    if hex.len() == 6 && hex.bytes().all(|b| b.is_ascii_hexdigit()) {
        format!("#{}", hex.to_ascii_uppercase())
    } else {
        "#6B7280".to_string()
    }
}

/// convert.sh qwen_tools: Claude Code tool names to Qwen's, deduplicated.
fn qwen_tools(source: &[u8]) -> Vec<u8> {
    let text = lossy(source);
    let mut out: Vec<&str> = Vec::new();
    for entry in text.split(',') {
        let t = entry.trim_matches(|ch: char| ch.is_ascii_whitespace() || ch == '\x0B');
        if t.is_empty() {
            continue;
        }
        let q = match t {
            "Read" => "read_file",
            "Write" => "write_file",
            "Edit" | "MultiEdit" => "edit",
            "Bash" => "run_shell_command",
            "Grep" => "grep_search",
            "Glob" => "glob",
            "LS" => "list_directory",
            "WebFetch" => "web_fetch",
            "WebSearch" => "web_search",
            "TodoWrite" => "todo_write",
            "NotebookEdit" => "notebook_edit",
            "Task" => "agent",
            other => other,
        };
        if !out.contains(&q) {
            out.push(q);
        }
    }
    out.join(", ").into_bytes()
}

// ---------------------------------------------------------------------------
// OpenClaw: split the body into SOUL.md and AGENTS.md by `## ` section
// ---------------------------------------------------------------------------

fn is_space(b: u8) -> bool {
    matches!(b, b' ' | b'\t' | b'\n' | 0x0B | 0x0C | b'\r')
}

/// lib.sh fence regex `^( {0,3})(`{3,}|~{3,})`: (marker, run length, bytes matched).
fn fence_run(line: &[u8]) -> Option<(u8, usize, usize)> {
    let indent = line.iter().take(3).take_while(|b| **b == b' ').count();
    let marker = *line.get(indent)?;
    if marker != b'`' && marker != b'~' {
        return None;
    }
    let run = line[indent..].iter().take_while(|b| **b == marker).count();
    (run >= 3).then_some((marker, run, indent + run))
}

/// lib.sh fence_closes_p.
fn fence_closes(line: &[u8], open_marker: u8, open_len: usize) -> bool {
    match fence_run(line) {
        Some((marker, run, matched)) => {
            marker == open_marker && run >= open_len && line[matched..].iter().all(|b| is_space(*b))
        }
        None => false,
    }
}

/// `a.b` as a Bash regex: `a`, any one character, `b`.
fn contains_gapped(text: &str, parts: &[&str]) -> bool {
    text.char_indices().any(|(start, _)| {
        let mut rest = &text[start..];
        for (i, part) in parts.iter().enumerate() {
            if i > 0 {
                let mut chars = rest.chars();
                if chars.next().is_none() {
                    return false;
                }
                rest = chars.as_str();
            }
            match rest.strip_prefix(part) {
                Some(tail) => rest = tail,
                None => return false,
            }
        }
        true
    })
}

fn is_soul_header(line: &[u8]) -> bool {
    let h = lossy(line).to_ascii_lowercase();
    h.contains("identity")
        || h.find("learning")
            .is_some_and(|i| h[i + 8..].contains("memory"))
        || h.contains("communication")
        || h.contains("style")
        || contains_gapped(&h, &["critical", "rule"])
        || contains_gapped(&h, &["rules", "you", "must", "follow"])
}

fn convert_openclaw(dir: &Path, agent: &Agent) -> Result<(), String> {
    let (mut soul, mut agents, mut section) = (Vec::new(), Vec::new(), Vec::new());
    let mut target_soul = false;
    let mut fence: Option<(u8, usize)> = None;

    // `<<< "$body"` always yields at least one (possibly empty) line.
    for line in agent.body.split(|b| *b == b'\n') {
        if let Some((marker, len)) = fence {
            if fence_closes(line, marker, len) {
                fence = None;
            }
        } else if let Some((marker, len, _)) = fence_run(line) {
            fence = Some((marker, len));
        } else if line.starts_with(b"##") && line.get(2).is_some_and(|b| is_space(*b)) {
            let bucket = if target_soul { &mut soul } else { &mut agents };
            bucket.append(&mut section);
            target_soul = is_soul_header(line);
        }
        section.extend_from_slice(line);
        section.push(b'\n');
    }
    let bucket = if target_soul { &mut soul } else { &mut agents };
    bucket.append(&mut section);

    soul.push(b'\n');
    agents.push(b'\n');
    write_file(&dir.join("SOUL.md"), &soul)?;
    write_file(&dir.join("AGENTS.md"), &agents)?;

    let emoji = get_field(&agent.raw, "emoji");
    let vibe = get_field(&agent.raw, "vibe");
    let identity = if !emoji.is_empty() && !vibe.is_empty() {
        join(&[b"# ", &emoji, b" ", &agent.name, b"\n", &vibe, b"\n"])
    } else {
        join(&[b"# ", &agent.name, b"\n", &agent.description, b"\n"])
    };
    write_file(&dir.join("IDENTITY.md"), &identity)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn field_unquotes_and_folds() {
        let raw =
            b"---\nname: \"A \\\"B\\\"\"\ndescription: one\n  two\ncolor: 'it''s'\n---\nbody\n";
        assert_eq!(get_field(raw, "name"), b"A \"B\"");
        assert_eq!(get_field(raw, "description"), b"one two");
        assert_eq!(get_field(raw, "color"), b"it's");
        assert_eq!(get_field(raw, "missing"), b"");
    }

    #[test]
    fn body_drops_frontmatter_and_trailing_newlines() {
        assert_eq!(
            get_body(b"---\nname: x\n---\n\n# T\ntext\n\n\n"),
            b"\n# T\ntext"
        );
    }

    #[test]
    fn slug_collapses_and_trims() {
        assert_eq!(slugify(b"Dev/Ops"), b"dev-ops");
        assert_eq!(slugify(b" UI & UX \xE2\x80\x94 Lead "), b"ui-ux-lead");
    }

    #[test]
    fn toml_escapes_controls() {
        assert_eq!(
            toml_escape(b"a\"\\\n\x01\x7F"),
            b"a\\\"\\\\\\n\\u0001\\u007F"
        );
    }

    #[test]
    fn qwen_maps_and_dedupes() {
        assert_eq!(
            qwen_tools(b"Read, MultiEdit,Edit , Custom"),
            b"read_file, edit, Custom"
        );
    }

    #[test]
    fn colors_resolve() {
        assert_eq!(resolve_opencode_color(b" Teal "), "#008080");
        assert_eq!(resolve_opencode_color(b"#ff00aa"), "#FF00AA");
        assert_eq!(resolve_opencode_color(b"ff00aa"), "#FF00AA");
        assert_eq!(resolve_opencode_color(b"mauve"), "#6B7280");
    }

    #[test]
    fn fences_follow_commonmark() {
        assert_eq!(fence_run(b"  ````md"), Some((b'`', 4, 6)));
        assert_eq!(fence_run(b"    ```"), None);
        assert!(fence_closes(b"  ``` ", b'`', 3));
        assert!(!fence_closes(b"```python", b'`', 3));
        assert!(!fence_closes(b"~~~", b'`', 3));
    }

    #[test]
    fn soul_headers() {
        assert!(is_soul_header(b"## Critical Rules"));
        assert!(is_soul_header(b"## Learning & Memory"));
        assert!(!is_soul_header(b"## CriticalRules"));
        assert!(!is_soul_header(b"## Workflow"));
    }
}
