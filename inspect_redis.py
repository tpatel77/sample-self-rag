
import redis
import json
import sys

def inspect_redis():
    try:
        r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        print("Connected to Redis.")
        
        # Scan for session keys (app_name is usually in config, defaults? "adk_app" in service?)
        # Orchestrator uses config.name but Service has app_name. 
        # Inspecting src/orchestrator.py, it passes config.name as app_name?
        # Actually, let's just scan all keys for now.
        keys = r.keys("*:session:*")
        
        if not keys:
            print("No session keys found in Redis.")
            return

        print(f"Found {len(keys)} keys matching pattern.")
        for key in keys:
            # Skip history keys in the main loop, we'll access them via the session key
            if key.endswith(":history"):
                continue
                
            print(f"\nKey: {key}")
            val = r.get(key)
            try:
                data = json.loads(val)
                print("State:", json.dumps(data.get("state", {}), indent=2))
            except:
                print("Raw Value:", val)
                
            # Check for history
            history_key = f"{key}:history"
            history_len = r.llen(history_key)
            print(f"History Length: {history_len}")
            if history_len > 0:
                # Show first and last event
                first = r.lindex(history_key, 0)
                last = r.lindex(history_key, -1)
                print(f"First Event: {first[:100]}...")
                print(f"Last Event: {last[:100]}...")
                
    except Exception as e:
        print(f"Error inspecting Redis: {e}")

if __name__ == "__main__":
    inspect_redis()
