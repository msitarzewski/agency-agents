#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$SCRIPT_DIR/check-agent-originality.sh" <<'PY'
from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile
checker = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="agency-originality-unicode-") as temp:
    root = Path(temp).resolve()
    (root / "scripts").mkdir()
    (root / "engineering").mkdir()
    shutil.copyfile(checker, root / "scripts/check-agent-originality.sh")
    (root / "divisions.json").write_text(json.dumps({"divisions": {"engineering": {}}}))
    def run(body, other):
        for filename, name, content in [("original.md", "Original", body), ("candidate.md", "Candidate", other)]:
            (root / "engineering" / filename).write_text(f"---\nname: {name}\ndescription: fixture\n---\n{content}\n", encoding="utf-8")
        return subprocess.run(["bash", str(root / "scripts/check-agent-originality.sh"), "engineering/candidate.md"], cwd=root, text=True, capture_output=True, env={**os.environ, "ORIGINALITY_FAIL": "40", "ORIGINALITY_WARN": "20"})
    for label, body in [
        ("Chinese", "核验每个证据来源保存原始材料记录测试失败比较修正前后结果保留回滚路径明确尚未解决的问题"),
        ("Japanese", "すべての入力を記録して結果を比較する失敗した試験を保存して変更を検証する不確かな結論を区別する"),
        ("accented Latin", "éclair façade naïveté übermäßige größer déjà mañana información acción revisión verificación evidencia"),
    ]:
        result = run(body, body)
        assert result.returncode == 1 and "100.0%" in result.stdout, (label, result.stdout, result.stderr)
        print(f"PASS identical {label} body rejected despite different metadata")
    result = run("核验每个证据来源保存原始材料记录测试失败比较修正前后结果保留回滚路径明确尚未解决的问题", "描写星辰海洋山川花朵日落清晨风雨季节画布颜色线条旋律故事角色音乐节奏舞台灯光")
    assert result.returncode == 0, (result.stdout, result.stderr)
    print("PASS unrelated Chinese body accepted")
    result = run("alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima", "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima")
    assert result.returncode == 1, result.stdout
    print("PASS existing English duplicate detection retained")
PY
