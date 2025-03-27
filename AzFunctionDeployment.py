import argparse
import subprocess
import sys
import os
import shutil
import zipfile
import json

try:
    from colorama import init
    init(autoreset=True)
except ImportError:
    pass

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"

def run_command(command, cwd=None):
    cmd_str = " ".join(command)
    print(f"{BLUE}Running command: {cmd_str}{RESET}")
    result = subprocess.run(cmd_str, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"{RED}Command failed: {cmd_str}{RESET}")
        sys.exit(result.returncode)

def zip_directory(folder_path, output_zip):
    print(f"{BLUE}Zipping directory {folder_path} to {output_zip}{RESET}")
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname=relative_path)
    print(f"{GREEN}Zipping complete.{RESET}")

def update_function_json_authlevel(publish_dir):
    print(f"{BLUE}Searching for function.json files in {publish_dir}{RESET}")
    for root, dirs, files in os.walk(publish_dir):
        if "function.json" in files:
            function_json_path = os.path.join(root, "function.json")
            print(f"{YELLOW}Found function.json at: {function_json_path}{RESET}")
            try:
                with open(function_json_path, "r") as f:
                    func_data = json.load(f)
                bool_updated = False
                if "bindings" in func_data:
                    for binding in func_data["bindings"]:
                        if binding.get("type", "").lower() == "httptrigger" and binding.get("authLevel", "").lower() != "anonymous":
                            print(f"{BLUE}Updating authLevel to anonymous for binding: {binding}{RESET}")
                            binding["authLevel"] = "anonymous"
                            bool_updated = True
                if bool_updated:
                    with open(function_json_path, "w") as f:
                        json.dump(func_data, f, indent=2)
                    print(f"{GREEN}Updated function.json authLevel to anonymous.{RESET}")
                else:
                    print(f"{YELLOW}No update needed in function.json (authLevel already anonymous).{RESET}")
            except Exception as e:
                print(f"{RED}Error updating function.json at {function_json_path}: {e}{RESET}")
                sys.exit(1)

def banner():
    print(r'''
                         _._
                          :.
                          : :
                          :  .
                         .:   :
                        : :    .
                       :  :     :
                      .   :      .
                     :    :       :
                    :     :        .
                   .      :         :
                  :       :          .
                 :        :           :
                .=w=w=w=w=:            .
                          :=w=w=w=w=w=w=.   ....
           <---._______:U~~~~~~~~\_________.:---/
            \      ____===================____/
.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.
"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"
"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"
    ''')

