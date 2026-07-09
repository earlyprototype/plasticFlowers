"""Check Redis stream for stale events."""
import asyncio
import redis.asyncio as redis

async def check_redis():
    r = redis.from_url('redis://localhost:6379')
    
    # Check pending messages in the stream
    print('=== REDIS STREAM: pf:chunks:added ===')
    try:
        info = await r.xinfo_stream('pf:chunks:added')
        print(f"Stream length: {info['length']}")
        first = info.get('first-entry')
        last = info.get('last-entry')
        print(f"First entry: {first[0] if first else 'none'}")
        print(f"Last entry: {last[0] if last else 'none'}")
    except Exception as e:
        print(f'Stream not found or error: {e}')
    
    # Check consumer group pending
    print('\n=== CONSUMER GROUP: gardener ===')
    try:
        groups = await r.xinfo_groups('pf:chunks:added')
        for g in groups:
            print(f"Group: {g['name']}, Pending: {g['pending']}, Consumers: {g['consumers']}")
    except Exception as e:
        print(f'No groups or error: {e}')
        
    # Check first 5 messages
    print('\n=== FIRST 5 MESSAGES (oldest) ===')
    try:
        msgs = await r.xrange('pf:chunks:added', count=5)
        for msg_id, data in msgs:
            session = data.get(b'session_id', b'?').decode()
            print(f'  {msg_id}: session={session}')
    except Exception as e:
        print(f'Error reading: {e}')
    
    # Check last 5 messages
    print('\n=== LAST 5 MESSAGES (newest) ===')
    try:
        msgs = await r.xrevrange('pf:chunks:added', count=5)
        for msg_id, data in msgs:
            session = data.get(b'session_id', b'?').decode()
            print(f'  {msg_id}: session={session}')
    except Exception as e:
        print(f'Error reading: {e}')
    
    await r.close()

if __name__ == "__main__":
    asyncio.run(check_redis())

