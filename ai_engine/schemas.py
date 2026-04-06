from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScalingConfig(BaseModel):
    enabled: bool = True
    min_replicas: int = Field(default=2, ge=1, le=100)
    max_replicas: int = Field(default=10, ge=1, le=500)
    target_cpu_utilization: int = Field(default=70, ge=10, le=95)


class DeploymentConfig(BaseModel):
    cloud: Literal["aws", "azure", "gcp"] | None = None
    region: str | None = None
    app_type: Literal["node", "python", "java", "go"] | None = None
    repo_url: str | None = None
    app_source: str | None = None
    replicas: int = Field(default=2, ge=1, le=100)
    scaling: ScalingConfig = Field(default_factory=ScalingConfig)
