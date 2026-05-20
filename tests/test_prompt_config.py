import pytest
from ebs_merger.prompt_config import PromptConfig


def test_get_returns_none_when_file_not_found():
    config = PromptConfig("nonexistent_file_xyz.yaml")
    assert config.get("any_prompt", count=1, if_info_block="x") is None


def test_get_returns_none_when_prompt_key_missing(tmp_path):
    yaml_file = tmp_path / "prompts.yaml"
    yaml_file.write_text("other_key:\n  template: hello\n", encoding="utf-8")
    config = PromptConfig(str(yaml_file))
    assert config.get("missing_key") is None


def test_get_formats_template(tmp_path):
    yaml_file = tmp_path / "prompts.yaml"
    yaml_file.write_text(
        "my_prompt:\n  template: 'Count={count}, Block={if_info_block}'\n",
        encoding="utf-8",
    )
    config = PromptConfig(str(yaml_file))
    result = config.get("my_prompt", count=3, if_info_block="data")
    assert result == "Count=3, Block=data"


def test_get_returns_none_on_missing_placeholder(tmp_path):
    yaml_file = tmp_path / "prompts.yaml"
    yaml_file.write_text(
        "my_prompt:\n  template: 'Need {missing_key}'\n",
        encoding="utf-8",
    )
    config = PromptConfig(str(yaml_file))
    result = config.get("my_prompt", count=1)
    assert result is None


def test_get_returns_none_on_invalid_yaml(tmp_path):
    yaml_file = tmp_path / "prompts.yaml"
    yaml_file.write_text("key:\n  bad: : yaml:\n", encoding="utf-8")
    config = PromptConfig(str(yaml_file))
    assert config.get("key") is None


def test_get_returns_none_on_non_dict_entry(tmp_path):
    yaml_file = tmp_path / "prompts.yaml"
    yaml_file.write_text("my_prompt: accidentally_a_string\n", encoding="utf-8")
    config = PromptConfig(str(yaml_file))
    assert config.get("my_prompt") is None
