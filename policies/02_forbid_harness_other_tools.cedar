// Policy 2: The mech-gov harness identity may call the decision writer and nothing else
forbid(
  principal is AgentCore::OAuthUser,
  action,
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:eu-west-2:123456789012:gateway/credit-decisioning"
)
when {
  principal.hasTag("role") &&
  principal.getTag("role") == "mech-gov-harness" &&
  !(action == AgentCore::Action::"AuditAPI___emit_decision_record")
};
