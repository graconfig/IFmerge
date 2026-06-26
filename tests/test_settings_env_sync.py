"""保存设置后,运行进程必须立即看到新值(无需重启)。

复现 bug:Settings.save() 只写 .env 文件,不刷新 os.environ;
而 ebs_merger.AIGenerator 通过 `param or os.getenv(...)` 回退读取 os.environ,
导致保存后到下次重启前,os.getenv 仍是启动时的旧值。
"""

import os

import pytest

from ifmerge_gui.config import settings as settings_mod
from ifmerge_gui.config.settings import Settings


@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    monkeypatch.setattr(settings_mod, "_ENV_PATH", env_path)
    for k in ("AICORE_AUTH_URL", "AICORE_CLIENT_ID", "AICORE_CLIENT_SECRET",
              "AICORE_BASE_URL", "AICORE_DEPLOYMENT_ID", "AICORE_MODEL_NAME"):
        monkeypatch.delenv(k, raising=False)
    return env_path


def test_save_syncs_os_environ(temp_env):
    """保存后 os.environ 应反映新值——AIGenerator 的 os.getenv 回退依赖它。"""
    s = Settings(
        aicore_auth_url="https://auth.example",
        aicore_client_id="cid",
        aicore_client_secret="sec",
        aicore_base_url="https://base.example",
        aicore_deployment_id="dep-123",
    )
    s.save()

    assert os.environ.get("AICORE_AUTH_URL") == "https://auth.example"
    assert os.environ.get("AICORE_BASE_URL") == "https://base.example"
    assert os.environ.get("AICORE_DEPLOYMENT_ID") == "dep-123"
