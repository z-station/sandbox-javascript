# JavaScript Node.js service

Web-сервис, который предоставляет программный интерфейс (API) для запуска кода на языке JavaScript через Node.js внутри Docker-контейнера.

Эта версия ориентирована на Linux/Docker.

[Спецификация API](docs/specification.md)

## Запуск

```bash
cd scripts
./up
```

Сервис будет доступен на порту `9003`.

## Проверка

```bash
curl http://localhost:9003/health

curl -X POST http://localhost:9003/run \
  -H "Content-Type: application/json" \
  -d "{\"code\":\"console.log('Hello from JS')\"}"
```
