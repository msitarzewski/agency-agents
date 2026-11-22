//! The per-file checks of scripts/lint-agents.sh, in one process.
//!
//! lint-agents.sh stays the entry point and the reference. This prints the
//! same report it prints, byte for byte: the header, every ERROR and WARN line
//! in the same order, and the result summary. scripts/test-lint-native.sh
//! holds the two to identical output.

use std::fs;
use std::io::{self, Write};
use std::path::Path;
use std::process::ExitCode;

use crate::{
    fence_closes, fence_run, get_field, is_soul_header, is_space, lines, lossy,
    strip_trailing_newlines,
};

const REQUIRED_FRONTMATTER: [&str; 3] = ["name", "description", "color"];
const RECOMMENDED_SECTIONS: [&str; 3] = ["Identity", "Core Mission", "Critical Rules"];
const QWEN_PLACEHOLDERS: [&str; 3] = [
    "${task_prompt}",
    "${hook_context}",
    "${external_inputs_override}",
];

#[derive(Default)]
struct Report {
    out: Vec<u8>,
    errors: usize,
    warnings: usize,
}

impl Report {
    fn line(&mut self, parts: &[&[u8]]) {
        for part in parts {
            self.out.extend_from_slice(part);
        }
        self.out.push(b'\n');
    }
    fn error(&mut self, file: &str, parts: &[&[u8]]) {
        self.out.extend_from_slice(b"ERROR ");
        self.out.extend_from_slice(file.as_bytes());
        self.line(parts);
        self.errors += 1;
    }
    fn warn(&mut self, file: &str, message: &str) {
        self.line(&[b"WARN  ", file.as_bytes(), b": ", message.as_bytes()]);
        self.warnings += 1;
    }
}

/// `files` is (name as the user gave it, path to open). They differ only where
/// the shell's path spelling is not the platform's.
pub fn run(files: &[(String, String)], known_colors: &str) -> Result<ExitCode, String> {
    let known: Vec<&str> = known_colors.split_whitespace().collect();
    let mut report = Report::default();
    report.line(&[format!("Linting {} agent files...", files.len()).as_bytes()]);
    report.line(&[]);
    for (name, path) in files {
        lint_file(&mut report, name, Path::new(path), &known);
    }
    report.line(&[]);
    let summary = format!(
        "Results: {} error(s), {} warning(s) in {} files.",
        report.errors,
        report.warnings,
        files.len()
    );
    report.line(&[summary.as_bytes()]);
    let failed = report.errors > 0;
    report.line(&[if failed {
        b"FAILED: fix the errors above before merging.".as_slice()
    } else {
        b"PASSED".as_slice()
    }]);
    io::stdout()
        .write_all(&report.out)
        .map_err(|e| format!("writing report: {e}"))?;
    Ok(if failed {
        ExitCode::FAILURE
    } else {
        ExitCode::SUCCESS
    })
}

fn contains(haystack: &[u8], needle: &[u8]) -> bool {
    haystack.windows(needle.len()).any(|w| w == needle)
}

/// A frontmatter line whose value is a folded or literal-free `>` block:
/// `^\s*[alnum_-]+:\s*>([-+][1-9]?|[1-9][-+]?)?(\s+#.*)?\s*$`
fn is_folded_scalar(line: &[u8]) -> bool {
    let text = lossy(line);
    let rest = text.trim_start_matches(|c: char| c.is_ascii() && is_space(c as u8));
    let key_len: usize = rest
        .chars()
        .take_while(|c| c.is_alphanumeric() || *c == '_' || *c == '-')
        .map(char::len_utf8)
        .sum();
    if key_len == 0 {
        return false;
    }
    let Some(rest) = rest[key_len..].strip_prefix(':') else {
        return false;
    };
    let rest = rest.trim_start_matches(|c: char| c.is_ascii() && is_space(c as u8));
    let Some(rest) = rest.strip_prefix('>') else {
        return false;
    };
    let tail_ok = |tail: &[u8]| {
        let after = tail.iter().position(|b| !is_space(*b));
        match after {
            None => true,
            Some(i) => i > 0 && tail[i] == b'#',
        }
    };
    let b = rest.as_bytes();
    let sign = |c: u8| c == b'-' || c == b'+';
    let digit = |c: u8| (b'1'..=b'9').contains(&c);
    // No indicator, a one-character one, or a two-character one.
    tail_ok(b)
        || (!b.is_empty() && (sign(b[0]) || digit(b[0])) && tail_ok(&b[1..]))
        || (b.len() >= 2
            && ((sign(b[0]) && digit(b[1])) || (digit(b[0]) && sign(b[1])))
            && tail_ok(&b[2..]))
}

