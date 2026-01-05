# test_connection.py
import grpc
import auth_pb2
import auth_pb2_grpc
import time

def test_auth_connection():
    print("🔍 Testing Auth Server Connection...")
    print("=" * 60)
    
    ports = [50051, 50052, 50053, 50054]
    
    for port in ports:
        print(f"\nTesting port {port}...")
        try:
            channel = grpc.insecure_channel(f'127.0.0.1:{port}')
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            
            start_time = time.time()
            try:
                future = grpc.channel_ready_future(channel)
                future.result(timeout=3)
                
                request = auth_pb2.LoginRequest(username="test", password="test")
                response = stub.Login(request, timeout=5)
                
                elapsed = time.time() - start_time
                print(f"✅ Port {port} - CONNECTED ({elapsed:.2f}s)")
                print(f"   Server responded: {response.message}")
                return port
                
            except grpc.FutureTimeoutError:
                print(f"⏱️  Port {port} - TIMEOUT (no response)")
            except grpc.RpcError as e:
                elapsed = time.time() - start_time
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    print(f"❌ Port {port} - UNAVAILABLE")
                else:
                    print(f"⚠️  Port {port} - Error: {e.code().name}")
            except Exception as e:
                print(f"❌ Port {port} - Error: {str(e)[:50]}")
                
        except Exception as e:
            print(f"❌ Port {port} - Failed: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("❌ No auth server found!")
    print("\nTo fix this:")
    print("1. Open a NEW terminal")
    print("2. Run: python auth_server.py")
    print("3. Wait for '✅ Auth Server is RUNNING' message")
    print("4. Then run this test again")
    return None

if __name__ == "__main__":
    port = test_auth_connection()
    if port:
        print(f"\n🎉 Auth server found on port {port}!")
        print(f"   You can now run: python app.py")