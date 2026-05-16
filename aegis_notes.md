# AEGIS API Gateway
## Current State
- Auth middleware complete
- Rate limiting in progress
- Dead end: Redis-based rate limiting caused latency spikes
- Next: Implement in-memory sliding window instead