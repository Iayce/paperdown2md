#!/usr/bin/env bash
# 所有 paperdown2md 的 Python 必须在 skillsplace conda 环境中执行。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

resolve_skillsplace_python() {
  if [[ -n "${SKILLSPLACE_PYTHON:-}" && -x "${SKILLSPLACE_PYTHON}" ]]; then
    echo "${SKILLSPLACE_PYTHON}"
    return 0
  fi
  # macOS 本机（skillscreate-workplace 默认）
  local mac_py="/Users/jaycexu/anaconda3/envs/skillsplace/bin/python"
  if [[ -x "${mac_py}" ]]; then
    echo "${mac_py}"
    return 0
  fi
  # jumphost-inner
  local inner_py="${HOME}/xsjenv/miniconda3/envs/skillsplace/bin/python"
  if [[ -x "${inner_py}" ]]; then
    echo "${inner_py}"
    return 0
  fi
  # Windows Git Bash / WSL 常见路径
  local win_py="/d/Anaconda/envs/skillsplace/python.exe"
  if [[ -x "${win_py}" ]]; then
    echo "${win_py}"
    return 0
  fi
  if command -v conda >/dev/null 2>&1; then
    local via_conda
    via_conda="$(conda run -n skillsplace python -c 'import sys; print(sys.executable)' 2>/dev/null || true)"
    if [[ -n "${via_conda}" && -x "${via_conda}" ]]; then
      echo "${via_conda}"
      return 0
    fi
  fi
  return 1
}

PY="$(resolve_skillsplace_python || true)"
if [[ -z "${PY:-}" ]]; then
  echo "error: 未找到 skillsplace 环境。请先创建/激活 skillsplace，或设置 SKILLSPLACE_PYTHON=..." >&2
  echo "  macOS:  conda activate /Users/jaycexu/anaconda3/envs/skillsplace" >&2
  echo "  Windows: conda activate D:\\Anaconda\\envs\\skillsplace" >&2
  echo "  inner:   conda activate ~/xsjenv/miniconda3/envs/skillsplace" >&2
  exit 1
fi

exec "${PY}" "${SCRIPT_DIR}/paperdown2md.py" "$@"
