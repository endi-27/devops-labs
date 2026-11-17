# Звіт до Лабораторної роботи №5: GitOps — розгортання проєкту через Argo CD

## 1. Архітектура та структура конфігурації GitOps

Розгортання платформи переведено на декларативну модель **GitOps** за патерном **App-of-Apps** на базі єдиного репозиторію `https://github.com/endi-27/devops-labs.git` (гілка `feature/lab5-gitops`).

```text
devops-labs/
├── .github/workflows/ci.yml              # додано paths-ignore для GitOps-шляхів
├── bootstrap/
│   └── root.yaml                         # кореневий Argo CD Application (стежить за argocd-apps/)
├── argocd-apps/
│   └── devops-platform.yaml              # Application для Helm-чарту платформи
├── helm/
│   └── devops-platform/                  # Helm-чарт із ЛР-4 (адаптований existingSecret)
│       ├── values.yaml
│       ├── values-minikube.yaml          # GHCR-образи, pullPolicy: IfNotPresent, existingSecret
│       └── templates/
└── services/users/
    ├── Dockerfile                        # ARG/ENV APP_VERSION
    ├── src/main.py                       # GET /version, GET /api/v1/users/version, APP_VERSION у /health
    └── tests/api/test_api.py             # тест test_version_endpoint
```

### Робота з секретами (`existingSecret`)
Щоб не зберігати паролі та ключі у `values-minikube.yaml` в Git:
* У шаблонах `Secret` (`postgres`, `users`, `products`, `orders`) додано умову `{{- if not .Values.<component>.existingSecret }} ... {{- end }}`.
* Відповідні `Deployment`-и посилаються на `{{ .Values.<component>.existingSecret | default "<component>-secret" }}`.
* Секрети `postgres-secret`, `users-secret`, `products-secret`, `orders-secret` створені вручну в кластері у просторі імен `devops-platform`, тож Argo CD не керує ними й не видаляє їх навіть при увімкненому `prune: true`.

---

## 2. Образи застосунку в GHCR та версіонування

* У [services/users/src/main.py](../../services/users/src/main.py) додано зчитування змінної `APP_VERSION` і ендпоінти `GET /version` та `GET /api/v1/users/version`.
* Тести й лінтери `services/users`: `ruff check`, `ruff format --check`, `mypy`, `pytest` (8/8 passed).
* Зібрано та опубліковано в GitHub Container Registry (`ghcr.io/endi-27/`):
  * `ghcr.io/endi-27/devops-users-service:1.0.0` та `:1.1.0`
  * `ghcr.io/endi-27/devops-products-service:1.0.0`
  * `ghcr.io/endi-27/devops-orders-service:1.0.0`
  * `ghcr.io/endi-27/devops-gateway:1.0.0`

---

## 3. Встановлення Argo CD та первинний деплой (Етапи 3–4)

* Argo CD встановлено в `namespace: argocd` (усі 7 подів у статусі `1/1 Running`).
* Єдиний ручний `apply`: `kubectl apply -f bootstrap/root.yaml`.
* Стан після синхронізації `1.0.0`:
  * `argocd/root` — `Synced / Healthy`
  * `argocd/devops-platform` — `Synced / Healthy` (ревізія `11673f3`)
  * `helm list -n devops-platform` — порожній (Argo CD використовує Helm лише як рендерер шаблонів).
  * `curl -s http://localhost:8081/version` → `{"service":"users-service","version":"1.0.0"}`.

---

## 4. Оновлення через Git (`1.0.0` → `1.1.0`) (Етап 5)

* Коміт `843bdad`: у [values-minikube.yaml](../../helm/devops-platform/values-minikube.yaml) змінено `users.image.tag: "1.0.0"` → `"1.1.0"`.
* Після `argocd app get devops-platform --refresh` відпрацював `PreSync`-хук `devops-platform-pre-upgrade-backup`, контролер оновив `deployment/users`, статус повернувся до `Synced / Healthy`.
* Перевірка версії:
  ```text
  $ curl -s http://localhost:8081/version
  {"service":"users-service","version":"1.1.0"}
  ```

---

## 5. Дрейф конфігурації, `selfHeal`, `Degraded` та відкат через `git revert` (Етап 6)

### 6a. Дрейф без `selfHeal` і з `selfHeal: true`
1. **Без `selfHeal`:** після `kubectl -n devops-platform scale deployment users --replicas=5`:
   ```text
   Sync Policy:   Automated (Prune)
   Sync Status:   OutOfSync from feature/lab5-gitops (843bdad)
   Health Status: Progressing
   ```
   Усі 5 подів залишалися в кластері, доки `selfHeal` був вимкнений.
2. **З `selfHeal: true` (коміт `e5b7c29`):** додано `selfHeal: true` у [devops-platform.yaml](../../argocd-apps/devops-platform.yaml). Після повторного `kubectl scale --replicas=5` Argo CD за кілька секунд самостійно повернув кількість реплік до декларативного значення з Git (`2/2`):
   ```text
   $ kubectl -n devops-platform get deployment users
   NAME    READY   UP-TO-DATE   AVAILABLE   AGE
   users   2/2     2            2           17m
   ```

### 6b. `Synced`, але `Progressing / Degraded` (неіснуючий тег `9.9.9`)
* Коміт `e544485`: змінено `users.image.tag` на `"9.9.9"`.
* Маніфест у кластері відповідає Git, тому `Sync Status: Synced to feature/lab5-gitops (e544485)`, проте новий под не може завантажити образ:
  ```text
  NAME                     READY   STATUS             RESTARTS   AGE
  users-774cc44fc5-vw8ns   0/1     ImagePullBackOff   0          19s
  users-7cd74bc45d-49pwb   1/1     Running            0          2m35s
  users-7cd74bc45d-9h2lh   1/1     Running            0          2m53s
  ```

### 6c. Відкат через `git revert`
* Коміт `2e3acbb`: виконано `git revert --no-edit e544485 && git push`.
* Підсумок: статус `Synced / Healthy`, помилковий под прибрано, версія знову `1.1.0`:
  ```text
  $ argocd app history devops-platform
  SOURCE  https://github.com/endi-27/devops-labs.git
  ID      DATE                           REVISION
  0       2026-11-17 21:34:22 +0200 EET  feature/lab5-gitops (11673f3)
  1       2026-11-17 21:50:01 +0200 EET  feature/lab5-gitops (843bdad)
  2       2026-11-17 21:51:52 +0200 EET  feature/lab5-gitops (e5b7c29)
  3       2026-11-17 21:52:35 +0200 EET  feature/lab5-gitops (e544485)
  4       2026-11-17 21:53:15 +0200 EET  feature/lab5-gitops (2e3acbb)

  $ curl -s http://localhost:8081/version
  {"service":"users-service","version":"1.1.0"}
  ```
