import re
from typing import List
from .schema import Model, Field

class SchemaSyntaxError(Exception):
    """Custom exception for schema parsing errors."""
    pass

class Parser:
    def parse(self, text: str) -> List[Model]:
        models = []
        current_model = None

        for line_number, line in enumerate(text.splitlines(), start=1):
            original_line = line
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse Model definition
            if line.startswith("Model:"):
                model_name = line.replace("Model:", "").strip()
                if not model_name or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", model_name):
                    raise SchemaSyntaxError(
                        f"Line {line_number}: Invalid model name '{model_name}'. "
                        "Model names must be valid alphanumeric strings."
                    )
                current_model = Model(name=model_name)
                models.append(current_model)
                
            # Parse Field definition
            elif line.startswith("-"):
                if current_model is None:
                    raise SchemaSyntaxError(
                        f"Line {line_number}: Found field definition '{line}' "
                        "but no 'Model:' was defined prior to this."
                    )
                
                # E.g., - name (string) [indexed]
                # E.g., - authors (list[Author])
                # We expect '- field_name (type)' as mandatory
                match = re.match(r"-\s*([\w_]+)(?:\s*\(([^)]+)\)|\s*:\s*([^\s]+))", line)
                if not match:
                    raise SchemaSyntaxError(
                        f"Line {line_number}: Invalid field syntax '{line}'. "
                        "Expected format: - field_name (type) [optional_modifiers] or - field_name: type [optional_modifiers]"
                    )
                    
                field_name = match.group(1)
                field_type = match.group(2) or match.group(3)
                
                # Check for modifiers like [pk] or [indexed]
                modifiers = line[match.end():].strip()
                is_pk = "[pk]" in modifiers.lower()
                is_indexed = "[indexed]" in modifiers.lower()
                
                # Note: The Normalizer will later handle converting 'list[Author]' into is_many_to_many, etc.
                # Here we just blindly pass the type and check for explicit modifiers.
                
                field = Field(name=field_name, type=field_type)
                
                # If explicit modifiers exist, we can tag them early.
                # Otherwise, normalizer handles relational types.
                if is_pk:
                    field.is_primary_key = True
                if is_indexed:
                    field.is_indexed = True
                    
                current_model.fields.append(field)
                
            else:
                # Unrecognized syntax - safely ignored (allows conversational plain text)
                continue
                
        if not models:
            raise SchemaSyntaxError("No valid 'Model:' definitions found in the schema file.")
            
        return models
