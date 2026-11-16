# Формат подключаемого пакета DIABLO_666

Каждый компонент, допущенный к установке, хранится в `packages/<package_dir>/`:

- `manifest.json`
- `files/...` — исходные файлы компонента

Пример `manifest.json`:

```json
{
  "module_id": "example_module",
  "game_version": "2.4.1.1",
  "author": "Author",
  "source_url": "https://official-source.example/mod",
  "license": "MIT",
  "redistribution_permission": "license_allows_redistribution",
  "files": [
    {
      "source": "files/example.wotmod",
      "destination": "mods/2.4.1.1/example.wotmod",
      "sha256": "PUT_REAL_SHA256_HERE"
    }
  ]
}
```

## Правила установщика
- Установка возможна только для `status: ready` и `redistribution_permission: confirmed` либо `license_allows_redistribution`.
- Версия `game_version` должна точно совпадать с версией из `version.xml`.
- Проверяется SHA-256 каждого файла.
- Назначения разрешены только в `mods/` и `res_mods/` внутри выбранной папки игры.
- Игра должна быть закрыта.
- Перед заменой существующих файлов создаётся резервная копия.
- Состояние установки хранится отдельно для каждой папки игры.
- Удаление восстанавливает оригиналы и удаляет только файлы, зарегистрированные установщиком.
- Если файл изменён после установки, удаление пропускает его, чтобы не затереть чужие изменения.

Ни один из текущих внешних кандидатов не становится устанавливаемым автоматически: сначала нужны файлы от первоисточника, проверка Fair Play, точная лицензия/разрешение и тест.
