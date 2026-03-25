#!/bin/bash
# run_k8s_tests.sh — Run integration + contract tests in Kubernetes sequentially

echo "=== 1. Building Docker image ==="
docker build -t mdb-api-tests .

echo "=== 2. Creating K8s Secret from .env ==="
kubectl delete secret tmdb-secrets --ignore-not-found
kubectl create secret generic tmdb-secrets --from-env-file=.env

echo "=== 3. Launching test jobs ==="
kubectl delete job integration-tests contract-tests --ignore-not-found
kubectl apply -f k8s/integration-test-job.yaml -f k8s/contract-test-job.yaml

echo "=== 4. Watch job status ==="
kubectl get jobs,pods -l app=tmdb-api-tests

echo "=== 5. Wait for pods to start running ==="
kubectl wait --for=condition=Ready pod -l suite=integration --timeout=300s
kubectl wait --for=condition=Ready pod -l suite=contract --timeout=300s

echo "=== 6. Poll for reports, then copy (within 60s sleep window) ==="
TIMEOUT=300  # Max seconds to wait for reports

INT_POD=$(kubectl get pod -l suite=integration -o jsonpath='{.items[0].metadata.name}')
SECONDS=0
until kubectl exec $INT_POD -- test -f /app/report/tmdb_non_contract_report.html 2>/dev/null; do
  if [ $SECONDS -ge $TIMEOUT ]; then
    echo "ERROR: Timed out waiting for integration report"
    break
  fi
  echo "Waiting for integration tests to finish... (${SECONDS}s)"
  sleep 10
done
kubectl cp $INT_POD:/app/report/tmdb_non_contract_report.html ./report/tmdb_non_contract_report.html

CON_POD=$(kubectl get pod -l suite=contract -o jsonpath='{.items[0].metadata.name}')
SECONDS=0
# Loop should never run forever if for some reason the report is not created
until kubectl exec $CON_POD -- test -f /app/report/tmdb_contract_report.html 2>/dev/null; do
  if [ $SECONDS -ge $TIMEOUT ]; then  # Bash built-in SECONDS variable counts seconds since script start
    echo "ERROR: Timed out waiting for contract report"
    break
  fi
  echo "Waiting for contract tests to finish... (${SECONDS}s)"
  sleep 10
done
kubectl cp $CON_POD:/app/report/tmdb_contract_report.html ./report/tmdb_contract_report.html

echo "=== 7. Wait for jobs to finish, then stream logs ==="
kubectl logs job/integration-tests
kubectl logs job/contract-tests

echo "=== 8. Cleanup ==="
kubectl delete job integration-tests contract-tests --ignore-not-found
#kubectl delete secret tmdb-secrets

echo "=== Done! Reports saved to ./report/ ==="