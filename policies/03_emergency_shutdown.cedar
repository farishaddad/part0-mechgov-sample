// Policy 3: Emergency shutdown. Overrides every permit (forbid wins).
// Keep detached. Attach to stop all tool calls on the gateway; detach to restore.
forbid(
  principal,
  action,
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:eu-west-2:123456789012:gateway/credit-decisioning"
);
