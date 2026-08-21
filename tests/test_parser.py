import pytest
from magicmodels.parser import Parser, SchemaSyntaxError

def test_valid_schema():
    parser = Parser()
    text = """
Model: User
- id (Int) [pk]
- username (String) [indexed]
- is_active (Boolean)
"""
    models = parser.parse(text)
    assert len(models) == 1
    assert models[0].name == "User"
    assert len(models[0].fields) == 3
    
    id_field = models[0].fields[0]
    assert id_field.name == "id"
    assert id_field.type == "Int"
    assert id_field.is_primary_key is True
    
    username_field = models[0].fields[1]
    assert username_field.name == "username"
    assert username_field.type == "String"
    assert username_field.is_indexed is True

def test_missing_model_prefix():
    parser = Parser()
    text = """
- name (String)
"""
    with pytest.raises(SchemaSyntaxError) as exc:
        parser.parse(text)
    assert "no 'Model:' was defined prior to this" in str(exc.value)

def test_invalid_field_syntax():
    parser = Parser()
    text = """
Model: User
- name String
"""
    with pytest.raises(SchemaSyntaxError) as exc:
        parser.parse(text)
    assert "Invalid field syntax" in str(exc.value)

def test_invalid_model_name():
    parser = Parser()
    text = """
Model: User Name
- name (String)
"""
    with pytest.raises(SchemaSyntaxError) as exc:
        parser.parse(text)
    assert "Invalid model name" in str(exc.value)
    
def test_empty_schema():
    parser = Parser()
    with pytest.raises(SchemaSyntaxError):
        parser.parse("")
