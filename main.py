import argparse
from pathlib import Path

import DataStructures
import DatasetParser

parser = argparse.ArgumentParser(description="University timetabling solver")
parser.add_argument("--input", required=True, help="Path to the XML dataset")
args = parser.parse_args()

def main():
    print(f"Dataset name: {args.input}")
    file = Path(args.input)
    if (not file.is_file() or file.suffix != ".xml"):
        print(f"Invalid dataset file: {args.input}")
        return
    
    dataset = DatasetParser.Parse_Dataset(args.input)
    print(dataset.summary())

if __name__ == "__main__":
    main()
