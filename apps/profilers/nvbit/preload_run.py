import os
import sys
import argparse
import subprocess

def remove_ld_preload():
    print("Removing any existing LD_PRELOAD...")
    if "LD_PRELOAD" in os.environ:
        del os.environ["LD_PRELOAD"]
def set_ld_preload(tool_path):
    os.environ["LD_PRELOAD"] = tool_path
    print(f"LD_PRELOAD set to: {tool_path}")
def run_application(app_command):
    print("Running the application with the preloaded tool...")
    subprocess.run(app_command, shell=True)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Preload a tool with LD_PRELOAD and run an application.")
    parser.add_argument("-r", "--remove", action="store_true", help="Remove any existing LD_PRELOAD.")
    parser.add_argument("-a", "--add", metavar="TOOL", help="Add a tool to LD_PRELOAD.")
    parser.add_argument("-t", "--app", required=True, help="Application command to run.")
    
    # Parse the arguments
    args = parser.parse_args()

    # Handle the "remove" flag
    if args.remove:
        remove_ld_preload()

    # Handle the "add" flag
    if args.add:
        # Resolve the absolute path of the tool
        tool_path = os.path.abspath(args.add)
        
        # Check if the .so tool exists
        if not os.path.exists(tool_path):
            print(f"Error: The file {tool_path} does not exist.")
            sys.exit(1)
        
        # Set LD_PRELOAD to the resolved absolute path
        set_ld_preload(tool_path)

    # If neither flag is set, print an error
    if not args.remove and not args.add:
        print("Error: You must specify either --remove or --add <tool_path>.")
        sys.exit(1)

    # Run the application with the preloaded tool
    run_application(args.app)

if __name__ == "__main__":
    main()

