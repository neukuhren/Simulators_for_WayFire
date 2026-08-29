# Рабочая директория на Mac (канонический путь)

/Users/me/dev/Simulators_for_WayFire

## Быстрая установка

На **вашем Mac** в Терминале:

```bash
cd /Users/me/dev
git clone -b cursor/planning-wayfire-simulators-91b3 \
  https://github.com/neukuhren/Simulators_for_WayFire.git
cd Simulators_for_WayFire
bash scripts/setup-mac.sh
```

Если репозиторий уже клонирован в другое место — проще перенести или переклонировать:

```bash
# Вариант А: переклонировать в нужный путь
mkdir -p /Users/me/dev
git clone -b cursor/planning-wayfire-simulators-91b3 \
  https://github.com/neukuhren/Simulators_for_WayFire.git \
  /Users/me/dev/Simulators_for_WayFire

# Вариант Б: переместить существующую папку
mv /старый/путь/Simulators_for_WayFire /Users/me/dev/
```

Затем установка зависимостей:

```bash
cd /Users/me/dev/Simulators_for_WayFire
bash scripts/setup-mac.sh
```

## Открыть в Cursor

**File → Open Folder…** → `/Users/me/dev/Simulators_for_WayFire`

Дальнейшая работа (агент, терминал) — только из этой папки.

## Что ставит setup-mac.sh

| Компонент | Как |
|-----------|-----|
| Python-пакет `wayfire_sim` | `pip install -e ".[dev]"` в `.venv` |
| mitmproxy / mitmdump | через pip |
| PyYAML, pytest | через pip `[dev]` |
| Конфиги | копии из `*.example.yaml`, если локальных ещё нет |
| CA mitmproxy | первый запуск `mitmdump` → `~/.mitmproxy/` |

Вручную на Mac (вне pip):

- **Xcode** — App Store (для `simctl`)
- **idb** — `brew install idb-companion` (для UI-тапов)

## Проверка

```bash
cd /Users/me/dev/Simulators_for_WayFire
source .venv/bin/activate
python -m wayfire_sim check-config
pytest
```

## Почему облачный агент не может «перенести» сам

Cursor Cloud Agent работает на Linux-ВМ (`/workspace`), без доступа к `/Users/me/...` на вашем Mac. Перенос и `venv` выполняются **локально** этим скриптом или командами выше.
