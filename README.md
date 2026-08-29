# Simulators for WayFire

Репозиторий — единый источник правды для работы с проекта с разных устройств в одном аккаунте Cursor.

Продукт: **Wayfair Service Pro** (Wayhome). Установку IPA на симулятор и первичный вход в аккаунты делаете **вы**; этот проект автоматизирует остальное.

## Статус

**Итоговый план готов** — [`docs/plan-itogovyy.md`](docs/plan-itogovyy.md). Реализация кода — следующий этап (фазы 1–5 в плане).

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

## Быстрый старт (после реализации кода)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config/profiles.example.yaml config/profiles.local.yaml
cp config/settings.example.yaml config/settings.yaml
cp config/ui/pro-01.example.yaml config/ui/pro-01.yaml
# UDID, координаты UI, bundle id

python -m wayfire_sim run
```

## Документы

- [Итоговый план](docs/plan-itogovyy.md)
- [Исследование](docs/issledovanie.md)
- [Ответы итерации 2](docs/otvety-iteraciya-2.md) / [3](docs/otvety-iteraciya-3.md)

## Зависимости на Mac (вне pip)

- Xcode + Simulator
- `idb` (Facebook) для UI-тапов
- `mitmproxy` (ставится через `requirements.txt` в venv)

Cursor Cloud симуляторы не запускает — прогон только на вашем Mac.
