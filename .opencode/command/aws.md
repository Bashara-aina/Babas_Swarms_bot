---
description: >-
  AWS infrastructure operations using AWS Serverless MCP, AWS IaC MCP, and
  AWS Pricing MCP toolsets. Validates templates, deploys serverless apps,
  analyzes costs, and troubleshoots deployments.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /aws — AWS Infrastructure Operations

## WHEN TO USE

Use `/aws` when:
- Deploying serverless applications (SAM, Lambda)
- Validating CloudFormation templates
- Analyzing AWS costs
- Troubleshooting failed deployments
- Managing AWS infrastructure as code

## AVAILABLE TOOLS

### AWS Serverless (aws-serverless-mcp)
- SAM init/build/deploy/local invoke/logs
- Lambda event schema lookup
- ESM guidance (Kafka, Kinesis, SQS, DynamoDB streams)
- Serverless template examples

### AWS IaC (awsiac)
- CloudFormation template validation (cfn-lint)
- CloudFormation compliance checking (cfn-guard)
- CloudFormation deployment troubleshooting
- CDK documentation and samples

### AWS Pricing (awspricing)
- Service discovery and pricing lookup
- Cost analysis report generation
- CDK/Terraform project analysis
- Bedrock patterns

## USAGE

```
/aws validate [template file]
/aws deploy [sam project directory]
/aws cost [service] [region]
/aws troubleshoot [stack name] [region]
/aws sam-init [project name] [runtime]
```

## EXAMPLES

### Validate CloudFormation template
```
/aws validate templates/my-template.yaml
```
Output: Validation results with line numbers for any errors.

### Deploy SAM application
```
/aws deploy . --region us-east-1
```
Output: Deployment status, stack outputs, endpoint URLs.

### Cost analysis
```
/aws cost Lambda us-east-1
```
Output: Pricing breakdown, cost estimates based on usage.

### Troubleshoot failed deployment
```
/aws troubleshoot my-stack us-east-1
```
Output: CloudFormation events, root cause analysis, suggested fixes.

## VALIDATION WORKFLOW

```
1. Validate template
   → /aws validate [template]

2. Check compliance
   → cfn_guard check

3. Estimate cost
   → /aws cost [service] [region]

4. Deploy (after user confirmation)
   → /aws deploy [project]
```

## ANTI-HALLUCINATION RULES

1. **Validate before deploy** — never skip validation
2. **Show actual errors** — cite exact line numbers from validation
3. **Cite cost estimates** — show actual pricing data
4. **Confirm region** — verify correct region for all operations
5. **Require confirmation for deploy** — pause for user yes/no

## DEPLOYMENT REQUIREMENTS

Before deploying, you MUST:
1. ✅ Validate template with `/aws validate`
2. ✅ Check compliance with cfn-guard
3. ✅ Get cost estimate
4. ✅ Get user confirmation via @collaborator
5. ✅ Document rollback procedure

## STATUS
```
AWS STATUS: ✅ [operation] | ❌ FAILED | ⏸️ NEEDS CONFIRMATION
Service: [AWS service]
Region: [region]
Action: [what was done]
```
