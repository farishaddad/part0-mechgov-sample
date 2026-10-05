// Policy 1: Role-scoped credit assessment with parameter-level threshold guard
permit(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"CreditDecisionAPI___assess_credit_case",
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:eu-west-2:123456789012:gateway/credit-decisioning"
)
when {
  principal.hasTag("role") &&
  principal.getTag("role") == "credit-analyst" &&
  context.input.exposure_amount <= 500000 &&
  context.input has case_reference
};
