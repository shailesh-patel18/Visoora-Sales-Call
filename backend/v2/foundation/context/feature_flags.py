from typing import Dict
from v2.foundation.context.middleware import get_platform_context
import structlog

logger = structlog.get_logger("feature_flags")

# Hardcoded for now. In prod, this would fetch from LaunchDarkly or Redis.
GLOBAL_FLAGS: Dict[str, bool] = {
    "WEBSITE_ANALYZER_V2_ENABLED": False,
    "SHADOW_MODE_WEBSITE_ANALYZER": True
}

class FeatureFlags:
    @staticmethod
    def is_enabled(flag_name: str) -> bool:
        """
        Checks if a feature flag is enabled for the current context.
        First checks tenant-specific overrides in PlatformContext, 
        then falls back to global flags.
        """
        ctx = get_platform_context()
        if ctx and flag_name in ctx.feature_flags:
            return ctx.feature_flags[flag_name]
            
        return GLOBAL_FLAGS.get(flag_name, False)
