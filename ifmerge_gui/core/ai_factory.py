"""用 GUI Settings 显式构造 ebs_merger 的 AIGenerator(使设置成为权威来源)。"""

from ebs_merger.ai_generator import AIGenerator

from ifmerge_gui.config.settings import Settings


def build_ai_generator(settings: Settings) -> AIGenerator:
    """根据 settings 构造 AIGenerator。

    deployment_id / model_name 为空时传 None:AIGenerator 会回退到
    环境变量 AICORE_DEPLOYMENT_ID,仍为空则抛 ValueError(由调用方捕获)。
    """
    return AIGenerator(
        auth_url=settings.aicore_auth_url or None,
        client_id=settings.aicore_client_id or None,
        client_secret=settings.aicore_client_secret or None,
        base_url=settings.aicore_base_url or None,
        resource_group=settings.aicore_resource_group or "default",
        deployment_id=settings.aicore_deployment_id or None,
        model_name=settings.aicore_model_name or None,
    )
