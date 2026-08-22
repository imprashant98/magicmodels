from typing import List
from .schema import Model

class Normalizer:
    def normalize(self, models: List[Model]) -> List[Model]:
        # Identify related models
        model_names = {m.name for m in models}
        
        for model in models:
            # Auto-add ID if not present
            has_id = any(f.name.lower() == 'id' for f in model.fields)
            if not has_id:
                from .schema import Field
                model.fields.insert(0, Field(name="id", type="int", is_primary_key=True))
                
            for field in model.fields:
                field_type = field.type
                
                # Check for Many-to-Many
                if field_type.startswith("list[") and field_type.endswith("]"):
                    related_name = field_type[5:-1].strip()
                    if related_name in model_names:
                        field.is_many_to_many = True
                        field.related_model = related_name
                        field.type = "many_to_many"
                    else:
                        raise ValueError(f"Model '{related_name}' referenced in '{model.name}.{field.name}' not found in schema.")
                
                # Check for Foreign Key
                elif field_type in model_names:
                    field.is_foreign_key = True
                    field.related_model = field_type
                    field.type = "foreign_key"
                    field.is_indexed = True # usually foreign keys are indexed
                    
                # Basic indexing
                elif field_type in ("string", "int", "boolean", "text", "datetime"):
                    if field.name.lower() in ("email", "username", "uuid") or field.name.endswith("_id"):
                        field.is_indexed = True
                
                # Catch invalid capitalized types that look like models
                elif field_type[0].isupper():
                    raise ValueError(f"Model '{field_type}' referenced in '{model.name}.{field.name}' not found in schema.")
                        
                if field.name.lower() == "id":
                    field.is_primary_key = True

        return models


class NormalizationChecker:
    def check(self, models: List[Model]) -> List[str]:
        warnings = []
        model_names = {m.name for m in models}
        
        # 1. Foreign key hints
        for model in models:
            for field in model.fields:
                if field.name.endswith("_id") and not field.is_foreign_key:
                    warnings.append(f"Model '{model.name}' has field '{field.name}' which looks like a foreign key but is not explicitly mapped to a model.")
        
        # 2. Redundant field groups (heuristics)
        # Check if multiple models have exact same subset of fields (e.g. address_line1, city, zip)
        all_fields = {}
        for model in models:
            all_fields[model.name] = {f.name for f in model.fields if f.name != "id"}
            
        model_list = list(models)
        for i in range(len(model_list)):
            for j in range(i + 1, len(model_list)):
                m1, m2 = model_list[i], model_list[j]
                common = all_fields[m1.name].intersection(all_fields[m2.name])
                if len(common) >= 3:
                    warnings.append(f"Models '{m1.name}' and '{m2.name}' share {len(common)} fields ({', '.join(common)}). Consider extracting these into a separate model (3NF).")
        
        # 3. Circular dependencies
        deps = {m.name: set() for m in models}
        for model in models:
            for field in model.fields:
                if field.is_foreign_key and field.related_model:
                    deps[model.name].add(field.related_model)
                    
        def has_cycle(node, visited, stack):
            visited.add(node)
            stack.add(node)
            for neighbor in deps.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, stack):
                        return True
                elif neighbor in stack:
                    return True
            stack.remove(node)
            return False
            
        for node in deps:
            if has_cycle(node, set(), set()):
                warnings.append(f"Circular dependency detected involving model '{node}'.")
                break
                
        return warnings
