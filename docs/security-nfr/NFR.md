| ID         | Название              | Описание                                    | Метрика/Порог                           | Проверка (чем/где)            | Компонент    | Приоритет |
| ---------- | --------------------- | ------------------------------------------- | --------------------------------------- | ----------------------------- | ------------ | --------- |
| NFR-SEC-01 | Защита паролей        | Пароли хранятся с Argon2id, cost >= 3       | `time_cost >= 3`, `memory_cost >= 64MB` | Code review / Pytest security | AuthService  | High      |
| NFR-SEC-02 | JWT TTL               | Срок жизни токена не превышает 60 минут     | `TTL <= 3600s`                          | Unit test (settings)          | AuthService  | Medium    |
| NFR-SEC-03 | HTTPS only            | Все запросы идут только по HTTPS            | 100% HTTPS                              | E2E / nginx config            | Gateway      | Critical  |
| NFR-SEC-04 | Лимит RPS             | Ограничение на запросы от одного IP         | ≤ 100 RPS                               | Load test / Nginx             | API Gateway  | High      |
| NFR-SEC-05 | Логирование ошибок    | Все 4xx/5xx логируются с user_id, timestamp | ≥ 99% записей                           | Kibana / Loki                 | Backend      | Medium    |
| NFR-SEC-06 | Ротация секретов      | Секреты JWT обновляются каждые 90 дней      | ≤ 90 days                               | Secrets policy / Vault        | DevOps       | Medium    |
| NFR-SEC-07 | Время ответа          | p95 API ≤ 300ms при 50 RPS                  | p95 ≤ 0.3s                              | Load test (k6)                | Backend      | Medium    |
| NFR-SEC-08 | Время исправления CVE | Critical CVE закрываются ≤ 7 дней           | ≤ 7 days                                | Dependabot / CI report        | All services | High      |
