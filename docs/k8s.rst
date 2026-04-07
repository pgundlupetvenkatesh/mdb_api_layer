Kubernetes Jobs
=================

A Kubernetes Job creates one or more Pods and ensures that a specified number of them successfully terminate.
As pods successfully complete, the Job tracks the successful completions.
When a specified number of successful completions is reached, the task (ie, Job) is complete.
Deleting a Job will clean up the Pods it created.

Job Files
---------

* ``k8s/contract-test-job.yaml`` - A Kubernetes Job manifest for running contract tests.
* ``k8s/integration-test-job.yaml`` - A Kubernetes Job manifest for running integration tests.

Contract Test Job
~~~~~~~~~~~~~~~~~
.. literalinclude:: ../k8s/contract-test-job.yaml
   :language: yaml
   :caption: contract-test-job.yaml

Integration Test Job
~~~~~~~~~~~~~~~~~~~~
.. literalinclude:: ../k8s/integration-test-job.yaml
   :language: yaml
   :caption: integration-test-job.yaml