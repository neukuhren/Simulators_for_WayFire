#!/usr/bin/env bash
# Установка проекта на Mac в фиксированную директорию.
# Запускайте на вашем Mac в Терминале (не в облачном агенте):
#   bash scripts/setup-mac.sh

set -euo pipefail

PROJECT_DIR="/Users/me/dev/Simulators_for_WayFire"
REPO_URL="https://github.com/neukuhren/Simulators_for_WayFire.git"
BRANCH="cursor/planning-wayfire-simulators-91b3"

echo "==> Каталог проекта: ${PROJECT_DIR}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Ошибка: этот скрипт только для macOS." >&2
  exit 1
fi

mkdir -p "$(dirname "${PROJECT_DIR}")"

if [[ -d "${PROJECT_DIR}/.git" ]]; then
  echo "==> Репозиторий уже есть — обновляем"
  git -C "${PROJECT_DIR}" fetch origin
  git -C "${PROJECT_DIR}" checkout "${BRANCH}" 2>/dev/null || git -C "${PROJECT_DIR}" checkout -b "${BRANCH}" "origin/${BRANCH}"
  git -C "${PROJECT_DIR}" pull origin "${BRANCH}"
else
  echo "==> Клонируем репозиторий"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${PROJECT_DIR}"
fi

cd "${PROJECT_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Ошибка: нужен python3 (Xcode CLT или python.org)." >&2
  exit 1
fi

echo "==> Виртуальное окружение .venv"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Python-зависимости (pip)"
python -m pip install --upgrade pip
pip install -e ".[dev]"

echo "==> Конфиги (если ещё нет)"
[[ -f config/settings.yaml ]] || cp config/settings.example.yaml config/settings.yaml
[[ -f config/profiles.local.yaml ]] || cp config/profiles.example.yaml config/profiles.local.yaml
[[ -f config/ui/pro-01.yaml ]] || cp config/ui/pro-01.example.yaml config/ui/pro-01.yaml
[[ -f .env ]] || cp .env.example .env

mkdir -p secrets data/capture/flags

echo "==> Сертификат mitmproxy (если ещё нет)"
if [[ ! -f "${HOME}/.mitmproxy/mitmproxy-ca-cert.pem" ]]; then
  timeout 3 mitmdump -p 18080 >/dev/null 2>&1 || true
fi

echo "==> Проверка Xcode"
if ! xcode-select -p >/dev/null 2>&1; then
  echo "Предупреждение: Xcode Command Line Tools не найдены. Установите Xcode из App Store."
else
  echo "Xcode: $(xcode-select -p)"
fi

echo "==> Проверка idb (опционально, для UI-тапов)"
if command -v idb >/dev/null 2>&1; then
  echo "idb: $(command -v idb)"
else
  echo "Предупреждение: idb не в PATH. Установите: brew install idb-companion"
  echo "  и pip install fb-idb (или idb из fb-idb) в venv при необходимости."
fi

echo ""
echo "Готово."
echo "  cd ${PROJECT_DIR}"
echo "  source .venv/bin/activate"
echo "  python -m wayfire_sim check-config"
echo ""
echo "Откройте в Cursor папку: ${PROJECT_DIR}"
