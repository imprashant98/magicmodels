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
                    related_name = field_type[5:-1]
                    if related_name in model_names:
                        field.is_many_to_many = True
                        field.related_model = related_name
                        field.type = "many_to_many"
                
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
                        
                if field.name.lower() == "id":
                    field.is_primary_key = True

        return models
