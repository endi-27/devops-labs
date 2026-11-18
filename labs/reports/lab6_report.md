# Звіт до Лабораторної роботи №6: Progressive Delivery (Blue-Green з Argo Rollouts)

## 1. Архітектура та встановлення Argo Rollouts через Argo CD

Лабораторна робота продовжує GitOps-конфігурацію з ЛР-5 у репозиторії `https://github.com/endi-27/devops-labs.git` (гілка `feature/lab5-gitops`).

* Першим окремим комітом (`5725b52`) додано [argocd-apps/argo-rollouts.yaml](../../argocd-apps/argo-rollouts.yaml):
  * Helm-чарт `argo-rollouts` (`https://argoproj.github.io/argo-helm`, версія **`2.43.12`**, app `v1.10.2`);
  * анотація `argocd.argoproj.io/sync-wave: "-1"` для гарантованого створення контролера та CRD до синхронізації застосунків;
  * `CreateNamespace=true` у простір імен `argo-rollouts`.
* Результат синхронізації: 2/2 поди `argo-rollouts` у `Running`, усі CRD (`rollouts.argoproj.io`, `analysistemplates.argoproj.io`, `analysisruns.argoproj.io`, `clusteranalysistemplates.argoproj.io`, `experiments.argoproj.io`) зареєстровані.
* У [argocd-apps/devops-platform.yaml](../../argocd-apps/devops-platform.yaml) додано `retry` (`limit: 5`, `backoff: 10s..3m`) та `ignoreDifferences` для `/spec/selector` у `Service` (щоб Argo CD не вважав інжектований хеш `rollouts-pod-template-hash` розбіжністю `OutOfSync`).

---

## 2. Міграція `users` на `kind: Rollout` і стратегія Blue-Green (коміт `35d5018`)

Обрано стратегію **Варіант b: Blue-Green** для мікросервісу `users`:
* [helm/devops-platform/Chart.yaml](../../helm/devops-platform/Chart.yaml): збільшено версію чарту `0.1.0` → `0.2.0`.
* [deployment.yaml](../../helm/devops-platform/templates/services/users/deployment.yaml): обгорнуто умовою `{{- if not .Values.users.rollout.enabled }}`.
* [rollout.yaml](../../helm/devops-platform/templates/services/users/rollout.yaml): створено ресурс `argoproj.io/v1alpha1` `kind: Rollout` з тим самим шаблоном пода та `strategy`.
* [service-preview.yaml](../../helm/devops-platform/templates/services/users/service-preview.yaml): додано сервіс `users-preview` (порт `8001`, ім'я `http`) для перевірки нової версії до перемикання трафіку.
* [values-minikube.yaml](../../helm/devops-platform/values-minikube.yaml):
  ```yaml
  users:
    replicas: 2
    rollout:
      enabled: true
      strategy:
        blueGreen:
          activeService: users
          previewService: users-preview
          autoPromotionEnabled: false
          scaleDownDelaySeconds: 30
  ```
* Під час переходу Argo CD автоматично видалив старий `Deployment/users` і підняв `Rollout/users` (`1.1.0`, `2/2 Healthy`).

---

## 3. Реліз через Git (`1.1.0` → `1.2.0`) і `promote` (коміт `9ac5312`)

1. Підготовлено та опубліковано в GHCR образи `ghcr.io/endi-27/devops-users-service:1.2.0`, `:1.3.0`, `:1.4.0`.
2. Після зміни тегу на `"1.2.0"` і пушу Argo CD синхронізував маніфест, а `Rollout` підняв `revision:2` (`users-6f77c87cc8`) та зупинився на паузі `BlueGreenPause`:
   * Argo CD статус: `Sync Status: Synced`, `Health Status: Suspended`.
   * `svc/users` (`:8081`) продовжував віддавати `{"service":"users-service","version":"1.1.0"}`.
   * `svc/users-preview` (`:8082`) уже віддавав `{"service":"users-service","version":"1.2.0"}`.
3. Виконано `kubectl argo rollouts promote users -n devops-platform`:
   * Селектор `svc/users` перемкнувся з `6b8667d599` на **`{"app":"users","rollouts-pod-template-hash":"6f77c87cc8"}`**.
   * `curl -s http://localhost:8081/version` почав повертати `{"service":"users-service","version":"1.2.0"}`.
   * Статус `Rollout` та Argo CD: **`Synced / Healthy`**.

---

## 4. Скасування релізу (`1.3.0` → `abort` → `git revert`)

1. **Коміт `bdb39f3` (`1.3.0`)**: після виходу `revision:3` у `Paused` виконано:
   ```text
   $ kubectl argo rollouts abort users -n devops-platform
   rollout 'users' aborted
   ```
   * `Rollout users`: `Status: ✖ Degraded` (`RolloutAborted: Rollout aborted update to revision 3`), `stable, active` залишився на `1.2.0`.
   * Argo CD: `Sync Status: Synced` (маніфест відповідає Git із `1.3.0`), `Health Status: Degraded`.
   * Активний сервіс `:8081` продовжував обслуговувати версію `1.2.0`.
2. **Коміт `d8ff90c` (`git revert --no-edit bdb39f3`)**:
   * Опис у Git повернуто до `"1.2.0"`.
   * `Rollout users` повернувся до **`✔ Healthy`** (`1.2.0 (stable, active)`), а Argo CD — до **`Synced / Healthy`**.
