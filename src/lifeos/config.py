"""Config loader for lifeos. Non-secret settings only; secrets live in Keychain."""
from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "lifeos" / "config.toml"


class WeightsConfig(BaseModel):
    school: int = 40
    mentors: int = 30
    spiced: int = 20
    javvas: int = 20
    other: int = 5


class CanvasConfig(BaseModel):
    major_points_threshold: int = 100


class LearningSuiteConfig(BaseModel):
    courses: list[str] = Field(default_factory=list)


class GoogleConfig(BaseModel):
    accounts: list[str] = Field(default_factory=list)
    gcal_exclude: list[str] = Field(default_factory=list)
    calendar_domains: dict[str, str] = Field(default_factory=dict)


class ICloudConfig(BaseModel):
    calendars: list[str] = Field(default_factory=list)


class OutlookConfig(BaseModel):
    accounts: list[str] = Field(default_factory=lambda: ["personal", "byu"])


class SlackConfig(BaseModel):
    workspaces: dict[str, str] = Field(default_factory=dict)


class ShopifyConfig(BaseModel):
    stores: dict[str, str] = Field(default_factory=dict)
    order_sla_days: int = 2
    low_stock_threshold: int = 10


class RoutingConfig(BaseModel):
    senders: dict[str, str] = Field(default_factory=dict)
    sender_domains: dict[str, str] = Field(default_factory=dict)
    vip: list[str] = Field(default_factory=list)


class Config(BaseModel):
    vault: str = "~/LifeOS"
    timezone: str = "America/Denver"
    canvas_base_url: str = "https://<school>.instructure.com"

    weights: WeightsConfig = Field(default_factory=WeightsConfig)
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    learning_suite: LearningSuiteConfig = Field(default_factory=LearningSuiteConfig)
    google: GoogleConfig = Field(default_factory=GoogleConfig)
    icloud: ICloudConfig = Field(default_factory=ICloudConfig)
    outlook: OutlookConfig = Field(default_factory=OutlookConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    shopify: ShopifyConfig = Field(default_factory=ShopifyConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)

    @property
    def vault_path(self) -> Path:
        return Path(self.vault).expanduser()


def load_config(path: Path | None = None) -> Config:
    """Load config.toml. Returns defaults if the file doesn't exist yet."""
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return Config()
    with path.open("rb") as f:
        data = tomllib.load(f)
    return Config.model_validate(data)


def write_example_config(path: Path | None = None) -> Path:
    """Write the example config.toml from the spec skeleton, without overwriting an existing one."""
    path = path or DEFAULT_CONFIG_PATH
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(EXAMPLE_CONFIG_TOML)
    return path


EXAMPLE_CONFIG_TOML = """\
vault = "~/LifeOS"
timezone = "America/Denver"
canvas_base_url = "https://byu.instructure.com"

[weights]
school = 40
mentors = 30
spiced = 20
javvas = 20
other = 5

[canvas]
major_points_threshold = 100

[learning_suite]
courses = []                 # feed URLs live in Keychain as ls_feed:<COURSE>

[google]
accounts = []
gcal_exclude = []            # calendars that duplicate Learning Suite feeds
calendar_domains = {}        # "calendar id" = "domain"

[icloud]
calendars = []               # iCloud-native calendars only

[outlook]
accounts = ["personal", "byu"]

[slack]
workspaces = {}              # "workspace" = "domain"

[shopify]
stores = {}                  # spiced = "<store>.myshopify.com", javvas = "<store>.myshopify.com"
order_sla_days = 2
low_stock_threshold = 10

[routing]
senders = {}                 # exact address = domain (checked first)
sender_domains = {}          # "byu.edu" = "school"
vip = []                     # professors, TAs, Mentors leads
"""