def copy_directory(source_dir, destination_dir, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = []
    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        if any(ex in rel_path.split(os.sep) for ex in exclude_dirs):
            continue
        dest_root = os.path.join(destination_dir, rel_path) if rel_path != "." else destination_dir
        os.makedirs(dest_root, exist_ok=True)
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            print(f"{BLUE}Copying file from {src_file} to {dest_file}{RESET}")
            shutil.copy2(src_file, dest_file)

def main():
    parser = argparse.ArgumentParser(
        description="Deploy a Windows C# Azure Function project."
    )
    parser.add_argument("--project-name", type=str, required=True,
                        help="Name for the Azure Functions project (e.g., MyFunctionApp)")
    parser.add_argument("--function-name", type=str, required=True,
                        help="Name for the new function (e.g., ForwardRequestFunction)")
    parser.add_argument("--functioncode", type=str, required=True,
                        help="Path to the C# function code file")
    parser.add_argument("--resource-group", type=str, required=True,
                        help="Azure Resource Group name (will be created if it doesn't exist)")
    parser.add_argument("--location", type=str, required=True,
                        help="Azure location for all resources (e.g., westus, eastus)")
    parser.add_argument("--functionapp", type=str, required=True,
                        help="Name of the Azure Function App (deployment target)")
    parser.add_argument("--storage-account", type=str, required=True,
                        help="Name of the Azure Storage Account (globally unique)")
    parser.add_argument("--newprefix", type=str, required=True,
                        help="New HTTP route prefix to use in host.json (e.g., 'wkl')")
    parser.add_argument("--base-dir", type=str, default=".",
                        help="Directory in which to create the project (default: current directory)")
    args = parser.parse_args()

    banner()

    # Check for required executables.
    for tool in ["az", "func"]:
        if not shutil.which(tool):
            print(f"{RED}Error: '{tool}' command not found. Please install and ensure it's in your PATH.{RESET}")
            sys.exit(1)
    if not shutil.which("dotnet"):
        print(f"{RED}Error: 'dotnet' command not found. Please install and ensure it's in your PATH.{RESET}")
        sys.exit(1)

    base_dir = os.path.abspath(args.base_dir)
    project_dir = os.path.join(base_dir, args.project_name)
    print(f"{BLUE}Project directory: {project_dir}{RESET}")

    # Project Initialization
    if not os.path.exists(project_dir):
        run_command(["func", "init", args.project_name, "--worker-runtime", "dotnet"], cwd=base_dir)
    else:
        print(f"{YELLOW}Project directory already exists; assuming it's already initialized.{RESET}")

    os.chdir(project_dir)

    # Create New Function
    function_file = os.path.join(project_dir, f"{args.function_name}.cs")
    if not os.path.exists(function_file):
        run_command(["func", "new", "--name", args.function_name, "--template", "\"HTTP trigger\"", "--authlevel", "anonymous"], cwd=project_dir)
    else:
        print(f"{YELLOW}Function file {function_file} already exists; it will be overwritten with your provided code.{RESET}")
    if not os.path.exists(args.functioncode):
        print(f"{RED}Error: The specified function code file does not exist: {args.functioncode}{RESET}")
        sys.exit(1)
    print(f"{BLUE}Copying file from {args.functioncode} to {function_file}{RESET}")
    shutil.copy2(args.functioncode, function_file)

    # Update host.json with new route prefix.
    host_json_path = os.path.join(project_dir, "host.json")
    host_data = {}
    if os.path.exists(host_json_path):
        try:
            host_data = json.loads(open(host_json_path, "r").read())
        except Exception as e:
            print(f"{RED}Error reading host.json: {e}{RESET}")
            sys.exit(1)
    else:
        host_data = {"version": "2.0"}
    if "extensions" not in host_data:
        host_data["extensions"] = {}
    if "http" not in host_data["extensions"] or host_data["extensions"]["http"] is None:
        host_data["extensions"]["http"] = {}
    host_data["extensions"]["http"]["routePrefix"] = args.newprefix
    try:
        with open(host_json_path, "w") as f:
            json.dump(host_data, f, indent=2)
        print(f"{GREEN}Updated host.json with routePrefix: {args.newprefix}{RESET}")
    except Exception as e:
        print(f"{RED}Error writing host.json: {e}{RESET}")
        sys.exit(1)

    # Build/Publish: C# project
    publish_dir = os.path.join(project_dir, "publish")
    run_command(["dotnet", "restore"], cwd=project_dir)
    run_command(["dotnet", "publish", "--configuration", "Release", "--output", "publish"], cwd=project_dir)
    zip_output = os.path.join(project_dir, "functionapp.zip")
    zip_directory(publish_dir, zip_output)

    # Azure Resource Creation and Deployment
    run_command(["az", "group", "create", "--name", args.resource_group, "--location", args.location])
    run_command(["az", "storage", "account", "create", "--name", args.storage_account, "--location", args.location,
                 "--resource-group", args.resource_group, "--sku", "Standard_LRS"])
    run_command([
        "az", "functionapp", "create",
        "--resource-group", args.resource_group,
        "--consumption-plan-location", args.location,
        "--runtime", "dotnet",
        "--functions-version", "4",
        "--name", args.functionapp,
        "--storage-account", args.storage_account
    ], cwd=project_dir)
    run_command(["az", "functionapp", "deployment", "source", "config-zip",
                 "--resource-group", args.resource_group,
                 "--name", args.functionapp,
                 "--src", zip_output], cwd=project_dir)

    print(f"{GREEN}Function deployment completed successfully.{RESET}")

if __name__ == "__main__":
    main()