fn is_hex_color(color: &[u8]) -> bool {
    let hex = color.strip_prefix(b"#").unwrap_or(color);
    hex.len() == 6
        && hex
            .iter()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(b))
}

fn lint_file(report: &mut Report, file: &str, path: &Path, known_colors: &[&str]) {
    let raw = match fs::read(path) {
        Ok(raw) if path.is_file() => raw,
        _ => {
            report.error(file, &[b": not a file or does not exist"]);
            return;
        }
    };

    // 0. CRLF: the repo standard is LF.
    if raw.contains(&b'\r') {
        report.error(
            file,
            &[
                b": CRLF line endings detected \xE2\x80\x94 convert to LF (e.g. 'perl -i -pe \"s/\\r$//\" ",
                file.as_bytes(),
                b"'); repo uses LF per .gitattributes",
            ],
        );
        return;
    }

    // 1. Frontmatter delimiters.
    let all: Vec<&[u8]> = lines(&raw).collect();
    if all.first() != Some(&b"---".as_slice()) {
        report.error(file, &[b": missing frontmatter opening ---"]);
        return;
    }
    let Some(close) = all.iter().skip(1).position(|l| *l == b"---") else {
        report.error(file, &[b": missing frontmatter closing ---"]);
        return;
    };
    let close = close + 1; // index of the closing fence in `all`
    let frontmatter = &all[1..close];
    if frontmatter.iter().all(|l| l.is_empty()) {
        report.error(file, &[b": empty or malformed frontmatter"]);
        return;
    }
    // `$(...)` dropped the trailing blank lines before grep saw the block.
    let last = frontmatter
        .iter()
        .rposition(|l| !l.is_empty())
        .map_or(0, |i| i + 1);
    let frontmatter = &frontmatter[..last];

    if frontmatter.iter().any(|l| is_folded_scalar(l)) {
        report.error(
            file,
            &[b": folded YAML frontmatter is unsupported \xE2\x80\x94 use a single-line scalar"],
        );
        return;
    }

    // 2. Required fields.
    for field in REQUIRED_FRONTMATTER {
        let key = format!("{field}:");
        if !frontmatter.iter().any(|l| l.starts_with(key.as_bytes())) {
            report.error(
                file,
                &[b": missing frontmatter field '", field.as_bytes(), b"'"],
            );
        } else if get_field(&raw, field).iter().all(|b| is_space(*b)) {
            report.error(
                file,
                &[
                    b": frontmatter field '",
                    field.as_bytes(),
                    b"' must not be empty",
                ],
            );
        }
    }

    // 2b. The color has to be one the converters can resolve.
    let color = get_field(&raw, "color").to_ascii_lowercase();
    if !color.is_empty()
        && !known_colors.is_empty()
        && !is_hex_color(&color)
        && !known_colors.iter().any(|k| k.as_bytes() == color)
    {
        report.error(
            file,
            &[
                b": color '",
                &color,
                b"' is not a #RRGGBB value or a name the converters know",
            ],
        );
        let mut names = String::new();
        for k in known_colors {
            names.push_str(k);
            names.push(' ');
        }
        report.line(&[b"      known names: ", names.as_bytes()]);
        report.line(&[
            b"      use a hex value, or add '",
            &color,
            b"' to resolve_opencode_color() in scripts/convert.sh",
        ]);
    }

    // 3. Recommended sections. This body drops every `---` line, as the awk does.
    let mut body = Vec::new();
    let mut fences = 0;
    for line in &all {
        if *line == b"---" {
            fences += 1;
        } else if fences >= 2 {
            body.extend_from_slice(line);
            body.push(b'\n');
        }
    }
    let body = strip_trailing_newlines(body);
    let body_lower = body.to_ascii_lowercase();
    for section in RECOMMENDED_SECTIONS {
        let needle = section.to_ascii_lowercase();
        let found = body_lower
            .split(|b| *b == b'\n')
            .any(|l| contains(l, needle.as_bytes()));
        if !found {
            report.warn(file, &format!("missing recommended section '{section}'"));
        }
    }

    // 4. Meaningful content.
    let words = body
        .split(|b| is_space(*b))
        .filter(|w| !w.is_empty())
        .count();
    if words < 50 {
        report.warn(file, "body seems very short (< 50 words)");
    }

    // 4b. Names Qwen Code substitutes at launch are reserved.
    if QWEN_PLACEHOLDERS
        .iter()
        .any(|p| contains(&body, p.as_bytes()))
    {
        report.error(
            file,
            &[
                b": uses a placeholder Qwen Code fills at launch (${task_prompt}, ${hook_context} or ${external_inputs_override}) \xE2\x80\x94 rename it",
            ],
        );
    }

    // 5. Fences and section headers, walked from the file so errors can name a line.
    let (mut soul_headers, mut agents_headers) = (0, 0);
    let mut fence: Option<(u8, usize, usize)> = None; // marker, run length, opening line
    for (index, line) in all.iter().enumerate().skip(close + 1) {
        let lineno = index + 1;
        if let Some((marker, len, opened)) = fence {
            if fence_closes(line, marker, len) {
                fence = None;
            } else if fence_run(line).is_some_and(|(m, run, _)| m == marker && run >= len) {
                let m3 = [marker; 3];
                let m4 = [marker; 4];
                report.error(
                    file,
                    &[
                        format!(":{lineno}: '").as_bytes(),
                        line,
                        format!("' inside the block opened at line {opened} does not nest \u{2014} the next bare ").as_bytes(),
                        &m3,
                        b" closes the outer block instead",
                    ],
                );
                report.line(&[
                    b"      fence the outer block with a longer run (e.g. ",
                    &m4,
                    b"markdown ... ",
                    &m4,
                    b") so the inner ones stay inside it",
                ]);
            }
            continue;
        }
        if let Some((marker, len, _)) = fence_run(line) {
            fence = Some((marker, len, lineno));
        } else if line.starts_with(b"##") && line.get(2).is_some_and(|b| is_space(*b)) {
            if is_soul_header(line) {
                soul_headers += 1;
            } else {
                agents_headers += 1;
            }
        }
    }

    if let Some((_, _, opened)) = fence {
        report.error(
            file,
            &[format!(
                ":{opened}: code block is never closed \u{2014} everything after line {opened} renders as code"
            )
            .as_bytes()],
        );
    }
    if soul_headers == 0 {
        report.warn(file, "no section headers map to SOUL.md in convert.sh");
    }
    if agents_headers == 0 {
        report.warn(file, "no section headers map to AGENTS.md in convert.sh");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn folded_scalars() {
        assert!(is_folded_scalar(b"description: >"));
        assert!(is_folded_scalar(b"  description:   >-  "));
        assert!(is_folded_scalar(b"description: >2+ # note"));
        assert!(is_folded_scalar(b"description: >+1"));
        assert!(!is_folded_scalar(b"description: > text"));
        assert!(!is_folded_scalar(b"description: >#x"));
        assert!(!is_folded_scalar(b"description: a > b"));
        assert!(!is_folded_scalar(b": >"));
    }

    #[test]
    fn hex_colors() {
        assert!(is_hex_color(b"#a1b2c3"));
        assert!(is_hex_color(b"a1b2c3"));
        assert!(!is_hex_color(b"#a1b2c"));
        assert!(!is_hex_color(b"teal"));
    }
}
