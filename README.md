# Simulators for WayFire

Репозиторий — единый источник правды для работы с проекта с разных устройств в одном аккаунте Cursor.

Продукт: **Wayfair Service Pro** (Wayhome). Установку IPA на симулятор и первичный вход в аккаунты делаете **вы**; этот проект автоматизирует остальное.

## Статус

**Код реализован** (фазы 1–5). План: [`docs/plan-itogovyy.md`](docs/plan-itogovyy.md).

## Что делает проект

По очереди для каждого профиля (`pro-01`, …):

1. Запускает симулятор (`simctl`).
2. Открывает приложение и выполняет UI-сценарий (тапы через `idb`).
3. Через локальный `mitmproxy` перехватывает `GetAvailableJobs`.
4. Сохраняет сырой `curl` в `secrets/<profile_id>/` (не в git).

Poll / claim — в другом репозитории.

## Правила проекта

1. На Mac всегда работаем внутри `venv`.
2. Общение, документация и комментарии — на русском.
3. Секреты и живые curl в git не кладём.

## Установка (Mac)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp config/profiles.example.yaml config/profiles.local.yaml
cp config/settings.example.yaml config/settings.yaml
cp config/ui/pro-01.example.yaml config/ui/pro-01.yaml
```

Отредактируйте `profiles.local.yaml` (UDID симулятора), `config/ui/pro-01.yaml` (координаты тапов).

Один раз на симулятор — доверие CA mitmproxy:

```bash
xcrun simctl boot <UDID>
xcrun simctl keychain booted add-root-cert ~/.mitmproxy/mitmproxy-ca-cert.pem
```

## Команды

```bash
# Проверить конфиги
python -m wayfire_sim check-config

# Один профиль из очереди (для отладки)
python -m wayfire_sim once

# Бесконечный цикл (пауза 1 мин между профилями)
python -m wayfire_sim run

# Вручную сохранить curl (если сняли в Charles)
python -m wayfire_sim import-curl pro-01 -f request.curl
```

## Тесты (без Mac)

```bash
pytest
```

## Документы

- [Итоговый план](docs/plan-itogovyy.md)
- [Исследование](docs/issledovanie.md)

## Зависимости на Mac (вне pip)

- Xcode + Simulator
- `idb` (`brew install idb-companion`, CLI `idb` в PATH)

Cursor Cloud симуляторы не запускает — прогон только на вашем Mac.
