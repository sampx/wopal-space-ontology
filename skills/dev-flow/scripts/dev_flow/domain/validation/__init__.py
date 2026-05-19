# Validation domain layer
#
# Provides:
#   - check_doc_plan: Plan document completeness validation
#   - check_user_validation: User Validation section gate check
#   - check_acceptance_criteria: Agent Verification checkbox gate
#   - check_step_completion: Implementation Done/Step checkbox gate
#   - ValidationError: Exception for validation failures
#
# Note: check_step_completion handles both template versions:
#   - New template: Task Done checkboxes
#   - Old template: Changes/Verification/Test Plan Step checkboxes
#
# Ported from lib/check-doc.sh, lib/plan.sh

from .check_doc import (
    check_doc_plan,
    check_user_validation,
    check_acceptance_criteria,
    check_step_completion,
    ValidationError,
)

__all__ = [
    'check_doc_plan',
    'check_user_validation',
    'check_acceptance_criteria',
    'check_step_completion',
    'ValidationError',
]