---
description: >-
  MongoDB, Pinecone, and other MCP tool operations. Query databases,
  manage vector search indexes, perform aggregations, and handle data operations.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /mcp — Database & MCP Tool Operations

## WHEN TO USE

Use `/mcp` when:
- Need to query or update MongoDB
- Need to perform vector search (Pinecone)
- Need to connect to external MCP services
- Need to run database aggregations
- Need to manage index schemas

## AVAILABLE SERVICES

### MongoDB (mongodb-mcp)
- CRUD operations on collections
- Aggregation pipelines
- Index management
- Schema analysis

### Pinecone (pinecone-mcp)
- Vector similarity search
- Index management
- Cascading multi-index search
- Reranking

### GitHub (github-mcp via github-agent)
- PR creation and review
- Issue management
- Repository operations

### AWS (via aws-agent)
- SAM/CloudFormation operations
- Cost analysis

## USAGE

```
/mcp mongo [database] [collection] [operation]
/mcp pinecone [index] [operation]
/mcp list
/mcp status [service]
```

## EXAMPLES

### MongoDB operations
```
/mcp mongo mydb users find '{"status": "active"}'
/mcp mongo mydb users aggregate '[{"$match": {"age": {"$gt": 18}}}]'
/mcp mongo mydb users insert '[{"name": "test", "email": "test@test.com"}]'
```

### Pinecone operations
```
/mcp pinecone my-index search '{"text": "query text"}'
/mcp pinecone my-index list
/mcp pinecone my-index describe
```

### Status check
```
/mcp status mongodb
/mcp status pinecone
```

## CONNECTION PATTERNS

### MongoDB
```
1. Check connection: /mcp status mongodb
2. List databases: mongo_show_databases()
3. List collections: mongo_list_collections(database)
4. Query: mongo_find(database, collection, filter)
```

### Pinecone
```
1. Check connection: /mcp status pinecone
2. List indexes: pinecone__list_indexes()
3. Describe index: pinecone__describe_index(name)
4. Search: pinecone__search_records(name, namespace, query)
```

## ANTI-HALLUCINATION RULES

1. **Verify connection** — check status before operations
2. **Show actual results** — paste query output
3. **Cite document counts** — don't estimate, show count
4. **Verify schema** — check schema before writing
5. **Confirm destructive ops** — upsert/delete need confirmation

## STATUS
```
MCP STATUS: ✅ [operation] | ❌ FAILED | 🔌 NOT CONNECTED
Service: [service]
Database/Index: [name]
Operation: [what was done]
Result: [actual output]
```
