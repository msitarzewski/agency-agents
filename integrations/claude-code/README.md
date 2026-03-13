# Claude Code 集成

The Agency 是专为 Claude Code 打造的。无需转换 —— 智能体可以直接以原本的 `.md` + YAML Frontmatter 格式运行。

## 安装

```bash
# 将所有智能体复制到你的 Claude Code 智能体目录
./scripts/install.sh --tool claude-code

# 或者手动复制某个类别
cp engineering/*.md ~/.claude/agents/
```

## 激活智能体

在任何 Claude Code 会话中，通过名称引用智能体：

```
激活前端开发工程师，帮我构建一个 React 组件。
```

```
使用现实检查员验证此功能是否已具备生产就绪条件。
```

## 智能体目录

智能体按部门组织。详见 [主 README](../../README.md) 以获取完整的 61 位专家阵容。
