#!/bin/bash
set -e
export PATH=$PATH:/home/endi/.local/bin
REPORT_FILE="/home/endi/Unic/DevOps/Project/labs/reports/lifecycle_experiments_output.txt"

# Clear report file
> "$REPORT_FILE"

log_section() {
    echo -e "\n================================================================================" | tee -a "$REPORT_FILE"
    echo -e "=== $1" | tee -a "$REPORT_FILE"
    echo -e "================================================================================\n" | tee -a "$REPORT_FILE"
}

run_cmd() {
    echo -e "$ $1" | tee -a "$REPORT_FILE"
    eval "$1" 2>&1 | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
}

log_section "ЕКСПЕРИМЕНТ 1: САМОВІДНОВЛЕННЯ (SELF-HEALING)"
echo "1.1 Отримання списку поточних подів users до симуляції збою:" | tee -a "$REPORT_FILE"
run_cmd "kubectl get pods -n devops-lab3 -l app=users -o wide"

POD_TO_DELETE=$(kubectl get pods -n devops-lab3 -l app=users -o jsonpath='{.items[0].metadata.name}')
echo "1.2 Симуляція аварії: примусове видалення пода $POD_TO_DELETE..." | tee -a "$REPORT_FILE"
run_cmd "kubectl delete pod $POD_TO_DELETE -n devops-lab3"

echo "1.3 Перевірка автоматичного самовідновлення (ReplicaSet негайно створив новий под взамін видаленого):" | tee -a "$REPORT_FILE"
run_cmd "kubectl get pods -n devops-lab3 -l app=users -o wide"

sleep 3
run_cmd "kubectl get pods -n devops-lab3 -l app=users -o wide"

log_section "ЕКСПЕРИМЕНТ 2: МАСШТАБУВАННЯ (SCALING)"
echo "2.1 Масштабування кількості реплік сервісу users з 2 до 4:" | tee -a "$REPORT_FILE"
run_cmd "kubectl scale deployment users --replicas=4 -n devops-lab3"

echo "2.2 Очікування завершення розгортання реплік:" | tee -a "$REPORT_FILE"
run_cmd "kubectl rollout status deployment/users -n devops-lab3"

echo "2.3 Перевірка 4 активних подів users:" | tee -a "$REPORT_FILE"
run_cmd "kubectl get pods -n devops-lab3 -l app=users -o wide"

echo "2.4 Перевірка оновлених Endpoints (сервіс users зареєстрував усі 4 IP подів):" | tee -a "$REPORT_FILE"
run_cmd "kubectl get endpoints users -n devops-lab3"

log_section "ЕКСПЕРИМЕНТ 3: ОНОВЛЕННЯ БЕЗ ЗУПИНКИ (ROLLING UPDATE)"
echo "3.1 Оновлення версії образу deployment/users на devops-users:1.1.0:" | tee -a "$REPORT_FILE"
run_cmd "kubectl set image deployment/users users=devops-users:1.1.0 -n devops-lab3"

echo "3.2 Відстеження процесу Rolling Update (поступова заміна подів без простою):" | tee -a "$REPORT_FILE"
run_cmd "kubectl rollout status deployment/users -n devops-lab3"

echo "3.3 Перевірка оновлених подів (всі мають новий ReplicaSet):" | tee -a "$REPORT_FILE"
run_cmd "kubectl get pods -n devops-lab3 -l app=users -o wide"

echo "3.4 Тестування доступності та версії через API Gateway (NodePort 30080):" | tee -a "$REPORT_FILE"
run_cmd "curl -s http://192.168.49.2:30080/api/v1/users/health"

log_section "ЕКСПЕРИМЕНТ 4: ВІДКАТ ДО ПОПЕРЕДНЬОЇ ВЕРСІЇ (ROLLBACK)"
echo "4.1 Перегляд історії ревізій deployment/users:" | tee -a "$REPORT_FILE"
run_cmd "kubectl rollout history deployment/users -n devops-lab3"

echo "4.2 Виконання відкату (Rollback) до попередньої стабільної ревізії:" | tee -a "$REPORT_FILE"
run_cmd "kubectl rollout undo deployment/users -n devops-lab3"

echo "4.3 Очікування завершення процедури відкату:" | tee -a "$REPORT_FILE"
run_cmd "kubectl rollout status deployment/users -n devops-lab3"

echo "4.4 Перевірка статусу подів після відкату:" | tee -a "$REPORT_FILE"
run_cmd "kubectl get pods -n devops-lab3 -l app=users -o wide"

echo "4.5 Тестування ендпоінту через API Gateway (перевірка повернення до версії 1.0.0):" | tee -a "$REPORT_FILE"
run_cmd "curl -s http://192.168.49.2:30080/api/v1/users/health"

log_section "ЕКСПЕРИМЕНТ 5: ДІАГНОСТИКА ТА TROUBLESHOOTING"
echo "5.1 Симуляція помилки: оновлення на неіснуючий тег образу devops-users:error-tag-999:" | tee -a "$REPORT_FILE"
run_cmd "kubectl set image deployment/users users=devops-users:error-tag-999 -n devops-lab3"

echo "Очікування 10 секунд для фіксації помилки Kubelet..."
sleep 10

echo "5.2 Спостереження за станом подів (виявлення статусів ErrImagePull / ImagePullBackOff):" | tee -a "$REPORT_FILE"
run_cmd "kubectl get pods -n devops-lab3 -l app=users"

BROKEN_POD=$(kubectl get pods -n devops-lab3 -l app=users --no-headers | grep -E "ImagePullBackOff|ErrImagePull" | awk '{print $1}' | head -n 1)
if [ -z "$BROKEN_POD" ]; then
    BROKEN_POD=$(kubectl get pods -n devops-lab3 -l app=users --sort-by=.metadata.creationTimestamp --no-headers | tail -n 1 | awk '{print $1}')
fi

echo "5.3 Детальна діагностика проблемного поду ($BROKEN_POD) за допомогою kubectl describe:" | tee -a "$REPORT_FILE"
run_cmd "kubectl describe pod $BROKEN_POD -n devops-lab3"

WORKING_POD=$(kubectl get pods -n devops-lab3 -l app=users --field-selector=status.phase=Running --no-headers | awk '{print $1}' | head -n 1)
echo "5.4 Перегляд логів контейнера працюючого поду ($WORKING_POD):" | tee -a "$REPORT_FILE"
run_cmd "kubectl logs -n devops-lab3 $WORKING_POD --tail=20"

echo "5.5 Інтерактивний доступ до контейнера через kubectl exec:" | tee -a "$REPORT_FILE"
run_cmd "kubectl exec -n devops-lab3 $WORKING_POD -- sh -c \"echo 'Interactive terminal check: logged into container as user \$(whoami)'\""

echo "5.6 Виправлення аварійної ситуації: відкат на стабільну ревізію (rollout undo):" | tee -a "$REPORT_FILE"
run_cmd "kubectl rollout undo deployment/users -n devops-lab3"

echo "5.7 Очікування завершення стабілізації:" | tee -a "$REPORT_FILE"
run_cmd "kubectl rollout status deployment/users -n devops-lab3"

echo "5.8 Фінальна перевірка відновлення працездатності та здорового стану всіх подів:" | tee -a "$REPORT_FILE"
run_cmd "kubectl get pods -n devops-lab3 -l app=users -o wide"
run_cmd "curl -s http://192.168.49.2:30080/api/v1/users/health"

echo -e "\n=== ВСІ ЕКСПЕРИМЕНТИ УСПІШНО ЗАВЕРШЕНО ===" | tee -a "$REPORT_FILE"
