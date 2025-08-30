import os
import signal
import subprocess
import time

# Configurable parameters
command = ["poetry", "run", "-C", "/app/_hp", "python", "/app/wpt", "serve", "--config", "/app/_hp/wpt-config.json"]
restart_interval = 600  # Time in seconds before restarting
max_retries = 4  # Max number of restart attempts (in an row)

def run_with_restart():
    retries = 0

    while retries < max_retries:
        print(f"Attempt {retries + 1} of {max_retries}...")
        try:
            # Start the process in a new process group
            process = subprocess.Popen(
                command,
                preexec_fn=os.setsid  # Create a new process group
            )

            # Wait for the process to complete or timeout after the configured interval
            exit_code = process.wait(timeout=restart_interval)

            # Check if the exit code was an error (non-zero)
            if exit_code != 0:
                raise Exception(f"Process exited with error code {exit_code}")
            print(f"Process completed successfully with exit code {exit_code}. Restarting...")
            retries = 0  # Reset retry count after a successful run

        except subprocess.TimeoutExpired:
            print("Timeout reached. Sending SIGINT to process group...")
            # Send SIGINT to the entire process group
            os.killpg(os.getpgid(process.pid), signal.SIGINT)
            process.wait()  # Ensure the process fully terminates
            retries = 0 # Reset retry count afer a successful run (until timeout)

        except KeyboardInterrupt:
            print("Keyboard interrupt received. Sending SIGINT to process group...")
            # Send SIGINT to the entire process group in case of Ctrl+C
            os.killpg(os.getpgid(process.pid), signal.SIGINT)
            process.wait()  # Ensure the process terminates
            return

        except Exception as e:
            print(f"Error: {e}. Restarting in 10 seconds...")
            retries += 1
            if retries >= max_retries:
                print("Max restart attempts reached. Exiting.")
                break
            time.sleep(10)

if __name__ == "__main__":
    run_with_restart()
