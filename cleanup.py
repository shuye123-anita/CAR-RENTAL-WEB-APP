# cleanup.py
import os
import subprocess
import time

print("🧹 Cleaning up ports and processes...")

# Check for processes on port 50051
try:
    result = subprocess.run(
        ['netstat', '-ano', '|', 'findstr', ':50051'], 
        shell=True, 
        capture_output=True, 
        text=True
    )
    
    if result.stdout:
        print("Found processes on port 50051:")
        print(result.stdout)
        
        # Extract PIDs
        for line in result.stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                try:
                    subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                  capture_output=True, 
                                  text=True)
                    print(f"✅ Killed process with PID: {pid}")
                except:
                    pass
    else:
        print("✅ No processes found on port 50051")
        
except Exception as e:
    print(f"⚠️ Error: {e}")

print("\n🎯 Now you can start fresh:")
print("1. Run: python auth_server.py")
print("2. In a NEW terminal, run: python app.py")