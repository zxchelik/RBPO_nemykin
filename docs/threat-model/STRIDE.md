| Поток/Элемент    | Угроза (STRIDE)                     | Риск | Контроль                                    | Ссылка на NFR          | Проверка/Артефакт  |
| ---------------- | ----------------------------------- | ---- | ------------------------------------------- | ---------------------- | ------------------ |
| F1 /login        | S: Spoofing (подделка пользователя) | R1   | Argon2id + rate-limit                       | NFR-SEC-01, NFR-SEC-04 | e2e + ZAP baseline |
| F2 Auth req      | T: Tampering (подмена запроса)      | R2   | HTTPS, JWT подпись                          | NFR-SEC-03, NFR-SEC-02 | SSL config + unit  |
| F3 SQL (auth)    | I: Information disclosure           | R3   | Исключения без деталей, логирование 4xx/5xx | NFR-SEC-05             | pytest + RFC7807   |
| F4 /tasks CRUD   | D: Denial of Service                | R4   | Rate limit + circuit breaker                | NFR-SEC-04, NFR-SEC-07 | k6 perf test       |
| F5 gRPC internal | R: Repudiation                      | R5   | Корреляционный ID в логах                   | NFR-SEC-05             | Loki traces        |
| DB2 Tasks        | E: Elevation of Privilege           | R6   | owner-only access control                   | NFR-SEC-01             | API tests / authz  |
