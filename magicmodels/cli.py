import argparse
import sys
import os
from .parser import Parser, SchemaSyntaxError
from .normalizer import Normalizer
from .generators.django import DjangoGenerator
from .generators.fastapi import FastAPIGenerator

def main():
    argparser = argparse.ArgumentParser(description="MagicModels CLI")
    argparser.add_argument("schema", help="Path to the schema.txt file")
    argparser.add_argument("--framework", choices=["django", "fastapi"], default="django", help="Framework to generate code for")
    argparser.add_argument("--output", default="./generated_api", help="Output directory for the generated project")
    
    args = argparser.parse_args()
    
    if not os.path.exists(args.schema):
        print(f"Error: Schema file '{args.schema}' not found.")
        sys.exit(1)
        
    with open(args.schema, 'r') as f:
        text = f.read()
        
    parser = Parser()
    try:
        models = parser.parse(text)
    except SchemaSyntaxError as e:
        print(f"❌ Syntax Error in '{args.schema}':")
        print(f"  {e}")
        sys.exit(1)
    
    normalizer = Normalizer()
    models = normalizer.normalize(models)
    
    if args.framework == "django":
        generator = DjangoGenerator()
    else:
        generator = FastAPIGenerator()
        
    print(f"Generating {args.framework.title()} project in {args.output}...")
    generator.generate(models, args.output)
    print("Done! ✅")
    
if __name__ == "__main__":
    main()
