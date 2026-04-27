---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic>
description: "Look up AWS CLI commands. Usage: /aws <topic>"
---

# /aws — AWS CLI reference

Search and display AWS CLI commands for common operations.

## Usage
```
/aws s3 ls
/aws ec2 describe-instances
/aws iam list-users
```

## Available Topics
- s3 (ls, mb, rb, cp, sync, mb, rb)
- ec2 (describe-instances, start, stop, reboot)
- iam (list-users, create-user, attach-policy)
- lambda (list, invoke, update)
- ecs (list-clusters, describe-services)
- logs (filter, tail)

## Swarm-Bot Context
This bot does NOT run on AWS. AWS commands are for external infrastructure management only.

## Notes
- Output truncated to 50 lines
- Use `aws <command> --help` for full options
- Configure: `aws configure` or env vars AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
