
import psutil
import os
import signal

def kill_process_on_port(port):
    print(f"Checking port {port}...")
    killed = False
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port:
                pid = conn.pid
                if pid:
                    try:
                        proc = psutil.Process(pid)
                        print(f"Found process {pid} ({proc.name()}) on port {port}. KIlling...")
                        proc.kill()
                        killed = True
                    except psutil.NoSuchProcess:
                        pass
                    except psutil.AccessDenied:
                        print(f"Access denied to kill process {pid}. user manual intervention required.")
    except Exception as e:
        print(f"Error checking ports with psutil: {e}")

    if not killed:
        print(f"No process found listening on port {port}.")

if __name__ == "__main__":
    kill_process_on_port(8000)
    kill_process_on_port(8001)
