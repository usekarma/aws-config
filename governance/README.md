# Steady-state cost contract

This directory declares the expected steady-state AWS cost for the infrastructure experiment. It is configuration and policy only; it does not query, deploy, modify, or delete AWS resources.

`steady_state_costs.json` is the machine-readable source of truth for the experiment:

- `strall.com`: **$0.51/month**
- `usekarma.dev`: **$0.61/month**
- combined: **$1.12/month**
- allowed unattributed recurring spend: **$0.00**
- remediation mode: **proposal only**
- destructive actions: **disabled**

Validate the contract locally before any reconciliation work:

```bash
python scripts/validate_steady_state_costs.py
```

The next stage belongs in `aws-iac`: read this contract, inspect actual AWS resources and Cost Explorer data, reconcile desired state vs. actual state vs. cost, and produce evidence plus a safe remediation plan. That stage must stop before apply/delete.
