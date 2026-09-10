"""Provider credential custody — EXCLUSIVE to the model gateway (MOD-001).

This module is the only place in the entire production tree that may read
provider credential configuration. The boundary gate
(``tests/model_gateway/test_boundary.py``) fails the build if any other
production module references provider credential material or provider SDKs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCredentials:
    profile_id: str
    base_url: str
    api_key: str | None
    protocol: str


def load_credentials(profile_id: str) -> ProviderCredentials:
    prefix = "QUAL_PROVIDER_" + profile_id.upper().replace("-", "_")
    base_url = os.environ.get(f"{prefix}_BASE_URL", "")
    if not base_url:
        raise KeyError(f"no credential configuration for provider profile {profile_id}")
    return ProviderCredentials(
        profile_id=profile_id,
        base_url=base_url,
        api_key=os.environ.get(f"{prefix}_API_KEY"),
        protocol=os.environ.get(f"{prefix}_PROTOCOL", "openai-chat"),
    )
