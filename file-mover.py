import argparse
import glob
import os
import re
import shutil
import yaml


class VariableBag():
    def __init__(self):
        pass

    def get(self, key: str, default=None) -> str:
        if key in os.environ:
            return os.environ[key]

        return default

    def set(self, key: str, value):
        os.environ[key] = value

    def substitute(self, input: str) -> str:
        result = input

        matches = re.finditer(r"\$\((\w+)\)", input)

        if matches is not None:
            for m in matches:
                source = m.group(0)
                variable_name = m.group(1)
                variable_value = self.get(variable_name)

                if variable_value is not None:
                    result = result.replace(source, variable_value)

        return result


def format_source_destination_string(source: str, destination: str) -> str:
    return "\"%s\" -> \"%s\"" % (source, destination)


DEFAULT_CONFIGURATION_FILE_NAME = "file-mover.config.yaml"

parser = argparse.ArgumentParser()

parser.add_argument("path", type=str, help="Input path")
parser.add_argument("--config", nargs="?", const=True,
                    default=f"./{DEFAULT_CONFIGURATION_FILE_NAME}")

args = parser.parse_args()

variable_bag = VariableBag()

# Read the configuration file
with open(args.config, "r") as f:
    configuration = yaml.load(f, Loader=yaml.FullLoader)

# Setup environment variables
for (n, v) in configuration["environment"].items():
    variable_bag.set(n, v)

# Get a list of all files in source path
files = glob.glob(args.path + "\\*")

# Stores info about source files and target destinations
queue = []

for i in configuration["rules"]:
    for f in files:
        found = False

        for rule in i["patterns"]:
            matches = re.search(rule, f)

            if matches is not None:
                found = True

                break

        if found is True:
            # Resolve the destination file name
            destination_file = os.path.join(variable_bag.substitute(
                i["destination"]), os.path.basename(f))

            queue.append({
                "source": f,
                "destination": destination_file
            })


# Show affected files list
for i in queue:
    print(format_source_destination_string(i["source"], i["destination"]))

print("\n")

confirmation = input("Confirm moving? (Y/n) ")

if confirmation.upper() == 'Y':
    for i in queue:
        source = i["source"]
        destination = i["destination"]

        print("Moving: " + format_source_destination_string(source, destination))

        try:
            shutil.move(source, destination)
        except Exception as e:
            print("[!] Failed to move %s: %s" % (source, e))
